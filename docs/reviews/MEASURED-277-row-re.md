# MEASURED-277: the `--row-re` refusal was FALSE, and the fix is a second refusal

Branch `fix/277-rebased`, off `main` @ `d314283`. One file changed:
`docs/reviews/check-row-floor-exactness.py`.

This is a RE-DERIVATION, not a rebase. The original branch
`fix/277-row-re-quotes` @ `d34eb6f` was cut from `origin/main` @ `1636f56`,
19 commits behind, and in that gap the target file went 1020 -> 2020 lines:
`_external_floors()` gained step-block parsing, a shard count, a
two-gate-line refusal and a `raw`/`consumers` test seam. A three-way merge
across that is more likely to smuggle damage in than to save time, so the
three arms and the helper were re-applied by hand and every citation
re-measured against `d314283`. `fix/277-row-re-quotes` is superseded and can
be abandoned.

## The citations, re-measured on `d314283`

All SHA-pinned with `git grep -n ... d314283`:

* The defect is at `docs/reviews/check-row-floor-exactness.py:731` -
  `row_re = re.search(r"--row-re\s+'([^']*)'", tail)` - inside
  `_external_floors()` (`:682`), and its refusal is `:733`-`:737`.
  (On the ORIGINAL base `1636f56` the same code sat at `:345`; the old
  record's `:345` was right for that object and is wrong for this one.)
* The file DOES state the governing principle on this base:
  `:483` **"THE MESSAGE HAS TO BE TRUE (R270-R2-L1)"** in
  `_env_shard_values()`, and again at `:1584`. The old record said the
  principle was absent from the file - that was true of `1636f56` and is
  false of `d314283`; the R270 work in the gap wrote it in. `_row_re_arg()`
  now cites `:483`'s rule rather than inventing it.
* Consumer evidence, `scripts/ci-harness-gate.sh` on `d314283`:
  `:101` `--row-re) row_re="$2"; shift 2 ;;`
  `:417` `[ -n "$row_re" ] || { echo "::error::--min-rows needs --row-re"; exit 2; }`
  `:418` `rows=$(printf '%s\n' "$out" | grep -cE "$row_re")`

## Live-usage count on `d314283`: still ZERO

    git grep -n 'row-re' d314283 -- .github scripts

25 hits. Four are not gate-line flags (`scripts/check-u4-client-amputation.sh:26`
and `scripts/ci-harness-gate.sh:45,101,417` - a comment, the usage block, the
parser and the run-time refusal). The remaining 21 are gate-line `--row-re`
flags and **every one is single-quoted. Not one line in the repository uses
the double-quoted form.** Nothing was firing and nothing was mis-certified.
This is hardening, not a live breakage.

## Pre-fix arm: the FALSE message, on THIS tree

The unmodified `d314283` file, loaded as a module and fed a synthetic step
whose gate line carries a double-quoted `--row-re`:

    run: bash scripts/ci-harness-gate.sh a.sh --min-rows 10 --row-re "^r "

    PRE-FIX  REFUSAL: a.sh: --min-rows with no --row-re. ci-harness-gate.sh
             refuses that pairing at run time, so finding it here means
             ci.yml and the gate disagree.

    POST-FIX REFUSAL: a.sh: --row-re is present but DOUBLE-QUOTED. bash would
             interpolate the pattern before ci-harness-gate.sh saw it, so the
             ERE this file reads is not the one grep would run. Write it in
             single quotes.

The flag is on the line. The pre-fix message says it is not. That is the
defect, reproduced on the current base rather than carried over as a claim.

## The decision: remedy (b), REFUSE with a true message. Not (a)

Re-verified against the consumer, not accepted from the old record. The gate
never sees the quoting: `:101` receives `$2` **after bash has already dequoted
and expanded it**, and `:418` greps with exactly that. This checker instead
reads the pattern out of `ci.yml` as TEXT and hands it to `static_rows()` to
count rows statically. The whole claim this file makes is that those two
strings are THE SAME string.

They are the same string only where bash expanded nothing - which is to say
only under single quotes. Inside double quotes an ERE containing `$(`, a
backtick or `$name` is rewritten before `grep -cE` runs. Accepting the
double-quoted form would make this checker certify an exact row count against
a pattern that is not the pattern the gate greps with: quiet and wrong, in
place of loud and wrong. Remedy (a) would additionally require this file to
emulate bash's dequoting to stay honest - real machinery, for zero live users.
Refused.

So `_row_re_arg()` splits the one refusal into two true ones: double-quoted
gets its own message naming the interpolation, and the original message is
left for the genuine no-flag case that `ci-harness-gate.sh:417` enforces.

## Siblings: two more quote-shape-fragile parsers, both still present

Both re-probed by RUNNING them on `d314283`, not by reading them. Neither is
changed - both fail LOUD rather than silently certifying.

1. **`--min-rows\s+(\d+)`**, `d314283:docs/reviews/check-row-floor-exactness.py:728`.
   Requires BARE digits. Measured with a one-step fixture carrying
   `--min-rows "10" --row-re '^r '`:

       REFUSAL: parsed 0 --min-rows values but ci.yml carries 1 as flags.
       The join is wrong, and a wrong join here reports a reassuring zero
       rather than an error.

   The harness drops out of `found` and the `--min-rows` FLAG counter
   (`:766`'s refusal) then raises. **That message is misleading in the same
   way #277's was** - the join is fine, the quoting is not - but it is a red
   run, not a blessed one, so it is one severity down. Left alone; a separate
   ticket if anyone ever quotes a row count.

2. **`ci-harness-gate\.sh\s+(\S+)`**, `d314283:docs/reviews/check-row-floor-exactness.py:724`.
   Measured with `ci-harness-gate.sh "a.sh" --min-rows 10 --row-re '^r '`:

       {'"a.sh"': (10, '^r ', 1)}

   The key carries the quote characters, so it never matches a path on disk
   and `main()` reports "not on disk" - true-ish, and confusing. Also zero
   live users. Left alone: the honest fix has to decide what a quoted harness
   name MEANS to the gate, which is more than one line.

No other quote-shape-specific capture exists in `_external_floors()`.

## The three arms

Renumbered from the original's A21-A23. The arm set on `d314283` ends at A48,
so these are **A49-A51**, and `arm_floor` moves `48` -> `51` in the SAME
commit - this file refuses a floor that disagrees with its own arm count, and
it is the file being edited. They follow the file's convention (the label
string starts its own line), which is what
`docs/reviews/check-row-floor-controls.sh:197`'s ERE
`arm\(\n\s*"(?P<label>A[0-9]+) ` counts.

* **A49 (post-fix)** - a double-quoted `--row-re` is refused for the RIGHT
  reason: the message contains `DOUBLE-QUOTED` and does NOT contain
  `no --row-re`.
* **A50 (defect-pinning)** - the old single-quote-only capture, kept verbatim
  in the arm, returns `None` on that same line. Without it A49 could pass for
  a reason unrelated to what #277 measured.
* **A51 (negative control)** - a gate line with genuinely NO `--row-re` still
  gets the original `no --row-re` message. The new refusal must not swallow
  the real case the old one exists for.

## Before / after

    BEFORE (d314283, unmodified)
      python3 docs/reviews/check-row-floor-exactness.py --self-test
      HARNESS-RESULT name=check-row-floor-exactness.py rows=48 floor=48 fired=48/48 status=ok
      exit 0   |  PASSED=48  FAILED=0  SKIPPED=0

    AFTER
      HARNESS-RESULT name=check-row-floor-exactness.py rows=51 floor=51 fired=51/51 status=ok
      exit 0   |  PASSED=51  FAILED=0  SKIPPED=0

The arm harness has no skip mechanism, so 51 arms ran and 51 fired; the PASSED
count moved 48 -> 51, not just the exit code.

    AFTER, main() - the exactness claim over the whole repo
      python3 docs/reviews/check-row-floor-exactness.py
      docs/reviews/check-row-floor-exactness.py    floor  51  rows  51
      Harnesses checked for exactness: 34
      Harnesses carrying BOTH floors, checked for agreement: 8
      Harnesses whose --min-rows was compared to a live count: 16
      Every floor equals its harness's live row count. OK.
      exit 0

    ruff check   docs/reviews/check-row-floor-exactness.py   -> All checks passed
    ruff format --check ...                                  -> already formatted

## Not settled

* Whether bash's expansion of a double-quoted ERE is *always* damaging is not
  established and is not the argument. Many EREs survive double quotes intact.
  The argument is that this file cannot know which, so it must not vouch for
  the count either way. If someone later wants (a), the honest version has to
  dequote the way bash does, and that is a different ticket.
* The two sibling parsers above are diagnosed and reproduced but not fixed, by
  scope.
