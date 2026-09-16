# brnz PBO Project

A DayZ mod packing and deployment tool built for TheFactory server stack.

## Server modes

A **Server: Stable / Experimental** switch sits above the tabs. The tool remembers the
last mode used in `tool_settings.json`.

| Mode | Server folder | What you get |
|------|---------------|--------------|
| Stable | `C:\Program Files (x86)\Steam\steamapps\common\DayZServer` | Everything below |
| Experimental | `C:\Program Files (x86)\Steam\steamapps\common\DayZ Server Exp` | PBO Builder (local server only) + Local Server tab |

Each mode has its own `start.bat` and its own saved mod checklist
(`server_mod_selections.json` / `server_mod_selections_exp.json`).
Switching is blocked while a server started from the tool is still running.

## Features

- **Pack mods** from `P:\` using DayZ Tools AddonBuilder
- **Deploy to local server** — creates `@modname/addons/` and patches `start.bat` automatically
- **Stage mods** to `Desktop\Core Stuff\{core|gear|weapons|vehicles}`
- **Push to modpacks** — `D:\MODS\TheFactory{Core|Gear|Weapons|Vehicles}`
- **Sign PBOs** with the correct TheFactory or TheFactoryTest bikey via DSSignFile
- **Create license plates** — converts an image (plus optional normal map) to PAA and writes a plate config for TF_LicensePlates
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
| Local DayZ server (Stable) | `C:\Program Files (x86)\Steam\steamapps\common\DayZServer` |
| Local DayZ server (Experimental) | `C:\Program Files (x86)\Steam\steamapps\common\DayZ Server Exp` |
| Staging | `C:\Users\b_mal\Desktop\Core Stuff\` |
| Modpacks | `D:\MODS\` |
| DayZ Tools | `C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools` |

## Running

Double-click `launch.bat` or use the desktop shortcut.
