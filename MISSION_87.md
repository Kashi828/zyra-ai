# ZYRA AI — Mission 87

## First-run onboarding

- Persistent onboarding controller built on existing non-secret setup state.
- Setup API exposes onboarding status, completion, and repair/reset.
- Desktop onboarding panel verifies required runtime checks before completion.
- Optional voice status is displayed without blocking setup.
- Recheck/Continue actions avoid storing credentials in the renderer.
- Added automated tests for setup state transitions.

## Safety

No privileged installation, credential collection, or automatic network download was added.
