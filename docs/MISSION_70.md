# ZYRA AI — Mission 70
## Agent Runtime → Realtime Task Streaming

Mission 70 connects autonomous task lifecycle events to the unified realtime
hub used by Android.

### Normalized lifecycle
- `task.queued`
- `task.planning`
- `task.running`
- `task.approval_required`
- `task.completed`
- `task.failed`
- `task.cancelled`

Each event can carry task ID, device ID, status, phase, detail, and structured
payload.

### Architecture
Agent/orchestrator/workflow
→ task realtime bridge
→ unified realtime event hub
→ authenticated WebSocket
→ Android event listener/timeline.

The event bridge is intentionally separate from task execution; it reports
state and does not authorize or execute privileged actions itself.
