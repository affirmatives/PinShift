# PinShift

[中文](README.md) | English

**Version: 1.0.0** · **License: GPL-3.0-or-later** · [GitHub](https://github.com/affirmatives/PinShift)

Choose a location on your Mac and set it as your iPhone's simulated location over USB.

PinShift is a PySide6 desktop application with an embedded AMap JavaScript API 2.0 map. It uses [pymobiledevice3](https://github.com/doronz88/pymobiledevice3) to communicate with devices, for developing and testing location features on your own devices.

Version 1.0.0 supports macOS, USB connections, and one device at a time. A comprehensive macOS / iOS compatibility matrix is not available yet. The UI is currently in Chinese; English documentation does not imply an English UI.

## Features

- Scan USB devices and display their name, iOS version, and UDID.
- Select map locations, pan and zoom, or search and choose from multiple results.
- Display and copy coordinates, and optionally remember the last selection.
- Set and clear the iPhone's simulated location.
- Use macOS CoreLocation to center on the Mac's location, with a default Hangzhou center on failure.
- Switch between light and dark themes across the UI and map, with saved preferences.
- Configure AMap credentials, zoom level, and startup behavior; view version, author, copyright, license, and GitHub links.
- View UI and file logs, and build `.app` / `.dmg` packages.

## Screenshots

Main page

![PinShift main page: map selection and location simulation](docs/screenshots/main.png)

Settings page

![PinShift settings page: map settings and about information](docs/screenshots/settings.png)

## Requirements

| Component | Requirement |
| --- | --- |
| OS | macOS; Windows / Linux are currently unsupported |
| Python | 3.13 recommended, matching the current local environment; other versions need validation |
| Device | One unlocked iPhone connected with a USB data cable and trusting the Mac |
| iOS | Depends on pymobiledevice3 support; enable Developer Mode when required |
| Map | An AMap Web JavaScript API Key, its matching `securityJsCode`, and internet access |
| Node.js | Needed only for map regression checks, not to run the app |

See [requirements.txt](requirements.txt). Dependencies have lower bounds and are not locked. Device services require pymobiledevice3's asynchronous APIs; not every combination satisfying these lower bounds has been verified.

## Run from source

Download or clone the source, then run from the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

Alternatively, with uv:

```bash
uv venv --python 3.13 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
python main.py
```

Reuse an existing virtual environment rather than overwriting it.

### Configure AMap

1. Sign in to the [AMap Open Platform](https://lbs.amap.com/) and create an application.
2. Add a Key for the **Web JavaScript API** service.
3. Obtain the corresponding security code, `securityJsCode`.
4. Enter both values on PinShift's settings page (“配置”). Saving reloads the map.

Each user should supply their own credentials and follow AMap's terms and quota limits.

## Usage

1. Launch PinShift and configure the map.
2. Connect one iPhone over USB, unlock it, and choose “Trust This Computer.” Enable Developer Mode as required.
3. Click “扫描设备” (Scan devices) and confirm the device information.
4. Search and select a result, or click the map. Check the coordinates.
5. Click “设置虚拟定位” (Set simulated location) and check the result.
6. When finished, click “清除虚拟定位” (Clear simulated location) and confirm that location has returned to normal on the device.

Map selections and displayed coordinates use GCJ-02 and are converted to WGS-84 before being sent to the iPhone. Mac CoreLocation coordinates are converted from WGS-84 to GCJ-02 for display. Conversion is approximate and unsuitable for precision surveying.

### iOS 17+ and administrator authorization

PinShift first tries to reuse an existing `tunneld` connection, then attempts to create a USB CoreDevice tunnel. For specific `utun` / `pytun` creation errors, it requests administrator authorization through the macOS system dialog and starts a location helper.

The helper may remain running to maintain the tunnel and location session. Closing the window does not guarantee that simulation is cleared; explicitly clear it when finished. Canceling authorization causes the operation requiring elevated privileges to fail.

If automatic tunnel creation fails, run this in a separate terminal with the project environment activated:

```bash
pymobiledevice3 remote tunneld
```

Keep it running and retry in PinShift. Permissions and options depend on the dependency version; consult `pymobiledevice3 remote tunneld --help`.

## Settings and logs

Default data directory: `~/Library/Application Support/PinShift/`.

| File | Contents |
| --- | --- |
| `settings.json` | Map credentials, selected location, and UI preferences |
| `logs/pinshift.log` | Application logs |
| `logs/location_helper.log` | Administrator helper logs, when used |
| `location_helper*` | Helper status, command, and PID files |

Set `PINSHIFT_APP_SUPPORT_DIR` to use an isolated data directory, for example during testing.

Map credentials are stored locally in plain text. Loading maps and searching contacts AMap services. Logs include coordinates and some device information. Common Key fields are redacted by the code, but inspect logs, screenshots, and issue reports before sharing and remove credentials, UDIDs, and private locations.

## Development and checks

```text
main.py                 GUI and location helper entry points
config/                 JSON configuration
models/                 Settings and device models
services/               USB scanning, iPhone location, tunnels, Mac location
ui/                     Qt windows, pages, themes, and widgets
bridges/                Python / JavaScript Qt WebChannel bridge
web/                    AMap page, styles, and interactions
utils/                  Coordinate conversion, paths, log redaction, utilities
tests/                  Core, map, and UI regression checks
assets/                 Application icons
packaging/              macOS build scripts
```

Run from the project root with dependencies installed:

```bash
PYTHONPATH=. python tests/check_core.py
node tests/check_map.cjs
PYTHONPATH=. python tests/check_ui.py
```

Core checks cover settings, coordinate conversion, error handling, mocked USB scanning, dependency APIs, and repeated CoreLocation requests. Map checks mock the AMap API and need no real Key. UI checks require a macOS graphical session, briefly open a window, and save screenshots to `/private/tmp/pinshift-*.png`. Checks use temporary configuration directories.

These checks do not replace hardware validation. Verify device connections, setting / clearing location, iOS tunnels, and the administrator helper separately on a real device. See [AGENTS.md](AGENTS.md) for development conventions.

## Build for macOS

Run in the virtual environment with dependencies installed:

```bash
bash packaging/build_macos.sh
bash packaging/create_dmg.sh
```

Outputs are `dist/PinShift.app` and `dist/PinShift.dmg`. The build script uses `PinShift.spec`, bundles `web/`, `assets/`, the license and copyright notices, uses `assets/PinShift.icns`, writes version 1.0.0, copyright and location permission descriptions, and applies and verifies an ad-hoc signature. Scripts overwrite their corresponding build outputs.

Developer ID signing and Apple notarization are not configured, so downloaded builds are not guaranteed to pass Gatekeeper. Build and test processor architectures separately; the script does not produce a universal binary. Building directly from `PinShift.spec` omits the script’s signing post-processing; prefer the commands above.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| Blank map or `INVALID_USER_SCODE` | Key service type, matching security code, quotas, and network; save settings and retry |
| Mac location unavailable | System location permissions; search and map selection remain available |
| iPhone not detected | USB data cable, unlocked device, and trust pairing; use `pymobiledevice3 usbmux list` for diagnosis |
| Multiple devices detected | Connect only one iPhone; multi-device operation is unsupported |
| Setting or clearing fails | Developer Mode, unlock status, tunnel, authorization, dependency API compatibility, and logs |
| Packaged app fails | Try running from source to distinguish device / dependency issues from packaging issues; report architecture and OS version |

## Contributing and licensing status

Report problems through GitHub Issues or propose improvements through Pull Requests. Include macOS / iOS / Python / pymobiledevice3 versions, architecture, source or packaged execution, reproduction steps, and redacted logs. Describe code changes and checks performed. Do not commit environments, build outputs, personal settings, or device data.

## Author and license

- Author: [affirmatives](https://github.com/affirmatives).
- Project: [affirmatives/PinShift](https://github.com/affirmatives/PinShift) (planned repository URL, available after upload).
- Version: **1.0.0**.
- Copyright (C) 2026 affirmatives.
- License: **GNU General Public License v3.0 or later (GPL-3.0-or-later)**.

You may use, modify, and redistribute this project under GPL version 3 or any later version. When distributing the application or modified versions, comply with the GPL, including providing corresponding source and preserving license and copyright notices. The software is provided without warranty.

See [LICENSE](LICENSE) for the full terms, [COPYRIGHT](COPYRIGHT) for the project grant, and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for dependencies and map content. Third-party content retains its original rights and licenses; screenshots do not change the licensing of AMap content. Review licenses of the actual bundled components and validate release packages before public distribution.

## Acknowledgments

- [PySide6 / Qt for Python](https://doc.qt.io/qtforpython-6/): desktop UI and WebEngine.
- [pymobiledevice3](https://github.com/doronz88/pymobiledevice3): iOS communication and location simulation.
- [AMap Open Platform](https://lbs.amap.com/): maps and place search.
- [PyObjC](https://pyobjc.readthedocs.io/): CoreLocation bridge.
- [PyInstaller](https://pyinstaller.org/): application packaging.
