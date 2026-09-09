# ZYRA AI — Mission 46
## Transfer Controls & Notifications

Adds resumable transfer checkpoints and user-visible event mapping.

Checkpoints:
- transferred byte count
- next chunk sequence
- running/paused/completed/failed/cancelled state

The Android layer maps transfer state into progress/completion/failure/cancelled notifications.
Real persistence and transport should use the authenticated ZYRA device session.
