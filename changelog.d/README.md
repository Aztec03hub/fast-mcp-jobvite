# Changelog fragments

Agents working in worktrees drop a fragment here instead of editing `CHANGELOG.md`
directly, so parallel work never conflicts on one file.

**One fragment per unit of work.** Filename: `<task-id>-<slug>.md`, e.g. `07-jobvite-client.md`.

Format:

```markdown
### Added
- Jobvite HTTP client with token-bucket rate limiting. (task #7)

### Fixed
- ...
```

Use only these headings: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.

Only the orchestrator merges fragments into `CHANGELOG.md` and deletes them afterwards.
