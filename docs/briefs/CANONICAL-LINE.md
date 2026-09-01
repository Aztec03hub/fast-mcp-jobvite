# Brief - task #107: ONE canonical machine line per harness

Read `docs/briefs/PREAMBLE.md` first. It governs; this file names only this task's work.

Agent: `canonical-line`. Branch: `chore/canonical-line`. Worktree:
`/home/plafayette/claude_projects/fmj-worktrees/canonical-line`.
`docs/DESIGN.md` is frozen at `aca9397`.

## The problem, as dispatched

Harnesses under `scripts/` report results in PROSE, and the checkers reading them carry a
hand-kept list of the prose SHAPES they accept. `docs/reviews/check-row-floor-controls.sh`
has a `floor_line()` accepting THREE breach-message shapes, with a parallel display grep
that must be kept matching the same three. Task #102 found a SIXTH tally shape across the
family.

This is the container defect this project has found seven times: **a hand-kept list of the
forms to accept is blind to the form nobody added**, and when list and reality drift the
failure is SILENT - #102 found "CONTROL FIRED" printed above a BLANK evidence block because
the display grep matched a shape the parser did not.

## The lead handed over, and how it settled

The previous (read-only) dispatch reported by globbing: 36 scripts, 24 emitting a floor
line - 20 of shape `N/M ROWS - THE HARNESS LOST ROWS`, 3 of `holds N rows, below its floor
of M`, 1 of `ONLY N ROWS RAN against a floor of M` - against the checker's own comment
claiming 23 harnesses and 19 of the first shape. The question was whether the enumeration
was already stale by one.

**Settled: BOTH numbers are right, and they count different populations.** Re-derived here,
not inherited - see `docs/worklogs/CANONICAL-LINE-REPORT.md` for the commands and output.

## The fix

Every script under `scripts/` emits ONE canonical machine-readable line in addition to its
human prose; every checker parses only that line.

### The grammar, and the decision on `fired=`

    HARNESS-RESULT name=<basename> rows=<n> floor=<n> status=<ok|breach|refused>

**`fired=` is DROPPED**, as the previous pass suggested and for reasons I re-derived rather
than inherited:

1. **It would carry four incompatible meanings.** Across the family the "fired" tally is
   `FIRED/TOTAL controls fired.` (mutation controls), `RESULT: N killed, M not killed`
   (audit/client controls), `ROWS: N   ANCHORS APPLIED: M` (amputation harnesses), and for
   amputation harnesses the pass condition is INVERTED - survivors are the OUTPUT, not a
   failure, which is why `ci-harness-gate.sh` has a `--amputation` flag at all. One field
   name over four semantics lies more loudly than an absent field.
2. **`ci-harness-gate.sh` says in its own prose why they must not collapse:** "each is
   printed beside a different diagnosis, and collapsing them would send the next reader to
   the wrong place." Unifying them into `fired=` is exactly that collapse.
3. **`status=` already carries the verdict**, and carries it from the harness's REAL exit
   code rather than from a counter a refactor could leave behind. A checker asking "did
   this pass" does not need `fired=`.
4. `rows`, `floor` and `status` are universal and each has exactly one meaning.

The tally shapes in `ci-harness-gate.sh` are therefore NOT deleted by this task. That is a
separate change with a different blast radius (it moves `ci.yml` flag semantics), and it is
filed as its own task rather than smuggled in here.

### `status` semantics, and why they are derived not declared

- `refused` - the harness did not reach the end of its rows. This is the DEFAULT: a script
  that aborts, is killed, or dies in setup emits `refused` without having to remember to.
- `ok` - the harness completed its rows and exited 0.
- `breach` - the harness completed its rows and exited non-zero.

`ok`/`breach` are computed from `$?` inside the EXIT trap, so the line cannot disagree with
the exit code. `refused` is the default state, so **a silent harness and a passing one
cannot render identically** - the defect that let 119 consecutive CI failures go unread.

### Requirements

- Human prose STAYS. This adds a line; it does not replace the report.
- EVERY script under `scripts/` emits it, `ci-harness-gate.sh` included. The population is
  the GLOB, never a typed list - a partition into "harnesses" and "not harnesses" would be
  the same hand-kept list one level up. `name=` disambiguates: a gate's own line and the
  line of the harness it ran differ by `name=`.
- Emitted from ONE shared sourced file. The format string appears exactly once.
- Checkers parse this line and NOTHING else. The shape list is DELETED, not extended.

## How not to fool myself (the controls this task owes)

1. **Enumerate the container.** Population = `scripts/*.sh` by glob. Assert the set emitting
   the line EQUALS the set that exists.
2. **Force an abort** and confirm `status=refused` - not a pass, not a crash.
3. **Plant a breaching value** in a `HARNESS-RESULT` line and confirm the rewritten checker
   exits non-zero. A checker rewritten and never watched FAIL is untested.
4. **Compare exit codes before and after.** This is a reporting refactor; if any exit code
   moves, behaviour changed and the report says so.

## Gates

Floors DERIVED from `ci.yml` by grep, never retyped. 0 skips. Gate commands run argument for
argument (`uv run --frozen mypy`, not `mypy src`); `ruff check` and `ruff format --check`
chained with `&&`, never `cmd; echo "EXIT=$?"`. ShellCheck v0.10.0 at `--severity=warning`
from `~/.local/bin/shellcheck` - verify the binary actually runs, an absent one checks
nothing silently.

## Delivery

Report to `docs/worklogs/CANONICAL-LINE-REPORT.md`, committed on `chore/canonical-line`.
**Commit only. Do NOT merge, do NOT push.** Then `SendMessage` to `team-lead`.
