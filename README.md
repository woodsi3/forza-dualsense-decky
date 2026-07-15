# Forza DualSense Haptics for Decky

SteamOS Decky plugin that maps Forza Horizon 6 telemetry to DualSense adaptive triggers.

### Highlights

* Native SteamOS backend
* Decky Loader integration
* Adaptive throttle and brake resistance
* Dynamic traction guidance
* Early grip-loss feedback based on slip, throttle demand and slip trend
* ABS vibration
* Gear-shift kick
* Rev-limiter feedback
* Surface-state telemetry
* Live effect controls
* Expandable advanced tuning
* Saved and renameable profiles
* Automatic per-car profile selection
* Safe Global profile fallback
* Controller diagnostics
* Built-in haptic tests
* Automatic settings and profile migration

### Dynamic traction guidance

Traction guidance uses smooth adaptive-trigger resistance rather than vibration.

As available grip decreases, accelerator resistance increases progressively. This gives the driver an early, physical indication that the tyres are approaching their limit and encourages finer throttle modulation.

### Project status

The core feature set is now considered complete.

Future releases will focus on:

* Bug fixes
* Hardware and SteamOS compatibility
* Feedback from public testing
* Telemetry refinements
* Documentation improvements

### Notes

Forza UDP data-out must be enabled and configured to send telemetry to the SteamOS device running the plugin.
IP: 127.0.0.1
Port: 5300

Decky plug in is submitted but not yet approved for download via the decky store. Please see the Release notes for manual installation instructions.


## Safety rules

- Never restart `plugin_loader` while Game Mode/Gamescope is active.
- Frontend changes are built and deployed in Desktop Mode, followed by a reboot.
- The plugin only terminates its exact child backend process; it never signals a process group.
- Every deployment creates a timestamped rollback backup.

## Repository setup

```bash
chmod +x scripts/*.sh
./scripts/init-git.sh
```

## Build

```bash
./scripts/build.sh
```

## Deploy safely

Switch to Desktop Mode first, then:

```bash
./scripts/deploy.sh
sudo reboot
```

The deploy script refuses to run while Gamescope is active.

## Roll back

From Desktop Mode:

```bash
./scripts/rollback.sh
sudo reboot
```

## Verify without building

```bash
./scripts/verify.sh
```

## Runtime configuration

Decky settings are stored separately from the repository under:

```text
/home/deck/homebrew/settings/forza-dualsense-settings.json
```

For local Forza Data Out, use `127.0.0.1` and UDP port `5300`.

## Safe branch workflow

- From the existing tested repository 
- Copy this source update into the repository, then verify, build and commit.
- Deploy only from Desktop Mode

Do not restart `plugin_loader` while Game Mode is active.

## Preset naming

The alpha UI avoids an on-screen keyboard dependency. New presets are named automatically as `Preset 1`, `Preset 2`, and so on. Duplicates use `Copy`, `Copy 2`, etc. Custom renaming can be added after the core preset workflow is validated.

## Battery and firmware diagnostics

Battery information appears only when SteamOS exposes a matching `sony_controller_battery_*` power-supply entry. Firmware is displayed as unavailable because the direct hidraw path used by this alpha does not expose a reliable firmware version.
