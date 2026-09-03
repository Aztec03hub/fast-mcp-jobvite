# MEASURED-295: retiring the orphaned records, and what the ratio does not do

Date: 2026-09-02 21:04 CDT. Branch `docs/295-archive`, base `60c3359` on `main`.
Every figure below is derived by the command shown beside it, at that base
unless stated. Nothing was deleted; every retirement is a `git mv`.

## Headline

**Archive-prefixing cannot move the docs/(src+tests) ratio, because
`docs/archive/` is still `docs/`.** 29 files and 448,719 bytes changed
directory and the total ratio moved 5.77x -> 5.78x, upward, because the pass
wrote its own account. The plan's §3.2 target
("docs under 2x src+tests") is unreachable by §3.1's method, and no amount of
correct archiving reaches it. What the pass did buy is a smaller LIVE surface
and a stranded count of zero. Read §1 for both numbers.

**The orphan set is 29, not ~74.** The forensics report counted files with no
inbound link *from another doc*; I counted files nothing in the whole tracked
tree names, which is the question a retirement actually has to answer. Under
the stricter test 73 of 312 docs `.md` are unreferenced, of which 40 are
briefs and 4 are review rounds - both parsed populations, both refused.

## 1. The ratio, three ways, before and after

Method (`git ls-files` is the population; tracked bytes because on-disk `du`
counts `__pycache__` that `src`/`tests` carry and `docs` does not):

```
f=$(git ls-files <dir> | wc -l)
b=$(git ls-files -z <dir> | xargs -0 stat -c%s | paste -sd+ | bc)
l=$(git ls-files -z <dir> | xargs -0 cat | wc -l)
```

Denominator, unchanged by this pass: `src`+`tests` = 66 files / 1,279,950 B /
31,439 lines.

Measured with the whole branch staged, **this report included**, so the AFTER
rows are what a reader of the merged commit will re-derive:

| population | files | ratio | bytes | ratio | lines | ratio |
|---|---:|---:|---:|---:|---:|---:|
| docs, BEFORE (`60c3359`) | 436 | 6.61x | 7,387,632 | 5.77x | 133,554 | 4.25x |
| docs, AFTER (total) | 438 | 6.64x | 7,404,044 | 5.78x | 133,892 | 4.26x |
| docs, AFTER minus `docs/archive` | 408 | 6.18x | 6,955,325 | 5.43x | 125,331 | 3.99x |
| `docs/archive` alone | 30 | - | 448,719 | - | 8,561 | - |

**The total ratio went UP, 5.77x -> 5.78x**, and that is the honest number: the
pass added `docs/archive/README.md`, this file, and the register reason in §4 -
2 files and 16,412 bytes of new prose against a move that relocates bytes
without removing any. A retirement pass that writes its own account is a net
add to `docs/` by construction. The figure that fell is the LIVE surface,
5.77x -> 5.43x, and only because 448,719 bytes are now behind a prefix a reader
and a template-extraction pass can both skip.

An earlier draft of this table read 437 / 7,389,815 / 5.77x. It was derived
before this file existed and was stale the moment it was saved into the tree it
describes.

**Do not quote the 5.65x from `REPORT-docs-bloat-2026-09-02.md` today.** It was
derived at `99ebf05`; at this branch's base the same commands give 5.77x. The
figure decayed inside one day, which is the behaviour that report itself
predicted.

## 2. What was moved, and the evidence nothing reads it

**Search method, stated so each zero can be judged.** For every tracked
`docs/**/*.md`, I read the full text of all 578 tracked files and asked whether
that file's *basename* or its *full path* appears as a substring anywhere else
in the tree. Substring, not a link parser: a bare mention in a CI comment, a
register row, a shell heredoc or prose all count as a reader. I then repeated
the search with the `.md` suffix stripped, in case a reference drops it - that
second pass returned **zero additional hits for all 33 candidates**, which is
the check that would have caught a reference written `REVIEW-R11` rather than
`REVIEW-R11.md`.

