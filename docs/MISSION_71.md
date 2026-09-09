# ZYRA AI — Mission 71
## Live Workflow Supervision: Approval + Cancellation

Mission 71 turns the task event stream into a real supervision channel.

### Control plane
- Each remotely supervised task is registered with an owner device.
- Approval is allowed only while the task is awaiting approval.
- Cancellation is allowed only for non-terminal tasks.
- Both controls require an authenticated device-bound session.
- Cross-device control is rejected.

### Realtime
Approval and cancellation immediately publish normalized task events to the
same realtime hub used by Android.

### Android
Task control API and a realtime task timeline adapter provide the UI-facing
contracts for approval, cancellation, and live progress.

### Important
The registry currently tracks active execution control in memory. A later
mission should persist task-control state/checkpoints so controls survive
process restarts and can be reconciled with the autonomous workflow engine.
