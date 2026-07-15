# Contributing

Thank you for your interest in contributing to **Forza DualSense Haptics for Decky Loader**.

Whether you're fixing a bug, improving documentation, adding new features, or simply suggesting improvements, contributions are welcome.

---

# Development Philosophy

This project has a simple goal:

> **Improve the driving experience through meaningful controller feedback.**

Features should enhance immersion and help the driver understand what the car is doing, without adding unnecessary complexity or excessive configuration.

Whenever possible:

- Prefer simplicity over feature creep.
- Build intuitive feedback rather than visual clutter.
- Keep the user interface clean.
- Prioritise reliability over adding more options.

---

# Repository Workflow

Development follows a simple Git workflow.
main
#│
#├── develop
#│
#└── feature/vX.Y.Z

## main Contains stable releases. Every commit on `main` should represent a working version of the project. ## develop Integration branch for upcoming releases. Completed feature branches are merged here before the next release. ## Feature branches New work should be completed on feature branches. Examples:
feature/v0.6.1 feature/new-surface-feedback feature/profile-improvements


Feature branches should remain focused on a single logical change.

---

# Coding Standards

## General

- Keep code readable.
- Prefer explicit code over clever code.
- Comment **why**, not **what**.
- Keep functions focused on a single responsibility.

## Backend (Python)

- Follow PEP 8 where practical.
- Avoid unnecessary dependencies.
- All settings must remain backwards compatible.
- New settings must be included in migration logic.

## Frontend (TypeScript / React)

The UI should remain intentionally simple.

New controls should only be added when they provide meaningful value.

Advanced configuration should remain hidden behind expandable sections wherever possible.

---

# User Interface Guidelines

The main settings page should answer:

> **"What features do I want enabled?"**

Advanced sections should answer:

> **"How do I want those features to behave?"**

Avoid overwhelming users with large numbers of sliders or configuration options.

---

# Haptic Design Principles

Every effect should communicate a different part of the driving experience.

#| Effect | Purpose |
#|————|————|
#| Pedal Resistance | General throttle and brake feel |
#| Dynamic Traction Guidance | Communicates available grip through progressive trigger resistance |
#| ABS Vibration | Indicates brake lock intervention |
#| Gear Kick | Represents drivetrain shifts |
#| Rev Limiter | Indicates engine limiter |

Avoid multiple effects feeling identical.

Different telemetry should produce clearly distinguishable controller feedback.

---

# Testing Checklist

Before submitting changes, verify:

- Plugin builds successfully
- Plugin deploys successfully
- Backend starts correctly
- No Python exceptions
- No TypeScript build errors
- Settings persist correctly
- Existing settings migrate correctly
- Profiles load correctly
- Automatic car profiles function correctly
- Controller diagnostics remain operational
- Live telemetry continues updating

If modifying haptic behaviour:

- Test with multiple vehicles where practical.
- Verify effects remain distinct.
- Avoid introducing oscillation or unintended vibration.
- Confirm behaviour remains smooth during normal driving.

---

# Pull Requests

Please keep pull requests focused.

A pull request should ideally solve one problem or implement one feature.

Include:

- What changed
- Why it changed
- Any user-visible behaviour changes
- Testing performed

---

# Bug Reports

Helpful bug reports should include:

- SteamOS version
- Decky Loader version
- Controller firmware
- Game tested
- Plugin version
- Steps to reproduce
- Relevant logs if available

---

# Feature Requests

Feature requests are encouraged.

Before suggesting a feature, consider:

- Does it improve the driving experience?
- Does it increase immersion?
- Can it be implemented without complicating the UI?
- Does it align with the project's philosophy?

---

# License

By contributing to this project, you agree that your contributions will be licensed under the project's MIT License.
