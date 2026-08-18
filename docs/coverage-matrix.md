# Reverse-engineering coverage matrix

This is the project's completion ledger for the decrypted 2.0.0 build. A narrow
domain is `complete` only when all applicable shipped data is catalogued, its
structure and consumer code are understood, its behavior is validated against
the original, and the result is captured in a reproducible parser, note, or
test. Finding a filename or surviving symbol is evidence, not completion.

Status vocabulary:

- **Complete** — complete for the known 2.0.0 artifact at the stated scope.
- **Partial** — useful evidence exists, but at least one completion gate is open.
- **Not started** — inventory anchors may exist, but no substantive RE is done.
- **Blocked** — a named external dependency currently prevents progress.

## Complete at the stated scope

| Domain | What is complete | Boundary of the claim |
| --- | --- | --- |
| 2.0.0 artifact integrity | Original filename, provenance, byte size, SHA-256, read-only preservation, and extracted bundle | Does not cover missing releases |
| Bundle metadata | `Info.plist`, bundle/version/build IDs, executable name, minimum OS, and bundle tree | Known artifact only |
| Mach-O packaging | ARMv6/ARMv7 slices, hashes, sections, load commands, linked libraries, and `cryptid = 0` | Does not imply function semantics |
| Mechanical symbol index | 12,210 per-slice symbol records, Objective-C metadata, imports, and 152 object-file names | Names and addresses only |
| File-level resource inventory | Every non-executable bundle file has path, extension, size, and SHA-256 | Assets are not all semantically classified |
| Map-pack and record structure | Four indexed containers, 78 exact records, and byte-complete parsing into bases, cell planes, labels, text, events, and commands | Event/command semantics remain separate |
| Localization extraction | Both shipped encodings, all 282 tables and 6,894 locale/table/key/value records | Runtime lookup/fallback behavior is separate |
| Original Linux bootstrap | Reproducible touchHLE patch boots the ARMv7 original into a playable tutorial | Full-game compatibility is not proven |

## Incomplete data and content domains

| Domain | Status | What we know | Required next evidence |
| --- | --- | --- | --- |
| Other IPA versions/Lite build | Partial | 1.1.0 and Lite leads exist; only 2.0.0 bytes survive locally | Acquire, hash, and compare additional binaries |
| Map regulation fields | Partial | Full section boundaries, dimensions, two flags, and every trailing structure are proven | Type bytes `0x001..0x01e` and flags at `0x599..0x59a` |
| Terrain/tile grid | Partial | Two exact 2-byte-per-cell planes are catalogued; this loader only skips them | Determine historical purpose and live renderer/texture layout |
| Roads and graph topology | Partial | All 2,628 active nodes, directional edges, port gates, coordinates, and BFS are decoded | Differentially validate representative/tied paths |
| Bases and headquarters | Partial | All base records/types/owners/garrisons plus production and timed fort/mine rules are decoded | HQ relocation and all capture/battle edge cases |
| Player/general definitions | Partial | Localized IDs and exact item/escape/active tables for 12 generals | Remaining statistics, AI meaning, and scenario assignment |
| Scenario event records | Partial | All 659 event boundaries and 30-byte headers are extracted | Type every trigger/header field |
| Scenario command language | Partial | Rich named `Script::*` interpreter survives | Recover dispatch grammar, commands, operands, and control flow |
| Scenario-to-text linkage | Partial | 720 labels and 4,212 embedded Shift-JIS text slots are decoded | Prove command operands select slots and locale overrides |
| `stage.dat` | Not started | 420-byte standalone DAT file | Locate its consumer and derive record layout |
| YAS animation body | Partial | Magic, version, header words, texture names, and loader are known | Decompile `yas::Animation::open`; decode frames and timing |
| PNG assets | Partial | All files and hashes are known | Record dimensions, roles, atlases, consumers, and duplicates |
| PVR textures | Partial | All files and hashes are known; `PVRLoader` survives | Decode metadata/pixels, map texture roles, and upload path |
| NIB and property-list UI data | Partial | Files are inventoried and standard formats are readable | Catalogue objects/keys and connect them to runtime screens |
| Audio files | Partial | 30 WAV and 10 M4A files are preserved and directly playable | Map cues, loop points, volume rules, and callsites |
| Content variants/locales | Partial | Cross-locale string identities are linked | Explain locale-specific image/YAS differences and fallback |

## Incomplete engine and behavior domains

