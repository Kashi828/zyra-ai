# Mission 140 — In-Memory Flutter Session Context

## Goal
Keep the authenticated device/session context consistent across the Flutter Home and Devices surfaces during an app run without persisting credentials.

## Delivered
- Added `ZyraSessionContext` as an app-process-only state holder.
- Stores only `device_id` and `session_id` required by the protected APIs.
- Devices initializes its session fields from the shared context.
- Loading the Devices session inventory synchronizes the shared context.
- Session revocation uses the shared authenticated context when available.
- No device secret, refresh token, or other authentication secret is persisted.

## Security invariants
- The context is memory-only and disappears when the application process ends.
- Backend authorization remains authoritative.
- Session identifiers are not treated as secrets or exchanged for stronger credentials.
