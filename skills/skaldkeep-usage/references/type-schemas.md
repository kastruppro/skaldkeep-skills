# Document type schemas (frontmatter conventions)

Snapshot of the Skaldkeep server's per-type schemas (the same source as `get_type_schema` and
`GET /api/document-types`), checked 2026-11-07 against server 0.4.0. Frontmatter is free-form: these keys are
conventions the UI understands, not a closed schema, and unknown keys are kept. Always call
`get_type_schema(type)` on the connected server before the first write of a type - it wins
whenever it differs from this file.

## Conventions that apply to every type

- Bodies are markdown. Link other documents with [[slug]] or [[slug|label]]; targets are document slugs (lowercase, hyphenated). Links to documents that don't exist yet are fine - they become 'wanted pages'.
- frontmatter is free-form YAML/JSON; the keys below are conventions the UI understands, not a closed schema. Unknown keys are kept verbatim.
- aliases: list of alternative names for link resolution and search.
- tags: list of free-form tags.
- portrait: every type has a picture field (uploaded image filename shown as the page's picture - portrait or illustration). Since 0.3.1 it is also the page's half-transparent backdrop and its thumbnail in every overview, so pick an image that reads well small and large (subject centred). Set it with `set_document_image`. Since 0.4.0 a page without `portrait` uses the first image embedded in its body (never one from `dm_notes`), and a session's picture is also the default cover of its recaps.
- dm_notes is a SEPARATE field (not frontmatter), never visible to players; reading or writing it requires the access_dm_notes capability (the DM's alone - a scribe never sees it).
- visibility: 'player' (default), 'dm_only' (hidden from players entirely; requires write_dm_content) or 'personal' (private to the author and their chosen audience; requires write_own_notes and cannot change later).

## `session` - One play session: what happened at the table, chronologically.

| key | hint | values |
|-----|------|--------|
| `session` | session number (finite number; decimals such as 2.5 or 2,5 allowed) |  |
| `date` | real-world date the session was PLAYED, YYYY-MM-DD; the site shows this instead of the last-edited date, so always set it |  |
| `party` | list of PC slugs who were present |  |
| `npcs` | list of NPC slugs that appeared |  |
| `locations` | list of location slugs visited |  |
| `items_acquired` | list of loot slugs gained this session |  |
| `status` | completed \| upcoming |  |

Facets: status. Badges: -.

- Structure the body with H2 sections (## Summary, ## Events, ## Important Quotes, ...) - the UI builds section navigation from them.
- After writing the session, create a campaign snapshot named after it (e.g. 'After Session 24') so players can diff what changed.

## `npc` - A non-player character.

| key | hint | values |
|-----|------|--------|
| `race` | e.g. human, harengon |  |
| `gender` | their gender |  |
| `role` | what they are in the story, e.g. blacksmith, cult leader |  |
| `prominence` | story importance | `central` \| `recurring` \| `cameo` |
| `status` | alive \| dead \| missing \| unknown |  |
| `relationship` | stance toward the party: ally \| enemy \| neutral |  |
| `location` | slug of where they usually are |  |
| `faction` | slug of their faction, if any |  |
| `family` | family/house name or slug, if relevant |  |
| `first_met` | session number or YYYY-MM-DD |  |
| `last_seen` | session number or YYYY-MM-DD |  |
| `portrait` | uploaded image filename shown as this page's picture (portrait or illustration); set it with `set_document_image` |  |

Facets: prominence, location, faction, family, status, relationship, race. Badges: faction, location.

- location/faction values should be document slugs so filters and links stay connected.

## `location` - A place: city, dungeon, building, plane.

| key | hint | values |
|-----|------|--------|
| `region` | optional label; when empty the region is derived from the top ancestor in the location tree |  |
| `location_type` | city \| village \| dungeon \| building \| landmark \| plane |  |
| `status` | active \| destroyed \| abandoned \| unknown |  |
| `parent_location` | **slug** (or alias) of the containing location - builds the location tree (any depth: region > city > district > building, or planes/areas). Never a title: a title resolves to nothing and the place becomes a root. |  |
| `first_visited` | session number or YYYY-MM-DD |  |
| `last_visited` | session number or YYYY-MM-DD |  |
| `map_x` | campaign-map pin, horizontal fraction 0.0-1.0 |  |
| `map_y` | campaign-map pin, vertical fraction 0.0-1.0 |  |

Facets: region, location_type, status. Badges: region, location_type.

- map_x/map_y are 0-1 fractions of the campaign map image; the map view sets them when you drop or drag a pin.

## `quest` - A quest or plot thread the party can pursue.

| key | hint | values |
|-----|------|--------|
| `quest_type` | classification | `main` \| `side` \| `personal` |
| `character` | for personal quests: the PC slug the quest belongs to |  |
| `parent_quest` | slug of the main quest this quest is a subquest of (one level deep: a main quest never has a parent_quest itself) |  |
| `status` | available \| active \| paused \| completed \| failed \| abandoned (paused = on hold, e.g. because its PC is away; a terminal completed/failed/abandoned is never auto-changed) | `available` \| `active` \| `paused` \| `completed` \| `failed` \| `abandoned` |
| `priority` | urgency | `critical` \| `high` \| `medium` \| `low` |
| `quest_giver` | NPC slug (or name) who gave the quest |  |
| `location` | location slug (or name) where the quest currently leads |  |
| `next_step` | short, actionable next step for the party |  |
| `deadline` | in-world or real-world deadline, preferably YYYY-MM-DD |  |
| `progress_current` | completed objective count (integer) |  |
| `progress_total` | total objective count (integer) |  |
| `started` | session number or YYYY-MM-DD |  |
| `completed` | session number or YYYY-MM-DD |  |

Facets: quest_type, status, priority, character. Badges: quest_type, status, character. Card fields: parent_quest, next_step, deadline, progress_current, progress_total, quest_giver, location.

- subquests carry parent_quest: <quest-slug> of a top-level quest; the hierarchy is one level deep.
- personal quests carry both quest_type: personal AND character: <pc-slug>.

## `loot` - An item, stack, container or campaign possession. Importance controls whether it is presented as a full chronicle entry or a compact inventory row.

| key | hint | values |
|-----|------|--------|
| `rarity` | D&D rarity | `common` \| `uncommon` \| `rare` \| `very rare` \| `legendary` \| `artifact` |
| `item_type` | physical form of the item | `weapon` \| `armor` \| `wondrous_item` \| `potion` \| `scroll` \| `book` \| `treasure` \| `currency` \| `material` \| `consumable` \| `container` \| `mundane` \| `other` |
| `item_role` | narrative role, separate from physical item_type | `quest` \| `personal` \| `party` \| `lore` \| `ordinary` |
| `importance` | presentation weight: featured card, standard card or compact row | `featured` \| `standard` \| `minor` |
| `attunement` | true/false or the attunement requirement text |  |
| `attuned_to` | PC slug currently attuned to the item |  |
| `owner` | PC/NPC/faction slug the item belongs to |  |
| `holder` | PC/NPC/faction slug currently carrying the item |  |
| `location` | location slug where the item is stored or left |  |
| `container` | loot-container slug holding this item |  |
| `status` | current lifecycle state (inactive = still owned and held, but out of play, e.g. its holder's PC is paused or it only works on a plane the party cannot reach; hidden from the default loot views) | `carried` \| `stored` \| `lent` \| `missing` \| `consumed` \| `sold` \| `destroyed` \| `returned` \| `inactive` |
| `quantity` | stack count (non-negative integer; 0 when consumed) |  |
| `charges` | remaining charges or uses |  |
| `charges_max` | maximum charges or uses |  |
| `related_quest` | quest slug this item advances or unlocks |  |
| `acquired` | session number or YYYY-MM-DD |  |
| `origin` | where it came from |  |

Facets: rarity, item_role, item_type, status, importance, holder, location, attunement. Badges: rarity, item_role, holder.

- owner, holder, location, container, attuned_to and related_quest MUST be document slugs (not display names) so the UI can resolve and link them.
- Do not use visibility: personal to mean personally owned equipment. Use item_role: personal plus owner: <pc-slug>; visibility remains an access rule.
- A container is itself a loot document with item_type: container. Minor items inside it use container: <container-slug> and importance: minor.
- Use holder for custody, owner for ownership, location for storage, and attuned_to for attunement; these concepts must not be collapsed together.

## `faction` - An organisation: guild, cult, noble house, pantheon.

| key | hint | values |
|-----|------|--------|
| `type` | guild \| cult \| noble house \| order \| gang \| pantheon |  |
| `alignment` | moral stance, e.g. LG ... CE or friendly/hostile |  |
| `relationship` | stance toward the party: ally \| enemy \| neutral |  |
| `status` | active \| disbanded \| destroyed \| unknown |  |
| `location` | slug of their base of operations |  |

Facets: type, alignment, relationship, status. Badges: type, relationship.

## `pc` - A player character.

| key | hint | values |
|-----|------|--------|
| `race` | e.g. harengon |  |
| `class` | class and subclass, e.g. Chronurgy Wizard |  |
| `player` | the real player's name |  |
| `status` | active \| paused \| retired \| dead (paused = temporarily out of the campaign but expected back; retired = left for good; both keep the document, only hide it from active rosters) |  |
| `conditions` | list of current status effects, e.g. [cursed, poisoned] |  |
| `curses` | list of long-running curses/afflictions, a short label each |  |
| `abilities` | list of special abilities/boons worth surfacing |  |

Facets: status. Badges: class.

- The player dashboard renders conditions/curses/abilities as chips: keep each entry a SHORT string (details belong in the body) and update them when processing a session so the dashboard stays current.
- Loot held by this PC is found via the loot documents' holder field (this PC's slug) - don't duplicate an inventory here.

## `companion` - A companion bound to one character: familiar, beast companion, steed, mount or pet.

| key | hint | values |
|-----|------|--------|
| `owner` | **slug** of the PC this companion belongs to (never a display name, so renames and merges follow) |  |
| `kind` | what sort of companion it is | `familiar` \| `beast_companion` \| `steed` \| `mount` \| `pet` \| `other` |
| `ruleset` | rules edition the statblock follows; unset shows both | `dnd5e-2014` \| `dnd5e-2024` |
| `template` | source template, e.g. `srd52-owl` (info only) |  |
| `summary` | one or two sentences shown on the character page |  |
| `statblock` | object with size, creature_type, alignment, ac, ac_note, hp, hp_dice, speed (text, e.g. '10 ft., fly 60 ft.'), abilities (str, dex, con, int, wis, cha as integers), saves, skills, senses, languages, cr, traits and actions (lists of {name, text}) and optionally reactions |  |
| `portrait` | uploaded image filename shown as this page's picture; set it with `set_document_image` |  |

Facets: kind, ruleset, owner. Badges: kind.

- Create companions with `add_companion` (copies an SRD template from `list_companion_templates`, or a blank one); edit them with the normal document tools.
- The statblock is validated on write: it must be an object, ability scores integers 1-30, traits/actions/reactions lists of at most 50 `{name, text}` entries. Unknown keys survive.
- A companion takes its PC's visibility; one of a `dm_only` PC is hidden from players.
- The campaign setting `ruleset` (`dnd5e-2014` / `dnd5e-2024` / unset) picks the default edition for templates; `get_my_access` and `list_campaigns` report it.

## `note` - Anything that fits no other type: lore, rules, handouts.

| key | hint | values |
|-----|------|--------|
| `session` | session SLUG this note belongs to, if any (personal session notes surface in the My-notes panel on that session) |  |

Facets: session. Badges: -.

- Player notes are notes with visibility 'personal': private to the author and their chosen audience (the DM and/or selected players).
