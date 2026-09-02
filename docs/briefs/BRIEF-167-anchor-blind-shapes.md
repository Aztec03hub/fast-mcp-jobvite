# BRIEF — #167: the anchor checker sees 12 of 15 in one file, and the floor is derived from it

You are `suborch-167`.

## §A — Standing rules (read FIRST, in this order)

1. `docs/DESIGN.md` — FROZEN. 2. `docs/adr/` in number order.
3. `docs/OBLIGATIONS.md` 4. `docs/briefs/PROTOCOL-sub-orchestrators.md`
5. `CONTRIBUTING.md`
6. **`docs/reviews/REVIEW-156-u1-landing-guard.md`** — the report that
   found this, first-hand.

Hard rules:

- **NEVER print or commit a secret.** No `Co-Authored-By:` trailers, ever.
- **You do not push and you do not merge.**
- **Own worktree**, from `origin/main` at `22c9873` or later:
  `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/w167 -b fix/167-anchor-shapes`
- **`TaskGet` before acting on any assignment** and compare the TEXT to
  this brief (#162: the echo is dated LATER and comes back under your own
  name). Never "check who sent it".
- **CI's exact invocations.** `uv run --frozen python`, never `python3`.
- **Report by `SendMessage` to `fastmcp-jobvite`**; findings to a `.md`.
- **Correct this brief where it is wrong.** Thirteen of thirteen have.

## §B — Files you OWN

    scripts/check-harness-anchors.py
    scripts/check-harness-anchors-controls.sh
    .github/workflows/ci.yml   (the anchor floor ONLY - one number)
    docs/reviews/<your findings .md>

You are the only agent in `ci.yml`. Change nothing in it but the floor.

## §C — The defect, measured by #156

`scripts/check-harness-anchors.py` resolves **12** anchors in
`scripts/check-u1-boot-amputation.sh`. **There are 15.** Two independent
selector limits:

1. `:417` matches `attr == "sub"`, so row H's `re.subn` is invisible.
2. `:331` requires `.replace(` or `re.sub(` in the body, so rows K and
   M's index-and-slice anchors are invisible.

**The floor of 458 is derived from that blind selector**, and the floor
is the number that makes "all anchors resolve" mean anything.

**IT ALSO SHAPES CODE AWAY FROM THE SAFER IDIOM.** #156 reports it
converted nothing to `re.subn` precisely because the obvious landing
check would have silently dropped four more anchors at exit 0. A gate
that punishes the better construct is worse than one that misses it.

## §D — What to do, IN THIS ORDER

1. **MEASURE THE CONTAINER FIRST, and this is the deliverable even if
   nothing else lands.** Enumerate every mutation site in every harness
   by KIND, and compare against what the checker resolves. **Nobody has
   this number.** #156 measured one file and said so; it did not
   generalise, and neither should you until you have counted.
2. **Then widen the selector** to the shapes actually in use, and
   **land the widening and the new floor together**. Expect the floor to
   RISE. **A widening that leaves 458 unchanged did nothing** — say so
   rather than reporting a green.
3. **DO NOT RAISE THE FLOOR FIRST.** #91 found a floor carrying 5 rows
   of slack; a floor set from a blind instrument is that defect with the
   slack invisible.

## §E — How your work will be judged

- **An arm asserting a known-hidden shape is now counted**, or the fix
  is unprovable. Amputate the widening and require that arm to go red.
- **Every count carries its container** — "15 anchors in
  check-u1-boot-amputation.sh at `<sha>`", never "15".
- `--self-check` must still pass, and all gates green, each exit code on
  its own line, including the full suite (887 passed, 0 skipped).
- Separate COULD NOT SETTLE from did not attempt.

## §F — Context

- #156 just landed guards in `check-u1-boot-amputation.sh`; read that
  file at HEAD, not from the report.
- **A smaller finding from the same report, yours if it is cheap:** all
  13 mutators in that harness run bare `python3` where CI uses
  `uv run --frozen python`. Harmless today (stdlib only) but it is the
  #46 shape, which has been a real defect here once. Fix it or report it
  — do not silently leave it.
- CI's first-ever deep run is in flight. Do not add a red step.