| Domain | Status | Current anchor | Completion requirement |
| --- | --- | --- | --- |
| Objective-C lifecycle shell | Partial | App delegate and `EAGLView` metadata | Full startup/shutdown/state ownership description |
| Manager/main loop | Partial | `Manager::init/update/draw`, observed ~30 FPS | Exact update order, time step, pauses, and frame pacing |
| Scene/state machine | Partial | Named Title/Menu/Story/Free/Game/Result scenes | Complete transition graph and state ownership |
| Renderer | Partial | OpenGL ES imports and named graphics/texture classes | Coordinate systems, batching, blend modes, layers, and effects |
| Input and gestures | Partial | Touch reaches tutorial; movement/HQ UI observed | Exact tap/hold/drag/pinch state machine and thresholds |
| Camera/map scrolling | Partial | Runtime scrolling and named script/camera functions | Bounds, interpolation, zoom, and scripted movement |
| Core game-state layout | Partial | `BASE_DATA` (`0xb4`), `ARMY_DATA` (`0x38`), arrays and primary fields recovered | Finish `STATE_DATA`, transient battle/item/UI state |
| Turn sequencing | Partial | Tutorial description and `turnEnd` symbol | Exact phase order, timers, production, events, and cleanup |
| Soldier production/economy | Partial | Exact owned-node/castle/stable table, turn formula, mine multiplier, and caps | Item/script modifiers and runtime differential tests |
| Troop movement | Partial | Packet layout, dispatch, edge timing, pass-through traffic, directed-edge occupancy, arrival reinforcement, third-side waiting, and chaining recovered | Cancellation edge cases and differential tests |
| Pathfinding | Partial | Backward unweighted BFS, ownership/union blocking, port gates, and tie order recovered | Differential tests across shipped graph edge cases |
| Combat and damage | Partial | Exact trial count, alliance-weighted scores, item multipliers, kill probability, casualty allocation, defender-wins-ties elimination, and animation-driven pulses recovered | Exact attack-YAS frame duration, sally edge cases, and differential tests |
| Base capture/control | Partial | Attacker/owner contest fields, elimination, ownership transfer, minimum garrisons, drop/capture events recovered | Sally edge cases, all scripted consequences, and differential tests |
| Headquarters relocation | Partial | UI and `SetNewHead` are known | Preconditions, costs, timing, and AI use |
| Items and effects | Partial | All 30 IDs/grades, durations, caps, targeting, combat modifiers, bomb fractions, draft amounts, Field HQ turns, and authored drop slots recovered | Teleport edge cases and runtime tests |
| Special terrain/structures | Partial | Stable/port gates, five-turn fort, three-turn mine, plus cannon targeting, timing, and nonlethal floor | Exact bombard loss arithmetic, bridge, lava, and hidden-base rules |
| AI | Not started | Numerous semantically named AI functions survive | Decision order, scoring, difficulty parameters, and tie-breaking |
| Victory/defeat | Partial | Script endings and win-info symbols survive | All conditions, precedence, results, rewards, and transitions |
| Story/free/tutorial progression | Partial | Modes, maps, text, and first tutorial are accessible | Unlock graph, scenario ordering, completion flags, and endings |
| Save/suspend/config formats | Not started | Save-related symbols and paths survive | Byte schemas, checksums/versioning, defaults, and round trips |
| Audio engine behavior | Partial | Original initializes audio; engine symbols survive | Cue dispatch, channel policy, fades, looping, and interruptions |
| Networking | Not started | Network/session/event-handler symbols survive | Protocol, state machine, and whether servers are required |
| StoreKit/downloadable content | Not started | Product/BuyMap/AddScenario symbols survive | Product mapping, entitlement gates, and shipped-content behavior |
| Full runtime compatibility | Partial | Title and early tutorial run stably | Exercise every mode, scenario, save path, input, and ending |
| Clean native reimplementation | Not started | Architecture direction is documented | Implement decoded content and rules with differential tests |

## The working loop

Repeat this loop in dependency order until every applicable row is complete:

1. Select the highest-leverage incomplete domain and name a bounded question.
2. Identify exact source bytes, symbols, addresses, and runtime observations.
3. Decompile the smallest consumer path that can answer the question.
4. Encode the result as a strict parser, typed schema, formula, or state machine.
5. Cross-link content records to their consumers and resulting behavior.
6. Validate representative and edge cases against the running original.
7. Add automated checks and update this matrix without overstating certainty.

The immediate dependency chain is map-record header → scenario event records →
scenario command language → text linkage. In parallel, YAS can be decoded from
its loader because it is largely independent of gameplay-state recovery.
