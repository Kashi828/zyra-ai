# Mission 09 — Local Memory & Persistent Context

ZYRA now has local-first persistent memory backed by SQLite.

## Capabilities
- Store explicit memories with kind, source, and importance.
- Search memories lexically and retrieve recent context.
- Delete one memory or clear the database through the memory service.
- Expose memory as policy-gated agent tools (`remember`, `recall`, `delete_memory`).
- Keep the default database at `data/memory.db` so no external service is required.

## Privacy model
Memory is local by default. The agent does not automatically upload memory contents to a cloud provider.

## Run
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

## Future upgrade
A local embedding index can be added later for semantic retrieval without changing the memory API.
