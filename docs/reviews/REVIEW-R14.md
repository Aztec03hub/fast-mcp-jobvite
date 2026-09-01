# REVIEW-R14 - the load-bearing config nobody read

<!-- REVIEW-COVERS: f699f74..dad014e PATHS: pyproject.toml .env.example .pre-commit-config.yaml server.json README.md docs/briefs -->

**What that declaration claims, and what it does not.** It is the paths I
opened and read in this range, nothing wider. R11 took `src tests
docs/adr docs/DESIGN.md` and R12 took `docs/reviews scripts .github`
over these same 45 commits; the two were treated as complementary halves
of a 133-file range and are not - 56 + 62 = 118. **This round is the
remainder, and it was nobody's until the declarations became precise
enough to notice.**

## Why these files and not others

`check-review-coverage.py` reports seven commits as PARTIAL. Resolving
"e.g." into the actual unclaimed set, by re-running the checker's own
join rather than reading its sample line:

    4  pyproject.toml            dependencies and every gate's config
    3  .env.example              secret-class values; the class must stay empty
    2  .pre-commit-config.yaml   the hooks that run before every commit
    1  README.md                 the Quickstart, which a test parses and runs
    1  server.json               the PUBLISHED MCP manifest
    1  docs/briefs/ADR-0025.md   the brief that shaped #112
    1  docs/briefs/ADR-BATCH.md  the brief that shaped #95

Every figure in the task record survived re-measurement unchanged, which
is rare enough here to be worth stating.

**One correction to my own first measurement.** I opened by reporting
that `d5340b7` fell outside `f699f74..dad014e`, so the suggested range
would not cover one of its own seven commits. That was wrong, and the
instrument was the reason: I tested `is-ancestor f699f74 d5340b7 &&
is-ancestor d5340b7 dad014e`, which is NOT what `A..B` means. `A..B` is
"reachable from B, not from A", and it therefore includes side branches
that never descend from `A` - which is exactly what `d5340b7` is. The
range is correct as suggested. **A single AND-ed test also hid which
half failed**, which is why the false finding survived to be written
down before being checked.

---

## R14-H1 (High) - the marker arm skipped the only artefact that leaves this repo

`docs/reviews/check-settings-are-read.py`

**FIXED.** `UNIMPLEMENTED_MARKER` requires a declared-but-unread setting
to carry `NOT YET IMPLEMENTED` in the artefacts an operator reads. The
docstring that argues the arm into existence ends by naming the harm:

> A declared one ships in `.env.example`, an operator sets it, and it
> silently does nothing - and `server.json` advertises it to registry
> consumers as a knob that works.

The enforced tuple was `("README.md", ".env.example")`.

**The artefact the paragraph names is the one the check omitted**, and
it is the only one of the three that leaves this repository.
`.env.example` and `README.md` are read by someone who has already
cloned us and can go read `config.py` when something looks wrong.
`server.json` is the published MCP manifest a registry consumer reads
*without ever seeing the other two*. The check covered the two audiences
that could recover and skipped the one that could not.

At the time of this round the manifest read:

    "Outbound self-throttle against Jobvite, requests per minute.
     A conservative guess, not a vendor figure..."

with no indication that no code reads it - while `EXEMPT` in the same
checker recorded that the throttle does not exist.

**Widening the tuple alone would have shipped an arm that cannot fire.**
The text rule requires the variable name and the marker on ONE line, and
a JSON object puts `"name"` and `"description"` on different lines by
construction. Adding `server.json` to the list and nothing else would
have produced a third artefact that reports a clean zero whatever the
manifest said. So JSON is read structurally: the entry is looked up by
name and its description must carry the marker, and an entry that is
absent RAISES rather than returning an empty list.

**Proved by `docs/reviews/probe-r14-manifest-marker.py`, 4/4 arms:**

    BASELINE   the tree as committed passes                     exit 0
    POSITIVE   an unmarked manifest is REFUSED, and named       exit 1
    AMPUTATE   the OLD two-artefact tuple passes the same lie   exit 0
    VACUITY    a manifest with no such entry REFUSES            exit 1

