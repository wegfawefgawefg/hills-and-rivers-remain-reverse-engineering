# Recovered gameplay core

This note records behavior proven from the decrypted ARMv6 executable. It is a
working reconstruction, not a claim that combat, AI, and every item are already
complete. Addresses refer to the 2.0.0 ARMv6 slice.

## Runtime records

`BASE_DATA` is `0xb4` bytes and the game owns exactly 100 records. The important
fields recovered so far are:

| Offset | Meaning |
| ---: | --- |
| `0x00` | base/route type |
| `0x04` | owner (`-1` neutral, `0..3` factions) |
| `0x08..0x14` | soldiers belonging to factions 0..3 |
| `0x18` | neutral soldiers |
| `0x1c` | attacking/contesting faction, `-1` outside battle |
| `0x24` | fort/gold-mine turn counter |
| `0x28` | cannon-related target/link |
| `0x34..0x40` | up/down/left/right neighbor indices |
| `0x44..0x50` | route requirement per direction |
| `0x54..0x60` | per-direction in-flight faction bitmasks |
| `0x64,+0x68,+0x6c` | three item IDs |
| `0x70,+0x74,+0x78` | parameter paired with each item ID |
| `0x7c,+0x80` | 10x10 matrix coordinate |
| `0x84,+0x88` | world-space position |
| `0x8c..0x9c` | displayed/current soldier totals for factions 0..3 and neutral |
| `0xa0..0xb0` | soldiers committed to dispatch for factions 0..3 and neutral |

`ARMY_DATA` is `0x38` bytes and the game owns exactly 30 records. It represents
a moving troop packet, not a different soldier class:

| Offset | Meaning |
| ---: | --- |
| `0x00` | faction, `-1` means unused |
| `0x04` | final multi-hop destination, `-1` for a single edge |
| `0x08` | soldier count |
| `0x0c` | source node |
| `0x10` | outgoing direction at source |
| `0x14` | next node |
| `0x18` | incoming direction at next node |
| `0x1c` | movement progress tick |
| `0x20` | edge duration in ticks |
| `0x24` | animation/path transition threshold |
| `0x28..0x30` | auxiliary targeting/state, reset on a new edge |
| `0x34` | current visual facing/direction |

This explains the apparent lack of conventional unit types: gameplay troops
are integer-sized packets modified by faction/general, base, and item state.
`GetScale` (`0xf12c`) selects only three presentation sizes from the packet's
soldier count: small for 0–9, medium for 10–29, and large for 30 or more. The
corresponding `heisi_s`, `heisi_m`, and `heisi_l` assets are visual variants,
not soldier classes. Capturing the base translated as Stable (Japanese `馬`,
literally “horse”) changes the faction-wide speed parameter; it does not turn
packets into a separately stored cavalry unit.

## Graph movement and routing

`Scene::Game::IsPassable` (`0x11b08`) checks a node's selected neighbor. A
requirement of 0 is open. Requirement 1 is open only when the moving faction's
owned-base counter for type 3 (Port) is positive. Missing/unused neighbors and
other requirement values are blocked.

`GetBasePath` (`0x1267c`) performs an unweighted breadth-first search backward
from the requested destination. Its 100-entry distance array blocks unused
nodes and, for multi-hop routing, nodes owned by a non-allied faction. The
destination is explicitly admitted. A 100-entry circular FIFO is used; neighbor
order is up, down, left, right, which is also the deterministic tie-break order.
It returns the direction of the first hop from the current node, or `-1` when
no path exists.

`SetArmyMove` (`0x23af8`) resolves the selected edge, records both direction
indices, clears edge-local state, calculates speed, marks the source edge's
faction bit, subtracts the packet from the source garrison, and clears that
faction's committed-dispatch count.

`BattleFunc` (`0x2fe9c`) advances each active packet's progress once per update.
It calls `ArmyArrival` after progress exceeds duration. Arrival either:

- starts battle when the destination owner is hostile;
- joins a friendly/allied garrison;
- joins an already contested side when allied;
- pauses at the battle boundary when neither side is allied; or
- computes and launches the next BFS hop toward a stored final destination.

The source direction's in-flight bit is cleared as the packet leaves that edge.

## Edge duration

`SetArmySpeed` (`0x2275c`) measures the Euclidean distance between direction-
specific endpoints at the source and destination. Let `d` be the integer
distance. The speed parameter is `GetUpParam(faction, 2)`, plus 200 while the
faction's timed Speed-up item state is active:

```text
base_ticks = floor((400*d + 31200) / 192)
speed = 100 + 100 * owned_stables
if Speed-up is active: speed += 200
duration = max(3, floor(base_ticks * 100 / speed))
transition = max(1, floor(duration * 39 / (d + 78)))
```

