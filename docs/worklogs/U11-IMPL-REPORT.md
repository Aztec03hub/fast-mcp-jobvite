# U11 - `scripts/check_advisories.py`, the advisory-expiry owner

**Branch:** `impl/u11-advisories`, worktree `/tmp/impl-u11-work`, forked at `ff9461a`.
**Status:** built, gated, rebased onto `origin/main`. One gate is red **by design and attributably** - see "The one red gate" below. It is an obligation anchor the team lead applies, not a defect in this unit.

---

## What I read

Read in full, from the frozen object where the brief said to:

- `docs/DESIGN.md` via `git show 135c3ac:docs/DESIGN.md` - §10 around `:1454-1473`, my specification, plus `:1438` (the CI check list) and `:1479-1495` (§10.1).
- `docs/plans/IMPLEMENTATION-PLAN.md` - `### U11` at `:1084-1103`, and §4's shared-file table, in particular `:1365` (the `ci.yml` ownership row) and `:1368` (the `check-obligations.py` row).
- `docs/OBLIGATIONS.md` - the B75 row at `:76`, and B82 at `:82`.
- `docs/adr/0015-licence-gate-is-a-deny-list.md` - in full, before wiring the CI step.
- `.github/workflows/ci.yml` - the whole `supply-chain` job and the header comment at `:10-31`.
- `pyproject.toml` - the advisory-ignores block and its comment, the ruff select list, mypy config.
- TIER-1 standards from `/home/plafayette/claude_projects/evolv/MUST-READ-DOCS.md`: `backend/python.md` (the §6 `datetime.now(UTC)` clause at `:220-228`, line length at `:33-35`, import order at `:40-58`).

**Not read in full, and I am naming it rather than implying coverage:** `devops/ci-cd.md` and `devops/quality-gates.md` I consulted only through `docs/COMPLIANCE-SPEC.md`'s citations of them and ADR-0015's quotation of `quality-gates.md:288-306`. I did not open either file directly. Nothing in my unit turned on a clause I had not read, but that is a claim about what I hit, not a claim of coverage.

**No clause I read contradicts the brief.** Nothing to escalate under `priority: required`.

---

## What was built

**`scripts/check_advisories.py`** - 291 lines, stdlib only.

- Reads `[tool.fast-mcp-jobvite.advisory-ignores] entries` from `pyproject.toml` with `tomllib`.
- Emits `--ignore-vuln <id>` pairs on stdout, **derived from the same table rows it validates**. There is no second list of ids anywhere in the file - the two-lists defect `DESIGN.md:1520-1522` names by name.
- Exits non-zero on any expired entry.

Exit codes, fail-closed: `0` every entry legal, `1` an entry refused, `2` the gate could not run (unreadable file, unparseable TOML, unreadable `--now`). A missing manifest is `2`, never a `0` "empty table".

**One design question I had to settle, stated because it is a real decision and the design does not spell it out.** `DESIGN.md:1517` says "an expiry date no more than 30 days out" without saying *out from when*. I measure the budget from the entry's recorded `date`, not from now. Measured from now the budget would refill on every CI run and an entry could sit legal forever, which is the exact drift the expiry exists to stop; measured from `date` the budget is fixed when the judgement is made and cannot be extended without editing a recorded date that shows up in a diff. This is reasoning from the design's stated intent, not a licence the design granted, and `test_the_30_day_budget_is_measured_from_the_recorded_date_not_from_now` pins it. **If the team lead reads `:1466` the other way, that test is the one to change and the ADR is small.**

**Field requirements** (`DESIGN.md:1513-1518`): `id` required and non-blank, `date` required, `reason` required and non-blank, `expires` required, within budget, and not past.

**No runtime dependency added.** `tomllib` is stdlib on `requires-python = ">=3.12"`. `pyproject.toml` was touched **not at all** - the table was already correct and already empty, and U11's job was the mechanism, not ignores. `impl-u1-boot`'s edits to `[project.scripts]` and `[project] dependencies` cannot conflict with a file I did not modify.

**Files changed:**

