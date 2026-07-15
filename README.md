# Forza DualSense Haptics for Decky

SteamOS Decky plugin that maps Forza Horizon 6 telemetry to DualSense adaptive triggers.

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

# v0.4.0-alpha development update

This branch adds four user-facing improvements:

1. **Live settings:** effect sliders and the enable toggle update the running engine without restarting it.
2. **Preset management:** cycle through presets, load one, save current values as a new numbered preset, duplicate, or delete.
3. **Controller diagnostics:** transport, battery where exposed by `hid-playstation`, product ID, serial and hidraw path.
4. **Test haptics:** controller-focusable buttons for pedal resistance, ABS, gear kick and rev limiter.

## Safe branch workflow

- From the existing tested repository 
- Copy this source update into the repository, then verify, build and commit.
- Deploy only from Desktop Mode

Do not restart `plugin_loader` while Game Mode is active.

## Expected v0.4 behaviour

- Moving a slider updates the UI immediately and writes the setting after a 400 ms debounce.
- The backend detects settings-file changes within approximately 250 ms.
- Slider changes no longer stop or restart the engine.
- Test effects are processed by the already-running engine; the Decky process does not open a second HID handle.
- Changing UDP host or port still requires **Restart engine**, because the listening socket must be rebound.

## Preset naming

The alpha UI avoids an on-screen keyboard dependency. New presets are named automatically as `Preset 1`, `Preset 2`, and so on. Duplicates use `Copy`, `Copy 2`, etc. Custom renaming can be added after the core preset workflow is validated.

## Battery and firmware diagnostics

Battery information appears only when SteamOS exposes a matching `sony_controller_battery_*` power-supply entry. Firmware is displayed as unavailable because the direct hidraw path used by this alpha does not expose a reliable firmware version.
