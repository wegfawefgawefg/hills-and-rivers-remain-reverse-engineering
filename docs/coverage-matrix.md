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
| Map-pack outer container | Big-endian version/count/offset table and 78 exact record ranges/hashes | Internal map records remain undecoded |
| Localization extraction | Both shipped encodings, all 282 tables and 6,894 locale/table/key/value records | Runtime lookup/fallback behavior is separate |
| Original Linux bootstrap | Reproducible touchHLE patch boots the ARMv7 original into a playable tutorial | Full-game compatibility is not proven |

## Incomplete data and content domains

| Domain | Status | What we know | Required next evidence |
| --- | --- | --- | --- |
| Other IPA versions/Lite build | Partial | 1.1.0 and Lite leads exist; only 2.0.0 bytes survive locally | Acquire, hash, and compare additional binaries |
| Map-record header | Partial | Marker and fixed width/height offsets are proven for all 78 records | Type the remaining fixed prefix and variable-section cursor |
| Terrain/tile grid | Not started | Map PVRs and map-related classes survive | Identify dimensions, cell encoding, and renderer lookup |
| Roads and graph topology | Not started | Runtime roads and pathfinding symbols survive | Decode node/edge records and validate paths |
| Bases and headquarters | Partial | Runtime behavior and named getters/mutators survive | Decode base records, types, ownership, production, and HQ rules |
| Player/general definitions | Partial | `General` and parameter symbols plus localized names survive | Recover record layout, statistics, and scenario assignment |
| Scenario event records | Partial | `LoadMapEvent` and named event checks survive | Locate event region and decode trigger records |
| Scenario command language | Partial | Rich named `Script::*` interpreter survives | Recover dispatch grammar, commands, operands, and control flow |
| Scenario-to-text linkage | Partial | Dialogue tables and likely key vocabulary are decoded | Prove how event operands select table/key entries |
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
| Core game-state layout | Not started | Many getters/mutators retain names | Recover types, arrays, invariants, and ownership |
| Turn sequencing | Partial | Tutorial description and `turnEnd` symbol | Exact phase order, timers, production, events, and cleanup |
| Soldier production/economy | Partial | HQ production observed; calculation symbols survive | Formulas, caps, modifiers, and timing |
| Troop movement | Partial | Command UI works; movement/path symbols survive | Dispatch rules, speed, merging, cancellation, and arrival |
| Pathfinding | Not started | `GetBasePath`, `GetArmyPath`, `IsPassable` | Graph algorithm, weights, restrictions, and tie-breaking |
| Combat and damage | Not started | `DamageCalculate` and `BattleFunc` | Complete formula, state transitions, timing, and edge cases |
| Base capture/control | Partial | Ownership mutations and flags are visible | Capture thresholds, contested states, and special-base behavior |
| Headquarters relocation | Partial | UI and `SetNewHead` are known | Preconditions, costs, timing, and AI use |
| Items and effects | Partial | Text/assets and named item/effect functions survive | Every item parameter, duration, target rule, and stacking rule |
| Special terrain/structures | Partial | Gold mine, fort, bombard, lava, cannon symbols survive | Decode parameters and all turn/battle effects |
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
