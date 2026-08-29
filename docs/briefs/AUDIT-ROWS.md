# AUDIT-ROWS - two `result_status = "error"` rows are asserted by nothing, one on the write

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `audit-rows`. Your branch is `fix/audit-rows`. Your report goes to
`docs/worklogs/AUDIT-ROWS-REPORT.md`, committed on your branch. Your task record is **#101**.

## The measurement, and it is already done - do not redo it, verify it

`#97` enumerated the container rather than stopping at the files its own brief named.
`grep -rn 'result_status = "error"' src/` gives SIX sites. Each was deleted one at a time and the
WHOLE suite run. The probe is committed at `docs/reviews/probe-audit-row-container.sh` - **run it
yourself on your branch before you touch anything.** A worklog paragraph about a measurement is a
claim that it once ran; the script is the artefact.

    jobs.py:411        search_jobs        exit 1  ASSERTED
    jobs.py:701        get_job_feed       exit 0  VACUOUS -> closed by #97
    candidates.py:646  search_candidates  exit 0  *** YOURS ***
    candidates.py:692  get_candidate      exit 1  ASSERTED (#94's A11)
    candidates.py:778  approval refusal   exit 1  ASSERTED
    candidates.py:806  create_candidate   exit 0  *** YOURS ***

**Line numbers move. Anchor on the subject, not the number**, and require the subject to be unique -
the bare `except` line appears three times in that module.

## Why coverage cannot see this, which is the whole point

`tools/candidates.py` measures **100.00% line and 100.00% branch** and is on `DESIGN.md:1364`'s
critical-path list at ADR-0010's 95/90 floors. Both arms are EXECUTED on every run. The cases
driving them assert the caller-visible half - `is_error`, the problem object - and never read the
audit row. A branch can be walked through without being checked, and this is what that looks like
in a module with a perfect coverage number.

**`candidates.py:806` is the more serious.** It is `create_candidate`, the WRITE, on a path where
the write may or may not have landed. Delete the line and a failed or ambiguous create is recorded
as a success. The audit row is the only surviving evidence anyone has afterwards.

## The fix, whose shape is measured rather than guessed

The cases that drive these two arms already exist. They need the second claim, exactly as #94 did
for `get_candidate` and #97 did for `get_job_feed`: assert `event["result_status"] == "error"` from
the captured audit stream, with a message naming why - **a read or write that fails and is written
down as a success is a record that lies.**

Then two rows in `scripts/check-critical-coverage-amputation.sh`, on A11's model: each deletes ONE
`event.result_status = "error"` line and nothing else, so it proves the audit assertion
specifically rather than the error arm generally. **Raise `ROW_FLOOR` from your run, never by
adding two to the 18 that is there** - and hand me the new `--min-rows` for `ci.yml:804`, which is
mine to edit, not yours.

## Do not chase the number

Both modules are already at 100/100, so nothing you do here moves coverage at all. That is the
point: the only evidence that counts is **the amputation going red**. For each of the two, delete
the behaviour and show the new assertion failing. A row you cannot kill is a row you have not
tested. If either arm turns out to be unreachable, that is a finding and a different fix - say so
and prove it rather than reaching it artificially.

## Gates

Floors DERIVED from `ci.yml` by grep, never retyped - 867 and 456 as this was written and they move
hourly. **0 skips.** Run the gate's OWN commands argument for argument: `uv run --frozen mypy`, NOT
`mypy src`; `ci.yml:422` is the authority. Run any `ci.yml` step you intend to suggest, before you
suggest it.

## In the report

The probe's output on your branch. Per arm: the case, the assertion added, and the amputation that
proves it can fail. The new `ROW_FLOOR` and where you read it. Then what you could not settle.
