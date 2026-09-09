# Contributing to ZYRA AI

## Mission workflow

Keep one focused commit per mission.

Example:

    mission-92: repository hygiene

Run before pushing:

    python -m pytest -q
    python -m compileall -q .
    node --check electron/main.js
    node --check electron/preload.js

## Safety

Do not commit:
- API keys, passwords, session tokens, certificates, private keys
- local SQLite databases
- personal ZYRA configuration
- build output or installers

Changes that add a new privileged OS action must pass through ZYRA's existing policy,
authorization, and audit layers rather than exposing raw shell access to the model.
