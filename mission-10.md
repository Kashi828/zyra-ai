# Mission 10 — Background Tasks + Device Foundation

## Added
- SQLite-backed background task store and scheduler.
- Long-running local tasks with persistent states: scheduled, running, pending_approval, completed, failed, blocked, cancelled.
- Scheduled jobs reuse the same agent planner and policy engine and cannot silently bypass confirmation requirements.
- Explicit Windows/Android device registry with pairing and revocation states.
- Task handoff message schema for future phone↔PC communication.

## Safety
Background execution does not auto-approve impactful tools. A job that needs confirmation moves to `pending_approval` instead of executing.

## Next
Build authenticated device-to-device transport, Android companion UI, notification delivery, and secure remote task dispatch.
