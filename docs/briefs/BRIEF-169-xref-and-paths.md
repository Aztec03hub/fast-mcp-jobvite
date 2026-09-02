# BRIEF — #169: a zero that is 62 vacuous skips, and a path list that is still hand-kept

You are `suborch-169`. Three items left from review round R17. **The
first is the real one; the other two are smaller and one may be a
no-op.**

## §A — Standing rules (read FIRST, in this order)

1. `docs/DESIGN.md` — FROZEN. 2. `docs/adr/` in number order.
3. `docs/OBLIGATIONS.md` 4. `docs/briefs/PROTOCOL-sub-orchestrators.md`
5. `CONTRIBUTING.md`
6. **`docs/reviews/REVIEW-R17.md`** and **`FINDINGS-168-range-before-paths.md`**
   — first-hand, not from this brief.

Hard rules:

- **NEVER print or commit a secret.** No `Co-Authored-By:` trailers, ever.
- **You do not push and you do not merge.**
- **Own worktree**, from `origin/main` at `0087e27` or later:
  `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/w169 -b fix/169-xref-and-paths`
- **`TaskGet` before acting on any assignment, and compare the TEXT.**
  ANY `TaskUpdate` re-emits a task's ORIGINAL description as an
  assignment, timestamped LATER than the completion, `assignedBy` naming
  you. Measured four times (#162). Never "check who sent it".
- **CI's exact invocations.** `uv run --frozen python`, never `python3`.
  `actionlint` needs `SHELLCHECK_OPTS=--severity=warning` — and if a
  tool is missing, SAY SO rather than claiming the gate. `suborch-167`
  did exactly that last run and it was the right call.
- **Report by `SendMessage` to `fastmcp-jobvite`**; findings to a `.md`.
- **Correct this brief where it is wrong.** Fifteen of fifteen agents
  have, and the last three corrections each changed what got built.

## §B — Files you OWN

    docs/reviews/measure-xref-population.py
    docs/reviews/REVIEW-R17.md        (its declaration line ONLY, if you widen it)
    docs/reviews/review-coverage-backlog.txt
    tests/test_audit_phase_sites.py   (L2 only)
    docs/reviews/<your findings .md>

**NOT yours:** `.github/workflows/ci.yml`, `check-review-coverage.py`,
`probe-coverage-ratchet.py`, `check-harness-anchors.py`,
`check-landing-published.py`. All were touched tonight and all are
settled; do not adjust them to make your work easier.

## §C — R17-M1, the one that matters: a zero over an empty population

`docs/reviews/measure-xref-population.py:48` excludes `docs/briefs/` and
`docs/reviews/`, while its docstring claims it covers "every tracked
`*.md` outside the RECORD paths" — and `check-review-coverage.py`
refuses `docs/briefs` as a RECORD path **by name**, so the exclusion
contradicts a live ruling.

**REMOVING THE EXCLUSION ALONE DOES NOT HELP, and this is the finding.**
It hard-codes `referent=None` outside `docs/adr/`, so briefs measure
**62 tracked, 0 MEASURED, 62 SKIPPED, 0 unresolved** — a completely
vacuous zero hiding **83 section references across 18 files**.

R17's own first run of it reported "0 across 0 files" and it nearly
published that: an `except ValueError: continue` had swallowed the whole
population.

**REQUIREMENTS:**

- **Never report a zero from this file without also reporting how many
  were MEASURED.** A zero over an empty population is the defect, and it
  has now fooled one reviewer already.
- Give the non-ADR paths a referent, or rule that they cannot have one
  and make the tool SAY so per file rather than counting them as clean.
- **Report the number of unresolved references you find.** If it is
  non-zero, that is a finding of its own and each one needs a decision —
  do not fix 83 citations silently.

## §D — R17-H2: unblocked, and probably smaller than it looks

#168 landed, so widening a declaration can no longer bank range
artifacts. R15 §1c's path list misses six paths — `CONTRIBUTING.md`,
`docs/DESIGN-FREEZE.txt`, `docs/README.md`, `scratch139/fix.py`,
`scratch139/measure.py`, `sweep.log` — and four of the six are in §1c's
OWN residual table ten lines above the proposal that omits them.

**RE-MEASURE BEFORE ACTING.** §1c's "PARTIAL 42 → 9" was taken when
PARTIAL was 42. It is **8** at `0087e27`. The remaining gain may be one
or two commits, in which case **say so and do nothing** — widening a
declaration to claim files nobody read is the defect R17-H1 was about,
and a declaration is a claim by its author that no checker can verify.

**You may only widen R17's declaration for paths YOU have read.** If you
have not read them, the correct outcome is a report saying so.

## §E — R17-L2: latent, and possibly already covered

`tests/test_audit_phase_sites.py`'s container walks `tools/` BY PATH.
Complete today — all 13 non-dispatcher sites present, `audit.py`'s two
correctly excluded — but an emission added in `approval.py` or
`services/` would be invisible while the test prints a clean equality.

Note that `SITES_PER_PAIR` now asserts multiplicity as well, so a new
site under an existing pair IS caught. **Work out whether the by-path
walk is still a gap given that, and say which.** If it is not, close it
with the reason; a fix nobody needs is inoperative code.

## §F — How your work will be judged

- **Every behaviour change ships an arm that goes red without it.**
- **Every count carries its container and its sha.**
- All gates green before you report, each exit code on its own line,
  including `pre-commit run --all-files`, `mypy`, and the full suite
  (887 passed, 0 skipped). **mypy caught 8 errors in the last agent's
  new file after it reported green — run it on anything you add.**
- Separate COULD NOT SETTLE from did not attempt.
