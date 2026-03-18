
Persistent Story Universe Platform

AI powered storytelling platform with persistent worlds.

Local setup notes:
- Use `local_backend_env.example.bat` as the tracked template for backend environment values.
- Run `setup_local_backend_env.bat` to create a local-only `local_backend_env.bat`.
- `local_backend_env.bat`, virtual environments, caches, logs, and generated batch output are intentionally git-ignored.
- If a secret was ever used in a blocked push attempt, rotate it even if GitHub prevented the push.
