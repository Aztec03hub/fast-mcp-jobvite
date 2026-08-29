# COMMENT-REPAIR - the flowed-colon damage, repaired

Agent `comment-repair`, task #30. Base `555bad6`, branch `fix/comment-repair`,
11 commits, `555bad6..0166b71`. Worktree `/tmp/comment-work`, removed at the end
of this report.

## The count, before and after

The brief's grep, run at `555bad6` in my worktree:

```
$ grep -rn "^\s*# : " --include="*.py" src/ tests/ scripts/ | wc -l
55
$ grep -rn "^\s*# : " --include="*.py" src/ tests/ scripts/ docs/ | wc -l
55
```

**55, not 44.** The brief's 44 was measured at `59f0a8b`; `555bad6` carries
eleven more. Including `docs/` changes the number not at all, but the brief was
right to ask: `find docs -name '*.py'` returns **14 files**, all under
`docs/reviews/` (the checkers, plus the three `b49b/` scripts including
`reflow-doc-lines.py` itself). I checked all 14 and none carries the damage -
`grep -rnE "^\s*#.*( : | :\$)" docs/` is empty. So the exclusion was real
coverage that happened to find nothing, not a directory that could not have
been affected.

That grep also **undercounts the damage by a factor of about four**, because it
only sees the FIRST line of a run. The continuation lines lost their `#` too, so
they read as ordinary `# ` comments with a colon somewhere in the middle. The
measure that sees those:

```
$ grep -rnE "^\s*#.*( : | :$)" --include="*.py" src/ tests/ scripts/ docs/ | wc -l
195
```

After:

```
$ grep -rn "^\s*# : "                  --include="*.py" src/ tests/ scripts/ docs/ | wc -l
0
$ grep -rnE "^\s*#.*( : | :$)"         --include="*.py" src/ tests/ scripts/ docs/ | wc -l
0
$ grep -rn "^\s*#: "                   --include="*.py" src/ tests/ scripts/ docs/ | wc -l
321        # was 81
```

81 -> 321 is the repair itself: every continuation line in a damaged run gets
its marker back, and there were 240 of them.

## What the damage actually is

`#:` is Sphinx's attribute-doc prefix. A reflow stripped the `#` from the marker
and left the `:` as a word in the body, wherever the rewrap put it. Three shapes,
all of them present here:

1. **An N-line run carries exactly N stray colons.** This held on every one of
   the 45 runs I repaired, and it is what made the work checkable: count the
   lines, count the colons, and if they disagree you have misread something.

2. **A paragraph break renders as `: :`.** A bare `#:` continuation line
   contributes its marker, and so does the line after it, so the two colons
   arrive adjacent with the blank line gone. **17 of these**, counted from git
   objects rather than a working tree: `git grep -o " : : " 555bad6 -- '*.py' |
   wc -l` gives 17. They are the reason a prefix-only fix produces text that is
   not merely mis-marked but *wrong* - two paragraphs run together
   mid-sentence, and I reverted exactly that experiment before starting.

3. **A section divider absorbs the marker.** In `config.py` the single-line
   `# --- Limits ------` divider was wrapped by the sweep and the following
   line's marker landed on its end: `------------ :`. That colon belongs to no
   sentence at all.

## Per file