Recalculation preserves fractional progress as
`new_progress = old_progress * new_duration / old_duration`. The endpoint
offset table still needs symbolic names, but the timing arithmetic and state
transitions are recovered.

## Base bonuses, production, and strength

`GetUpParam` (`0x19a08`) starts production at 0 and combat/speed at 100, then
adds this table for every owned node:

| Runtime type | Production | Combat | Speed |
| ---: | ---: | ---: | ---: |
| route (0) | 50 | 0 | 0 |
| castle (1) | 50 | 50 | 0 |
| stable (2) | 50 | 0 | 100 |
| port/cannon/fort/gold-mine (3..7) | 50 | 0 | 0 |

At turn end (`0x1e178`), a faction's headquarters receives:

```text
base_recruits = floor(production / 100) + 3
recruits = floor(base_recruits * (active_gold_mines + 2) / 2)
```

Thus every two owned nodes add one recruit (integer rounding), and each active
gold mine multiplies production by another 50%. A temporary Field HQ receives
the same amount while its effect is active. `AddSoldier` caps the faction-wide
total at 999; one game mode additionally caps the selected base plus its
departing packet at 100.

`GetSolPow` (`0x19aa4`) computes the effective strength of a soldier count:

```text
combat = 100 + 50 * owned_castles
factor = floor(combat * 100 / (combat + 100))
strength = floor(2 * soldiers * factor / 100)
```

With no castle, strength equals the raw soldier count.

## Combat and capture

`DamageCalculate` (`0x2eea8`) resolves one combat pulse at a contested base. It
first totals all five resident soldier buckets (four factions plus neutral) and
chooses this many casualty trials for each side:

```text
trials = min(max(5, floor(all_resident_soldiers / 10)), attackers, defenders)
```

The attacker is the faction stored at `BASE_DATA + 0x1c`; the defender is the
owner at `+0x04`, or the neutral bucket. Each side starts with separate attack
and defense scores equal to:

```text
side_score = side_soldiers * GetUnionParam(base, faction, combat)
```

`GetUnionParam` (`0x1a308`) averages the faction's `GetUpParam` combat value
with the combat values of allied factions that currently have soldiers in the
base. This makes allied troops participate in both the side total and its
castle-derived modifier. Neutral defenders use a modifier of 100.

The active timed-item states then modify scores in this exact order:

- Battle adds 100 to both the attack and defense score;
- Offense multiplies the resulting attack score by 3; and
- Defense multiplies the resulting defense score by 3.

For each side `s`, the probability that one trial kills one of its soldiers is:

```text
kill_percent[s] = floor(
    opponent_attack * 100 / (opponent_attack + own_defense)
)
casualties[s] = count(Random(100) < kill_percent[s], repeated trials times)
```

Casualties are apportioned across the side's faction buckets in proportion to
their pre-pulse soldier totals, using integer division. Any rounding remainder
is removed from the principal faction's bucket. When an allied participant's
proportional loss would reduce its bucket to zero while that side still
survives, the routine restores one soldier; this preserves the participant
until the side itself is eliminated.

If the attackers reach zero, contest state is cleared and a defender/neutral
garrison is clamped to at least one. This check runs before defender elimination,
so simultaneous elimination is explicitly a defender win. If only the defenders
reach zero, the attacker becomes the owner, receives any eligible one-time item
drop, capture events run, and the new owner's garrison is clamped to at least
one. The same routine has a special branch for a packet that sallies from a base
and later folds that packet back into the ownership/capture result.

`BattleFunc` calls `DamageCalculate` whenever the base's three-part attack YAS
animation reports completion, then recreates and replays the animation if both
sides remain. Thus the combat pulse cadence is animation-driven rather than a
fixed combat timer in `DamageCalculate`. The mathematical state transition is
recovered; the exact YAS frame duration and every sally edge case still need
runtime differential tests.

“Sally” here is the original symbol name in `IsSallyBase`; it is not a special
unit or player command. It covers the brief overlap in which a dispatched army
packet is still associated with its source/base state while battle or cannon
damage is being reconciled. The edge cases concern avoiding duplicated or lost
soldiers if that packet is damaged or its base changes hands during the
transition.

## Timed special bases

- An occupied fort (type 5) advances its counter at each turn end and becomes a
  castle (type 1) after five turns (`turnEndFort`, `0x1c7f0`). Recapture resets
  the counter.
- An occupied active gold mine (type 6) contributes its 50% production bonus
  for three turn ends, then becomes spent runtime type 7
  (`turnEndGoldMine`, `0x1c5a4`).
