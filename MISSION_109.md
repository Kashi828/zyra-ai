# Mission 109 — Startup & Onboarding Regression Lock

## Goal
Prevent the first-run preparation/onboarding state regression from returning in future beta builds.

## Changes
- Added automated regression coverage for the persistent startup state machine.
- Verified a fresh installation enters onboarding/setup-required state.
- Verified passing diagnostics does not mark the wizard complete.
- Verified onboarding completion transitions startup to workspace.
- Verified a diagnostics reset returns the installation to the setup-required state.

## Verification
The tests use an isolated temporary `FirstRunState` file, so they do not touch a developer's real `%LOCALAPPDATA%/ZYRA AI/setup.json` state.

## Safety
This mission changes test coverage only. It does not expand OS, shell, browser, credential, network, or remote-control permissions.
