# BASH-STANDARD - a `priority: required` standard with zero coverage

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `bash-standard`. Your branch is `chore/bash-standard`. Your report goes to
`docs/worklogs/BASH-STANDARD-REPORT.md`, committed on your branch.

## What is true, measured

`standards/devops/bash.md` is `priority: required`, `applicable_to: [bash, shell, ci-cd]`. This repo
has **13 `scripts/*.sh`, 2580 lines**, plus shell inside every `ci.yml` step. And:

```
grep -c "bash.md" docs/OBLIGATIONS.md          -> 0
grep -rl "bash.md" --include="*.md" .          -> nothing
```

**No obligation row cites it. No project document references it.** This is the CONF-6 propagation
failure exactly: *an obligation propagated if and only if a document somebody executed against
happened to name it.* Nothing named `bash.md`, so nothing did.

## The three gaps I measured. Confirm each yourself before acting.

1. **`shellcheck` runs nowhere.** `bash.md:738-741` requires it; `:763-766` gives a ready-made
   pre-commit config. The only occurrence of the word in this repo is a `# shellcheck disable=SC2086`
   in `ci.yml` - a suppression for a linter that never runs.
2. **`set -uo pipefail`, not `set -euo pipefail`.** All 13 scripts use the former; `bash.md:40`
   specifies the latter. **DO NOT "FIX" THIS BY ADDING `-e`.** These harnesses must continue past a
   deliberately failing test run; `-e` would abort each at its first intentional red and turn
   survivors into crashes. It looks like a considered deviation. A deviation from a
   `priority: required` clause is an ADR or it is drift, and there is no ADR.
3. **Line length is NOT a gap.** `bash.md` says nothing about it - I checked. Task #23 already
   decided the 62 over-72 dividers stay. Do not reopen that.

## MEASURE BEFORE YOU WIRE. This is the whole shape of the task.

`shellcheck` is not installed on this host. **Install it however your environment allows, run it over
all 13 scripts, and report the counts by severity BEFORE changing anything.** The number is the
finding.

**If it is noisy, say so and do not wire it.** A gate that lands red teaches everyone to ignore it,
and this project has refused that three times on the record: the cross-reference gate was wired only
on the day it went green, `pip-audit` is deferred rather than half-run, and no commitlint gate runs
against history. Wiring a red shellcheck would be the fourth refusal, not the first.

If it is clean or nearly so, wire it - via the pre-commit hook `bash.md` itself specifies, pinned the
way every other hook and action here is pinned. **Never `uv run --with shellcheck`**: that resolves
outside the lock, the defect ADR-0015 records. shellcheck is a binary, not a Python dependency.

## The ADR question, which is yours to answer and not to assume

Decide whether `set -uo pipefail` is (a) a deviation needing a numbered ADR, or (b) actually
compliant because the clause admits it. **Read `bash.md:40` and its surrounding context at source
before deciding** - do not take my summary of it as the clause. Next free ADR number is **0022**.

If it is a deviation, the ADR must say what these harnesses need that `-e` prevents, and be specific:
a harness runs a test suite that is *expected* to fail under a mutation, and reads the exit code.

## Obligation rows

`bash.md` should stop being invisible. Add rows to `docs/OBLIGATIONS.md` for the clauses this repo
actually has a subject for. **Anchors carry NO line number** (task #6) - `path` plus a subject string
that must be UNIQUE in the file. Run `docs/reviews/check-obligations.py` and `--controls`.

Do not add a row for a clause with no subject here. `docs/CODE-REVIEW-CHECKLIST.md` shows the
established way to record a rule that has no subject in this repository rather than dropping it
silently.

## In the report

The shellcheck counts by severity, before anything else. Your reading of `bash.md:40` quoted at
source. The ADR decision and its reasoning. Which clauses got rows and which were recorded as having
no subject here. Every gate by exit code. **End with what you could not settle.**
