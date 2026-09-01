# BRIEF #120 — the tally half of the shape-list defect

## §A — Read the canon FIRST

**Read `docs/briefs/PREAMBLE.md` in full before anything else, and follow
it.** Standards order, design-freeze rule, `REVIEW-COVERS` obligation.
Nothing below overrides it. Read the design at the freeze:

    git show "$(cat docs/DESIGN-FREEZE.txt)":docs/DESIGN.md

Then, in this order:

1. `scripts/ci-harness-gate.sh` — the subject. Read its header comments
   in full; it argues its own design and you must engage with that
   argument rather than replace it.
2. `docs/briefs/EVIDENCE-120-tally-shapes.md` — the measured census.
3. `docs/reviews/check-harness-result.sh` and its `-controls.sh` sibling
   — the canonical-line grammar #107 established, and its parser.
4. `docs/reviews/probe-harness-exit-codes.sh` — your before/after
   instrument. It exists; #107 added it.

## §B — Context you cannot infer from the tree

#107 gave every script under `scripts/` one canonical line:

    HARNESS-RESULT name=... rows=... floor=... status=<ok|breach|refused>

and DELETED three hand-kept prose literals from
`check-row-floor-controls.sh`. That closed the **floor** half. The
**tally** half is still open: `ci-harness-gate.sh` carries three prose
shapes, one per flag.

**#107 LEFT THIS DELIBERATELY, and the reason is load-bearing.** Its
grammar has no `fired=` field because the tally means four incompatible
things across this family: controls fired, mutations killed, anchors
applied, and — for the amputation harnesses — an INVERTED pass condition
where survivors are the OUTPUT, not a failure. `ci-harness-gate.sh` says
so about these exact phrases: *"each is printed beside a different
diagnosis, and collapsing them would send the next reader to the wrong
place."* **One field over four meanings is a field that lies.** Do not
add `fired=` to everything.

## §C — What I measured, and the finding nobody has filed

    printed "controls fired"  : 14 scripts   ci.yml passes --controls-fired : 9
    printed "RESULT: killed"  :  2 scripts   ci.yml passes --result-killed  : 2
    printed "ANCHORS APPLIED" : 10 scripts   ci.yml passes --anchors-applied: 2

**Roughly thirteen harnesses print a tally that no gate reads.** They
compute a number, print it, and nothing asserts anything about it. That
is not the shape-list defect #120 was raised for — it is a second,
larger one sitting underneath it, and it is the more interesting half.

Treat those two as separate questions and answer both:

- **Q1 (the filed defect).** Replace the three hand-kept prose shapes
  with something derived from the canonical line.
- **Q2 (what the census exposes).** For each harness printing an unread
  tally: should its step assert that tally, or is the tally genuinely
  decorative? **Both answers are legitimate** — say which per harness and
  why. A number printed and never read is either a missing assertion or
  a line that should not claim to be a measurement.

## §D — The hypothesis, offered as a hypothesis

#120 suggests: extend the grammar with SEMANTICALLY NAMED fields rather
than one generic one — `fired=N/M` only on harnesses that count controls,
`killed=N/M` only on those that count mutations — and have the gate
select the field its flag names. The `key=value` grammar already tolerates
fields absent on some scripts, and `check-harness-result-controls.sh`
parses by key lookup, not position, so adding fields cannot break it.

**This is a hypothesis, not an instruction.** #107's own suggested fixes
were measured WRONG twice in this repo, and so were R6's and R7's. If
measurement says otherwise, follow the measurement and say so.

## §E — Blast radius and the ledger

This moves flag semantics across ~20 harness steps in `ci.yml`.
**Before you change anything**, run `docs/reviews/probe-harness-exit-codes.sh`
and record every harness's exit code. Run it again after. **Any exit code
that moves must be explained in the worklog** — an unexplained move is a
finding, not noise, and "it's probably fine" is how a real regression
lands green.

Watch for the specific failure this family has produced before: a gate
that greps for a phrase a harness never prints is an INOPERATIVE gate
that passes silently. If you add a field, prove the gate FAILS when the
field is absent or wrong — a positive control per flag, not per file.

## §F — Constraints

- Branch `fix/tally-shapes` off current `main`.
- **Do not merge and do not push.** I merge and push, always.
- No `Co-Authored-By` or "Generated with" trailer.
- Do not `git stash` — other agents are live on this tree.
- `git commit -F` with a **quoted** heredoc (`<<'MSG'`).
- Shell here runs `set -uo pipefail` with **no `-e`** and
  `check-no-errexit.py` enforces it. `cmd; rc=$?` must stay reachable.
- `printf ... | grep -q` returns 141 on large output under `pipefail`.
  Use a here-string. `check-no-sigpipe-pipelines.py` gates this.
- Cite `file:line` only from `grep -n` or a numbered Read.

## §G — Report back

`SendMessage` to `team-lead`: the Q1 answer, the Q2 answer per harness,
the before/after exit-code ledger with every move explained, the positive
controls and what each proved, and anything you could not settle. If a
number in this brief is wrong, say so — I would rather be corrected than
agreed with, and the last several agents each corrected me on one.
