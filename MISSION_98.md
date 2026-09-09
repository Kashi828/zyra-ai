# ZYRA AI — Mission 98

## Cross-platform beta build pipeline

- Converted the Android source scaffold into a real Gradle application.
- Added Android build configuration using AGP 9.3.1, Kotlin 2.4.20, Gradle 9.5, and JDK 17.
- Added a minimal secure companion launcher activity and Android manifest.
- Added GitHub Actions CI for Python, Windows NSIS, and Android APK builds.
- Added a beta-release workflow that publishes Windows `.exe` and Android debug `.apk` artifacts as a GitHub prerelease from the `beta` branch.
- Beta Android builds are installable debug APKs; production signing remains a release-hardening step.
