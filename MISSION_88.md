# ZYRA AI — Mission 88

## Startup lifecycle gate

- Added a persistent desktop startup decision: onboarding vs workspace.
- Exposed `/v1/setup/startup` for the renderer.
- Renderer now fails closed to onboarding when startup state cannot be determined.
- Added startup gate script and workspace visibility rules.
- Desktop startup lifecycle remains local-first and does not grant extra OS privileges.
