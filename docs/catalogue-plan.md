# Full catalogue plan

The project aims for a complete, evidence-backed understanding of the shipped
game. It does not aim to reproduce the original executable byte for byte. The
future implementation may use different code and architecture as long as the
catalogue explains the original rules, content, presentation, and behavior.

## Work products

1. **Artifact ledger** — every known IPA/build, provenance, hashes, metadata,
   architecture, encryption state, and relationships between duplicate files.
2. **Mechanical binary index** — all slices, sections, imports, symbols,
   compilation units, Objective-C metadata, strings, constants, and addresses.
3. **Semantic binary map** — recovered types, call graph, global state, data
   structures, ownership, subsystem boundaries, and pseudocode with confidence.
4. **Content catalogue** — every asset and data record, decoded format, semantic
   identity, consumers, variants, and visual/audio preview where useful.
5. **Behavior catalogue** — original-game recordings and traces for screens,
   state transitions, controls, timings, rules, AI decisions, saves, and edge
   cases.
6. **Reimplementation specification** — clean interfaces and tests derived from
   the catalogues, without requiring source-level or binary equivalence.

## Analysis order

The ARMv6 slice is the canonical static-analysis target because Ghidra imports it
cleanly and it contains the same rich symbol set as ARMv7. ARMv7 remains a second
independent reference and is the execution target in touchHLE. Differences
between slices must be measured rather than assumed away.

Initial subsystem order:

| Area | First anchors | Desired result |
| --- | --- | --- |
| Startup | `main`, `shogunAppDelegate`, `EAGLView` | lifecycle and root state graph |
| Main loop | `EAGLView::drawView`, update symbols | tick ordering and timing model |
| Rendering | OpenGL ES imports, texture classes | coordinate, batching, effects |
| Input | touch and accelerometer selectors | gestures and input-state machine |
| Scenario/map | `Scenario`, `Map`, loader object files | complete schemas and decoding |
| Units/battle | unit, action and animation types | rules, formulas, state transitions |
| AI | AI compilation units and callers | decision tree and parameters |
| Save/progress | filesystem calls and `DATA` paths | file format and progression flags |
| Audio | OpenAL/AudioToolbox callers | cue table, streaming and mixing behavior |
| Network/IAP | Reachability and StoreKit code | isolate optional/dead online behavior |
| Localization | `.lproj`, strings and locale code | text IDs, language fallback behavior |

## Definition of understood

A component is complete only when we can connect:

- shipped bytes or metadata;
- the code that loads or acts on them;
- the runtime behavior they produce; and
- a testable plain-language description suitable for reimplementation.

Unknown fields, unreachable branches, unused assets, and contradictory evidence
remain explicit catalogue entries. They are not silently discarded.