Every path in the candidate list was taken from `git ls-files` output, so no
zero here is the clean-empty a search at a nonexistent path returns.

**What the substring test cannot see** is a reader that builds a path
dynamically or globs a directory. That is handled separately in §3 by
enumerating the parsed populations rather than by searching, because a glob
names no file.

### Retired to `docs/archive/reviews/` (21)

All 21 were in `check-review-coverage.py`'s directory population and all 21
were already **excluded by that checker with a stated reason** before the move
(they are records, not review rounds). Removing them moved exactly one line of
that checker's report - see §4.

```
F2-RULING.md                        MEASURED-294-retier.md
FINDINGS-153-wiring-container.md    MEASURED-probe-median-fit.md
FINDINGS-167-anchor-blind-shapes.md MEASURED-u15-u1boot.md
MEASURED-249-port.md                R1-SUPERSEDED-RULING.md
MEASURED-252-u3-selection.md        TASK-139-xref-classification.md
MEASURED-254-remediation.md         WORKLOG-209-recipe-left-edge.md
MEASURED-277-row-re.md              WORKLOG-212-census-short-by-one.md
MEASURED-290-u4-selection.md        WORKLOG-214-ci-comment-census.md
                                    WORKLOG-221-inherited-interpreter.md
                                    WORKLOG-222-merge-invented-content.md
                                    WORKLOG-223-floor-integrity.md
                                    WORKLOG-224-verdicts-row-and-fallback.md
                                    WORKLOG-232-exit-2-label.md
```

### Retired to `docs/archive/worklogs/` (8)

`docs/worklogs` is already ruled a RECORD path by `check-review-coverage.py`.
No checker globs the directory.

```
AUDIT-SHAPES-sweep-run1-killed.md   WORKLOG-130-assignment-operator.md
SHELL-HYGIENE-REPORT.md             WORKLOG-148-150-checker-integrity.md
U11-IMPL-REPORT.md                  WORKLOG-157-mirror-minutes.md
WORKLOG-116-timeout-names.md        WORKLOG-120-tally-shapes.md
```

## 3. What I refused to move, and why

**40 briefs.** `docs/briefs/*.md` is parsed whole as a population by
`check-brief-report-references.py` (`BRIEFS = ROOT / "docs/briefs"`). 40 of the
83 have zero inbound references and are still not orphans: the checker reads
the directory, not a list.

**4 review-round documents, and this one was measured rather than reasoned.**
`REVIEW-R11.md`, `REVIEW-144-145-R1.md`, `REVIEW-231B-R1.md` and
`REVIEW-218-R2.md` each pass the zero-inbound test. I moved all four, ran
`check-review-coverage.py`, and the report changed substantively:

```
- Review documents in the population: 27      + ... 23
-   DECLARED  REVIEW-144-145-R1.md: e119e75..51723c9
-   DECLARED  REVIEW-231B-R1.md: 7e8adfa..830d299
-   DECLARED  REVIEW-R11.md: f699f74..dad014e   (45 commits)
-   UNDECLARED REVIEW-218-R2.md
- Fully covered: 389   -> 382
- COVERED BY NOTHING: 201 -> 202
- Backlog measured now: 224 -> 231   (ENTERED, unrecorded: 158 -> 165)
```

Three of them DECLARE a reviewed range; retiring them un-covers the commits
those rounds read, which would have demanded 7 new backlog lines - a register
edit that would have recorded work as unreviewed when it was reviewed. **I
reverted all four rather than top up the backlog.** A review round is a member
of a parsed population by the brief's own entry rule, so this is the rule
applying, not an exception to it.

**The remaining 128-minus-73 gap.** `REPORT-docs-bloat` measured 128 of 306
`.md` unlinked *by markdown link from another doc*. My prose-only equivalent is
77 of 312, and the difference is method, not tree drift: my test counts any
substring mention, including a backticked path inside a paragraph, where a link
extractor counts only `](...)`. State whichever you use; they answer different
questions.

