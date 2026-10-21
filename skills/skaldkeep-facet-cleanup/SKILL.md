---
name: skaldkeep-facet-cleanup
description: >-
  Tidy inconsistent filter values across a Skaldkeep campaign: one spelling per
  NPC location, faction, loot holder, quest status and so on, so the app's
  filters and badges group correctly. Use when the user says things like "the
  location filter is a mess", "clean up the NPC factions", "merge Mistvale and
  mistvale", "normalize the facets", "ryd op i filtrene", "saml stavemåderne" or
  "why are there two filters for the same place". Drives Skaldkeep's MCP tools
  list_facet_values and normalize_facet_values: inventory, agreed mapping, dry run
  first, then an atomic change that stages for the DM's review by default. Not for
  rewriting document bodies or renaming slugs (use rename_document for that).
license: MIT
---

# Skaldkeep facet cleanup

Skaldkeep's overview filters and badges are built from frontmatter fields (an NPC's
`location`, `faction`, `status`; a loot item's `holder`; a quest's `status`, ...). Over many
sessions the same value drifts into several spellings - `mistvale` and `Mistvale`,
`Harrowgate (docks area)` instead of the `harrowgate` slug - and the filter splits. This
skill merges them in one reviewable, atomic change.

## Step 1 - Confirm access and pick the type

Call `get_my_access(campaign_slug=<ref>)` first. Reading needs `read_player_content`;
applying needs `write_player_content`. Hidden (`dm_only`) documents are only included when
the token can see them, so a co-DM token cleans more than a player token.

Ask which document type to clean if the user did not say (`npc`, `location`, `quest`,
`loot`, `faction`, `pc`, `session`, `note`). `get_type_schema(type)` lists the type's facet
fields and their allowed values.

## Step 2 - Take the inventory

```
list_facet_values(campaign_slug=<ref>, type="npc")
list_facet_values(campaign_slug=<ref>, type="npc", fields=["location", "faction"])
```

`fields` defaults to the type's facet and badge fields; any frontmatter key works. For each
field you get every value with its count and the documents holding it, a **suggested
mapping**, and - for slug-reference fields (location, faction, holder, ...) - the
`unresolved_slug_values` that match no document. Values from pending drafts are included
(`in_pending_draft`), because that is the base the normalizer patches.

## Step 3 - Agree on the mapping with the user

Show the suggestions as a short table per field: current value, proposed value, how many
documents. Suggestions are proposals, not decisions:

- A qualifier such as `Harrowgate (in disguise)` may be information that belongs in the
  body - say so and let the user decide before mapping it away.
- An unresolved slug value may be a page that should exist rather than a typo; offer to
  leave it, or to create the page first with `upsert_document`.
- `null` as the new value removes the field from those documents. Only propose it when the
  user wants the value gone.

Never apply a mapping the user has not seen.

## Step 4 - Dry run, then apply

```
normalize_facet_values(campaign_slug=<ref>, type="npc", field="location",
                       mapping={"Mistvale": "mistvale", "Harrowgate (docks area)": "harrowgate"},
                       dry_run=true)
```

Show the dry-run changes (which documents, before and after). On the user's go-ahead, run
the same call without `dry_run`. It is one atomic call per field (at most 200 documents; any
error rolls the whole call back). Values match exactly after trimming; list fields such as
a session's `locations` are rewritten per element and de-duplicated. Bodies, titles,
visibility and `dm_notes` are never touched.

**Stage, don't publish.** The default stages every change into one review batch; pass a
stable `batch_label` (e.g. `"Facet cleanup"`) so all fields of one cleanup land together.
Pass `publish=true` only when the user explicitly wants the live documents changed now.

## Step 5 - Report

Call `list_staging(campaign_slug=<ref>)` and tell the user which documents wait in the batch
and that the DM publishes it in the web app's **Review** tab. Re-run `list_facet_values` to
confirm each field now has one spelling per value.

## Rules

- One field per `normalize_facet_values` call; run several calls under the same
  `batch_label` for a multi-field cleanup.
- Never change slugs here - a document's own slug is renamed with `rename_document`, which
  also rewrites every `[[link]]`.
- Respect scope: if `get_my_access` says hidden documents are out of scope, say the cleanup
  covers only what this token can see.
- Plain hyphens (no em/en-dashes) in anything you write.
