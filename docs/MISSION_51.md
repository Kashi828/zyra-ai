# ZYRA AI — Mission 51
## Product Configuration & Permissions Foundation

Mission 51 prepares ZYRA for a user-facing release.

Product configuration:
- explicit development/staging/production environments
- local-first production defaults
- remote access disabled by default
- sensitive-action confirmation enabled by default
- optional notifications and telemetry
- explicit agent autostart setting

Permission profiles:
- capabilities are device-scoped
- blocked capabilities override granted capabilities
- sensitive capabilities can require confirmation
- grants and blocks remain separate from the AI model

The UI should expose these settings clearly and never hide security-critical state.
