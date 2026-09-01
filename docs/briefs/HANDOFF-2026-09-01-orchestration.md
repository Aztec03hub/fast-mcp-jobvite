# HANDOFF — 2026-09-01, written against compaction

Everything below was verified by running it, not recalled. Main is
`5c391d9`, pushed to both remotes.

## Main is GREEN locally, on every gate

    ruff check .                    0
    mypy                            0
    check-design-citations          0
    check-design-citation-shape     0
    check-design-freeze             0
    check-checkers-are-wired        0

CI has still **never** produced a green run on this trunk. One run has
ever CONCLUDED (`0606ea5`, 4 of 5 jobs green, failing on a defect since
fixed). Everything since is `cancelled` — my own pushes evicting the
single queued slot. See #105 for the corrected rule: a RUNNING run on main
is protected and a PENDING one has consumed nothing, so check
`gh run view <id> --json jobs --jq '.jobs|length'` before deciding whether
a push costs anything.

## Three agents live, and what each owes

**`suborch-142`** — Tier-1, opus, worktree `fmj-worktrees/t142-exempt-scope`,
branch `fix/142-exempt-scope`.
**RULED: Option 2, the keyed register.** Its own argument decided it — four
committed records legitimately cite the same out-of-bounds address as the
plant, so only IDENTITY separates them and no inline form can meet the
brief's positive arm. My refinements: the key must NOT be a line number
(#6 — anchors carry none so they cannot drift), key on `(path, citation)`
with a required non-blank reason, and the register's size must print with
its reasons every run. It chose `.tsv` because that suffix is in neither
gate's scan set, which solves the recursion structurally — keep it, and
say WHY in the register header or someone will convert it to JSON.
**Owes**: the apply pass, four controls, gate exit codes.

**`suborch-144`** — Tier-1, opus, worktree `fmj-worktrees/t144-145`,
branch `fix/144-145-detectors`. #144 + #145 as one piece: two detectors I
wrote today that cannot see the failure each was written for. Regex
widening is FORBIDDEN; shlex token walk required. #145's disposition is
deliberately NOT pre-ruled.
**Owes**: spellings measured, what each control proved, its #145 decision.

**`tally-shapes`** — #120, worktrees `tally-shapes` (probe running) and
`tally-rebuild` (`dbad618`, the committed work). **DO NOT prune either.**
**Owes**: the before/after exit-code ledger.

## Unmerged branches, and why each is still out

    fix/142-exempt-scope        in flight
    fix/144-145-detectors       in flight
    fix/tally-shapes-work       dbad618, committed, ledger outstanding
    fix/kind-not-path           SUPERSEDED by kind-not-path-2 (merged); the
                                WIP is 104 commits stale, keep as a record
    rescue/adr-0024-scan-bound  pre-existing, unexamined today
    rescue/r6-probe-half-open   pre-existing, unexamined today

## The one number that keeps moving

`REPOINT-EXEMPT` marked lines: **47 → 51 → 60 → 61**, in a day. Every
increment was prose *about* the marker, not an exemption of anything —
two briefs discussing it, then the review that found the defect. 36 of the
first 51 carried no citation at all. This is the live argument for #142
and it will keep growing until that lands.

Ten times today a document was flagged by a gate for QUOTING the defect it
was reporting. The tenth was `REVIEW-R13.md`, the report that found the
mechanism.

## Ruled today, so nobody re-opens them

- **Records vs load-bearing** (`a1773e8`): `CHANGELOG.md`, `docs/worklogs`,
  `docs/plans` are RECORDS and out of review-coverage scope, each with a
  stated reason. `docs/briefs` is deliberately IN scope — a brief
  instructs an agent, so a wrong one produces wrong work. Residual: 7
  commits touching genuinely unreviewed config (#140).
- **Every job capped** (`b1c4376`): all seven were inheriting 6 hours.
  Sized from 40 runs; the `test` job has legitimately run 125 minutes.
- **Three-tier orchestration** (`PROTOCOL-sub-orchestrators.md`): what only
  Tier 0 may do, the pane budget, and the three environment traps the
  first two runs measured.

## What I would pick up first

1. Collect the two Tier-1 reports and merge what they deliver.
2. `tally-shapes`'s ledger, which unblocks #116.
3. #140 — seven commits of unreviewed `pyproject.toml`, `.env.example`,
   `server.json`, `README.md`, `docs/briefs`. It is a small round and it
   is the last thing standing between #119 and a wireable coverage gate.
