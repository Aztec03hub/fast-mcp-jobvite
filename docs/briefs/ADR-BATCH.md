# ADR-BATCH - apply eight Accepted ADRs to the frozen design, and re-freeze

## Tools you must load before you start

    ToolSearch with query: select:TaskCreate,TaskGet,TaskList,TaskUpdate

`TaskList`, then `TaskGet` **task #1** immediately before claiming it. Claim with `TaskUpdate`
(`owner: "adr-batch"`, `status: "in_progress"`).

**You will receive your own claim back as an assignment. Do not act on it** - `TaskUpdate(owner=you)`
enqueues a notification delivered after the work, with `assignedBy` naming YOU and a timestamp older
than your work. `TaskGet` before acting on any assignment; if it is `completed`, say so and stop.

## What this is

`docs/DESIGN.md` has been FROZEN at `135c3ac` all project. **Eight ADRs are Proposed against it and
this is the single commit that applies them all.** I have decided every one; none is open.

| ADR | Change |
|---|---|
| 0012 | Add `utils/constraints.py` to §3's module layout |
| 0013 | §8 gains a positive pairing for the log stream; #2 rewritten to name it |
| 0014 | C8-I1's evidence clause: `.env.example` has every **secret-class** variable empty |
| 0017 | The unmapped error row becomes `/problems/internal-error`, 500 - not `about:blank` |
| 0018 | `os._exit(status)`, not `os._exit(0)`, so a crash does not report a clean stop |
| 0019 | `DESIGN.md:603`'s `(§5.4)` becomes `(§4.1)` - there is no §5.4 |
| 0021 | Define `approval_mechanism` in §5.3 with a closed vocabulary, and repoint the two rows |
| 0022 | The cookie-jar clause: a disable, not an omission |

**Read each ADR in full before touching anything.** Each has a Decision section saying exactly what
to change; several also say what NOT to change and those limits bind you. **0014 changes no rating
and no disposition** - only the sentence describing evidence. **0017 does not close the
`about:blank` question**, which survives for unmapped HTTP statuses from Jobvite.

**0022's subject may not be `DESIGN.md`.** `grep -in cookie docs/DESIGN.md` returns nothing; its
clause is in `JOBVITE-CONTRACT.md` §2.3. **Find its real subject before editing** - if that document
is not in this repository, say so and apply the other seven.

## THE CITATION PROBLEM, which is the actual work

**841 `DESIGN.md:N` citations exist across 81 files.** A five-line insertion at line 300 moves
**723 of them**. Every stale one is a wrong citation shipped.

**The tool exists. Use it; do not repoint by hand.**

```
python3 docs/reviews/check-design-citations.py              # bounds + inventory
python3 docs/reviews/check-design-citations.py --since 135c3ac
python3 docs/reviews/check-design-citations.py --controls
```

`--since` maps old line numbers to new through a real diff and prints two kinds of line:

- **`MOVED: file:line: DESIGN.md:A -> DESIGN.md:B`** - mechanical. Apply it.
- **`BROKEN: file:line: DESIGN.md:A - that line CHANGED`** - **the tool refuses to guess, and so
  must you.** Open the new text, find where the subject went, repoint by SUBJECT. If the subject is
  gone, report it; do not invent one.

**Repoint from the tool's OWN OUTPUT, parsed, never retyped.** Retyping a value just read is the
step that has failed repeatedly here. Parse the report with a regex, assert you parsed a non-zero
number of lines, and fail loudly if a target string is not where the report said. **Beware multiple
citations on one line** - key on (file, line, old-range) triples, not naive string replacement.

## Two code changes, because two ADRs change shipped behaviour

- **ADR-0017 changes `src/fast_mcp_jobvite/errors.py`.** The unmapped kind becomes
  `/problems/internal-error`, 500, "Internal Server Error". **`INTERNAL_ERROR` stops being dead
  code.** U2's mutant **M10, which its harness killed, becomes correct behaviour** - that inversion
  is the clearest evidence this is a real change. Update `tests/test_error_contract.py` and U2's
  harness, and say which mutation rows changed meaning.
- **ADR-0018 changes `src/fast_mcp_jobvite/__main__.py`.** Its Decision block has the exact code.
  `os._exit` still runs unconditionally, so the stdio hang stays closed and the SIGTERM mitigation is
  unchanged - **only the constant moves.** U1's shutdown tests and harnesses must still pass.

## Flip every status, and re-stamp the freeze

- Each of the eight: `**Status:** Proposed` -> `**Status:** Accepted`.
- **The freeze SHA moves to your commit.** Grep the tree for `135c3ac` and update every place naming
  it as the frozen design. **State the new SHA prominently** - every future brief cites it.
- `docs/plans/IMPLEMENTATION-PLAN.md` may describe these as Proposed. Fix what is now false.

## Then wire the gate that has been waiting for this

`docs/reviews/check-cross-references.py` exits 1 today on **exactly one** finding: `DESIGN.md:603`'s
`§5.4`, which ADR-0019 fixes. It is deliberately unwired so it never landed knowingly red.

**Once it exits 0, wire it into `ci.yml`'s `design-gates` job and add it to `CONTRIBUTING.md`'s gate
list IN THE SAME COMMIT.** Also name `check-design-citations.py` in CONTRIBUTING as a tool run
around a design edit, stating plainly that it is **not** a CI gate and why. If the cross-reference
gate does NOT go green, do not wire it - report why.

## Standing requirements

- **Verify by SUBJECT, never by line arithmetic.** Three range-contraction defects were found in one
  day and every one still resolved to plausible text.
- **`docs/OBLIGATIONS.md` anchors will move.** Repoint from `check-obligations.py`'s own output.
- **Report passed-counts, never the word "green".** Baseline **294 passed, 2 deselected, 0 skipped**.
- **No `Co-Authored-By:` or "Generated with" trailer.** Absolute. **No em dashes** in prose.

## Isolation

- Pin SHA `70cd2ca`. `git worktree add /tmp/adr-batch-work 70cd2ca`.
- **Do NOT check anything out in the shared checkout.**
- Commit to **`adr/batch`**. **I merge and push.** Rebase onto `origin/main` before reporting and
  re-run the gate after the rebase.
- **Commit early and often.** A previous run of this exact task was destroyed by a restart with zero
  commits and its brief was lost with it, which is why this brief lives in the repository. **Commit
  each ADR as you finish it** rather than one commit at the end.
- **Remove your worktree when done** and say so.

## Gates

The full list is `CONTRIBUTING.md`'s "The gates, and how to run them before you push". **mypy is the
type gate, not pyright.** **Judge by exit code on its own line** - under `set -euo pipefail`,
`cmd | grep FAIL || echo clean` prints "clean" when `cmd` FAILS. **Always quote your heredoc
delimiter** (`<<'PY'`). The control harnesses are slow; budget for them, do not skip them.

## How to reach me

`SendMessage` with `to: "team-lead"`. **`to: "main"` does NOT work.**

## How to deliver

1. `docs/worklogs/ADR-BATCH-REPORT.md`, **committed on your branch**. Not `/tmp` - a 48KB report was
   lost that way today.
2. `SendMessage` `to: "team-lead"` with the full report.

State: what each ADR changed, before and after; **the new frozen SHA**; how many citations MOVED and
how many were BROKEN and what you did with each; which mutation rows changed meaning under 0017 and
0018; whether the cross-reference gate went green and was wired; and the merge command.

**End with what you did NOT verify.**
