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
| Map/scenario records | 78 | Exact record boundaries; internal schema pending |
| Localization tables | 282 | Fully decoded binary-plist/OpenStep dictionaries |
| Localized strings | 6,894 | Stable locale/table/key identity and text |
| YAS animations | 139 | Confirmed header/version; field semantics pending |
| YAS-referenced assets | 93 | Unique directly resolved texture files |

The catalogue contains 12,633 relationships. These include pack containment,
cross-language alignment, 19 byte-identical map-record links, and 129 resolved
YAS-to-texture references. Consumer links connect every map pack and YAS file to
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
`FileManager::ReadBuffPackData`. `Script::LoadMapEvent(std::string const&, int)`
is the strongest next anchor for locating event data inside each record. The
scarcity of readable text in the DAT files, combined with the separate
localization tables, indicates a compact binary map/event representation rather
than source-like scripts.

## Next decoding pass

1. Decompile `ReadBuffPackData`, `LoadMapData`, and `LoadMapEvent` into typed
   readers and record every cursor advance.
2. Split map records into header, terrain, bases, players, events, and script
   payloads only when consumer code proves the boundaries.
3. Recover command opcodes and argument grammar from `Script::ScriptFunc` and
   its named handlers.
4. Cross-reference text operands with locale table/key identities and validate
   them against tutorial execution.
5. Decode `yas::Animation::open` and derive a complete animation timeline schema.
6. Turn recovered rules into small executable specifications and compare their
   results against touchHLE traces.

This is the level required for a clean reimplementation: not merely knowing
that a function or file exists, but knowing which shipped bytes represent a
scenario, how the original interprets them, and what observable behavior they
produce.
