# BRIEF #126 — sweep the 47 citations that end on a blank line

## §A — Read the canon FIRST

**Read `docs/briefs/PREAMBLE.md` in full before anything else, and follow it.**
It carries the standards order, the design-freeze rule, and the
`REVIEW-COVERS` obligation. Nothing below overrides it.

Read the design **at the freeze**, never from the working tree:

    git show "$(cat docs/DESIGN-FREEZE.txt)":docs/DESIGN.md

That SHA is the single declared home for the freeze. Do not retype it.

Then read, in this order:

1. `docs/reviews/check-design-citation-shape.py` — the checker that
   raises this. Its docstring states what it can and cannot see.
2. `docs/briefs/EVIDENCE-126-blank-end-citations.md` — every site,
   measured, plus the grouping you actually work from.

## §B — Context you cannot infer from the tree

This started as **"2 instances"**. The reviewer (R12) read two, wrote the
check, and the check found **46**. It corrected itself in place, and said:
*a finding raised from a partial read IS a partial check*. That
self-correction is worth more than the finding, and it is the reason this
brief hands you a measured container instead of a list to trust.

I re-measured on the merged trunk and it is now **47**, not 46. The count
in the task title is stale; the file above is ground truth. **Do not
propagate 46.**

The sweep was blocked on three live branches colliding. They merged at
`92cb89b` (#124). That blocker is gone — you are the single owner, on one
branch, over the merged tree.

## §C — The shape of the work, which is NOT 47 decisions

    47 sites  →  26 distinct ranges  →  19 distinct END lines

The defect is a property of the **end line**, not of the range. Nineteen
end lines are blank at the freeze (I verified all 19 — zero exceptions).
Several ranges share one end: end `383` carries 7 sites across 5 ranges;
end `1144` carries 6 across 2; end `1453` carries 6 in a single range.

So: **decide once per end line, then apply to every site that shares it.**
A per-site pass will drift, because a shared end line decided twice is how
two sites end up with different answers to the same question.

## §D — The rule, and the trap in it

The obvious fix is `end - 1`. On the three I checked by hand (`383`,
`1453`, `1144`) that is exactly right: real prose ends at `end-1`, the end
line is blank, and the line after starts a new paragraph or a `---`.

**Do not apply it mechanically to the other sixteen.** A range ending on a
blank line may be one deliberately widened to absorb a following paragraph
that simply overshot, or one whose subject genuinely ends earlier than
`end-1`. This repo has already carried a wrong sentence forward through two
commits by mechanically repointing (#114 — five citations that RESOLVE and
name the wrong sentence).

**The predicate, for every end line:**

> Read what the citing site CLAIMS. Then read the trimmed range. Does the
> trimmed range still contain that claim?

If yes, trim. If the claim is not in the trimmed range, the citation was
already wrong about something else — **report it, do not silently repoint
it**. That is a finding, not a chore.

Note the overlapping families, where one decision constrains a neighbour:
`312-314`/`312-319`; `674-680`/`678-680`; `901-907`/`905-907`/`906-907`;
`207-213`/`207-238`; `354-383`/`373-383`; `984-1030`/`1028-1030`;
`1134-1144`/`1143-1144`.

## §E — Definition of done

1. `python3 docs/reviews/check-design-citation-shape.py` exits **0**.
2. `python3 docs/reviews/check-design-citations.py` still exits **0** —
   trimming must not push any range out of bounds.
3. The full local gate is green. Run each checker and read **its own exit
   code on its own line**. Do not write `cmd; rc=$?` under `set -e`, and do
   not chain the commit behind `&&` off a tally you printed yourself —
   both have shipped red here.
4. A short worklog at `docs/reviews/WORKLOG-126-blank-end-sweep.md`
   recording, per end line: the decision, and the claim you checked it
   against. Nineteen rows. If any site was a genuine finding rather than a
   trim, it gets its own section.
5. **Do NOT wire the checker.** Wiring is #125 and it is mine. Say in your
   report that it is now green and ready to wire.

## §F — Constraints

- Work on branch `fix/blank-end-citations`, off current `main`.
- **Do not merge and do not push.** I merge and push, always.
- No `Co-Authored-By` or "Generated with" trailer, in any commit.
- Do not `git stash` — other agents are live on this tree.
- Commit messages via `git commit -F` and a **quoted** heredoc
  (`<<'MSG'`). An unquoted delimiter executes backticks and has destroyed
  content here at exit 0.
- Cite `file:line` only from `grep -n` or a numbered `Read`. Never count
  offsets inside a `sed -n X,Yp` window.

## §G — Report back

`SendMessage` to `team-lead` when done: the 19 decisions in one line each,
both checkers' exit codes, anything you found that was not a trim, and
anything you could not settle. If a number in this brief turns out wrong,
say so plainly — the last three agents each corrected me on one, and each
was right.