| File | Runs | Lines | Recovered from history | Rewritten by me |
|---|---:|---:|---|---:|
| `tests/test_workflow_contexts.py` | 1 | 2 | 0 (see below) | 0 |
| `tests/test_redaction.py` | 1 | 3 | 3, `4637b9f` | 0 |
| `scripts/probe-exception-redaction.py` | 1 | 3 | 3, `0d04a19` | 0 |
| `tests/test_readme.py` | 1 | 4 | 4, `370ac32` | 0 |
| `src/fast_mcp_jobvite/services/jobvite_client.py` | 4 | 11 | 11, `dd3e82c` | 0 |
| `tests/boot_process.py` | 2 | 14 | 6, `c15b138`; 8 prefix-only | 0 |
| `src/fast_mcp_jobvite/errors.py` | 2 | 14 | 14, `e87a859` | 0 |
| `tests/test_suite_floor.py` | 2 | 19 | 19, `79417d9` | 0 |
| `src/fast_mcp_jobvite/config.py` | 6 | 17 | 17, `c15b138` | 0 |
| `src/fast_mcp_jobvite/__main__.py` | 3 | 27 | 27, `dd3e82c` | 0 |
| `src/fast_mcp_jobvite/utils/redaction.py` | 6 | 29 | 29, `4637b9f` | 0 |
| `src/fast_mcp_jobvite/audit.py` | 10 | 31 | 31, `3cd1ff1` | 0 |
| `tests/test_logging_process.py` | 6 | 39 | 39, `dd3e82c` | 0 |
| **Total** | **45** | **213** | **203 recovered / 8 prefix-only / 2 inferred** | **0** |

**Nothing on this branch was rewritten by me.** I set out expecting to have to
compose replacement sentences and did not have to once. Every damaged run except
two had a clean ancestor in git, and in each case the damaged text is the clean
text with N colons inserted - the words are the author's, verbatim.

The two that are not verbatim recoveries, named explicitly because the brief
asks for them by name:

- **`tests/test_workflow_contexts.py:42-43`** was BORN damaged at `647442f`.
  There is no clean ancestor. The run is two lines with two colons
  (`# : Contexts...` and `deliberately : absent`), removing them yields a
  grammatical English sentence, and no other reading of those tokens is
  available. I did not invent words, but I cannot cite a commit for it. **If you
  want one site re-read by a second pair of eyes, this is the one.**

- **`tests/boot_process.py:29-36`** (the R3-M2 pid note) was likewise written by
  hand at `647442f` already carrying `# : ` on every line - the author copied the
  style of the broken neighbour above it. There are no mid-line colons in it at
  all, so the prose was never damaged and the repair is the prefix alone. Eight
  lines, zero words changed. Distinguishing it from real damage is why the
  "prefix-only" column exists.

## The two traps, and what happened at them

The task said some colons in those lines are real punctuation. Every one I found:

| Kept (real punctuation) | Removed (the marker), same line or the next |
|---|---|
| `Measured before the fix:` | the ` :` two characters later |
| `` `noqa: E501` `` | ` : : ` immediately before it |
| `An audit failure fails the call: no audit` | the leading `# : ` |
| ``not `time.time`: a clock adjustment`` | ` : ` after `and not` |
| ``W3C `traceparent`: `version-...` `` | the ` : : ` after it |
| `is a log-forging vector: a value carrying` | the ` : ` after `inbound` |
| `` `finally: os._exit(0)` `` | the ` : ` after the closing backtick |
| ``from `sysexits.h`: the serving path`` | the ` : ` in `ADR-0018: :` |
| `handler: `tests/test_boot.py` imports` | the ` : ` after `module` |
| `MEASURED before the ... landed: both` | the ` : : ` before `MEASURED` |
| ``ADR-0017 settled this:`` | the ` : ` before `this` |

`redaction.py` also held a case no colon rule of any kind would have caught:
`a length- : preserving mask`. The hyphen is a real hyphen in
`length-preserving`, split across lines by the pre-sweep wrap, so the repair had
to rejoin a word as well as delete a colon. **Every re-wrap on this branch runs
with `break_on_hyphens=False`** so `length-preserving` and `audit-failure` cannot
be split again.

## Where the damage came from

The brief says the origin was NOT ESTABLISHED and that 38 sites already existed
at `f0c3764~1`, so the sweep was not the whole cause. I traced every file's
`# : ` count across every commit that touched it - `git show <sha>:<path> |
grep -c` at each one, which reads git objects rather than a working tree - and
the transitions settle it. **Four separate mechanisms, not one.**

**1. The b49b sweep, `e4a3fb1`.** Nine files went 0 -> damaged in that single
commit: `jobvite_client.py` (4), `config.py` (5), `audit.py` (10),
`redaction.py` (7), `errors.py` (2), `__main__.py` (4), `boot_process.py` (2),
`test_logging_process.py` (3), `test_redaction.py` (1). Every parent is 0.

