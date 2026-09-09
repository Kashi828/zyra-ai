# Mission 78 — Direct Local Voice Integration

## Added

- Optional local STT initialization using `ZYRA_VOICE_STT=local`
- Optional local TTS initialization using `ZYRA_VOICE_TTS=local`
- Local pyttsx3 TTS adapter
- Voice capabilities endpoint
- Authenticated voice speak endpoint
- Loopback-only desktop voice bootstrap for a device/session
- Desktop MediaRecorder microphone capture
- Captured audio sent to the authenticated voice transcription endpoint
- Local transcript inserted into the existing goal box
- Browser SpeechRecognition remains as a fallback when MediaRecorder is unavailable

## Security

Desktop credential bootstrap is limited to loopback clients. Captured voice
audio is not accepted by the STT endpoint without a valid ZYRA device/session.
Voice-to-task execution still uses the normal goal/task pathway and existing
approval/security controls.

## Local voice setup

Optional dependencies are listed in `requirements-voice.txt`. Local STT is
enabled with `ZYRA_VOICE_STT=local`; the model and compute settings can be
changed with the corresponding `ZYRA_VOICE_STT_*` environment variables.

## Next

Mission 79 can add voice activity detection (VAD), silence timeout, push-to-talk
polish, and streaming task-status speech responses.
