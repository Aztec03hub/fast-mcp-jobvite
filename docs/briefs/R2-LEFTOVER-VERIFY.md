# R2-LEFTOVER-VERIFY - thirteen findings that may or may not still exist

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `r2-verify`. **You are READ-ONLY on `src/` and `tests/`** - see Isolation below.
Your report goes to `docs/reviews/R2-LEFTOVER-VERDICTS.md`, on branch `review/r2-leftovers`.

## The job

`docs/reviews/REVIEW-CODE-R2.md` is merged on `main`: 6 High, 8 Medium, 7 Low, 4 nits over U1, U3 and
U4. Most are closed. **Thirteen have never been checked against the tree since R2 ran, and eleven
merges have landed since.** Task #13 lists them and says, in its own words, *"DO NOT TRUST THIS LIST
OVER THE TREE"*:

    M-1, M-2, M-3, M-4, M-6, M-8, L-4, L-5, L-6, nit-1, nit-2, nit-3, nit-4

For each one, return a verdict from exactly this set, with evidence:

- **STILL OPEN** - reproduced. Say how, at `file:line`, and ship a suggested fix.
- **FIXED** - name the commit that fixed it and quote the line that closes it.
- **FIXED INCIDENTALLY** - it is closed but no commit was aiming at it. Say what closed it.
- **WRONG** - the finding did not describe the code correctly even at R2. Show why, and say so
  plainly; a reviewer being wrong is a normal outcome and burying it is not.
- **SUPERSEDED** - a later round filed the same defect. Name the finding that replaced it.

**M-8 is already known to be stale** - it cites a coverage figure and coverage now reports 93%+. Do
not spend time proving that; confirm it in a sentence and move on.

## The method, which task #13 states and I am repeating because it is the whole value here

> I found H-5 by reading the module rather than the report - the report said what was wrong, but the
> contradiction was visible in twenty lines of source. **Read the code first and use the report to
> confirm, not the other way round.**

H-5 was `companyId` sitting in `NON_SENSITIVE_ARGUMENT_KEYS` while `companyid` sat in
`SECRET_QUERY_PARAMS` - one credential, redacted on one path and published in the clear on another,
by two lists eighty lines apart in one file whose own docstring said which was right. **Two review
rounds read past it.** Reading the report first is how that happens: the report tells you what to
look for and you stop looking.

## Two verdicts are not the same and you must not merge them

**"I could not reproduce it" is not "it is fixed."** If you cannot tell, say STILL OPEN and describe
exactly what you tried. An absence is a claim about where you looked - this repository has recorded
that failure enough times to have a name for it. Prove the path you searched exists before reporting
a clean zero from it.

## Isolation - READ-ONLY, and this is not negotiable

`r4-fixes` is live in `src/` and `tests/` right now and is mid-sweep across a dozen files. **You do
not edit either tree.** Not a test, not a comment, not a docstring. Your output is one report on your
own branch.

If a finding's fix is one line, **write the line into the report as a suggested diff** and let the
owner apply it. Every finding ships a suggested fix - that is standing policy - but shipping it as
text rather than as an edit is what keeps two agents out of one file.

To reproduce anything that needs a mutation: **copy the file to a scratch path, mutate the copy,
restore with `cp` and verify with `cmp`**, never `git checkout` and never `git stash` - a stash takes
whatever `r4-fixes` has uncommitted. If a check genuinely cannot be done without editing the tree,
say so in the report and leave it unverified rather than reaching into another agent's files.

## A worked example of the standard, which I measured this morning

R2-H-4 said the inbound `request_id` regex was untested at the log-forging shape, on the evidence
that `grep` over `tests/test_correlation.py` found nothing. **The test exists** - in
`tests/test_audit.py:610`, parametrised with
`"11111111-1111-4111-8111-111111111111\ninjected=audit_bypass"`. The finding was a search at one
path reported as an absence everywhere.

**And it was still half right, for a reason nobody had written down.** `_UUID4_RE` is anchored
`\A...\Z`. I mutated `\Z` to `$` and **the whole audit suite stayed green at 43 passed**, while
`resolve_request_id("...-111111111111\n")` echoed the newline back - the exact C7-T1 vector. Python's
`$` matches before a trailing newline; `\Z` does not. The embedded-newline case cannot catch it
because the injected text after the newline breaks the match either way.

That is the bar: **a verdict that survives an amputation of the thing it claims to test.** Where a
finding is about a guard, ask what mutation of that guard the suite would not notice.

## In the report

One section per finding, in the order listed above. Verdict, evidence at `file:line`, and for
anything STILL OPEN a suggested fix as text.

**End with what you could not settle**, and put anything you did not try in that list rather than
inferring a verdict from silence. A cheap item parked in "could not settle" reads as rigour and is
not; if it was cheap, do it.
