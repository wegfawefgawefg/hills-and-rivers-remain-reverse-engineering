# Functional catalogue baseline

The initial database was an inventory, not a reconstruction specification. It
proved what survived, but it did not identify authored records or connect them
to the code that consumes them. The functional catalogue closes that gap one
format and subsystem at a time.

The method follows the useful parts of the local Phantom Crash and Adventures
with Chickens projects: stable original identities, exact byte provenance,
typed relationships, explicit confidence, and a clean separation between
immutable authored content and future mutable play state. Hills and Rivers
Remain does not target byte-identical recompilation. The eventual implementation
should express recovered rules plainly and validate its behavior against the
running original.

## Generated coverage for 2.0.0

| Kind | Entries | Current meaning |
| --- | ---: | --- |
| Indexed map packs | 4 | Confirmed container boundaries and loader |
| Map/scenario records | 78 | Exact boundaries and complete structural parse |
| Active route/base nodes | 2,628 | Typed graph node, owner, garrison, edges, route gates, and item slots |
| Legacy cell planes | 156 | Exact two-plane boundaries and hashes; live meaning unresolved |
| Embedded map labels | 720 | Decoded Shift-JIS label slots |
| Embedded map text | 4,212 | Nonempty entries from each record's 256-slot text table |
| Scenario events | 659 | Exact 30-byte header and command-list boundaries |
| Scenario commands | 17,119 | Exact opcode, payload length, bytes, and source offset |
| Localization tables | 282 | Fully decoded binary-plist/OpenStep dictionaries |
| Localized strings | 6,894 | Stable locale/table/key identity and text |
| YAS animations | 139 | Confirmed header/version; field semantics pending |
| YAS-referenced assets | 93 | Unique directly resolved texture files |

The 2.0.0 catalogue contains 38,127 relationships. These include pack and
record containment, cross-language alignment, byte-identical map-record links,
and resolved YAS-to-texture references. Consumer links connect every map pack and YAS file to
the corresponding surviving loader symbol in both ARM slices.

## Scenario engine evidence

The executable is unusually cooperative for this work. It retains named C++
symbols for a substantial `Script` interpreter, including:

- flow: `entryScript`, `gotoScript`, `randomGotoScript`, `ifScript`,
  `ConditionCheck`, `yesNoScript`, and timers;
- triggers: `CheckTimerEvent`, `CheckExtraEvent`, `CheckAreaEvent`,
  `CheckBaseEvent`, `EventCheck`, and `EventDataInit`;
- world mutation: `mapWriteScript`, `mapFillScript`, `setBaseTypeScript`,
  `setBaseUserScript`, `setBaseSoldierScript`, and `baseChainScript`;
- presentation: messages, fades, tones, map scrolling, effects, BGM, and sound;
- progression: flags, expressions, items, win information, and game endings.

`MapData::readPackData(int) const` loads the indexed DAT containers through
`FileManager::ReadBuffPackData`. `MapData::LoadMapData` and
`Script::LoadMapEvent(std::string const&, int)` now account for every byte in
all 78 records. Story dialogue is not solely in localization tables: every map
also carries 256 big-endian-length Shift-JIS text slots and a small Shift-JIS
label table. The remaining scenario work is semantic opcode and trigger typing,
not boundary discovery.

## Next decoding pass

1. Recover command opcodes and argument grammar from `Script::ScriptFunc` and
   its named handlers.
2. Type all 30 event-trigger header bytes through the event checkers.
3. Cross-reference text operands with embedded/localized text and validate
   them against tutorial execution.
4. Decode `yas::Animation::open` and derive a complete animation timeline schema.
5. Turn recovered rules into small executable specifications and compare their
   results against touchHLE traces.

This is the level required for a clean reimplementation: not merely knowing
that a function or file exists, but knowing which shipped bytes represent a
scenario, how the original interprets them, and what observable behavior they
produce.
