# BRIEF — #166 + #169: a checker enforcing half its own stated invariant, and five counts beside growing containers

You are `suborch-166`. Two review rounds found these; each has a
verified fix and none is large. **They are grouped because they share
one shape: a claim that was true when written.**

## §A — Standing rules (read FIRST, in this order)

1. `docs/DESIGN.md` — FROZEN. 2. `docs/adr/` in number order.
3. `docs/OBLIGATIONS.md` 4. `docs/briefs/PROTOCOL-sub-orchestrators.md`
5. `CONTRIBUTING.md`
6. **`docs/reviews/REVIEW-R16.md` and `REVIEW-R17.md`** — the findings,
   first-hand, not from this brief.

Hard rules:

- **NEVER print or commit a secret.** No `Co-Authored-By:` trailers, ever.
- **You do not push and you do not merge.**
- **Own worktree**, from `origin/main` at `22c9873` or later:
  `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/w166 -b fix/166-drifted-claims`
- **`TaskGet` before acting on any assignment** and compare the TEXT
  (#162). Never "check who sent it".
- **CI's exact invocations.** `uv run --frozen python`, never `python3`.
- **Report by `SendMessage` to `fastmcp-jobvite`**; findings to a `.md`.
- **Correct this brief where it is wrong.** Thirteen of thirteen have.

## §B — Files you OWN

    docs/reviews/check-landing-published.py
    docs/reviews/measure-xref-population.py
    tests/test_audit_phase_sites.py
    CONTRIBUTING.md
    docs/README.md
    docs/adr/README.md
    scripts/one-shot/apply-116-timeout-names.py
    src/fast_mcp_jobvite/utils/redaction.py   (ONE comment line)
    docs/reviews/<your findings .md>

**NOT yours:** `.github/workflows/ci.yml` (`suborch-167` holds it),
`docs/reviews/check-review-coverage.py` and `probe-coverage-ratchet.py`
(`suborch-168`), `scripts/check-harness-anchors.py` (`suborch-167`).

## §C — The real one first (R16-M2)

`docs/reviews/check-landing-published.py:185-189` reports a finding only
when the window contains `return`. **A branch that prints the landing
diagnostic and FALLS THROUGH is neither fatal nor counted, and is not
reported** — while the docstring states the invariant as "either FATAL
or publishes a tally". The prose is right; the code enforces half of it.

Measured both ways with a planted TRACKED script: fall-through gives 0
findings exit 0; the same file with `return 1` gives 1 finding exit 1.

**R16's first arm here was VACUOUS and it caught that**: `container()`
reads `git ls-files`, so an UNTRACKED plant is invisible — only the "37
scripts scanned" count told it. **Your arms must assert the population
size, not just the finding count.** That is #163's trap and it has now
bitten twice.

FIX: invert to "report unless positively disposed of", exempt
`scripts/ci-harness-gate.sh` by name with its reason (its vocabulary
array at :74-77 is the only thing that would newly match), and add BOTH
shapes as arms. Latent today: 0 real fall-through instances.

## §D — R17-M1: a zero that is 62 vacuous skips

`docs/reviews/measure-xref-population.py:48` excludes `docs/briefs/` and
`docs/reviews/` while its docstring claims "every tracked *.md outside
the RECORD paths" — and `check-review-coverage.py:161-170` refuses
`docs/briefs` as a RECORD path **by name**.

**Removing the exclusion alone does not help.** It hard-codes
`referent=None` outside `docs/adr/`, so briefs measure **62 tracked, 0
MEASURED, 62 SKIPPED, 0 unresolved** — a vacuous zero hiding **83
section references across 18 files**. R17's own first run reported "0
across 0 files" and it nearly published that: an
`except ValueError: continue` had swallowed the population.

**Do not report a zero from this file without also reporting how many
were MEASURED.** A zero over an empty population is the defect.

## §E — R17-M2, and five counts

**R17-M2:** `tests/test_audit_phase_sites.py:503-516` compares a SET of
`(function, phase)`, so 13 AST call sites collapse to 6 pairs. A site in
an already-covered function with an already-covered phase is invisible.
R17 called it the strongest test in its population; the fix is to
compare `Counter`s keyed by call site.

**The counts, all beside growing containers:**

- `docs/README.md:22` "Eleven decision records" and `docs/adr/README.md:7`
  "eleven ADRs" — there are **33**. `docs/README.md`'s own opening
  paragraph explains a count was DELETED from that file for going stale,
  nine lines above. **DELETE both numbers; do not replace 11 with 33.**
  Its siblings "Seven reports" (7) and "Six further gates" (6) are
  correct — leave them and say you checked.
- `CONTRIBUTING.md` "it is thirteen harnesses and takes a while" — the
  command it prescribes returns **32**, in the paragraph explaining the
  list is DERIVED so it cannot go stale. A costing, not a typo: the
  slowest member measured is ~1040s. **The same stale 13 in REPORT-147
  §6 is a dated record — leave that one.**
- `scripts/one-shot/apply-116-timeout-names.py` emits "Three names
  because the arms are three separate decisions" into 32 files, then
  emits only the names each file uses: 10 declare 3, 19 declare 2, 2
  declare 1. Fix at the template, count-free.
- **R16-N3/N4 are in `ci.yml` and are NOT YOURS.** Report them.
- `redaction.py:54` imports `httpx2._client` privately — correct per
  ADR-0026, loud ImportError on failure, but nothing says so. One
  comment.

## §F — How your work will be judged

- **Every fix that changes behaviour ships an arm**; the count fixes do
  not, and saying which is which is part of the report.
- **Read every site before changing a rule.** #152's shape rule was
  wrong on 4 of 6, #159's premise was a grep over a word, and my own
  probe classification was too crude to ship. That is three in one
  evening.
- All gates green, each exit code on its own line, full suite 887/0.
- Separate COULD NOT SETTLE from did not attempt.