## 4. The register I edited, and the one I did not

**Edited: `docs/reviews/check-review-coverage.py`, `RECORD_PATHS`.** Added
`docs/archive` with a reason. This is **forward-looking only**, and the reason
row says so: the checker reads the file list git recorded *at* each commit, so
a path retired today leaves every historical commit reading exactly as before.
Without the row, a future commit touching only the shelf would enter the
backlog as if it were work.

**Measured effect of the whole pass on that checker**, before vs after, full
output diffed:

```
3c3
< Excluded, with a reason: 84
---
> Excluded, with a reason: 63
```

One line. Declared rounds, covered/partial/uncovered counts, the measured
backlog (224) and the unrecorded count (158) are all **byte-identical**.

**Not edited, and each has a reason:**

- `REPOINT-EXEMPT.txt`, `WRONG-SUBJECT-REGISTER.md`,
  `brief-report-refs-known-missing.txt` - none names a moved file. Checked by
  the same substring search; `check-design-citations.py` and
  `check-clause-citations.py` both still exit 0.
- `review-coverage-backlog.txt` - see §3. Its measured set did not move, so
  there was nothing to record. It is *already* red at this base (rc=1, 158
  unrecorded entries) and this branch neither improves nor worsens that.
- The wiring registry in `check-checkers-are-wired.py` - its container is
  `("docs/reviews", "scripts")` filtered to `.py`/`.sh`. **Only `.md` files
  moved**, which is why Members stayed 156 and WIRED stayed 77. Had a single
  script moved, the registry would have shrunk silently.

## 5. Dangling links: 34 targets found, 2 repointed, 32 refused

Scan: markdown `](target)` links plus backticked `docs|scripts|src|tests/...`
paths across all tracked docs `.md`, resolved relative and checked against
`git ls-files` **and** the working tree. **34 distinct missing targets across
50 occurrences** - wider than the report's ~9, because I included targets
outside `docs/`.

