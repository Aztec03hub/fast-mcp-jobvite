# BRIEF #142 (TIER 1) — give `REPOINT-EXEMPT` a scope and a reason

You are a **Tier-1 sub-orchestrator**. Read
`docs/briefs/PROTOCOL-sub-orchestrators.md` in full and follow it — it
governs what you may spawn, what you must commit, and what only I may do.

## §A — Canon first

Read `docs/briefs/PREAMBLE.md` in full. Read the design at the freeze:

    git show "$(cat docs/DESIGN-FREEZE.txt)":docs/DESIGN.md

Then read `docs/reviews/REVIEW-R13.md` (branch `review/r13`), finding H1.

## §B — The defect, proved

`REPOINT-EXEMPT` is a bare substring. A line carrying it is skipped
entirely by **both wired citation gates**. R13 proved it and I reproduced
it before dispatching you:

    # PLANT DESIGN.md:99999-99999 REPOINT-EXEMPT

prepended to a real source file → `check-design-citations.py` exit 0,
`check-design-citation-shape.py` exit 0, nothing printed. A citation
97,866 lines past the end of a 2133-line file, silently accepted.

Three compounding weaknesses:

1. **No scope.** The marker does not say what it exempts.
2. **Line granularity.** A line holding one legitimate record AND one
   wrong citation loses both.
3. **No reason**, in a repo whose every other exemption mechanism refuses
   a blank one and argues that the reason IS the exemption.

Partly fixed at `93d1c93`: the skip count is now printed and reads **47**.
That number is a hypothesis about your container — verify it.

## §C — The work, and its decomposition

**1. MEASURE FIRST.** Enumerate every marked line across both checkers'
containers. For each: which file, what it is exempting, and — the load
bearing question — **does the line carry anything OTHER than the thing
being exempted?** That count decides whether granularity is a real defect
here or only a theoretical one. Report the number you get, not 47.

**2. DESIGN the scoped form.** R13 suggests
`REPOINT-EXEMPT(DESIGN.md:373-383)`. That is a suggestion, not a ruling.
Consider at least: what an unscoped bare marker should mean after the
change (reject? warn? grandfather?), and whether a reason should be
required inline or by a keyed register like `check-no-errexit.py`'s
`EXEMPT` dict. **Bring me the choice with its trade-offs before applying
it at scale** — this is a wired gate and the decision is Tier 0's.

**3. APPLY**, once I have ruled. This is the part to hand to a Tier-2
sonnet worker: an enumerated container, a mechanical transform, and an
acceptance test. Give it the list; do not let it decide which sites are
legitimate.

**4. CONTROL IT, and this is yours alone.** The new form must:
   - still skip what it legitimately exempts (negative arm),
   - **refuse the plant above** (positive arm) — a scoped marker must not
     exempt `DESIGN.md:99999-99999`,  <!-- REPOINT-EXEMPT: the plant, quoted as the defect -->
   - refuse a marker whose scope does not match the citation on the line,
   - keep the printed count non-vacuous (plant one, watch it move).

## §D — What you must not do

- **Do not merge, do not push.** I merge and push, always.
- Do not wire anything new; both gates are already wired.
- Do not `git stash`. Other agents are live on other worktrees.
- No `Co-Authored-By` or "Generated with" trailer.
- `git commit -F` with a **quoted** heredoc (`<<'MSG'`).
- Do not let a Tier-2 worker make a correctness call.
- Do not rewrite a record to make a gate green — the statements marked
  today were TRUE when written (#111).

## §E — Budget

At most **2** Tier-2 agents at once. Close each with `TaskStop` the moment
you have its result AND that result is committed on your branch. Do not
spawn one for work you could finish in a single tool call.

## §F — Report

`SendMessage` to `team-lead`: the marked-line count you measured (and
whether 47 held), how many carry more than the exempted item, your
recommended scoped form with its trade-offs, every gate exit code on its
own line, and what you could not settle.

**If anything in this brief is wrong, say so.** Six agents corrected me
today and every one of them was right.
