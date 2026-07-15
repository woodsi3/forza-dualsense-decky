# Changelog

All notable changes to this project will be documented in this file. Commits are out of order, git repo was corrupted, restored repo from current point v0.4.0 (tested & confirmed good), with v0.5.0 as the next working feature branch. all other code history was then restored for audit trail.

---

# Forza DualSense Haptics

## Changes from v0.5.0-alpha to v1.0.0

This release marks the completion of the core feature set and the project's first stable release. Development during this period focused on refining the driving experience, improving usability, increasing reliability, and preparing the project for public release.

---

## Haptic Improvements

### Dynamic Traction Guidance

* Replaced pulsed traction vibration with smooth adaptive-trigger resistance.
* Added predictive grip-loss detection using throttle demand, wheel slip and slip trend.
* Improved engagement timing for earlier feedback before significant wheelspin.
* Smoothed resistance transitions to eliminate vibration-like behaviour.
* Tuned force progression to better communicate available grip.

### Surface Awareness

* Added surface-state telemetry decoding.
* Improved traction guidance behaviour across varying road conditions.

### Individual Effect Controls

* Added independent enable/disable toggles for:

  * Pedal Resistance
  * ABS Vibration
  * Gear Kick
  * Rev Limiter
  * Dynamic Traction Guidance

Each haptic effect can now be enabled or disabled independently without affecting the others.

---

## User Interface

### Live Controls Redesign

The Live Controls panel has been reorganised to provide a simpler, more intuitive interface.

* Added expandable **Advanced** sections for each effect.
* Moved tuning controls into their corresponding advanced panels.
* Renamed controls for improved clarity.
* Reduced visual clutter while keeping advanced configuration easily accessible.

### Profile Management

Expanded the profile system with:

* Profile creation
* Profile duplication
* Profile deletion
* Profile renaming
* Automatic profile assignment to individual vehicles
* Automatic Global profile fallback for unassigned vehicles

Profiles can now be fully managed without leaving the Decky interface.

---

## Reliability

### Settings

Improved settings handling by introducing:

* Automatic settings migration
* Automatic profile migration
* Safe concurrent settings updates
* Improved persistence reliability
* Correct migration of newly introduced settings

### Backend

Improved backend stability with:

* Safer backend lifecycle management
* Improved process handling
* Better startup behaviour
* Improved deployment workflow

---

## Diagnostics

Expanded built-in diagnostics with:

* Controller information
* Runtime engine status
* Surface reporting
* Traction status
* Vehicle telemetry
* Built-in haptic testing

---

## Project Improvements

The project infrastructure has also been significantly improved.

### Source Control

* Reconstructed complete project history after repository corruption.
* Migrated to GitHub.
* Implemented a structured Git workflow.
* Added release tags.
* Added protected branches.

### Documentation

Added or expanded:

* README
* CHANGELOG
* CONTRIBUTING
* History reconstruction documentation
* Release packaging workflow

---

## Bug Fixes

Resolved numerous issues including:

* Settings failing to save
* Settings migration failures
* Profile migration failures
* Traction settings persistence
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

Future releases will focus on:

* Community feedback
* Hardware compatibility
* SteamOS compatibility
* Performance improvements
* Bug fixes
* Incremental enhancements

---------------------------------------------------

## v0.5.0-alpha
- Added surface-state and traction-state decoding.
- Added dynamic R2 traction feedback.
- Added fixed response curves: Linear, Progressive and Aggressive.
- Added compact telemetry health, packet rate and latency diagnostics.
- Added per-car profile assignment foundation with opt-in automatic mode.
- Custom response curves are intentionally out of scope.

## v0.4.0-alpha

- Apply effect sliders and enable/disable changes without restarting the engine.
- Add preset creation, selection, loading, duplication and deletion.
- Add controller diagnostics: transport, battery where available, product ID, serial and HID path.
- Add controller-focusable test buttons for pedal resistance, ABS, gear kick and rev limiter.
- Preserve exact-child process control for safe engine restarts.

### Changed
- Live settings persistence
- Improved Decky frontend
- Improved backend process management
- Safer deployment workflow

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
- Restart engine control

### Changed
- Native HID communication
- Safe backend process handling

### Fixed
- Rev limiter behaviour
- Process shutdown handling
- SteamOS compatibility

---

## v0.2.0

### Added
- Initial Decky plugin prototype
- Linux backend proof of concept
- UDP telemetry support
- DualSense detection

### Changed
- Ported Windows implementation to Linux

---

## v0.1.0

### Added
- Initial SteamOS proof of concept
- Basic telemetry reception
- Basic DualSense communication

