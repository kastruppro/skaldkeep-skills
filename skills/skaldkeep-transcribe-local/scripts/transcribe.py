#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests>=2.31,<3",
#   "PyYAML>=6.0.1,<7",
# ]
# ///
"""Shared RPG transcription CLI: legacy/updated recipes, local gain and resumable jobs."""
import argparse
import copy
import difflib
import hashlib
import json
import math
import os
from pathlib import Path
import re
import statistics
import sys

from jobs import atomic_write, cache_key, fingerprint, run_job, save_json, write_outputs

SCRIPT_DIR = Path(__file__).resolve().parent
# Bundled with the skill: only example.yaml. Real campaign profiles live in the user's
# config directory so a skill update never overwrites (or publishes) them.
BUNDLED_CAMPAIGNS_DIR = SCRIPT_DIR / 'campaigns'
CONFIG_SUFFIXES = ('.yaml', '.yml', '.json')
AUDIO_EXTENSIONS = {'.mp3', '.m4a', '.wav', '.ogg', '.oga', '.opus', '.flac', '.aac',
                    '.mp4', '.mov', '.webm', '.aiff', '.aif', '.wma', '.amr'}
DEFAULT_CONTEXT = (
    'A Dungeons and Dragons tabletop session with a dungeon master and players. '
    'The conversation includes fantasy names, rules, dice rolls, narration and in-character dialogue. '
    'The dungeon master performs several fictional voices.'
)


def default_campaign_dir():
    configured = os.environ.get('SKALDKEEP_TRANSCRIBE_CAMPAIGNS')
    if configured:
        return Path(configured).expanduser()
    base = Path(os.environ.get('XDG_CONFIG_HOME') or '~/.config').expanduser()
    return base / 'skaldkeep' / 'transcribe' / 'campaigns'


def default_output_dir():
    # Outside the skill and outside any project: transcripts are private campaign content.
    configured = os.environ.get('SKALDKEEP_TRANSCRIBE_OUTPUT')
    if configured:
        return Path(configured).expanduser()
    base = Path(os.environ.get('XDG_DATA_HOME') or '~/.local/share').expanduser()
    return base / 'skaldkeep' / 'transcribe'


def campaign_dirs(directory=None):
    return [Path(directory)] if directory else [default_campaign_dir(), BUNDLED_CAMPAIGNS_DIR]


def load_campaign(name, directory=None):
    candidate = Path(name).expanduser()
    if candidate.suffix.lower() in CONFIG_SUFFIXES:
        if not candidate.is_file():
            raise ValueError(f'Campaign file {name!r} not found.')
        path = candidate
    else:
        if not re.fullmatch(r'[A-Za-z0-9_-]+', name):
            raise ValueError('Campaign names may contain only letters, numbers, hyphens and underscores.')
        dirs = campaign_dirs(directory)
        path = next((d / f'{name}{ext}' for d in dirs for ext in CONFIG_SUFFIXES
                     if (d / f'{name}{ext}').is_file()), None)
        if path is None:
            raise ValueError(f"Campaign {name!r} not found in {', '.join(map(str, dirs))}.")
    if path.suffix == '.json':
        cfg = json.loads(path.read_text(encoding='utf-8'))
    else:
        import yaml
        cfg = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(cfg, dict):
        raise ValueError('Campaign configuration must be an object.')
    return cfg


def session_campaign(campaign, absent=(), speakers=None):
    cfg = copy.deepcopy(campaign)
    names = cfg.get('speaker_names', [])
    if not isinstance(names, list) or any(not isinstance(n, str) or not n.strip() for n in names):
        raise ValueError('speaker_names must be a list of nonempty participant labels.')
    if len({n.casefold() for n in names}) != len(names):
        raise ValueError('Participant labels must be unique.')
    aliases = {k.casefold(): v for k, v in cfg.get('speaker_aliases', {}).items()}
    absent_names = {aliases.get(n.casefold(), n).casefold() for n in absent}
    unknown = absent_names - {n.casefold() for n in names}
    if unknown:
        raise ValueError(f'Unknown absent participant: {sorted(unknown)}.')
    cfg['speaker_names'] = [n for n in names if n.casefold() not in absent_names]
    configured_count = cfg.get('speakers_expected', len(names))
    if isinstance(configured_count, bool) or not isinstance(configured_count, int):
        raise ValueError('speakers_expected must be a positive integer.')
    count = speakers if speakers is not None else configured_count - len(absent_names)
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError('At least one human speaker is required.')
    cfg['speakers_expected'] = count
    cfg['absent'] = sorted(absent_names)
    return cfg


