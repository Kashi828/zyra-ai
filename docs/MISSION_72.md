# ZYRA AI — Mission 72
## Persistent Task Control + Checkpoints

Task supervision state is now persisted in the existing SQLite security
database.

### Persisted task state
- task ID
- owner device ID
- lifecycle status
- approval-required flag
- cancellation state
- structured checkpoint
- update timestamp

### Recovery
A new process can rebuild the task-control registry from durable records.
Terminal tasks are excluded from the recoverable queue.

### Control semantics
Approval and cancellation remain device-owner constrained. Checkpoints can be
updated independently of status so an autonomous worker can persist its last
safe continuation point.

### Reconciliation note
The persisted registry provides recovery state, but an actual workflow worker
must still reconcile recovered tasks against its own execution engine before
resuming work. No task is automatically executed merely because it is marked
recoverable.
