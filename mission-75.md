# Mission 75 — Voice Foundation

ZYRA now has a provider-neutral voice boundary shared by the secure runtime.

## Added

- `core/voice.py`
  - voice sessions bound to an authenticated device
  - transcript normalization and size limits
  - pluggable speech-to-text provider
  - pluggable text-to-speech provider
  - voice-to-goal handoff into the existing task pipeline
- `api/voice_routes.py`
  - authenticated voice session start/end
  - authenticated transcript-to-task endpoint
  - authenticated raw-audio transcription endpoint
- `api/app_factory.py`
  - application-level `VoiceGateway` wiring
- `tests/test_mission75_voice.py`
  - security, routing, session binding, limits, and provider injection coverage

## Safety

Voice input never bypasses the normal task authorization/security path. The gateway only converts a spoken/transcribed request into a normal ZYRA goal. Sensitive execution still remains subject to the existing permission, approval, authorization and audit controls.

## Next

Mission 76 can add a concrete local/offline STT adapter and desktop microphone capture without coupling the security layer to a speech vendor.