| File | Change |
|---|---|
| `scripts/check_advisories.py` | new |
| `tests/test_advisory_gate.py` | new, 33 tests |
| `scripts/check-u11-advisory-controls.sh` | new, the mutation + amputation harness |
| `.github/workflows/ci.yml` | the Advisory audit block only, uncommented and its prose corrected |
| `docs/worklogs/U11-IMPL-REPORT.md` | this file |

`CHANGELOG.md` untouched, as instructed.

---

## How I pinned the clock

**Every date in `tests/test_advisory_gate.py` is a literal, and `now` is passed in as a literal.** Nothing in the test module calls `date.today()` or `datetime.now()`. The implementation takes `now` as a **parameter** to `check_entries(entries, now)` and never reads a clock inside it; the CLI has a `--now ISO-DATE` option that exists solely so the end-to-end arms can pin it too.

```
NOW      = 2026-08-28      RECORDED = 2026-08-20
EXPIRES_AT_30 = 2026-09-19   (exactly 30 days after RECORDED)
EXPIRES_AT_31 = 2026-09-20   (31 days: one day over)
EXPIRES_AT_NOW = 2026-08-28  (expires today; the last legal day)
```

This is what the brief warned about. The natural way to write these tests is `expires = today + timedelta(days=31)` judged against `today` - which passes against **any** threshold the implementation happens to use, and passes against an implementation that reads the clock twice and compares it to itself. With both sides pinned, `EXPIRES_AT_30` and `EXPIRES_AT_31` straddle a fixed number, and the harness confirms it: moving `MAX_IGNORE_DAYS` to 29 **or** to 31 turns a named test red.

**Each rejection is attributable to one field.** The over-budget entry has *not* expired; the expired entry is *within* budget. Neither can be passing for the other's reason. `test_the_expired_arms_entry_would_be_legal_but_for_its_expiry` runs the identical fixture against an earlier `now` and shows it honoured - a positive control on the fixture itself, not just on the arm.

---

## The five verification arms

All assert on the **emitted flags**, not only the exit code.

| Arm | Required | Result | Test |
|---|---|---|---|
| entry past its recorded expiry | rejected | **rejected**, no flags | `test_an_entry_past_its_recorded_expiry_is_rejected` |
| entry within its expiry | honoured **and flag emitted** | **honoured**, `["--ignore-vuln", "GHSA-xxxx-yyyy-zzzz"]` | `test_an_unexpired_entry_is_honoured_AND_ITS_FLAG_IS_EMITTED` |
| entry with no expiry | rejected | **rejected**, no flags | `test_an_entry_with_no_expiry_is_rejected` |
| expiry more than 30 days out | rejected | **rejected**, no flags | `test_an_expiry_more_than_30_days_out_is_rejected` |
| blanket ignore (no advisory id) | rejected | **rejected**, no flags | `test_a_blanket_ignore_with_no_advisory_id_is_rejected` |

Arm 2 is #15's positive control and it is asserted **twice**: once on the returned flag list, and once end-to-end on real stdout (`test_cli_emits_the_flag_on_stdout_for_a_legal_entry` asserts `stdout.strip() == "--ignore-vuln GHSA-xxxx-yyyy-zzzz"`).

Beyond the five: both boundaries of the budget (30 honoured, 31 refused); both boundaries of expiry (expires-today honoured, expires-yesterday refused); blank and whitespace ids; blank reason; missing `date`; non-date `expires`; quoted vs bare TOML dates; a bare string where an entry table belongs; the three fail-closed exit-2 paths; and **one illegal entry suppressing every flag in the table**, so a partial emit cannot honour the legal rows while CI believes it refused.

**33 tests, all passing.**

---

## Mutation and amputation results

`scripts/check-u11-advisory-controls.sh`, run under `PYTHONDONTWRITEBYTECODE=1`. It works on a **copy** of the tree and restores from a pristine copy, never `git checkout --` - which would have reverted my uncommitted work along with the mutation. Each control greps that the mutation landed before running, aborts if the target string is not found (so a control that stops editing anything fails loudly instead of passing), and greps the pristine file back after restoring.