**2. A second sweep, `f0c3764`,** over the files added after b49b branched:
`test_suite_floor.py`, `test_readme.py` and `probe-exception-redaction.py`, each
0 -> damaged.

**3. Hand-written imitation.** `tests/test_workflow_contexts.py` was born
damaged at `647442f`, and the second paragraph of `tests/boot_process.py` was
hand-written in the damaged style at the same commit. Nothing reflowed those -
an author copied the broken form off the neighbouring lines. This is the
mechanism the tool fix at `59f0a8b` does not stop, and it is the reason the
repair matters beyond tidiness: until this branch lands the repository holds 240
lines teaching the wrong form by example.

**4. A MERGE RESOLVED IN FAVOUR OF THE DAMAGED SIDE.** This is the one I did not
expect and the one worth your attention. `dd3e82c` fixed `jobvite_client.py`,
`__main__.py` and `test_logging_process.py` on a branch whose copies were CLEAN
- all three go damaged -> 0 there. Then:

```
e26c199  0 -> 4   merge(main): resolve b49b's reflow against M-5, and lan...
```

The merge took b49b's side of the conflict and put the damage back into files a
commit had already cleaned. `test_logging_process.py` is the sharpest case: 3 at
`e4a3fb1`, 0 at `dd3e82c`, 5 again at `5538c65`, **8 after the merge**. The
count went UP through a resolution, because the merge combined damage from both
parents.

Suggested follow-up, and I have not filed it because it is outside this task:
a conflict resolved by "take the reflow branch's hunk" cannot distinguish a
reflow from a reflow-plus-corruption. If another reflow branch is ever merged,
the count above is the check to run on both sides of the merge base.

## Gates - each judged by its own exit code

Suite floor derived, not retyped:

```
$ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
check-suite-floor.sh 398
```

| Gate | Result | Exit |
|---|---|---|
| `ruff check src/ tests/ scripts/` | `All checks passed!` | 0 |
| `ruff format --check src/ tests/ scripts/` | `47 files already formatted` | 0 |
| `mypy src/` | `Success: no issues found in 17 source files` | 0 |
| `pytest` | `398 passed, 5 deselected in 47.19s` | 0 |
| `docs/reviews/check-obligations.py` | `Mappings: 31 \| anchors verified: 23 \| recorded as absent: 8` | 0 |
| `docs/reviews/check-cross-references.py` | `Every section reference resolves within its own document.` | 0 |
| `docs/reviews/check-design-citations.py` | `Every citation resolves to a line that exists.` | 0 |
| `docs/reviews/check-clause-citations.py` | all rows resolve | 0 |
| `docs/reviews/check-coupling.py` | `PASS: ids unique, STRIDE coverage complete, ...` | 0 |
| `docs/reviews/check-coupling-controls.py` | `34/34 controls fired.` | 0 |

**398 passed equals the floor of 398, and 0 skipped.** The 5 are *deselected*,
not skipped: they carry the `credentialed` marker, which `pyproject.toml:127`'s
`addopts` deselects and which `pyproject.toml:136` documents as deliberately
deselected rather than `skipif`. `scripts/check-suite-floor.sh:38` reads the
last `N passed` in the output, so deselection does not inflate it.

`check-obligations.py` was worth running rather than assuming: this branch
re-wraps comment text, and obligation anchors are subject strings inside it.
Nothing moved out from under an anchor.

## The comment-only check - and the check itself is wrong

The brief's command, run verbatim:

```
$ git diff 555bad6..HEAD -- src/ tests/ | grep -c "^+[^#+]"
22
```

**It is not 0, and all 22 lines are comments.** `^+[^#+]` requires the `#` in
column 1 of the added line, so it treats every INDENTED comment as code. The 22
are the `    #: ` runs inside `audit.py`'s `AuditPhase` enum and `AuditEvent`
dataclass, and inside `config.py`'s `Settings` class. All 22 are printed in full
in the commit for those files.

Indentation-aware, both directions:

