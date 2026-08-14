# Initial findings — version 2.0.0

## Executable

The universal Mach-O contains ARMv6 and ARMv7 slices. Both slices have
`LC_ENCRYPTION_INFO` with `cryptid 0`, so their code pages are plaintext. The
executable is also reported as unstripped. Its local symbols expose build paths
from a project named `shogun` and 152 compiled object names.

The startup bridge is conventional Objective-C:

- `main`
- `shogunAppDelegate`
- `applicationDidFinishLaunching:`
- `startGame`
- `EAGLView`
- `Manager::init`, `Manager::update`, and `Manager::draw`

Most of the game is C++. High-value recovered module names include:

- Core: `Manager`, `Game`, `System`, `Algorithm`, `TimerEffect`
- World/data: `Map`, `MapData`, `MapChip`, `Stage`, `StageConfig`, `Level`
- Gameplay: `General`, `GeneralParameter`, `Item`, `ItemEffect`, `WarInfo`
- Scenes/UI: `Title`, `Menu`, `Story`, `Free`, `Result`, `GameOver`
- Save/config: `Save`, `SaveData::Orientation`, `CommonConfig`, `Config`
- Rendering: `EAGLView`, `GLTexture`, `Texture`, `Graphic`, `PVRLoader`
- Audio: `BackGroundMusic`, `SoundEffect`, OpenAL Utility Toolkit objects
- Network: `Network`, `Session`, `Game_Network` and named per-event handlers
- Content/store: `Product`, `ProductId`, `BuyMap`, `AddScenario`, `AddEpilogue`

The complete local reports include imports, libraries, symbols, classes,
strings, Mach-O load commands, and the full 152-name object-file list under
`workspace/reports/`.

## Imports

The executable links Foundation, UIKit, OpenGLES, QuartzCore, AudioToolbox,
CoreGraphics, OpenAL, StoreKit, SystemConfiguration, CoreFoundation,
`libstdc++`, `libgcc_s`, `libSystem`, and `libobjc`.

## Resources

The IPA has 2,359 members and expands to 179,633,496 bytes. Major app-resource
counts are:

| Extension | Count | Initial interpretation |
| --- | ---: | --- |
| PNG | 1,182 | UI, characters, thumbnails, sprites |
| PVR | 683 | PowerVR textures, especially tiled maps |
| `.strings` | 282 | Localization resources |
| YAS | 139 | Likely proprietary animation/script data |
| WAV | 30 | Sound effects |
| M4A | 10 | Music |
| DAT | 5 | Maps/configuration or packed game data |

Visible names include `map_*.pvr`, `freemap.dat`, `trial_map.dat`,
`tgs2009_map.dat`, and many `*.yas` animation files. These are immediately
recoverable regardless of executable DRM status and should be format-mapped
separately.

## Execution outlook

The plaintext ARMv6/ARMv7 executable and iOS 3.0 deployment target make a real
jailbroken iOS 3–6 device the highest-confidence execution route. touchHLE is
the best emulator candidate, but framework/API coverage must be tested; this
title uses UIKit, OpenGL ES, OpenAL, StoreKit, and SystemConfiguration. Apple's
iOS Simulator cannot directly run device ARM Mach-O code.
