# ZYRA Mission 17 — Real Android Transport Integration

Mission 17 moves the Android companion from a demo UI toward a real authenticated WebSocket client.

## Included
- Local WebSocket hub on the Windows side (`communication/transport/realtime_server.py`)
- Authenticated message envelopes with HMAC-SHA256
- Freshness window and nonce replay protection
- Device revoke support in the hub
- 64 KiB message-size ceiling
- Android OkHttp WebSocket client with automatic reconnect/backoff
- Android Keystore-backed encrypted local secret storage
- Android network permission already present from earlier missions

## Security boundary
The PC policy engine remains the authority for privileged actions. The transport authenticates a paired device; it does not grant the device unrestricted OS access.

The included realtime hub is intentionally suitable for trusted/local-network development. Do not expose it directly to the public internet. A production WAN relay needs TLS, stronger identity/key management, rate limiting, abuse controls, and secure remote discovery.
