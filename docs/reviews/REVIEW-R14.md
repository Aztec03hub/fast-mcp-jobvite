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

**FIXED, then FIXED AGAIN after R14-R1 found two Highs in the fix.**
`UNIMPLEMENTED_MARKER` requires a declared-but-unread setting
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

**WHY THE JSON BRANCH EXISTS - AND THIS PARAGRAPH WAS WRONG THE FIRST
TIME (R14-R1 H1).** It said a widened line rule "reports a clean zero
whatever the manifest said". **False on this tree**, and R14-R1 proved
it by deleting the whole JSON dispatch: exit 0, a SURVIVOR. The cause
is the wording this round itself chose - `server.json`'s description
BEGINS with the variable name, so name and marker share a line and the
plain rule matches. I argued a structural fix was necessary while
writing the very fixture that made it unnecessary.

Re-measured, all four cells:

    manifest as shipped, JSON branch present ....... exit 0
    manifest as shipped, JSON branch DELETED ....... exit 0   SURVIVOR
    manifest reworded,   JSON branch present ....... exit 0
    manifest reworded,   JSON branch DELETED ....... exit 1   load-bearing

"Reworded" means the description carries the marker WITHOUT repeating
the variable name - a correctly marked manifest that the line rule
calls unmarked. **That false POSITIVE is what the branch prevents**, not
the false pass I claimed. The probe's LINE-RULE arm asserts it. The
amputation above is a recorded measurement, not an automated arm: the
probe refuses to run against a modified checker, so it cannot amputate
its own subject.

**Proved by `docs/reviews/probe-r14-manifest-marker.py`, 7/7 arms** -
four as first written, three added by R14-R1:

    BASELINE   the tree as committed passes                     exit 0
    POSITIVE   an unmarked manifest is REFUSED, and named       exit 1
    AMPUTATE   the OLD two-artefact tuple passes the same lie   exit 0
    LINE-RULE  a marker WITHOUT the name beside it is ACCEPTED   exit 0
    SCOPE-DUP  a DUPLICATE declaration is refused, not laundered exit 1
    SCOPE-OUT  a look-alike outside environmentVariables fails   exit 1
    VACUITY    a manifest with no such entry REFUSES            exit 1

AMPUTATE reproduces the original defect: it restores the previous tuple
and shows the old checker going green on a manifest that lies.
LINE-RULE is what stops the JSON branch being decorative, and
SCOPE-DUP/SCOPE-OUT are R14-R1 H2's two plants, both of which passed
against the first version of this fix.

## R14-R1-H2 (High, found by the review) - the fix laundered an unmarked entry

`docs/reviews/check-settings-are-read.py`

**FIXED.** The first `_json_marker_lines` walked the WHOLE document and
accepted the entry if ANY node with a matching name carried the marker.
Two plants passed against a lying manifest, both now probe arms:

- a **DUPLICATE** `JOBVITE_OUTBOUND_RATE_LIMIT`, one marked and one not,
  both inside `environmentVariables` - exit 0;
- the real entry **stripped** and a marked look-alike planted OUTSIDE
  `environmentVariables` - exit 0, on a manifest with no real
  declaration at all.

The manifest's ROOT object also carries `name` and `description`, so
the walk was searching places that are not variable declarations.

**This is R14-H1's own defect surviving inside R14-H1's fix**: a check
that looks in a wider place than the one that matters. The lookup is
now scoped to `packages[*].environmentVariables`, a duplicate name is
REFUSED rather than resolved (which one an operator reads is
undefined), and `_walk_json` is deleted for want of a caller.

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

**Scope - and the second half of this was WRONG (R14-R1 M3, M4).** I
reported "115 bare continuations, 114 of them in records". **The 115 is
not reproducible**: I recorded no command, and R14-R1 tried five
reasonable definitions and got 0, 64, 77, 910 and 957 - none of them
115. A number nobody can re-derive is not a measurement, and it should
have been pasted as a command the way the Gates section pastes exit
codes.

**"114 sit in records" is refuted.** Bare continuations of a `DESIGN.md`
citation also sit in `src/fast_mcp_jobvite/config.py`,
`services/jobvite_client.py` (twice), `tests/test_config.py`,
`tests/test_resilience.py` and three `docs/adr/` files. `src/`, `tests/`
and `docs/adr/` are NOT records and `a1773e8` does not exempt them -
they are R11's declared paths, which is a different thing. **The half
that carries the argument survives**: exactly one bare continuation sat
in live CONFIG, and it is M1. The half that told the next reader the
class was closed does not.

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

- **How many bare continuations there are, and whether they resolve.**
  My 115 is unreproducible (R14-R1 M3) and the records claim is refuted
  (M4). What holds: in-bounds is not correct - M1 was in bounds and
  wrong - and the `src/` and `tests/` sites are neither records nor
  swept. Filed rather than guessed at again.
- **Whether a fourth operator-facing artefact exists.** The three here
  are the three `check-env-vars-are-declared.py` names in its own
  docstring. Nothing enumerates that set from a container, so a fourth
  would have to be added by hand - the same shape as the defect H1
  fixed, one level up.
