### Added
- **`search_jobs`, and with it the first runnable server.** The tool composes every cross-cutting
  mechanism the earlier units built - configuration fail-fast, the RFC 9457 error contract, the
  audit path, the result cap and `_meta` - on the public job-data class, which is the least
  dangerous one in the tool surface. A single page is returned, capped at `JOBVITE_MAX_RESULTS`
  and reporting `showing N of total` rather than truncating silently. (task #2)
- `src/fast_mcp_jobvite/models/jobs.py`, the allow-listed output model for the job list. A field
  Jobvite returns that is not declared there does not reach the caller, and a new Jobvite field is
  dropped rather than failing the call. (task #2)
- **The fencing-path registry, generated from the output models rather than maintained beside
  them** (`models/fencing.py`). Model attributes are snake_case and fencing paths are Jobvite's
  camelCase, so two hand-kept lists that must correspond would be a defect waiting for the first
  schema change. Every field carries an explicit decision and a reason; a field with none raises
  at generation time rather than defaulting. Job fields take an explicit "not free text" decision,
  and U8 is where fencing actually fires. (task #2)
- `src/fast_mcp_jobvite/utils/constraints.py` under ADR-0012: the control-character and
  bidi-override rule every input model reuses. A name carrying a NUL or a bidi override is a
  well-formed short string that every length and regex check admits, which is why the rule is
  separate from `max_length`. (task #2)
- **The first credentialed arm in this repository**, `tests/credentialed/test_search_jobs_live.py`,
  and the first test file whose tests are all marker-excluded. Every credential read is inside a
  fixture body, so the module imports cleanly with no credential present. (task #2)
- `scripts/check-u5-jobs-controls.sh` (12 mutation rows, all firing) and
  `scripts/check-u5-jobs-amputation.sh` (11 amputation rows, all anchors applying), both wired
  into CI and `CONTRIBUTING.md`. (task #2)

### Changed
- **CI's credentialed-collect step now requires exit 0 and a non-zero collected count.** It
  accepted pytest's exit 5 as well, because the directory was empty and "the suite is empty" and
  "the suite is healthy" rendered identically. Now that an arm exists, the step distinguishes
  them. (task #2)
- `tests/test_server.py`'s "registers no tool yet" case is **rewritten** rather than deleted. Its
  assertion was true of a server with no tool modules rather than a property worth keeping; it now
  asserts what it was actually protecting - that registration goes through
  `settings.enabled_tools` - with a paired case proving the gate can still refuse.  (task #2)