**The repair rule I applied:** repoint only where the target EXISTS in the tree
at a different path. Where it never existed or was deleted, the record is true
as written and gets no edit - a dated record is not repointed (ruled `ec57a65`,
task #203).

**Repointed (2):**

| file | was | now |
|---|---|---|
| `docs/worklogs/U11-IMPL-REPORT.md` | `docs/COMPLIANCE-SPEC.md` | `docs/research/COMPLIANCE-SPEC.md` |
| `docs/worklogs/COMMENT-REPAIR-REPORT.md` | `docs/reviews/reflow-doc-lines.py` | `docs/reviews/b49b/reflow-doc-lines.py` |

**Refused, with the class:**

- **The brief's two headline examples are both wrong, and I read them before
  editing.**
  - `COMPLIANCE-SPEC`: the two remaining occurrences are at
    `docs/worklogs/U1-IMPL-REPORT.md:42` and `:415`, and both are *the finding
    itself* - ":42 reads "`docs/COMPLIANCE-SPEC.md`. The file is at
    **`docs/research/COMPLIANCE-SPEC.md`**. I read it there." Repointing would
    delete a recorded defect in a brief.
  - `REVIEW-R23.md` **was written.** It exists on branch `review/r23`, and the
    citing line already says so: `MEASURED-252-u3-selection.md:31` reads
    "`docs/reviews/REVIEW-R23.md` on `review/r23` at `028d80f`". Verified:
    `git ls-tree -r --name-only 028d80f -- docs/reviews` lists it. My scanner
    called it missing only because it looks at one branch. Correct as written;
    no edit.
- Deliberate placeholders in checker prose (12 occurrences): `REVIEW-X.md`,
  `REVIEW-R99.md`, `X.md`, `file.md`, `y`, `docs/adr/0018-...md` and
  `0034-...md` (ellipses), `vendor/tools/x.py`.
- A brief's wrong assignment quoted as a finding:
  `FINDINGS-161-secret-scan-baseline.md:80` ("§B assigns
  `docs/reviews/check-secrets-baseline.py`. That directory is ...").
- Files that existed and were deleted: `PENDING-DESIGN-CHANGES.md` (3, deleted
  at `b49d7ae`), `docs/research/FASTMCP-SPIKE.md`. True when written.
- One-shot scratch scripts named in dated records: `scripts/r9-plant.sh`,
  `zz-plant-unguarded.sh`, `probe-240-selected-row.sh`,
  `profile-harness-phases.sh`, and two amputation names since renamed.
- Files the plan proposed that were never built: `tests/fixtures/*`,
  `tests/*/conftest.py` (13 occurrences). `docs/plans` is a ruled RECORD
  (`0ec4c85`, task #111) and is not repointed; the `PLAN-REVIEW-R*` rounds
  quoting it are dated records for the same reason.
- Never existed anywhere: `docs/REPO-SETTINGS.md`,
  `docs/worklogs/U5-IMPL-REPORT.md` (`U5-REPORT.md` is what was written),
  `docs/guides/publishing/github-actions.md` (an upstream FastMCP doc path,
  not ours).

## 6. `docs/reviews/__pycache__` was ALREADY ignored

Plan §3.3 asks for it to be added to `.gitignore`. **No edit was needed and
none was made.** `.gitignore:2` is `__pycache__/`, which git applies at any
depth:

```
$ git check-ignore -v docs/reviews/__pycache__/repoint_exempt.cpython-312.pyc
.gitignore:2:__pycache__/  docs/reviews/__pycache__/repoint_exempt.cpython-312.pyc
```

The 265 KB is untracked-and-ignored, and was already excluded from every
tracked-byte figure in §1 and in the forensics report.

## 7. Standalone vs stranded

Of 312 tracked docs `.md` at the end of this pass:

| class | count | what it means |
|---|---:|---|
| referenced somewhere in the tracked tree | 239 | a reader exists |
| unreferenced but a checker PARSES its directory | 44 | 40 briefs + 4 review rounds. Intentionally standalone. |
| unreferenced, retired to `docs/archive` | 29 | this pass |
| **unreferenced, unparsed, still live** | **0** | stranded |

Also measured: **4 files have no inbound *doc* link but are named by code, CI
or a register.** They are the reason a docs-only link graph is the wrong
instrument for this question - it would have called all four orphans.

## 8. Gate, run on this tree

All exit codes read directly, not from a `tail`:

```
check-checkers-are-wired         rc=0   Members: 156  WIRED: 77  UNWIRED: 79
check-checkers-are-wired --self-test    rc=0
check-cross-references           rc=0
check-brief-report-references    rc=0
check-design-citations           rc=0
check-clause-citations           rc=0
check-adr-numbers                rc=0
check-row-floor-exactness        rc=0
check-design-citation-shape      rc=0
check-design-freeze              rc=0
check-obligations                rc=0
check-committed-file-types       rc=0
ruff check .                     rc=0   All checks passed
ruff format --check .            rc=0   149 files already formatted
pytest -q                        889 passed, 0 skipped, 6 deselected, 53.88s
```

Members 156 and WIRED 77 are unmoved from the base, which is the assertion that
the registry was not touched.

## Not settled

- `check-review-coverage.py` exits 1 at this base and still exits 1 here, on a
  backlog that is 158 entries behind. That is pre-existing and out of scope,
  but it means this gate cannot currently detect a *new* uncovered commit
  among the noise - including this branch's own commit.
- I did not execute the 79 `UNWIRED_BY_DECISION` scripts to confirm none reads
  a retired path at runtime. The substring search covers their source text,
  which is the mitigation, not a proof.
- The 40 unreferenced briefs are refused on the population rule, not read. Some
  may be genuinely spent; deciding that means reading them, which is a
  different pass.