- Capturing or losing a stable immediately recalculates every relevant moving
  packet's duration while preserving its progress ratio.

## Cannons and reinforcements

A cannon is authored base type 4, not a movable unit. The shipped help text says
an occupied cannon fires on enemy-occupied bases within two matrix squares in a
cardinal direction and never fires on neutral bases. `GetBombardTarget`
(`0x10d54`) constructs the eligible list and randomly selects a target;
`turnEndBombard` (`0x1dd3c`) schedules the shot, and `BombardFunc` (`0x1cabc`)
applies probabilistic losses but clamps the target garrison to at least one.
Consequently cannon fire weakens bases but cannot capture one by itself.

“Reinforcement” has two meanings, neither of them a unit class. Normal army
packets can arrive while a base is already contested and join their faction or
allied side. Scenarios can also inject additional generic soldiers after a turn
condition—the localized Free Mode text explicitly announces such timed
reinforcements. The remaining work is exact cannon casualty arithmetic and
typing each scenario command that creates scripted reinforcements.

## Items and grades

The 30 item IDs are ten effects in three grades. `effect = id % 10` and
`grade = floor(id / 10)`, where grades 0, 1, and 2 are the un-suffixed, A, and S
localized variants. `Scene::Game::UseItem` is at `0x229b0`.

| Effect | IDs | Recovered behavior by grade 0 / A / S |
| --- | --- | --- |
| Speed-up | 0/10/20 | faction effect timer +600 / +900 / +1200 update ticks, capped at 1800; adds 200 to the movement speed parameter and immediately retimes all moving packets |
| Battle | 1/11/21 | faction effect timer +600 / +900 / +1200, capped at 1800 |
| Offense | 2/12/22 | faction effect timer +600 / +900 / +1200, capped at 1800 |
| Defense | 3/13/23 | faction effect timer +600 / +900 / +1200, capped at 1800 |
| Hold | 4/14/24 | applies 450 / 600 / 750 ticks to every hostile, non-allied faction, capped at 900 |
| Shield | 5/15/25 | adds 900 / 1200 / 1500 shield ticks to the selected owned base, capped at 1800 |
| Teleporter | 6/16/26 | moves a selected troop packet from an owned source to an owned/allied or eligible neutral destination; requires more than one soldier at the source |
| Bomb | 7/17/27 | targets a non-owned, non-allied base; removes one-half / three-quarters / all troops from every side there, but leaves an owning garrison at a minimum of one |
| Field HQ | 8/18/28 | designates a second owned, non-primary HQ for 3 / 4 / 5 turn ends; it receives the normal HQ recruit amount |
| Draft | 9/19/29 | immediately adds 10 / 15 / 20 troops to the selected owned base |

Battle, Offense, and Defense feed the combat scores exactly as described above.
Hold and the first four timed faction effects are stored in
`STATE_DATA + 0x3c`; selected-use counters are at `+0x84`.

Each authored base record has three item IDs and three unsigned threshold
values. `ItemDrop` (`0x161dc`) tries them in order using separate random draws in
the range passed as `0xff`; the first draw below its paired threshold wins. A
base can drop only once, and the winning item goes to the first free one of five
inventory slots belonging to the battle victor. The catalogue exports both the
localized item name and raw threshold for every active map node.

## General parameter tables

The binary contains three explicit maps for the 12 playable/general IDs. The
localized ID order is Alan, Dean, Claude, Viola, Damon, Saki, Zelgius, Julius
Officer, Herbert Officer, Sandia Staff, Frost Commander, and Government
Officer.

| ID | General | item | escape | active |
| ---: | --- | ---: | ---: | ---: |
| 0 | Alan | 4 | 4 | 2 |
| 1 | Dean | 4 | 5 | 3 |
| 2 | Claude | 4 | 3 | 5 |
| 3 | Viola | 4 | 4 | 0 |
| 4 | Damon | 4 | 1 | 5 |
| 5 | Saki | 4 | 4 | 2 |
| 6 | Zelgius | 5 | 4 | 4 |
| 7 | Julius Officer | 2 | 3 | 2 |
| 8 | Herbert Officer | 2 | 3 | 3 |
| 9 | Sandia Staff | 2 | 3 | 4 |
| 10 | Frost Commander | 2 | 3 | 1 |
| 11 | Government Officer | 2 | 3 | 4 |

These values are exact from `GeneralParameter::item` (`0xbe4b4`), `escape`
(`0xbe694`), and `active` (`0xbe874`). Their AI decision semantics are not yet
fully reconstructed.
