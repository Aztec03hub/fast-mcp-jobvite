# R7-FIXES - close R7's findings over U8, U9, U12 and U10

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `r7-fixes`. Your branch is `fix/r7-findings`. Your report goes to
`docs/worklogs/R7-FIXES-REPORT.md`, committed on your branch.

**Read `docs/reviews/REVIEW-R7.md` in full before touching anything.** It is on `main` as of the
merge at `ad948b3`. Every finding below is stated there with its measurement; this brief tells you
what to do about them and what to distrust.

## The rule that governs this whole brief

**A review's suggested fix is a HYPOTHESIS, not an instruction.** On this project four of them have
now failed on measurement: R4's own H1 remedy carried the M3 defect, R4-L2 did not type-check, R6's
H1 fix hit the same `reset()` branch it was meant to avoid, R6's M1 fix burned the whole attempt cap,
and U12-F2's would have missed the path entirely. R7 is careful and says which of its fixes it ran -
**one of eight** - but that does not raise the other seven above hypothesis.

**Measure the defect yourself before you fix it, and measure the fix after.** If R7's suggestion is
wrong, say so with the measurement and do the right thing instead. A finding you rule WRONG with
evidence is a good outcome; a fix applied because a report suggested it is not.

## H2 IS NOT YOURS. I am doing it.

`check-u9-http-controls.sh` has no row floor. Leave it alone - I am editing that file. If your work
needs it, say so in your report and I will sequence it.

## Take these in this order

### H1 (HIGH) - a payload-logging middleware passes the entire 663-test suite

R7's mutation M4 added a middleware to `build_middleware` and **nothing went red**. Both
`EXCLUDED_MIDDLEWARE` (5 names) and its adopted counterpart are hand-kept lists beside a container
nobody enumerates, and seven middleware classes are in neither list.

This is the shape this project has now measured seven times: **a hand-kept list beside its container
is blind to the member nobody added.** The fix is not to add the eighth name. **Enumerate the
CONTAINER and assert the two sets are EQUAL** - subset passes on a bare addition, which is the whole
defect.

R7's suggestion (discover subclasses under `fastmcp.server.middleware` via `pkgutil.iter_modules`,
assert equality, keep `EXCLUDED_MIDDLEWARE` as documentation of *why* five were rejected, and add a
second assertion that adopted ∪ excluded ∪ ours accounts for every discovered class) is sound in
shape. **Verify that the enumeration actually sees every class before you trust it** - a discovery
mechanism that silently returns a short list gives you a green that means nothing, and this project
has recorded a wrong-zero from exactly that three times in one day. Prove it by construction: assert
the discovered count is greater than the number you can name by hand, and make one of the seven
currently-ungoverned classes appear in your output.

**Then re-run R7's M4 mutation and confirm it now goes RED.** A fix for a surviving mutation that
does not kill that mutation is not a fix.

### H3 (HIGH) - the approval-wording tripwire has a 160-character blind spot

A plain claim that a human approved something evades the tripwire whenever any unrelated "not" sits
within 160 characters, and R7 measured **6/6 evasions** plus that **24-40% of the scanned corpus sits
in that shadow** - the tripwire is blindest exactly where the prose denies the most, which is the
prose the rule exists for.

Second half of the same finding: the owned-file list at `:1217-1222` is hand-kept and short. Same
container rule as H1.

**This is the one claim this project has decided it may never make** - that a person approved
something when nothing proves a human approved anything. Treat it accordingly.

R7 offers a three-part fix, cheapest first. Take them in that order and **measure the evasion rate
after each part**, so the report says which part bought what. Do not report "fixed" on a rewrite you
did not re-run the 6 evasions against.

### M1 (MEDIUM) - three more dual-declared pydantic defaults, all in `tools/jobs.py`

`SearchJobsInput.ids` at `:121` and two others. The `send_email` fix never touched this file.
R7's mutation M1 set the inert copy to a type-invalid value and **nothing noticed**.