```
15/15 controls fired.
```

**Mutation (7/7 fired)** - budget 30 to 31; budget 30 to 29; `<` to `<=`; comparison inverted; budget measured from `now` instead of `date`; flag misspelled `--ignore-vulns`; blank-id check weakened.

**Amputation (8/8 fired)** - and these are the ones asked for specifically:

| Amputation | Fired via |
|---|---|
| **the flag emission deleted entirely, gate still exits 0** | `test_an_unexpired_entry_is_honoured_AND_ITS_FLAG_IS_EMITTED` (9 failed) |
| **the CLI stops printing the flags, exit codes unchanged** | `test_cli_emits_the_flag_on_stdout_for_a_legal_entry` (1 failed) |
| the expiry check deleted | `test_an_entry_past_its_recorded_expiry_is_rejected` (4 failed) |
| the 30-day budget check deleted | `test_an_expiry_more_than_30_days_out_is_rejected` (2 failed) |
| the blanket-ignore check deleted | `test_a_blanket_ignore_with_no_advisory_id_is_rejected` (4 failed) |
| the missing-expiry check deleted | `test_an_entry_with_no_expiry_is_rejected` (1 failed) |
| the written-reason check deleted | `test_an_entry_with_no_reason_is_rejected` (2 failed) |
| the whole validator short-circuited to accept everything | `test_an_entry_past_its_recorded_expiry_is_rejected` (25 failed) |

**The two bolded rows are the ones that matter, and they are the exact defect the brief named.** Delete the emission and the gate still exits 0 on a legal table - it simply emits nothing, silently disabling every ignore. Every exit-code assertion in the suite stays green through that. Both amputations were caught, by the flag-list assertion and by the stdout assertion respectively.

**So: amputation found no vacuous assertion in this unit.** I am stating that as a measured result of 8 amputations, not as a claim that none exists. The harness is committed and re-runnable, so the claim is checkable rather than a sentence in a worklog.

---

## The CI step, and B75

**Enabled only my block.** The other two commented blocks (`Capability drift diff`, `Coverage`, both DEFERRED TO U1) are untouched and still commented.

I also **rewrote the block's prose in place** rather than leaving it: its opening said "DEFERRED TO U11 ... U11 builds it and enables this step", which was false the moment I enabled it. It now reads "LANDED BY U11" and carries a stated ceiling on what a green means. This is inside my block.

### For `docs/OBLIGATIONS.md` - **I did not edit it. Two rows need your hand.**

**B75.** The anchor text `# - name: Advisory audit` **no longer exists in `ci.yml`** - my step is live, so the line is now `- name: Advisory audit` at **`ci.yml:385`**, without the comment marker. The anchor must be repointed, not just renumbered.

- **New class: still `CONTRADICTED`.** Two commented-out step blocks remain, deliberate and reasoned, with no ADR. **U11 closes the advisory third only.** It is not `MET`.
- **Suggested new anchor:** `.github/workflows/ci.yml:395`, text `# - name: Capability drift diff` - the first of the two survivors. Suggested amended note: *"Two commented-out step blocks remain (capability-drift diff, coverage), both DEFERRED TO U1, deliberate and reasoned, with no ADR. The advisory third closed at U11."*

**B82**, which I broke as a side effect and which you should apply at the same time: `Relative links resolve` was at `ci.yml:532` and is now at **`ci.yml:548`**. My edit added 16 lines above it. The checker prints this exact repointing itself.

### The one red gate

`check-obligations.py` exits **1** on my branch, on those two rows and nothing else. `--controls` exits 1 too, because it aborts rather than run controls over a red map.

**Positive-controlled:** I built a second worktree at the unmodified `ff9461a` and ran both there - `obligations:0`, `obl-controls:0`. So the two failures are caused by my `ci.yml` edit and by nothing else, and they clear when you apply the two repointings above.

---

## Gate results, by exit code

Run in `/tmp/impl-u11-work` **after** the rebase onto `origin/main`:

```
ruff:0
fmt:0
pytest:0          126 passed, 2 deselected, 0 skipped
obligations:1     B75 + B82 anchors - yours to apply, see above
obl-controls:1    aborts because the real map is red; clears with obligations
measurements:0
coupling:0
filetype:0
mypy:0            (not on the brief's list; run anyway, 16 source files)
```

**Baseline was 93 passed, 2 deselected, 0 skipped. Now 126 passed, 2 deselected, 0 skipped** - my 33, and **zero skips**. The count is from the terminal, not predicted.

---

## The defect I found

**`pip-audit` is required by `DESIGN.md:1489` and is run by no CI step at all.** Filed as **task #26**; not fixed here.

`grep -rn "pip-audit" .github/` returns **only comment lines**. My step enforces the expiry half correctly and prints the `--ignore-vuln` flags, but **nothing consumes them** - the design's model is `pip-audit $(python scripts/check_advisories.py)`, and the tool half was never wired. The ignore mechanism is now fully built and connected to nothing, and the dependency tree is not audited.

I did not fix it, for three binding reasons: `IMPLEMENTATION-PLAN.md:1365` gives me exactly my own block; `pip-audit` is not in the frozen lock and collision 10 gives U1 the dependency slot this wave; and `uv run --with pip-audit` would repeat **exactly** the defect ADR-0015 records for `pip-licenses` - a gate auditing the frozen resolve while itself unfrozen.

**I wrote that ceiling into the step's own comment block**, so "Advisory audit passed" cannot be misread as "no advisories". Task #26 carries a suggested fix and the ordering constraint (the expiry check must fail *before* `pip-audit` runs, or the expiry is advisory only).

**Also stale, and not mine to touch** (`:1365` says touch nothing else): `ci.yml:21-25` still reads *"pip-audit + scripts/check_advisories.py -> U11 (the script does not exist ...)"*. The script exists now. One line, in U0's header comment.

---

## Merge

I did not merge or push. Rebased onto `origin/main` and re-ran the gate after the rebase; results above are post-rebase.

```
git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite merge --no-ff impl/u11-advisories
```

No `--ff-only` promised: `main` moves and I am not the only writer this wave.

**Worktree removed.** `/tmp/impl-u11-work` and the baseline worktree `/tmp/impl-u11-baseline` are both torn down, and `git worktree list` shows neither.

---

## What I did NOT verify

Things I could not settle, as distinct from things I did not attempt.

1. **That `pip-audit` actually accepts the flag string I emit.** `--ignore-vuln <id>`, repeated per advisory, is taken from the design and the plan, both of which assert it. **`pip-audit` is not installed in this environment and adding it is exactly the dependency I was told not to add**, so I could not run `pip-audit --help` and read the flag off the tool. Every test asserts the string the design specifies - if the design is wrong about `pip-audit`'s interface, all 33 tests still pass and the flags are wrong. **This is the single largest unverified thing in the unit** and it resolves the moment task #26 puts `pip-audit` in the lock.

2. **That the step passes in real CI.** It has never run on a GitHub runner. I ran the exact command locally: `uv run --frozen python scripts/check_advisories.py` exits 0 against the real manifest and resolves inside the frozen lock, adding nothing - which is the ADR-0015 property I was asked to preserve. But a local green is not a runner green.

3. **Whether the 30-day budget should be measured from `date` or from `now`.** I settled it by reasoning from the design's stated intent (above) and pinned it with a test. I could not settle it from the text, because `:1466` does not say.

4. **That there is no *fourth* commented-out block somewhere in `.github/`.** I grepped `ci.yml` and found exactly three, of which I enabled one. I did not sweep the other workflow files for the same pattern, so "three commented blocks" is B75's claim carried forward, verified in `ci.yml` only.

5. **`devops/ci-cd.md` and `devops/quality-gates.md` unread in the original.** Named above under "What I read". I did not open either directly.

6. **Anything about reachability.** Step 1 of the policy is human judgement and explicitly not mine. This gate enforces the *shape* of a recorded judgement - that one exists, names a single advisory, and has not expired. **A well-formed entry whose `reason` is a lie passes it cleanly**, and that ceiling is written into the script's own docstring so it is not over-trusted later.
