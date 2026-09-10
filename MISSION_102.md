# Mission 102 — Android Beta Release Hardening

## Goal
Harden the Android beta package metadata and prepare the project for a repeatable signed release pipeline without committing signing credentials.

## Implementation
- Added centralized `app_name` Android resource metadata.
- Added packaging exclusions for common dependency license/signature metadata collisions.
- Kept release and debug build types explicit.
- Kept the current beta artifact as a debug APK until repository signing secrets are configured.
- No keystore, passwords, or signing credentials are stored in the repository.

## Release boundary
The Android release workflow may produce the installable debug beta today. A production-signed APK/AAB requires a user-provided Android keystore and GitHub Actions secrets; those credentials must remain outside source control.
