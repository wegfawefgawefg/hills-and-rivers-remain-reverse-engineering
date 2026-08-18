# Research log

Use dated UTC entries. Preserve exact URLs, query terms, archive item names, and
negative results so searches are reproducible and do not needlessly repeat.

## 2026-08-14 — Repository initialized

- Created the private project scaffold.
- Seeded two reported filename leads in the variant ledger.
- No IPA has yet been acquired or analyzed in this repository.

## 2026-08-14 — First artifact acquired

- Found Archive.org items `HillsAndRiversRemain`, `Over700iOSGames`, and
  `Hills_and_Rivers_Remain_2.0.0_ios_3.0`.
- Their file metadata identifies the same byte-for-byte 2.0.0 IPA, so only one
  preserved copy was downloaded.
- Confirmed ARMv6 and ARMv7 slices and `cryptid 0` in both.
- Confirmed that local symbols survive and extracted 152 original object names.
- Indexed the current Grand IPA Archive/AppDrop catalogue (roughly 157,000
  version entries). It contains only this same 2.0.0 artifact for the bundle ID.
- Confirmed the Lite App Store ID as `338528080`; no Lite IPA appeared in that
  catalogue or Archive.org metadata search.
- Confirmed the 1.1.0 scene filename in a January 2010 IPA-pack index. Its ten
  RapidShare parts are no longer available and produced no usable Wayback
  captures in this pass.

## 2026-08-14 — Static and Linux execution baseline

- Installed Ghidra 12.1.2 with OpenJDK 21 and completed headless analysis of
  separate ARMv6 and ARMv7 programs in the ignored `hrr-2.0.0` project.
- Built touchHLE commit `331903de883405a8597036e4ed5ce8333f1604c9`
  locally on x86-64 Linux.
- The stock emulator reached game initialization but stopped at missing
  Reachability scheduling and region-qualified `NSLocale` behavior.
- Added three narrow compatibility shims and preserved them as a standalone
  patch. The original ARMv7 executable then reached the English title screen,
  initialized audio, and remained stable at approximately 30 FPS for the
  30-second test window.
- Added a normalized SQLite catalogue schema and builder. The first generated
  catalogue indexes 2 slices, 48 sections, 28 library references, 12,210 symbol
  records, 10 Objective-C classes, 216 methods, 88 fields, 152 object files, and
  2,342 non-executable bundle files.
- Navigated the running original through Start Game, the tutorial choice, and
  into the first playable tutorial map. Confirmed live map rendering, dialogue,
  base selection, and the Move Troops, Relocate HQ, and Items command UI without
  encountering another emulator compatibility failure.

## 2026-08-14 — Functional content catalogue baseline

- Adopted stable content identities, exact source ranges/hashes, typed
  relationships, confidence, and independent extracted/linked/understood/
  presented coverage flags.
- Decoded four big-endian indexed map containers into 78 exact records and
  linked them to `MapData::readPackData` in both ARM slices. Nineteen records
  are byte-identical across packs.
- Decoded 282 localization tables into 6,894 entries across five languages,
  preserving both binary-plist and legacy UTF-8 OpenStep encodings.
- Indexed 139 version-1 YAS animation files, recorded their raw header words,
  and resolved 129 direct texture references to 93 unique assets.
- Identified the named `Script` scenario interpreter as the next primary RE
  target. Its surviving methods cover branching, conditions, event triggers,
  base/map mutation, dialogue, effects, audio, flags, and endings.
- Began the first matrix-driven RE loop at `MapData::LoadMapData`. Confirmed the
  record marker and fixed width/height offsets for all 78 records; observed
  dimensions from 15×15 through 30×30. Recorded the loader's probable
  two-16-bit-plane cursor calculation without yet claiming plane semantics.

## 2026-08-17 — Map and gameplay-core reconstruction

- Reconstructed every cursor advance in `MapData::LoadMapData` and
  `Script::LoadMapEvent`; the strict parser consumes every byte of all 78 map
  records with no remainder.
- Extracted 2,628 active route/base nodes, 156 legacy cell planes, 720 Shift-JIS
  labels, 4,212 nonempty embedded text slots, 659 events, and 17,119 commands.
- Recovered the complete 14-byte authored base record, graph directions, port
  gates, all base types, item IDs, and paired item parameters.
- Recovered the `BASE_DATA` and `ARMY_DATA` runtime layouts and the core troop
  dispatch, backward BFS, edge timing, progress, chaining, and arrival paths.
- Recovered owned-base production, castle combat and stable speed bonuses,
  three-turn gold-mine behavior, five-turn fort construction, soldier caps,
  and the three exact 12-general parameter maps.
- Recovered combat pulse trial counts, alliance-weighted scores, timed-item
  modifiers, casualty probability/allocation, elimination, and capture paths.
- Corrected movement documentation from a fresh `SetArmySpeed` audit: each
  stable contributes 100 through `GetUpParam`; the separate 200 increase is the
  timed Speed-up item. Confirmed combat pulses occur at attack-animation
  completion and simultaneous elimination resolves for the defender.
- Confirmed `GetScale` chooses small/medium/large army visuals solely at 0–9,
  10–29, and 30+ soldiers; horses are the Stable speed concept, not a cavalry
  class. Defined the internal sally transition and recovered cannon target
  selection, turn scheduling, random bombardment, and nonlethal garrison floor.
- Added a reproducible JSON map exporter and rebuilt the local catalogue to
  32,984 functional/content entries and 38,127 typed relationships for build
  `hrr-2.0.0`.
