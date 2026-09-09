# Mission 79 — Voice Activity + Spoken Task Updates

## Added

- Dependency-free PCM16 RMS voice activity detector
- Configurable speech threshold, minimum speech duration, and silence timeout
- Provider-neutral task status announcer with duplicate suppression
- Desktop microphone silence detection using the Web Audio analyser when available
- Automatic stop after sustained silence
- Spoken task lifecycle updates through the desktop runtime's local
  `speechSynthesis` interface
- Approval-required, completion, failure, and cancellation announcements

## Safety and UX

Voice activity detection is bounded and runs locally in the desktop process.
Automatic stopping only ends microphone capture; it never automatically approves
or executes a sensitive action. Task execution continues to use the existing
ZYRA security and approval path.

## Next

Mission 80 can add a proper packaged Windows desktop shell/runtime bridge and
wire authenticated voice session lifecycle into the desktop app instead of
using only the loopback bootstrap.
