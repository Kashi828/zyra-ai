# Mission 108 — Electron Local API Routing

## Problem
The packaged desktop renderer is loaded from `file://`. Its root-relative `fetch("/v1/...")` calls were therefore resolved as local filesystem URLs instead of the loopback ZYRA backend, producing `Failed to fetch` during first-run setup.

## Changes
- Added a renderer fetch adapter in `desktop/index.html` that routes root-relative API requests to `http://127.0.0.1:8000` when running in the Electron shell.
- Added FastAPI CORS handling for the Electron `null` origin and localhost/loopback development origins.
- Added regression tests covering the renderer routing and CORS configuration.

## Security
The adapter routes only root-relative API paths to the local loopback backend. Remote access remains unchanged and the renderer stays sandboxed.
