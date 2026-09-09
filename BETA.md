# ZYRA AI beta build

This branch is used to produce the first public beta prerelease.

## Windows
The CI build produces a per-user x64 NSIS installer. The current backend remains a Python-backed local service, so the beta installer assumes Python 3.11+ and the required backend dependencies are available on the test machine.

## Android
The CI build produces an installable debug APK for closed beta testing. Do not treat the debug APK signing identity as the production signing identity.

## Release
The beta release workflow creates a GitHub prerelease tagged from `release/beta-version.txt` and attaches both platform artifacts after successful builds.
