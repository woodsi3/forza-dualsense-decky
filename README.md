# Forza DualSense SteamOS Backend — Phase 2 MVP

This is a standalone, headless SteamOS/Linux backend for testing live Forza
Horizon 6 telemetry against a PS5 DualSense controller.

It currently implements:

- brake-pedal resistance on L2;
- throttle-pedal resistance on R2;
- ABS vibration on L2;
- gear-change kick on R2;
- rev-limiter vibration on R2;
- USB and Bluetooth DualSense detection/reconnection;
- safe trigger clearing when telemetry stops or the process exits;
- JSON settings;
- JSON status output for the later Decky sidebar;
- an optional systemd user service.

It deliberately excludes the Windows GUI and haptic-audio mixer for this phase.

## 1. Extract and install

```bash
cd ~/Downloads/forza_dualsense_backend
chmod +x install.sh uninstall.sh run_backend.py
./install.sh
```

The backend is installed under:

```text
~/.local/share/forza-dualsense/backend
```

Settings are stored at:

```text
~/.local/share/forza-dualsense/settings.json
```

Runtime status is written to:

```text
~/.local/share/forza-dualsense/status.json
```

## 2. HID permissions

You already installed a compatible rule during Phase 1. If needed:

```bash
sudo cp packaging/70-dualsense-hidraw.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Reconnect or power-cycle the controller afterward.

## 3. Confirm controller output

```bash
python3 ~/.local/share/forza-dualsense/backend/run_backend.py controller-test
```

## 4. Configure Forza Data Out

In Forza:

- Data Out: **On**
- IP address: the SteamOS machine's LAN IP initially
- Port: **5300**

The backend binds `0.0.0.0:5300`, which accepts local and LAN telemetry.

## 5. Run manually first

```bash
python3 ~/.local/share/forza-dualsense/backend/run_backend.py run
```

Leave the terminal open, start driving, and test:

- progressive L2 brake resistance;
- progressive R2 throttle resistance;
- L2 vibration during hard braking and wheel slip;
- R2 kick when the gear changes;
- R2 vibration near the rev limiter.

Stop with `Ctrl+C`. Both triggers should return to neutral.

## 6. View live status

From another terminal:

```bash
python3 ~/.local/share/forza-dualsense/backend/run_backend.py status
```

Or continuously:

```bash
watch -n 1 cat ~/.local/share/forza-dualsense/status.json
```

The future Decky UI will consume the same status fields.

## 7. Tune intensity

Edit:

```bash
nano ~/.local/share/forza-dualsense/settings.json
```

The four primary controls are:

```json
{
  "pedal_force_intensity": 1.0,
  "abs_intensity": 1.0,
  "gear_kick_intensity": 1.0,
  "rev_limiter_intensity": 1.0
}
```

Valid range is `0.0` to `2.0`.

Restart the backend after editing.

## 8. Run automatically

Only enable this after manual testing succeeds:

```bash
systemctl --user enable --now forza-dualsense-backend.service
```

Check it with:

```bash
systemctl --user status forza-dualsense-backend.service
journalctl --user -u forza-dualsense-backend.service -f
```

Stop it with:

```bash
systemctl --user disable --now forza-dualsense-backend.service
```

## Current limitations

- This MVP implements the four requested effects with a clean, simplified
  mapping rather than importing every upstream tuning algorithm.
- ABS is inferred from brake pressure, speed and front-wheel slip.
- Haptic audio is not included yet.
- Settings reload requires a restart.
- Only one controller is actively controlled.
- The backend does not yet expose Decky RPC methods; the JSON status/config
  boundary is intentionally designed for that next step.

## Attribution and licence

The Forza packet layout, DualSense USB/Bluetooth report layout and adaptive
trigger encoding are derived from `git-ducu/forza-dualsense-haptics`, released
under Apache License 2.0.

This package is a modified SteamOS-oriented backend prototype and is not an
official upstream release.
