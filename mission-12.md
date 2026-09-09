# Mission 12 — Universal Handoff & Notifications

Mission 12 adds the cross-device UX foundation for ZYRA:

- Text clipboard handoff messages with size limits.
- File staging with SHA-256 integrity verification and a configurable 250 MiB safety ceiling.
- Local notification queue for Android/PC task results.
- Read-state tracking for notifications.
- Task update event schema for continuation across devices.

## Security posture

All new actions must still pass ZYRA policy/permission checks. File transfers verify both size and SHA-256 before finalization. Destination filenames are sanitized with `Path.name` to prevent traversal. Clipboard data is size-limited.

The transport layer from Mission 11 remains responsible for device authentication/integrity. This mission does not claim end-to-end encryption by itself.

## Example commands

```text
"Send this text to my PC."
"Send report.pdf to my phone."
"Tell my phone when the build finishes."
"Show my unread ZYRA notifications."
```
