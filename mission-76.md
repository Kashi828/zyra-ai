# Mission 76 — Local Windows Voice

## Added

- `services/local_voice.py`
  - bounded Windows microphone recording via optional `sounddevice`
  - WAV conversion
  - local `faster-whisper` STT adapter
  - injectable model support for testing
  - explicit dependency errors instead of silent cloud fallback
- `ZyraRuntime.submit_voice_audio(...)`
  - turns captured audio into a normal ZYRA task through the existing voice gateway
- tests covering audio format, input bounds, optional dependency handling, and STT behavior

## Design

The voice stack remains local-first and provider-neutral. If `sounddevice` or
`faster-whisper` is not installed, the application does not silently send audio
to a cloud service. A deployment can install a local model and use CPU or a
configured accelerator.

Wake word, VAD/continuous listening, real TTS, and Android microphone transport
remain separate missions so each piece can be secured and tested independently.
