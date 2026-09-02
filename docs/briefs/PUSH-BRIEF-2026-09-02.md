# PUSH BRIEF — what this push changes, so it can be watched

**FOR PHIL. Only Phil pushes.** This is the "brief him on exactly what
the push changes before it lands" half of the rule; the other half is
that after it lands, the run is WATCHED TO A CONCLUSION before anything
else is pushed.

Derive everything below rather than trusting it:

    git rev-list --count origin/main..HEAD
    git diff --shortstat origin/main...HEAD
    git diff --name-only origin/main...HEAD | grep -E '^(src|tests)/'

## The one fact that sizes the risk

**NOTHING UNDER `src/` OR `tests/` CHANGES. Zero files.** Measured, not
assumed:

    git diff --name-only origin/main...HEAD | grep -cE '^(src|tests)/'   ->  0

So the 86-minute `Lint, types, tests` job cannot behave differently for
any reason internal to what it tests. Every changed file is
documentation, a checker, a control, or CI wiring.

    23  docs/reviews      the checkers, controls and reports
    11  docs/briefs       agent briefs and the handoff
     5  docs/adr          ADR-0035, and edits to 0017/0034
     4  docs              README, OBLIGATIONS, DESIGN-FREEZE
     2  scripts
     2  docs/worklogs
     2  .github/workflows ci.yml and mirror.yml

## What is genuinely new in CI, and what each costs

FIVE new steps. Each was run before being wired, and timed here on this
machine - a runner will differ, but not by minutes:

    The floor container's own arms                358ms
    Controls for the brief-report reference gate   817ms
    The mirror refuses a zero-ref push              35ms
    Every report a brief cites is committed         42ms
    The bare-citation discriminator's controls      33ms

**Under 1.3 seconds in total.** None of them touches the network, and
none runs pytest. They join the fast static job, not the long one.

## The change with real blast radius, and why it is small

`mirror.yml`'s push step gained a guard that REFUSES a zero-ref push:

    refs=$(git for-each-ref ... | wc -l)
    if [ "$refs" -eq 0 ]; then ... exit 1; fi

**That step has never executed in this repository's history**, because
there is no `MIRROR_TOKEN` and its `if:` has skipped it on every run.
So the guard changes the behaviour of code that does not currently run,
and it was proved by a probe that EXTRACTS the guard out of `mirror.yml`
with `awk` rather than retyping it - it cannot pass against a stale
copy. **No remote was touched to test it**: a mirror push is
`--force --prune` and is not a thing to test by running.

The same file also writes `GITHUB_STEP_SUMMARY` so a no-op mirror run
says so on the run's front page rather than only in the log.

## What is still NOT verified, and cannot be from here

- **`actionlint` is NOT INSTALLED on this machine.** Two workflow files
  changed and neither has been linted. CI runs it with
  `SHELLCHECK_OPTS=--severity=warning`; **that step is the first real
  test of both files.**
- **Nothing here has been through CI at all.** Every green in this
  session is local.
- The full `pytest` suite was not re-run for the last several commits,
  on the reasoning that nothing in `src/` or `tests/` changed. That
  reasoning is stated so it can be rejected: if you want it run first,
  it is `uv run --frozen pytest -q` and the floor is derived in `ci.yml`.

## What green looks like, and what to do if it is not

The trunk has **one** green run in its history (`33582613697`, head
`22c9873`). A second establishes that it repeats, which is the whole
reason this push was held.

**DO NOT PUSH AGAIN UNTIL THIS RUN CONCLUDES.** GitHub cancels older
QUEUED runs in a concurrency group regardless of `cancel-in-progress`,
so a second push destroys the evidence the first was pushed to gather.

If a NEW step is the thing that goes red, it is one of the five above
and each is under a second - read its own output, which is written to
argue its case rather than to assert a verdict. If `actionlint` goes
red, that is the expected first failure mode and it is on `ci.yml` or
`mirror.yml`.

## Local gate state at this sha

All green, each read from its own exit code: eight doc checkers, ruff
check, ruff format, mypy, shellcheck, the floor exactness checker and
its `--self-test`, and every control harness named above.
