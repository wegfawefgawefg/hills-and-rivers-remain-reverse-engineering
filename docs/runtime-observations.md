# Runtime observations

Runtime observations use the original decrypted executable and shipped assets.
Screenshots, logs, emulator state, and save data remain under the ignored
`workspace/` tree. Addresses below are ARMv6 virtual addresses unless noted.

## 2026-08-14 — First-run tutorial entry

Environment: patched touchHLE commit `331903d`, ARMv7 guest, x86-64 Linux,
Mesa llvmpipe through Xvfb. Input was injected as ordinary X11 mouse clicks and
arrived through touchHLE's iOS touch path.

Observed flow:

1. The animated English title screen presents `Start Game`.
2. Selecting it opens `Do you want to start the tutorial?` with `No` and `Yes`.
3. Selecting `Yes` loads a playable landscape map without an emulator crash.
4. The map shows turn zero, four bases with soldier counts, roads, forest,
   rocks, water, colored flags, a player portrait, and tutorial dialogue.
5. The tutorial identifies the red-flag base as the player's headquarters.
6. It states that soldiers are generated at headquarters every turn.
7. Selecting a base exposes `Move Troops`, `Relocate HQ`, and `Items` commands.

The tutorial and map remained animated and responsive throughout the capture
windows. Full gesture handling, combat, turn completion, saving, and later
scenarios are not yet validated.

## Binary anchors matching the observed systems

The surviving symbols give direct entry points for reconstructing the rules:

| Address | Symbol | Likely catalogue role |
| ---: | --- | --- |
| `0x0000f1b0` | `Scene::Game::getTurnCount() const` | displayed turn state |
| `0x0000ffd4` | `Scene::Game::calcSoldierPoint() const` | soldier scoring/generation analysis |
| `0x000107b8` | `Scene::Game::isHeadBase(int, int) const` | headquarters identity |
| `0x00010d10` | `Scene::Game::getHeadPos(int) const` | headquarters location |
| `0x00011fc8` | `Scene::Game::GetBaseSoldier(int) const` | base soldier count |
| `0x00013e9c` | `Scene::Game::AddSoldier(int, int, int)` | soldier mutation |
| `0x00015224` | `Scene::Game::SetNewHead(int, int)` | relocate-HQ command |
| `0x0001e178` | `Scene::Game::turnEnd()` | core end-of-turn processing |
| `0x00023af8` | `Scene::Game::SetArmyMove(int, int, bool)` | troop movement setup |
| `0x00023c84` | `Scene::Game::troop(int)` | troop command processing |
| `0x00026298` | `Scene::Game::ComputerFunc(int)` | AI turn logic |
| `0x0002eea8` | `Scene::Game::DamageCalculate(int)` | combat formula |
| `0x0002fe9c` | `Scene::Game::BattleFunc()` | battle state processing |

Other high-value named functions include pathfinding (`GetBasePath`,
`GetArmyPath`, `IsPassable`), AI decisions (`ComputerSendArmy`,
`ComputerRetreat`, `ComputerInroad`, `ComputerAvoidBomb`, `ComputerUseItem`),
special terrain/structures (`turnEndGoldMine`, `turnEndFort`, `turnEndBombard`),
save/load, event scripts, victory detection, touch gestures, camera zoom, and
map coordinate conversion.

This density of semantic names means the game rules can be recovered mainly by
decompiling a bounded set of named functions and validating them against the
running tutorial. Asset/data decoding is still required for scenario-specific
parameters and content.
