# B49b sweep report

**Agent:** `b49b-sweep`. **Branch:** `chore/b49b-line-length`. **Base:** `025aa55`.
**Worktree:** `/tmp/b49b-work`, removed at the end of this report - see the last section.
**Delivery:** one commit carrying the rule and the sweep together. I did not push.

## The obligation, quoted at its source

`evolv-coder-standards/standards/backend/python.md:36`, verbatim:

```
- For comments and docstrings: **72 characters**
```

The document's frontmatter is `priority: required`, `version: 1.5.4`,
`last_updated: 2026-06-14`. The code half is `python.md:35`
(`- Maximum line length: **88 characters** (`ruff format` default)`), which
`line-length = 88` has met since U0.

## The counts, measured rather than inherited

**1608, not 1343.** Measured at `025aa55` before touching anything:

```
$ uv run --frozen ruff check . --select W505 \
      --config 'lint.pycodestyle.max-doc-length = 72'
Found 1608 errors.
```

across **34 files**. Your figure of 1343 is 265 low; the merge that landed
between your count and mine accounts for the gap. The decision doc's 367 is
now 4.4x out of date, which is the decision doc's own point rather than a
criticism of it.

Final: **0**. `uv run --frozen ruff check .` (no `--select`, no `--config` -
the manifest alone) exits 0.

## `docs/DESIGN.md`: zero violations, no exemption, not edited

**W505 fired zero times inside `DESIGN.md`, for two independent reasons**, and
I checked both rather than either:

1. **W505 is a Python rule.** It reads Python comments and docstrings through
   ruff's tokenizer. `DESIGN.md` is markdown; ruff does not lint markdown, so
   it is not a candidate at all.
2. **`docs/` is excluded anyway.** `pyproject.toml`'s
   `extend-exclude = ["docs"]` keeps ruff out of the whole directory, so even
   the `.py` gate harnesses under `docs/reviews/` are out of scope. (For the
   record: run explicitly at that path, those harnesses hold 474 W505 lines.
   They are excluded by a deliberate, commented decision that predates me and
   I did not touch them.)

`DESIGN.md` is byte-identical to both `025aa55` and the frozen `c15b138`:

```
$ python3 docs/reviews/check-design-citations.py --since c15b138
DESIGN.md is byte-identical to c15b138. No citation can have moved.
```

**The trap in the brief was aimed at a risk that does not exist in this task.**
The 841-citation hazard is a hazard of *inserting lines into DESIGN.md*. This
sweep reflows *citing* files, which cannot move a cited line. What it *could*
have done is mangle a citation while rewrapping the sentence around it, and
that is the check I ran instead - see below.

## Exemption list: **empty**

No `noqa: W505` anywhere, no `per-file-ignores` entry for it. Grep over
`*.py`, `*.toml`, `*.cfg`, `*.yml` returns only the `pyproject.toml` select
entry and `docs/reviews/classify-w505.py`'s own prose.

**On the 81 "unbreakable" lines.** Your reading was right in substance and
slightly stale in number. There are now **92**, and **91 of them are dividers**
(`# ---...` and `# ===...`), every one exactly 77 characters, every one
shortened to 72 in one pass:

```
comment-divider lengths, base -> now
  base:  91 lines at 77
  now:   91 lines at 72   (plus 17 pre-existing shorter dividers, untouched)
```

**The 92nd is not a divider**, and it is the one your claim would have missed:

```
tests/test_manifest.py:51 (at 025aa55)
    `test_fastmcp_and_fastmcp_slim_are_pinned_at_the_same_version` - a name describing
```

The classifier's "unbreakable token" branch fires on it because the backticked
test name is 62 characters. It is not unbreakable: on its own line under a
4-space indent it is 66 characters and fits. No exemption needed. **So the
label was again not to be trusted, in the same way and for a different line.**

## What changed, and how

`docs/reviews/b49b/` carries the three scripts and the 149-row data file that
produced this diff, with a README giving the order. I ran them against a fresh
worktree at `025aa55` and diffed the result against the branch:

```
src IDENTICAL
tests IDENTICAL
scripts IDENTICAL
```

so the sweep is reproducible from the tree rather than from this prose.

1. **`reflow-doc-lines.py`** rewraps comment runs and docstring bodies. It
   preserves fenced blocks, tables, bullets (with a hanging indent),
   `Args:`/`Returns:`/`Raises:` items, deeper-indented listings, and dividers
   (shortened, never rewrapped). `ast.parse` guards every write. **1608 -> 179.**
