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

The original ARMv7 executable now boots to the English title screen in touchHLE
on x86-64 Linux. It initializes UIKit, OpenGL ES 1.1, audio, localization,
Reachability, touch input, and accelerometer input, then renders steadily at
about 30 FPS. Three small host compatibility shims are required; see
[`emulation.md`](emulation.md).

This makes touchHLE the primary comparison environment. A real jailbroken iOS
3–6 device remains valuable for validating behavior touchHLE approximates,
especially locale, reachability, StoreKit, accelerometer, and audio timing.
Apple's iOS Simulator cannot directly run this device ARM Mach-O code.
