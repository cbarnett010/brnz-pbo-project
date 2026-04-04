# brnz PBO Project

A DayZ mod packing and deployment tool built for TheFactory server stack.

## Features

- **Pack mods** from `P:\` using DayZ Tools AddonBuilder
- **Deploy to local server** — creates `@modname/addons/` and patches `start.bat` automatically
- **Stage mods** to `Desktop\Core Stuff\{core|gear|weapons|vehicles}`
- **Push to modpacks** — `D:\MODS\TheFactory{Core|Gear|Weapons|Vehicles}`
- **Sign PBOs** with the correct TheFactory or TheFactoryTest bikey via DSSignFile
- **Create new mods** — scaffolds folder structure and config.cpp from template
- **Open Publisher** — launches DayZ Tools Publisher for Steam Workshop uploads
- **Search mods** — filter the P:\ mod list by name, double-click to open folder

## Deployment Destinations

| Option | Description |
|--------|-------------|
| Local server (test) | Packs and deploys to local DayZServer, patches start.bat |
| Staging only | Packs to Desktop staging folder |
| Staging + Modpack | Packs to staging and copies to D:\MODS modpack |
| Modpack only | Packs directly into D:\MODS modpack |

## Signing

- Mods going into `TheFactory*` packs are signed with `TheFactory.biprivatekey`
- Mods going into `TheFactory*Test` packs are signed with `TheFactoryTest.biprivatekey`
- Keys live in `D:\MODS\@TheFactoryCore\Keys\` and `D:\MODS\@TheFactoryCoreTest\Keys\`

## Paths

| Purpose | Path |
|---------|------|
| Mod source | `P:\` |
| Local DayZ server | `C:\Program Files (x86)\Steam\steamapps\common\DayZServer` |
| Staging | `C:\Users\b_mal\Desktop\Core Stuff\` |
| Modpacks | `D:\MODS\` |
| DayZ Tools | `C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools` |

## Running

Double-click `launch.bat` or use the desktop shortcut.