2. **`split-long-summaries.py`**: a too-long summary cannot be wrapped, because
   `D205` requires the summary to be one line. Where the summary held more than
   one sentence, the later sentences moved into the body - nothing deleted.
   **179 -> 149.**
3. **`apply-short-summaries.py`** applies 149 hand-authored summaries. Each is
   a shortening; where shortening would have dropped a distinct claim, the
   claim moved into the docstring body as its own sentence.

**No violation was solved by deleting a sentence.**

## Three defects I hit while doing this, with fixes

### F-1 (fixed here): the `FIELD` regex ate ordinary prose

My first `Args:`-section detector was `^\s*[A-Z][A-Za-z ]*:\s*$`. That matches
`# The regression that the two shipped gates refused each other on:` - a
perfectly ordinary comment line ending in a colon - so the reflow skipped it
as "structure" and left it at 73 characters. **Fix applied:** the pattern now
names the Google section keywords explicitly. Worth carrying: a *shape* test
for structure will silently classify prose as structure.

### F-2 (fixed here): rewrapping split 24 inline code spans

The first pass ran clean on every gate and still degraded the artifact:
`` `... | INFO | __main__:<module>:2 - tool_invocation` `` was wrapped across a
line break, leaving an opening backtick on one line and its close on the next.
**Lines with an odd backtick count went from 4 at base to 28.** No gate saw
this - not ruff, not mypy, not the suite, not any of the four checkers.
**Fix applied:** short `` `code spans` `` are made unbreakable before wrapping.
The final tree has **0** such lines, which is 4 better than base.

### F-3 (fixed here, and it is a live gate defect): `check-obligations.py` cannot see `B49b`

`docs/reviews/check-obligations.py`'s row pattern was:

```python
ROW = re.compile(r"\|\s*(B\d+)\s*\|")
```

`B\d+` does not match `B49b`. **A `B49b` row in `OBLIGATIONS.md` would have
been skipped in silence and the checker would still have exited 0** - a row
that looks tracked and is never verified, which is the exact failure this file
exists to prevent. Amputation control, run both ways:

```
with r"(B\d+[a-z]?)":  Mappings: 29 | anchors verified: 22 | absent: 7   exit 0
with r"(B\d+)":        Mappings: 28 | anchors verified: 21 | absent: 7   exit 0
```

**Fix applied:** the pattern is `r"\|\s*(B\d+[a-z]?)\s*\|"`, with a comment
naming why. `--controls` still reports `9/9 controls fired`.

**This is a change to a gate script and you should look at it.** I made it
rather than filing it because without it my own delivery would have been a
silent no-op row. Suggested follow-up if you would rather it were narrower:
add a control to that script asserting a suffixed B-number is parsed, so the
next person cannot regress it.

## `OBLIGATIONS.md`

`B49`'s note rewritten in place (not appended); a `B49b` row added. Every
anchor that moved was repointed **by parsing the checker's own FAIL lines**,
never by retyping a number - the script that did it is `/tmp` scratch, and it
refuses to run if it parses zero FAIL lines. Five anchors moved:

```
B49b: `pyproject.toml:1` -> `pyproject.toml:222`
B50:  `pyproject.toml:214` -> `pyproject.toml:225`
B51:  `pyproject.toml:207` -> `pyproject.toml:210`
B52:  `pyproject.toml:201` -> `pyproject.toml:204`
B58:  `tests/test_collection_guard.py:173` -> `tests/test_collection_guard.py:189`
```

The `B49b` row anchors on `max-doc-length = 72`, **not** on the `W505` select
entry, because `W505` is inert without the setting: deleting the setting must
be what breaks the row.

## The rule, and the positive control that it fires

`pyproject.toml`: `max-doc-length = 72` under a new
`[tool.ruff.lint.pycodestyle]`, plus an explicit `"W505"` in `select` with a
comment saying it is inert without the setting. `line-length = 88` unchanged.

**A zero this clean needs a control.** Appending one 88-character comment line
to a swept file, then running the *bare* gate with no `--select` and no
`--config`, so the manifest alone is under test:

```
$ uv run --frozen ruff check . --output-format concise
src/fast_mcp_jobvite/utils/correlation.py:60:73: W505 Doc line too long (88 > 72)
Found 1 error.
EXIT nonzero (control fired)
```

