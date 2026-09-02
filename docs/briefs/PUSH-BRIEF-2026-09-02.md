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

## What is NOT resolved, and could bite

**25 CI steps invoke a checker under a bare inherited `python3`** - not one or
two. And `check-plan-measurements.py` gives a DIFFERENT VERDICT depending on
which interpreter answers:

    /usr/bin/python3         [STALE] M3, [STALE] M4   rc=1
    uv run --frozen python   [PASS] M1-M4             rc=0

Same file, same commit. **So CI's green may be an accident of what `python3`
resolves to on the runner.** Nobody has read a run log to find out; the risk is
conditional and I am not asserting the step is red. This is #221, in flight.

The one green run this project has ever had is `33582613697`, head `22c9873`,
and it presumably had all 25 of these steps green - which is evidence, and is
the thing to read first if CI fails on one of them.

## After you push

**WATCH THE RUN TO A CONCLUSION BEFORE PUSHING AGAIN.** GitHub supersedes older
QUEUED runs in a concurrency group regardless of `cancel-in-progress`, so a
second push destroys the evidence the first was sent to gather. The trunk has
exactly ONE green run in its history; a second would establish that it repeats,
and that is the whole point of this push.