def build_config(campaign, method='updated', *, identify=None, temperature=0, language=None):
    if isinstance(temperature, bool) or not math.isfinite(temperature) or not 0 <= temperature <= 1:
        raise ValueError('Temperature must be between 0 and 1.')
    cfg = {'speech_models': ['universal-3-5-pro'], 'temperature': temperature,
           'speaker_labels': True, 'speakers_expected': campaign['speakers_expected']}
    language = language or campaign.get('language_code', 'en_us')
    cfg.update({'language_detection': True} if language == 'auto' else {'language_code': language})
    if method == 'legacy':
        # Preserve the existing toolkit recipe, including historical identification syntax.
        cfg['custom_spelling'] = campaign.get('custom_spelling', [])
        cfg['prompt'] = campaign.get('prompt', '')
        if identify is not False:
            cfg['speech_understanding'] = {'request': {'speaker_identification': {
                'speaker_type': 'name', 'known_values': campaign['speaker_names'],
            }}}
    elif method == 'updated':
        cfg['prompt'] = campaign.get('context_prompt', DEFAULT_CONTEXT)
        terms = campaign.get('keyterms_prompt', [r['to'] for r in campaign.get('custom_spelling', [])])
        if not isinstance(terms, list) or any(not isinstance(t, str) or not t.strip() for t in terms):
            raise ValueError('keyterms_prompt must be a list of nonempty strings.')
        terms = list(dict.fromkeys(t.strip() for t in terms))
        if sum(len(t.split()) for t in terms) > 1000 or any(len(t.split()) > 6 for t in terms):
            raise ValueError('Keyterms exceed the documented word/phrase limits.')
        if terms:
            cfg['keyterms_prompt'] = terms
        # Recognition hints avoid replacing legitimate ordinary words after recognition.
        if campaign.get('updated_custom_spelling'):
            cfg['custom_spelling'] = campaign['updated_custom_spelling']
        if identify:
            metadata = campaign.get('speaker_metadata', {})
            cfg['speech_understanding'] = {'request': {'speaker_identification': {
                'speaker_type': 'name', 'speakers': [
                    {**metadata.get(name, {}), 'name': name} for name in campaign['speaker_names']
                ], 'effort': 'low',
            }}}
    else:
        raise ValueError('Unknown transcription method.')
    for rule in cfg.get('custom_spelling', []):
        if (not isinstance(rule.get('to'), str) or len(rule['to'].split()) != 1
                or not isinstance(rule.get('from'), list)
                or any(not isinstance(s, str) or not 1 <= len(s.split()) <= 5 for s in rule['from'])):
            raise ValueError('Invalid custom_spelling rule.')
    if not isinstance(cfg.get('prompt'), str):
        raise ValueError('Prompt must be a string.')
    return cfg


def resolve_audio_source(source):
    if source.startswith('https://'):
        return source
    path = Path(source).expanduser()
    if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS:
        raise ValueError('Provide an existing audio/video file or an HTTPS URL.')
    return str(path.resolve())


def hourly_cost(config):
    return (0.21 + 0.02 + (0.05 if config.get('prompt') else 0)
            + (0.05 if config.get('keyterms_prompt') else 0)
            + (0.02 if config.get('speech_understanding') else 0))


def metrics(result):
    words, utterances = result.get('words') or [], result.get('utterances') or []
    confidences = [w['confidence'] for w in words if isinstance(w.get('confidence'), (int, float))]
    return {'words': len(words), 'utterances': len(utterances),
            'speaker_labels': sorted({str(u.get('speaker')) for u in utterances}),
            'mean_word_confidence': statistics.mean(confidences) if confidences else None,
            'low_confidence_words': sum(c < 0.8 for c in confidences),
            'speech_model_used': result.get('speech_model_used'),
            'audio_duration_seconds': result.get('audio_duration')}


