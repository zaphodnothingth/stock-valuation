
# Agent Core Rules

Succinct, always-apply rules for any automated agent or contributor modifying this repository.

1. Scope changes narrowly: modify only files directly required for the requested change. Do not make unrelated refactors.
2. Preserve behavior: do not change public behavior or CLI semantics without tests and explicit owner approval.
3. Tests & lint: run unit tests and fix failures for any files you change; add tests for new logic when practical.
4. Docs: update `docs/` and `README.md` when behavior, CLI flags, or user-facing outputs change.
5. No secrets: never commit credentials, keys, or secrets. Use `.env` and ensure `.gitignore` excludes sensitive files.
6. Dependencies: do not add runtime dependencies without prior approval; prefer stdlib or small well-maintained libs.
7. Offline-first: respect the cache-first design — use `cache/` for tracked ticker lists and provide offline fallbacks.
8. Commits: create small, focused commits with clear messages; do not bundle unrelated changes.
9. License changes: do not add or change project license text without explicit owner instruction.
10. When uncertain: open an issue or ask the owner before making large or risky changes.

Keep edits minimal and reversible; rely on git history for archival details.
