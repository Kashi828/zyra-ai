# ZYRA AI — Mission 89

## First-run setup wizard

- Added a persistent three-step setup state machine:
  diagnostics → configuration → complete.
- Added wizard status, diagnostics, complete, and reset endpoints.
- Onboarding controller now uses the wizard while preserving its existing API.
- Added renderer setup-wizard controller and lifecycle events.
- No credentials, tokens, or privileged operations are stored by the wizard.