Precedence is confirmed on the locked `pydantic 2.13.5`, not cited. **Delete `default=None,` from
the three, then re-run M1 and confirm it dies.** Lower blast radius than `send_email` - all three are
`None` - but it is the same defect and the fix is three deletions.

**While you are there: grep for the fourth.** The `send_email` fix closed one instance, R7 found
three more in a file that fix never opened, and nobody has enumerated the whole population. Do that
enumeration and put the number in your report - a machine over every pydantic field, not a reading.

### M2 (MEDIUM) - U12's page-cap guard is a literal-substring scan

A genuine second copy of the cap spelled `1_000` under another name **survives the whole suite**
(R7's mutation M3). Neither would `items[0:1000]`.

R7's fix - match on **value, not spelling**, by parsing with `ast` and walking for the integer -
is the right shape. Watch the failure mode: an `ast` walk that finds nothing also passes. **Assert
it finds the cap that IS there** before trusting that it found no others.

The stake is on the record: U6-F1 was "the RESULT cap wrong in two halves that were each correct
alone".

### M3 (MEDIUM) - U12's caller-visible arm is unbuilt

The behaviour is correct today - R7 probed it and found no leak, `detail` is enumerated prose and
never `str(exc)`. **Nothing holds it there.** `errors.py` is one edit away from the shape R2-M5/L1
already found and fixed elsewhere.

Build the arm. R7 ran the probe, so the mechanics are proved; the missing piece is the ratchet.
**Amputate it when you are done** - make `detail` carry `str(exc)` and confirm your new arm goes red.

### M4 (MEDIUM) - and R7's own status line on it is wrong in a way you must not repeat

`send_email` is redacted to `[REDACTED:bool]`, so the audit event cannot answer *"did this write
email a live person?"* - against `DESIGN.md:1719` C1-T1, which names flipping `send_email` to `true`
a **High** threat, and `DESIGN.md:242`, which makes its `false` default a safety property.

R7 says this fix is **"RUN, and it is safe"**. **It is not in `main`.** I checked: `send_email`
appears nowhere in `src/fast_mcp_jobvite/utils/redaction.py` at `ad948b3`. R7 was read-only on
`src/`, so it measured the fix in its worktree and correctly reverted - but the report's wording
reads as landed. **Apply it, and treat "the report says it was run" as telling you the measurement
exists, never that the code is in the tree.**

### L1, L2 and the remaining nits

L1: the named guard on the era discriminator asserts two literals the test wrote itself are equal and
never calls the function it claims to protect. The branch IS covered by other cases (R7's mutation M2
dies), which is why it is a nit - **but a test whose name is a claim its body never exercises is on
this project's list of recorded defects.** Give it a body that matches its name.

L2: the write's PII-absence assertion checks one of four values and only `arguments`.

**Every finding at every severity ships with a fix, nits included.** If you rule one WRONG, that is a
fix too - say what you measured.

## Gates

The full list is in `CONTRIBUTING.md`. Specific to this branch:

- **The suite floor is 663 and the anchor floor is 371, and you must DERIVE both from `ci.yml`
  rather than retyping them.** Branch-local floors have been wrong on this project four times.
- Your changes should RAISE the suite count. Say what it is at the end, read from the terminal, and
  **run the full gate before folding, not after** - focused plus adjacent green is not the fold gate.
- **0 skips.** A skip is a green that tested nothing; compare PASSED counts.
- Re-run every harness whose file you touched, and **re-run the specific R7 mutation for each finding
  you claim to have fixed** - M4 for H1, M1 for the pydantic defaults, M3 for the page cap. A fix
  that does not kill its mutation is not a fix.

## In the report

Per finding: what you measured BEFORE, what you changed, what you measured AFTER, and whether R7's
suggested fix survived contact. Name every one that did not.

**End with what you could not settle.** That list is for what you CANNOT settle, not what you did not
try - a cheap item parked there reads as rigour and is not.
