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

## What does NOT get a fragment

`documentation/changelog-standard.md:94` is explicit and it is the rule most easily broken here:

> *"**Internal-only changes**: refactors, test-only changes, and CI changes that produce no
> user-visible effect MUST NOT appear in `CHANGELOG.md`. They live in commit history only."*

So: no fragment for a refactor, a test-only change, a CI job, a lint fix, a review document, or a
change to this file. Two entries were removed from `CHANGELOG.md` for breaching this - a CI
coupling checker and a "repository scaffolding" line - after a conformance re-sweep found them.

**Where the line falls on this repository specifically, because it is genuinely not obvious and
guessing produced the breach.** This is a public, pre-release repository whose only shipped output
so far *is* documents. That makes the tempting inference - "we have no users, so nothing is
user-visible, so nothing counts" - exactly backwards. The right test is not whether code shipped:

- **A document published in this repository IS user-visible.** The design, the ADRs, the threat
  model, the data inventory, the security policy, the research reports and the credential checklist
  are all things a reader of the public repo consumes. They get fragments.
- **Something that only changes how we produce those documents is not.** The CI gates, the coupling
  checker and its controls, the fragment workflow, the docs directory layout, review rounds and
  their reports. These are the machinery, not the output. Commit history only.
- **A test is never user-visible on its own.** A test that proves a *behaviour* belongs in the entry
  for that behaviour, not in an entry of its own.

When it is genuinely ambiguous, leave it out. A missing entry is recoverable from commit history;
an entry that should not exist is a standards breach in a published file.
