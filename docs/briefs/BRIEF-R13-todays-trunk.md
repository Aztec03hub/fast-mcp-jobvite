# BRIEF R13 — review the 18 unreviewed trunk commits, most of them mine

## §A — Read the canon FIRST

**Read `docs/briefs/PREAMBLE.md` in full first, and follow it**, including
its `REVIEW-COVERS` obligation, which this round MUST discharge. Read the
design at the freeze, never the working tree:

    git show "$(cat docs/DESIGN-FREEZE.txt)":docs/DESIGN.md

## §B — Scope, and why this round exists

    92cb89b..2584afb    18 commits, 45 files, +1950/-68, ALL paths

**Nothing has reviewed any of it.** `check-review-coverage.py` reports 83
trunk commits COVERED BY NOTHING, up from the 64 recorded when #119 was
written. I produced most of that increase today, pushing roughly ten times
without a reviewer, which is a direct violation of this project's standing
rule that a reviewer sees every change **before** the push, not in
batches.

**This is #118's defect happening again with me as the author**: the
review model only ever covered UNITS, so fix/chore/checker work has never
been in any round's scope by construction. This round is scoped by RANGE
and covers every path, deliberately.

## §C — What this change actually is, and where to be most adversarial

Most of it is **gates, checkers and probes** — machinery that decides
whether other things are correct. That is the most dangerous category in
this repo, because a defective gate reports green forever and nobody looks
again. Weight your attention accordingly:

1. `docs/reviews/check-checkers-are-wired.py` — new, wired. Requires every
   `docs/reviews/check-*` to be wired or carry a stated reason. **Ask
   whether its exemption mechanism can be used to silence a real gap**,
   whether its container is genuinely the right one (it excludes
   `scripts/check-*.sh` by an argument you should test rather than
   accept), and whether the `bare_python_steps` detector can miss a real
   case or fire on a safe one.
2. `docs/reviews/probe-ci-checker-steps.py` — new. It claims to run CI's
   steps verbatim, and runs 12 of 78. **Check that its classifier's
   refusals are honest** and that the 12 it runs really are byte-identical
   to the workflow's strings.
3. `docs/reviews/probe-docs-lint-amputation.py` — now prints the probed
   process's stdout AND stderr on failure. Check the window is not hiding
   the interesting end of the output.
4. The `#126` citation sweep (`26973a4`), 47 sites, and the three
   repointed citations in `fe237d5`. **Re-derive at least five of the 19
   end-line decisions yourself against the freeze** rather than reading
   the worklog's account of them.
5. `pyproject.toml` + `uv.lock` — pyyaml and types-PyYAML added. Check the
   lock is consistent and that nothing else moved.
6. `.github/workflows/ci.yml` — three steps added or changed.

## §D — Method

**One agent, both lenses.** Play the adversarial reviewer and the
responder yourself, in that order, and reach a settled disposition per
finding. Severity: Critical / High / Medium / Low / nit.

**EVERY finding ships a suggested fix**, at every severity including nits.
A finding without a proposed remedy is an observation.

**Verify, do not trust.** The commit messages in this range are long and
confident and several of them narrate my own errors. Treat every number in
them as a claim: re-measure it. Specifically, these are stated as fact and
are worth checking independently — 27 checkers / 23 wired / 4 exempt; 47
citation sites collapsing to 19 end lines; `Ran 12 of 78 run steps`; suite
873 passed.

**Look for the vacuous.** Several of these gates were proved "able to
fail" by controls I wrote. A control written by the same author who wrote
the gate shares its blind spot. Where you can, amputate the behaviour and
check the gate actually dies — and say plainly if a control tests a proxy
rather than the subject.

## §E — Constraints

- Branch `review/r13` off current `main`.
- **Do not fix anything, do not merge, do not push.** Report only. I merge
  and push, always.
- **Your report MUST carry the declaration**, on its own line:
  `<!-- REVIEW-COVERS: 92cb89b..2584afb -->`
  No `PATHS:` clause — this round covers the whole tree, and that is the
  claim you are making.
- No `Co-Authored-By` or "Generated with" trailer.
- Do not `git stash` — other agents are live on this tree.
- `git commit -F` with a **quoted** heredoc (`<<'MSG'`).
- Cite `file:line` only from `grep -n` or a numbered Read.
- Report to `docs/reviews/REVIEW-R13.md`.

## §F — Report back

`SendMessage` to `team-lead`: findings by severity with a suggested fix
each, which numbers you re-measured and whether they held, anything you
judged vacuous, and what you could NOT verify. **The last-named list is
for what you could not settle, not what you did not attempt.**

If this range contains something I have described in a commit message as
fixed that is not fixed, say so directly. Four agents have corrected me
today and every one of them was right.