def comparison_report(runs, output, source_id):
    key = cache_key(source_id, {'runs': [r['config'] for r in runs],
                               'provenance': [r['provenance'] for r in runs]})[:16]
    report = Path(output) / f'comparison-{key}.md'
    lines = ['# Transcription comparison', '',
             'These are observations, not measured accuracy. Confidence and word count do not establish a winner.',
             'Listen to the same timestamps and check names, missing speech, invented words and speaker attribution.',
             '', '| Variant | Words | Speakers | Mean word confidence |', '|---|---:|---|---:|']
    for run in runs:
        stats = run['metrics']
        mean = stats['mean_word_confidence']
        confidence = f'{mean:.3f}' if mean is not None else 'n/a'
        lines.append(f"| {run['label']} | {stats['words']} | {', '.join(stats['speaker_labels'])} | {confidence} |")
    for run in runs:
        directory = Path(run['directory'])
        lines += ['', f"## {run['label']}", '', f'[Timestamped transcript]({directory}/transcript_timed.txt)',
                  f"[Original JSON]({run['result_path']})", '', '```json',
                  json.dumps(run['config'], indent=2, ensure_ascii=False), '```']
    if len(runs) == 2:
        first, second = (Path(r['directory']) / 'transcript_raw.txt' for r in runs)
        diff = difflib.unified_diff(first.read_text(encoding='utf-8').splitlines(),
                                    second.read_text(encoding='utf-8').splitlines(),
                                    fromfile=runs[0]['label'], tofile=runs[1]['label'], lineterm='')
        lines += ['', '## Text differences', '', '```diff', *diff, '```']
    atomic_write(report, '\n'.join(lines) + '\n')
    save_json(report.with_suffix('.json'), {'runs': runs, 'winner': None, 'ground_truth': None})
    return report


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio', nargs='?')
    p.add_argument('--campaign', default='example',
                   help='Profile name (searched in --campaign-dir) or a path to a .yaml/.json file')
    p.add_argument('--campaign-dir', type=Path,
                   help='Profile directory (default: $SKALDKEEP_TRANSCRIBE_CAMPAIGNS or '
                        '~/.config/skaldkeep/transcribe/campaigns, then the bundled examples)')
    p.add_argument('--output-dir', type=Path,
                   help='Job cache and transcripts (default: $SKALDKEEP_TRANSCRIBE_OUTPUT or '
                        '~/.local/share/skaldkeep/transcribe)')
    p.add_argument('--list-campaigns', action='store_true')
    p.add_argument('--method', choices=['legacy', 'updated'], default='updated')
    compare = p.add_mutually_exclusive_group()
    compare.add_argument('--compare-methods', action='store_true')
    compare.add_argument('--compare', action='store_true', help='Historical prompt/no-prompt comparison')
    p.add_argument('--speakers', type=int)
    p.add_argument('--absent', action='append', default=[])
    p.add_argument('--language', help='Language code, or auto for mixed-language recognition')
    p.add_argument('--temp', type=float, default=0)
    identify = p.add_mutually_exclusive_group()
    identify.add_argument('--identify', dest='identify', action='store_true')
    identify.add_argument('--no-identify', dest='identify', action='store_false')
    p.set_defaults(identify=None)
    p.add_argument('--analyze', action='store_true', help='Local measurement only; no API calls')
    p.add_argument('--start', type=float, default=0, help='Excerpt start in source seconds')
    p.add_argument('--duration', type=float, help='Excerpt length in seconds (local files only)')
    level = p.add_mutually_exclusive_group()
    level.add_argument('--gain-db', type=float, default=0, help='Explicit gain in a lossless copy')
    level.add_argument('--normalize', action='store_true', help='Two-pass loudness normalization to -20 LUFS / -2 dBTP')
    p.add_argument('--dry-run', action='store_true', help='Validate and show plan without network calls')
    p.add_argument('--max-cost-usd', type=float, default=2, help='Planned-run cost cap (default $2)')
    p.add_argument('--url-version', help='Immutable content version/checksum for an HTTPS source')
    p.add_argument('--source-duration', type=float, help='Total seconds for an HTTPS source; needed for cost guard')
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    if args.list_campaigns:
        lines = []
        for directory in campaign_dirs(args.campaign_dir):
            names = sorted({p.stem for p in directory.glob('*') if p.suffix in CONFIG_SUFFIXES})
            lines += [f'  - {name}  ({directory})' for name in names]
        print('Available campaigns:\n' + '\n'.join(lines))
        return 0
    if args.output_dir is None:
        args.output_dir = default_output_dir()
    if not args.audio:
        raise ValueError('An audio file or HTTPS URL is required.')
    for name in ('start', 'gain_db', 'max_cost_usd', 'duration', 'source_duration'):
        value = getattr(args, name)
        if value is not None and not math.isfinite(value):
            raise ValueError(f"--{name.replace('_', '-')} must be finite.")
    if args.start < 0 or args.max_cost_usd <= 0 or (args.duration is not None and args.duration <= 0):
        raise ValueError('Invalid start, duration or cost limit.')
    source = resolve_audio_source(args.audio)
    local = not source.startswith('https://')
    if local:
        from audio_tools import measure, prepare, probe
        info = probe(source)
        total_duration = info['duration_seconds']
        if args.start >= total_duration or (args.duration is not None and args.start + args.duration > total_duration + 0.1):
            raise ValueError('Requested excerpt lies outside the recording.')
        if args.analyze:
            print(json.dumps({**info, **measure(source, args.start, args.duration)}, indent=2))
            return 0
    else:
        if args.analyze or args.start or args.duration is not None or args.gain_db or args.normalize:
            raise ValueError('Download audio locally before measuring, cropping or changing gain.')
        if not args.url_version or not args.source_duration or args.source_duration <= 0:
            raise ValueError('HTTPS requires --url-version and --source-duration for safe caching/cost estimation.')
        total_duration = args.source_duration
    campaign = session_campaign(load_campaign(args.campaign, args.campaign_dir), args.absent, args.speakers)
    methods = ['legacy', 'updated'] if args.compare_methods else [args.method]
    variants = [(m, build_config(campaign, m, identify=args.identify, temperature=args.temp,
                                 language=args.language)) for m in methods]
    if args.compare:
        base = variants[0][1]
        variants = [('with-prompt', base), ('without-prompt', {k: v for k, v in base.items() if k != 'prompt'})]
    duration = args.duration or total_duration - args.start
    estimate = sum(hourly_cost(c) * duration / 3600 for _, c in variants)
    plan = {'campaign': args.campaign, 'speakers': campaign['speakers_expected'],
            'absent': campaign['absent'], 'duration_seconds': duration, 'gain_db': args.gain_db,
            'normalize': args.normalize,
            'estimated_max_usd': round(estimate, 4), 'variants': dict(variants),
            'note': 'Legacy uses the existing recipe on the same U3.5 model; no retired U3 model is requested.'}
    print(json.dumps(plan, indent=2, ensure_ascii=False))
    if estimate > args.max_cost_usd:
        raise ValueError(f'Planned ${estimate:.2f} exceeds --max-cost-usd {args.max_cost_usd:.2f}.')
    if args.dry_run:
        return 0
    source_id = fingerprint(source) if local else hashlib.sha256(f'{source}\n{args.url_version}'.encode()).hexdigest()
    provenance = {'original_source_id': source_id, 'source_offset_seconds': args.start,
                  'duration_seconds': duration, 'source': args.audio}
    if local and (args.start or args.duration is not None or args.gain_db or args.normalize):
        source, _ = prepare(source, args.output_dir, start=args.start, duration=args.duration,
                            gain_db=args.gain_db, normalize=args.normalize)
        source = str(source)
        source_id = fingerprint(source)
    runs = []
    for label, config in variants:
        result, job_directory = run_job(source, source_id, config, args.output_dir)
        # A reused audio job may come from identical clips at different offsets.
        # Keep each source timeline separate without buying another transcript.
        view_key = cache_key(source_id, provenance)[:16]
        directory = job_directory / 'views' / view_key
        write_outputs(result, directory, offset_seconds=args.start)
        run = {'label': label, 'directory': str(directory.resolve()), 'config': config,
               'result_path': str((job_directory / 'result.json').resolve()),
               'provenance': provenance,
               'metrics': metrics(result), 'source_offset_seconds': args.start,
               'estimated_usd': hourly_cost(config) * duration / 3600}
        save_json(directory / 'run-summary.json', run)
        runs.append(run)
        print(f"{label}: {directory / 'transcript_timed.txt'}")
    if len(runs) > 1:
        print(f'Comparison: {comparison_report(runs, args.output_dir, source_id)}')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Exception, KeyboardInterrupt) as exc:
        message = 'Interrupted; job state preserved.' if isinstance(exc, KeyboardInterrupt) else str(exc)
        print(f'Error: {message}', file=sys.stderr)
        sys.exit(1)