Restored and verified byte-identical with `cmp` before continuing. The same
control run against an over-long *docstring* line also fired. So the zero is a
swept tree, not a disabled rule.

## Citations survived the rewrap

Every `*.md:N` citation in `src/`, `tests/` and `scripts/`, base vs now:

```
$ diff <(base) <(now)
116a117
>       1 DESIGN.md:701-705
```

**One addition, no loss and no contraction.** `tests/test_audit.py` carried
`(DESIGN.md:715-717, :701-705)`; the shorthand `:701-705` did not resolve to a
citation for any tool that looks for `DESIGN.md:N`. I expanded it to the full
form while shortening that summary. That is a contracted citation repaired,
which is the failure mode the citation checker's own NOTE warns it cannot see.

## Every gate, by exit code

```
uv run --frozen ruff check .                                EXIT=0  All checks passed!
uv run --frozen ruff format --check .                       EXIT=0  44 files already formatted
uv run --frozen mypy                                        EXIT=0  Success: no issues found in 32 source files
uv run --frozen pytest -q                                   EXIT=0  322 passed, 2 deselected in 21.67s
python3 scripts/check-committed-file-types.py               EXIT=0  42 file(s) checked, none refused.
python3 docs/reviews/check-obligations.py                   EXIT=0  Mappings: 29 | anchors verified: 22 | absent: 7
python3 docs/reviews/check-obligations.py --controls        EXIT=0  9/9 controls fired.
python3 docs/reviews/check-design-citations.py              EXIT=0  885 citations across 89 files
python3 docs/reviews/check-design-citations.py --since 025aa55  EXIT=0  byte-identical
python3 docs/reviews/check-cross-references.py              EXIT=0  0 unresolved in all three documents
python3 docs/reviews/check-plan-measurements.py             EXIT=0  Every plan measurement reproduces.
```

**322 passed, 2 deselected, 0 skipped** - identical to the `0d34c66` baseline
in `PREAMBLE.md`, which I reproduced at `025aa55` before starting.

`docs/reviews/classify-w505.py` now exits **1** against this tree, printing
`POSITIVE CONTROL FAILED: ruff reported no W505 at all.` **That is the script
working**, refusing to report a split it did not measure - but it means it can
never be wired into CI as-is. Suggested fix: give it a `--allow-empty` flag
that prints "0 violations - nothing to classify" and exits 0, so a future
caller does not "fix" the refusal by deleting the control.

## Findings for you, each with a fix

| # | Severity | Finding | Suggested fix |
|---|---|---|---|
| F-3 | **High** | `check-obligations.py` silently skipped any suffixed B-number, exiting 0 | Fixed here (regex widened). Add a control asserting a suffixed id parses |
| F-2 | Medium | Rewrapping split 24 inline code spans; every gate stayed green | Fixed here (spans protected). Nothing gates on this - consider a check for odd-backtick lines |
| F-1 | Low | A "structure" regex classified ordinary prose ending in `:` as a section header | Fixed here (keywords named explicitly) |
| F-4 | Low | 62 `# ----` dividers over 72 characters remain in four `scripts/*.sh` files | Left alone: `python.md` governs Python. If you want shell held to it too, that is a separate obligation and a separate ticket, not a silent extension of B49b |
| F-5 | Nit | `classify-w505.py` cannot run green on a clean tree | Add `--allow-empty` as above |

## What I did NOT verify

- **That every one of the 149 hand-shortened summaries still says what its
  author meant.** I preserved the claim in each and moved a distinct claim into
  the body rather than dropping it, but this is 149 editorial judgements and
  only a reader who knows the code can confirm them. `git diff` on the summary
  lines is the review surface; the shortened text is all in
  `docs/reviews/b49b/short-summaries.json` in one place.
- **That the reflow preserved every markdown nuance beyond code spans.** I
  measured fences (0 in Python files at base and now), tables (0), and inline
  code spans (4 at base, 0 now). I did not enumerate every other markdown
  construct that could survive a rewrap poorly.
- **Whether `docs/reviews/*.py`'s 474 W505 lines should stay excluded.** The
  exclusion is deliberate and commented and predates me; re-deciding it is not
  in this task.

## Worktree

`/tmp/b49b-work` **removed** after the final commit; the verification worktree
`/tmp/b49b-verify` was removed as soon as it had served its purpose.
`git worktree list` was run before every ref move.
