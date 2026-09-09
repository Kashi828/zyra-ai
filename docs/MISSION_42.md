# ZYRA AI — Mission 42
## File Handoff + Universal Clipboard

Mission 42 implements the data plane foundation for PC <-> Android handoff.

File transfer:
- Builds a manifest containing filename, size, chunk size, and SHA-256.
- Streams bounded chunks.
- Enforces a 250 MB maximum transfer.
- Verifies size and SHA-256 after transfer.
- Isolates transfer logic from network transport so it can use the authenticated device channel.

Clipboard:
- Queues cross-device text clipboard items.
- Preserves source device and creation time.
- Keeps the item model transport-neutral.

Production integration must keep these operations behind device-session/capability authorization.