```
$ git diff 555bad6..HEAD -- src/ tests/ | grep "^+" | grep -v "^+++" \
    | sed 's/^+[[:space:]]*//' | grep -vc "^#"
0
$ git diff 555bad6..HEAD -- src/ tests/ | grep "^-" | grep -v "^---" \
    | sed 's/^-[[:space:]]*//' | grep -vc "^#"
0
```

**Zero non-comment lines added and zero removed.** The removed-side check is the
one that matters and the brief does not ask for it: the added-side check alone
passes a diff that DELETES a line of code, and a repair pass that accidentally
ate a `REDACTED: Final = ...` line while rewriting the comment above it would
have scored 0.

Suggested fix for the brief: replace the command in `docs/briefs/COMMENT-REPAIR.md`
with the two indentation-aware pipelines above. I have not edited the brief -
it is not my file and `code-review-r4` may be reading it.

## Off limits - checked, no damage found

`scripts/*.sh` and `.github/workflows/` were scanned and **not** touched:

```
$ grep -rnE "^\s*#.*( : | :$)" scripts/*.sh .github/workflows/
(no matches)
```

Also clean: every `*.toml`, `*.cfg`, `*.ini`, `*.yml`, `*.yaml` in the
repository. The damage is confined to Python, which fits the mechanism - only
Python has a `#:` convention for the reflow to break.

I also avoided `tests/test_tools_jobs.py`, `src/fast_mcp_jobvite/models/` and
`src/fast_mcp_jobvite/tools/` as asked. None of them carried damage, so nothing
is owed there.

## Two things I left alone, deliberately

1. **The `# --- Limits ---` divider in `config.py` stays wrapped across two
   lines.** The b49b sweep split it; I removed the marker colon that landed on
   its end but did not rejoin it, because every other divider in that file is
   split the same way and rejoining one is an undeclared cosmetic edit in a
   comment-only branch. Suggested fix if you want it: shorten the dash run so
   the divider fits 72 in one line, as one commit across all the dividers in
   `src/`, not just this one.

2. **Six over-72 comment lines remain in `tests/test_logging_process.py`**
   (96, 98, 99, 111, 112, 113 after my change). They are inside the
   `FAILING_SINK_ENTRY` triple-quoted string, so they are string content and
   W505 does not see them - ruff exits 0. They are byte-identical to `555bad6`,
   where the same six sit at 91, 93, 94, 106, 107, 108 with the same lengths.

## No reflow tool was run

`docs/reviews/reflow-doc-lines.py` was never invoked on any file, before or
after repair. Every re-wrap on this branch is a `textwrap.wrap` in a one-off
script inside the commit that used it, at width 69 (or 68 for the indented
runs), with `break_on_hyphens=False`.

## What I did NOT verify

- **Whether `tests/test_workflow_contexts.py:42-43` says what its author meant.**
  I can prove no clean version ever existed and that my reading is the only
  grammatical one; I cannot prove it is the intended one. That is the single
  site on this branch not anchored to a commit.
- **Whether the recovered comments are still TRUE of the code.** I restored what
  the author wrote; I did not re-derive their claims. Several assert measured
  facts (`MEASURED before the sink-level redaction landed: both credentials came
  back in the clear, twice each`) that were true when written and that this task
  gave me no mandate to re-measure. If any drifted, it drifted before I arrived
  and my branch preserves the drift exactly.
- **Damage in non-`#:` comment forms.** My broad grep is `^\s*#.*( : | :$)`. A
  marker colon that landed somewhere producing neither ` : ` nor a trailing ` :`
  - immediately after a word with no space, say - would not appear in it. The
  N-lines/N-colons identity held on all 45 runs, which is evidence against such
  a case existing here, but it is evidence and not proof.
- **`docs/` prose, `.md` files.** My scope was `.py` per the brief's grep. I did
  not sweep Markdown for a comparable reflow artifact and do not know whether one
  exists.

## Worktree

`/tmp/comment-work` removed with `git worktree remove` after the final commit.
Branch `fix/comment-repair` is at `0166b71` in the shared repository. I have not
pushed and have not merged.
