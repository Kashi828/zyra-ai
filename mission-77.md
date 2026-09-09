# Mission 77 — Windows Voice UI

## Added

- Voice button in the desktop assistant
- Listening panel with live status and meter
- Language selection for English India/US, Hindi, and Kannada
- Start/stop listening controls
- Browser/desktop SpeechRecognition integration
- Transcript is written into the existing ZYRA goal field for review
- Existing task execution path remains unchanged

## Important

This mission adds the Windows-facing voice UX and speech-recognition adapter.
It does not claim offline recognition: the browser speech-recognition API may
use the runtime's configured speech service. Mission 76 remains the local
`faster-whisper` path for deployments that want explicitly local STT.

## Next

Mission 78 can bridge the desktop UI directly to the local audio recorder/STT
adapter and add a real TTS reply channel.
