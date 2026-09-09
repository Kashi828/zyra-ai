# ZYRA AI Release Checklist

## Beta

1. Run the full Python test suite.
2. Run Python compilation.
3. Validate Electron JavaScript syntax.
4. Run `npm run diagnostics`.
5. Build on a Windows runner with:
   `npm run build:win`
6. Verify the generated NSIS installer.
7. Create a Git tag matching the release version.

The development environment used to prepare source missions is not treated as a
Windows installer build runner. A real `.exe` release must therefore be produced
on Windows (or an equivalent Windows CI runner).