The AMPUTATE arm is the load-bearing one: it restores the previous
tuple and shows the old checker going green on a manifest that lies,
which is the defect reproduced rather than merely described.

## R14-M1 (Medium) - a bare continuation citation, wrong at BOTH freezes

`pyproject.toml:10`

**FIXED.** The line read:

    # Verbatim from DESIGN.md:1499-1501 (the pins; the block is :1366-1370).

The ADR batch repointed the NAMED half of that sentence (`1418-1420` ->
`1499-1501`) and left the bare `:1366-1370` beside it untouched. **A
bare `:N-M` carries no filename, so `check-design-citations.py` cannot
see it** - the sentence went half-stale with nothing able to say so.

**And the repoint is not what broke it.** At the old freeze `f699f74`,
`:1366-1370` already landed on redaction-coverage prose about ADR-0010,
not on the dependency block. The bare half never resolved to its subject
within the history I read. The repoint left a wrong citation wrong; it
did not make a right one wrong. Corrected to `:1497-1506`, the fenced
toml block from `dependencies` through `[tool.uv]`, read before writing.

**Scope, measured rather than assumed.** 115 bare continuations of a
`DESIGN.md` citation exist across all tracked files. **All 115 are in
bounds**, so none is detectably stale by address alone. 114 sit in
records - worklogs, reviews, plans - which the `a1773e8` ruling
deliberately does not repoint. **Exactly one was in live config**, and
this is it. The class is real but its live population was a single site,
and saying so is more useful than the raw 115.

## What I read and found NOTHING wrong with

Stated because a round that reports only its findings makes the rest
invisible.

- **`.env.example`** - the added `JOBVITE_OUTBOUND_BUDGET_SECONDS` block
  carries its unit, its non-per-request semantics, and says plainly that
  60 is a choice with nothing observed. Every secret-class value is
  still empty. The rate-limit block carries the `NOT YET IMPLEMENTED`
  marker.
- **`README.md`** - the table row was corrected from "per second" to
  "per **minute**", which matches `DESIGN.md:1657` and the manifest.
  Checked all live artefacts for the unit and found no disagreement.
- **`.pre-commit-config.yaml`** - citation repoints only; the two gates,
  their stated ceiling, and the `.env.example`-is-scanned-not-excluded
  rule are unchanged.
- **`pyproject.toml`** beyond M1 - the `extend-exclude` change from
  `["docs"]` to `["**/*.md"]` is argued in place and is the right
  narrowing: it keeps the `.py` files under `docs/` linted while keeping
  `ruff format` off Markdown, whose fenced blocks include seven inside
  the FROZEN design.
- **`docs/briefs/ADR-0025.md`** and **`ADR-BATCH.md`** - historical
  dispatch briefs for work since merged. Coherent, and each states the
  freeze SHA its citations were written against.

## Gates

    check-settings-are-read       0
    check-env-vars-are-declared   0
    check-design-citations        0
    check-design-citation-shape   0
    check-checkers-are-wired      0
    probe-142-exempt-controls     0
    probe-r14-manifest-marker     0   (4/4 arms)
    check-committed-file-types    0
    ruff check .                  0
    ruff format --check .         0
    mypy                          0
    pytest                        887 passed, 0 skipped, 6 deselected

## What this round could NOT settle

- **Whether the other 114 bare continuations are semantically right.**
  They are all in bounds, and in-bounds is not correct - M1 proves that
  precisely, since it was in bounds and wrong. They are records and out
  of repoint scope by ruling, so this is recorded rather than swept.
- **Whether a fourth operator-facing artefact exists.** The three here
  are the three `check-env-vars-are-declared.py` names in its own
  docstring. Nothing enumerates that set from a container, so a fourth
  would have to be added by hand - the same shape as the defect H1
  fixed, one level up.
