# ZYRA AI — Mission 49
## Background Transfer Recovery Worker

Adds a background worker that periodically scans recoverable transfers and
dispatches only safe resume jobs.

The worker:
- runs independently from the foreground agent
- can be started/stopped cleanly
- dispatches bounded resume checkpoints
- records the most recent jobs
- does not bypass device authentication or transfer authorization

The dispatcher must route each resume through the authenticated PC <-> Android
channel before data is sent or accepted.
