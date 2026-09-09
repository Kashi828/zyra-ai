# ZYRA AI — Mission 74
## Workflow Recovery Execution

Mission 74 connects reconciled recovery decisions to an explicit workflow
resume executor.

### Resume rules
- Recovery must first resolve to `resume`.
- Explicit acknowledgement is required before a workflow runner is invoked.
- The persisted checkpoint is passed unchanged to the workflow runner.
- Awaiting-approval tasks remain blocked until approval is re-established.
- Cancelled or terminal tasks cannot be resumed.
- Runner failures transition the task to `failed` and publish a realtime event.

### Security
Recovery acknowledgement is authenticated and bound to the task owner device.
The recovery layer itself does not grant extra Windows capabilities; normal
command authorization remains the authoritative privilege boundary.

### Operational behavior
If no workflow runner is configured, a validated recovery becomes `ready` but
is not executed. This makes the architecture safe to deploy before the final
workflow runtime adapter is installed.
