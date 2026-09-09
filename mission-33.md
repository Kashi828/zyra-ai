# Mission 33 — Android Live Agent Experience

Mission 33 connects the Android companion UI to ZYRA's realtime agent flow.

## Added
- Live agent event stream on Android.
- Command submission using authenticated envelopes.
- Approval and cancellation controls for action events.
- Local Android notifications for completed/failed work and approval requests.
- Persistent connection lifecycle continues to use the existing reconnect foundation.
- PC-side authorization remains authoritative.

## Important deployment notes
- The current realtime server is still intended for trusted/local deployment unless TLS is configured.
- The Android app requires the paired device secret through a secure pairing flow; do not hard-code production secrets.
- Production push notifications should use Android's approved background execution/notification architecture.
