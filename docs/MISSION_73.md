# ZYRA AI — Mission 73
## Workflow Recovery + Checkpoint Reconciliation

Mission 73 adds a recovery engine that compares durable task-control records
with any currently known runtime state before resuming work.

### Decisions
- `resume` — checkpoint is safe to reuse.
- `await_approval` — approval must be re-established after restart.
- `manual_review` — persisted and live checkpoints conflict or state is unclear.
- `reconcile_terminal` — live runtime has already reached a terminal state.
- `discard` — task was already cancelled/terminal.

### Safety rule
A recoverable task is not automatically executed merely because it exists in
the database. The recovery scan produces a decision, and an explicit
acknowledgement is required before a safe `resume` can be approved.

This prevents a stale checkpoint from silently triggering privileged work after
a process restart.
