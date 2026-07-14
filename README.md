# Forza DualSense Haptics — Decky MVP v0.2.0

This is the first Decky Loader integration of the validated SteamOS backend.

## Included sidebar features

- Backend running status
- Forza telemetry receiving/waiting status
- DualSense connected/disconnected status
- USB/Bluetooth transport display
- Current L2 and R2 effect names
- Speed, gear and RPM display
- Enable/disable toggle
- Pedal resistance intensity
- ABS intensity
- Gear-kick intensity
- Rev-limiter intensity
- Manual engine restart

The Decky Python plugin starts and owns the bundled telemetry backend. Do not
run the old standalone systemd service simultaneously, because both processes
would try to bind UDP port 5300 and open the controller.

Disable the standalone service first:

```bash
systemctl --user disable --now forza-dualsense-backend.service
```

## Build on the SteamOS machine or another Linux PC

This archive contains source code. The frontend must be compiled because Decky
loads `dist/index.js`.

```bash
cd forza_dualsense_decky
corepack enable
pnpm install
pnpm build
```

After building, confirm this exists:

```bash
ls -l dist/index.js
```

## Install locally

```bash
chmod +x install-plugin.sh
./install-plugin.sh
```

The plugin is copied to:

```text
~/homebrew/plugins/forza-dualsense-haptics
```

Restart Decky Loader or reboot SteamOS. The plugin should then appear as
**Forza DualSense Haptics** in the Quick Access menu.

## Settings and runtime data

Decky stores plugin settings and runtime data in its managed directories.
The backend process is started during plugin load and stopped during unload,
which clears both adaptive triggers.

## Important first test

1. Disable the old systemd backend.
2. Install and load the Decky plugin.
3. Open the sidebar before launching Forza.
4. Confirm Engine = Running and DualSense = Connected.
5. Launch Forza with Data Out on port 5300.
6. Confirm Telemetry changes to Receiving.
7. Drive and verify all four effects.
8. Move each slider and confirm the backend restarts and the new intensity is felt.

## Known limitation

Each slider save currently restarts the backend. That is safe and simple for
the MVP, but the next revision should support hot settings updates without
restarting or briefly dropping telemetry.
