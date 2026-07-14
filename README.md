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
