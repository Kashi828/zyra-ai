# ZYRA AI — Mission 48
## Automatic Transfer Recovery

On startup, ZYRA scans recoverable transfer checkpoints and determines:
- resume from a valid existing destination
- resume from the actual shorter destination boundary
- restart queued work when checkpoint data is missing
- fail invalid checkpoints

A recovered transfer still requires the normal authenticated device/session
path and final SHA-256 verification before it can become completed.
