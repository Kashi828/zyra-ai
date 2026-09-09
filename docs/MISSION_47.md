# ZYRA AI — Mission 47
## Persistent Transfer Recovery

Mission 47 adds restart-safe transfer state using a local SQLite store.

Persisted state includes:
- transfer identity and device endpoints
- destination path
- total/transferred byte counts
- next chunk sequence
- expected SHA-256
- lifecycle status

Recoverable states are queued, running, and paused.

On restart, ZYRA can restore a transfer checkpoint and use the already-present
destination size as a bounded resume point. Final manifest SHA-256 verification
remains required before completion.

Runtime databases are local artifacts and are excluded from release ZIPs.
