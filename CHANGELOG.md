# Changelog

All changes to this project are documented in this file, however, commits are out of order. The git repo was lost (I stupidly deleted everything during an early sync and was only running a local git repo at the time), restored repo from last known good v0.4.0 (tested & confirmed working), with v0.5.0 as the next working feature branch. All other code history (that I had copies of) was then restored for audit trail.

---

## Changes from v0.5.0 to v1.0.0

This release marks the completion of all key features I wanted to impliment, and the plugin's first stable release. Changes during this period focused on refining the adaptive trigger feedback, improving usability, increasing reliability, and tidying the git repo public release.

---

## Haptic Improvements

### Dynamic Traction Guidance

* Replaced pulsed traction loss vibration with dynamic resistance on a curve.
* Added predictive grip-loss detection using throttle demand, wheel slip and slip trend.
* Improved adaptive trigger engagement timing for earlier feedback before significant wheelspin.
* Smoothed resistance transitions to eliminate vibration-like behaviour that was confused with/lost alongside gear kick and rev limiter feedback..
* Tuned force progression to better relay available grip to the user.

### Surface Awareness

* Added surface-state telemetry decoding.
* Improved traction guidance behaviour to be impacted by varying road conditions.

### Individual Effect Controls

* Re designed UI from previous build, where all haptics/feedback were either on or off, with sliders for each active feedback's intensity settings, to independent enable/disable toggles for:

  * Pedal Resistance
  * ABS Vibration
  * Gear Kick
  * Rev Limiter
  * Dynamic Traction Guidance

Each haptic effect can now be enabled or disabled independently, or as previously built, all features can be enabled or disabled with a single toggle.

---

## User Interface

### Live Controls Redesign

The Live Controls panel was further refined with the switch to default toggles, rather than default feedback intensity sliders, buy adding/re organising the following UI elements:

* Added expandable **Advanced** sections for each effect.
* Moved tuning controls into their corresponding advanced panels.
* Renamed controls for improved clarity.
* Reduced visual clutter while keeping advanced configuration.

### Profile Management

Expanded the profile system with:

* Profile creation
* Profile duplication
* Profile deletion
* Profile renaming
* Automatic profile assignment to individual vehicles - Allows for automatic profile switch and load on changing to a vehicle with a profile assigned to it.
* Automatic Global default "balanced" profile set as fallback for unassigned vehicles

Profiles can now be fully managed without leaving the Decky interface.

---

## Reliability

### Settings

Improved settings by introducing:

* Improved persistence reliability
* Correct migration of newly introduced settings

### Backend

Improved backend stability with:

* Safer backend lifecycle management
* Improved process handling
* Better startup behaviour
* Improved deployment workflow, utilising the scripted safetey checks (like not restarting Plugin_Loader while in gamescope. Learnt the hard way and un-black screening my Steam Machine after not even a week of ownership was fun...)

---

## Diagnostics

Expanded built-in diagnostics with:

* Controller information
* Runtime engine status - bringing use to the resart engine button as you can now see if the engine has fallen over/is not responding.
* Traction status
* Vehicle telemetry
* Built-in haptic testing

---

## Project Improvements

The project infrastructure has also been significantly improved.

### Source Control

* Reconstructed (mostly) complete project history after repository loss.
* Added release tags.
* Added protected branches.

### Documentation

Added or expanded:

* README
* CHANGELOG
* CONTRIBUTING
* History reconstruction notice
* Release packaging workflow

---

## Bug Fixes

Resolved numerous issues including:

* Settings failing to save
* Settings migration failures
* Profile migration failures
* Traction setting persistence
* Missing backend settings lock
* Profile rename handling
* Automatic profile restoration
* Traction guidance timing
* Traction force modulation
* Multiple user interface inconsistencies

---

## Release Status

Version 1.0.0 represents the first stable release of Forza DualSense Haptics.

The core feature set is considered complete.

---

## v0.5.0-alpha
- Added surface-state and traction-state decoding.
- Added dynamic R2 traction feedback.
- Added fixed response curves: Linear, Progressive and Aggressive.
- Added compact telemetry health, packet rate and latency diagnostics.
- Added per-car profile assignment foundation.
- Custom response curves are intentionally out of scope to keep simplicity.

## v0.4.0-alpha

- Apply effect sliders and enable/disable changes without restarting the engine.
- Add preset creation, selection, loading, duplication and deletion.
- Add controller diagnostics: transport, battery where available, product ID, serial and HID path.
- Add controller-focusable test buttons for pedal resistance, ABS, gear kick and rev limiter.
- Preserve exact-child process control for safe engine restarts. (learnt the hard way)

### Fixed
- Settings persistence
- Decky RPC communication
- Plugin loading conflicts
- Controller navigation
- Backend restart behaviour

---

## v0.3.0-alpha

### Added
- Native Linux backend
- SteamOS Decky plugin
- Adaptive trigger support
- Gear kick
- ABS vibration
- Rev limiter support
- Engine status reporting
- Restart haptics engine control
- Native HID communication

### Fixed
- Rev limiter not sending adaptive trigger vibration
- Process shutdown handling
- Compatibility issues

---

## v0.2.0

### Added
- Initial Decky plugin prototype
- Linux backend proof of concept
- UDP telemetry support
- DualSense detection

### Changed
- Ported Windows .exe built by git-ducu (https://github.com/git-ducu/forza-dualsense-haptics) to Linux

---

## v0.1.0

### Added
- Initial SteamOS proof of concept
- Varified that steam input did not clash with HID communicating with Dualsense adaptive triggers.
- Basic telemetry reception
- Basic DualSense communication

