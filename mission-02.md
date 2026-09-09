# ZYRA AI — Mission 02: Working Agent Core

Mission 02 turns the architecture into an executable, dependency-light agent shell.

## Included
- Deterministic planner for common PC commands
- Granular tool registry
- Permission + allow-list policy engine
- Medium/high risk confirmation gate
- Emergency stop / resume
- Persistent audit log
- Windows application launch tool
- File read/search/create tools
- Explicit terminal tool behind confirmation
- Unit tests

## Supported commands
- `open <application>`
- `search files for <name>`
- `read file <path>`
- `create folder <path>`
- `create file <path> ['content']`
- `run command <command>`
- `stop`
- `resume`

## Run
From the repository root:

```powershell
python run_agent.py
```

Run tests:

```powershell
python -m unittest discover -s tests -v
```

## Safety boundary
The deterministic planner is deliberately small. It does not attempt unrestricted natural-language execution. The next mission can connect an LLM planner while preserving the same policy/tool boundary.
