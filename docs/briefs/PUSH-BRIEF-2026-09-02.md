# PUSH BRIEF - what this push changes, and the one measurement that sizes it

**Derive every number here before you trust it.** The commands are beside each
one. This file has already been wrong once, in the way described under
"A CORRECTION TO THE VERSION YOU MAY HAVE READ".

## The measurement that sizes the whole risk

    git diff --name-only origin/main...HEAD | grep -cE '^(src|tests)/'

**0.** Not one file under `src/` or `tests/` changes.

That is what bounds this push. The 86-minute test job cannot behave differently
for any reason internal to what it tests, because what it tests did not move.
The suite is 887 passed / 0 skipped locally, against `ci.yml`'s floor of 887.

    total files changed   git diff --name-only origin/main...HEAD | wc -l
    held commits          git rev-list --count origin/main..HEAD

At the time of writing those were 65 and 89. **They rise with every commit, so
run them.**

## A CORRECTION TO THE VERSION YOU MAY HAVE READ

The first version of this brief said every gate was green. **That was false when
written.** `check-design-citation-shape.py` was exiting 1 on `main`, and
`ci.yml:353` runs it with no `|| true`, so CI would have failed on it.

I had not run that particular checker. I ran the ones I had been thinking about
and reported the set I ran as though it were the set that exists. Another agent
found it while doing unrelated work and correctly refused to fix a file that was
not its own.

It is fixed now. The two flagged lines were not citations at all - they
REPRODUCE ADR-0017's own lines inside the probe whose subject IS that ADR, and
`DESIGN.md:489` being blank is the point of the probe. Both obvious repairs were
wrong: repointing the quotation falsifies it, and repointing the ADR is refused
by `ec57a65`. Closed with the exemption register, proved in both directions.

**The general lesson for reading this brief: a green list is a claim about what
I ran, not about the repo.**

## What actually changes

Documentation, checkers, controls, and CI wiring. Concretely:

- **Nine R21 review findings closed** (#209-#217), plus #194, #208, #212, #214.
- **Two new gates** and several widened containers.
- **One new probe**, `probe-stale-branch-regression.sh`, deliberately NOT wired
  and registered as such - see below.
- **`docs/DESIGN.md` does not move.** `check-design-freeze.py` rc=0.

## The two workflow files, which is where the real uncertainty is

    git diff --name-only origin/main...HEAD | grep '^\.github/'

`ci.yml` and `mirror.yml`.

**`ci.yml` NOW CARRIES HUNKS FROM THREE DIFFERENT AGENTS** - #194 added a
wiring-probe self-test step, #214 rewrote a comment that had frozen a live
census, #210 folded an ADR-index check into an already-wired step. All three
survived the merges; I verified each by name rather than trusting a clean
`git merge`. It parses as YAML.

**`actionlint` IS NOT INSTALLED HERE AND HAS NEVER SEEN ANY OF IT.** CI's own
actionlint step will be the first thing to lint these hunks. That is the single
largest unverified thing in this push and it is not a footnote.

**`mirror.yml`'s push step gained a zero-ref refusal** - counted before the
push, exit 1 on zero. That step has NEVER EXECUTED, because there is no
`MIRROR_TOKEN`. Proved by a probe that EXTRACTS the guard with `awk` rather than
retyping it. No remote was touched, because a mirror push is `--force --prune`.

## A CLAIM IN THE PREVIOUS VERSION, NOW REFUTED BY MEASUREMENT

That version told you **25 CI steps run a bare `python3` and CI's green may
be an accident of PATH.** That is FALSE, and the measurement that killed it is
better than the story it replaced.

    SAME 25   DIFFERENT 0   DIFFERENT-OUTPUT 0   FAILS-TO-RUN 0

All 25 sites give identical exit codes and identical normalised output under
both interpreters. All 23 distinct scripts behind them import stdlib only.

**The real cause was never the interpreter.** `check-plan-measurements.py` fell
back to `sys.executable` when `.venv` was absent, and `uv run` SYNCS `.venv` as
a side effect - so the interpreter arm looked causal while the venv did the
work. Held constant at `/usr/bin/python3`, varying only `.venv`, the verdict
still flips. Zero `ci.yml` lines were changed; the fix is `exit 2` in the
checker for an unmet precondition.

**And the runner was READ, not reasoned about.** From the one green run's log
(205KB, fetched via `gh api .../jobs/.../logs`, because `gh run view --log`
returns EMPTY at exit 0 on this repo - a clean zero that explains itself as
nothing): `python3` there is hostedtoolcache 3.12.14 with no `VIRTUAL_ENV`,
`uv sync` creates `.venv` before every step, and the step printed that it
selected `.venv/bin/python` itself.

**How to read this brief, given that:** a claim here is worth what its
measurement is worth. This document has now been wrong twice - once claiming
gates were green when a wired one was red, once passing on a diagnosis that
was right about WHICH and wrong about WHY. Both were caught by agents working
on something else.

## WHAT IS GENUINELY UNRESOLVED

**Ten merges in this repository's history contain lines present in NEITHER
parent** - 224 lines, and NINE of the ten predate `origin/main` and have never
been examined. Content entered with no branch diff to show it and no reviewer
able to see it. Among it: an entire `EXEMPT` dict and skip branch in a wired
gate, and three whole `ci.yml` steps.

The detector for it ships in this push (`check-merge-invented.py`, four
controls including two synthetic). It is deliberately NOT wired and NOT ruled
on - that decision is open.

## After you push

**WATCH THE RUN TO A CONCLUSION BEFORE PUSHING AGAIN.** GitHub supersedes older
QUEUED runs in a concurrency group regardless of `cancel-in-progress`, so a
second push destroys the evidence the first was sent to gather. The trunk has
exactly ONE green run in its history; a second would establish that it repeats,
and that is the whole point of this push.
