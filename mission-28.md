# Mission 28 — Production Observability & Reliability

Adds structured JSONL events, in-process metrics, agent run tracking, health diagnostics, and support-bundle generation.

## Reliability goals
- Make every important agent run traceable by `run_id`.
- Make failures diagnosable without exposing credentials or raw secrets.
- Keep metrics local-first and dependency-light.
- Keep support bundles limited to diagnostics and local logs.

## Health
`diagnostics.health.check()` reports runtime/version/platform information, optional dependency availability, uptime, and local metrics.

## Support bundle
`diagnostics.support.build_support_bundle()` creates a ZIP containing health metadata and the local structured log when present. It intentionally does not copy environment variables, credentials, browser cookies, or arbitrary user files.
