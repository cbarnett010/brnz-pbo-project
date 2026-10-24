# brnz PBO Project

A DayZ mod packing and deployment tool built for TheFactory server stack.

## Requirements

- Windows 10/11
- Python 3.10 or newer — https://www.python.org/downloads/windows/
  - Run the installer and tick **"Add python.exe to PATH"** before clicking Install Now
  - If the installer asks about disabling the 260 character path limit, click Yes
- DayZ Tools (from Steam, under Tools). This provides AddonBuilder, DSSignFile, ImageToPAA and Publisher, and mounts the `P:\` drive
- A local DayZ Server install (from Steam, under Tools) if you want to use the Local Server tab

## Setup

1. Download the repo (Code → Download ZIP) and unzip it anywhere, e.g. `C:\brnzpboproject`
2. Double-click `launch.bat`
3. If DayZ Tools or the DayZ Server are not at the default Steam location, the tool will offer to open
   the **⚙ Paths** dialog on first start. You can open it any time from the button in the top right.
4. Optional: right-click `create_shortcut.ps1` → Run with PowerShell to put a shortcut on your Desktop

## Paths

Click **⚙ Paths** (top right) to tell the tool where things live on your PC. Use **Browse…** or paste a path.
Choices are saved to `tool_settings.json` next to the script and take effect immediately.

| Setting | Default | Notes |
|---------|---------|-------|
| DayZ Tools folder | `C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools` | In Steam: right-click DayZ Tools → Manage → Browse local files |
| DayZ Server folder (Stable) | `C:\Program Files (x86)\Steam\steamapps\common\DayZServer` | Must contain `DayZServer_x64.exe` |
| DayZ Server folder (Exp) | `C:\Program Files (x86)\Steam\steamapps\common\DayZ Server Exp` | Only needed for Experimental mode |
| Mod source drive | `P:\` | Mounted by DayZ Tools |
| Staging folder | `Desktop\Core Stuff` | Where packed PBOs are staged |
| Modpacks folder | `D:\MODS` | Contains `@TheFactoryCore`, `@TheFactoryGear`, etc. and the signing keys |

If your Steam library is on another drive, e.g. `D:\SteamLibrary`, set the first three to
`D:\SteamLibrary\steamapps\common\DayZ Tools`, `...\DayZServer` and `...\DayZ Server Exp`.

## Server modes

A **Server: Stable / Experimental** switch sits above the tabs. The tool remembers the
last mode used in `tool_settings.json`.

| Mode | What you get |
|------|--------------|
| Stable | Everything below |
| Experimental | PBO Builder (local server only) + Local Server tab |

Each mode has its own `start.bat` and its own saved mod checklist
(`server_mod_selections.json` / `server_mod_selections_exp.json`).
Switching is blocked while a server started from the tool is still running.

## Features

- **Pack mods** from `P:\` using DayZ Tools AddonBuilder
- **Deploy to local server** — creates `@modname/addons/` and patches `start.bat` automatically
- **Stage mods** to `<Staging folder>\{core|gear|weapons|vehicles}`
- **Push to modpacks** — `<Modpacks folder>\TheFactory{Core|Gear|Weapons|Vehicles}`
- **Sign PBOs** with the correct TheFactory or TheFactoryTest bikey via DSSignFile
- **Create license plates** — converts an image (plus optional normal map) to PAA and writes a plate config for TF_LicensePlates
- **Create new mods** — scaffolds folder structure and config.cpp from template
- **Open Publisher** — launches DayZ Tools Publisher for Steam Workshop uploads
- **Search mods** — filter the P:\ mod list by name, double-click to open folder

## Deployment Destinations

| Option | Description |
|--------|-------------|
| Local server (test) | Packs and deploys to local DayZServer, patches start.bat |
| Staging only | Packs to the staging folder |
| Staging + Modpack | Packs to staging and copies to the modpack |
| Modpack only | Packs directly into the modpack |

## Signing

- Mods going into `TheFactory*` packs are signed with `TheFactory.biprivatekey`
- Mods going into `TheFactory*Test` packs are signed with `TheFactoryTest.biprivatekey`
- Keys are expected at `<Modpacks folder>\@TheFactoryCore\Keys\` and `<Modpacks folder>\@TheFactoryCoreTest\Keys\`

## Running

Double-click `launch.bat` or use the desktop shortcut.

## Troubleshooting

**Tool won't open** — Make sure Python is installed and on PATH. Run `python --version` in Command Prompt to check.

**Mod list is empty** — DayZ Tools has not mounted `P:\`. Open DayZ Tools once from Steam, or check the Mod source drive in ⚙ Paths.

**"AddonBuilder.exe was not found"** — The DayZ Tools folder in ⚙ Paths is wrong. In Steam, right-click DayZ Tools → Manage → Browse local files and copy that path.
