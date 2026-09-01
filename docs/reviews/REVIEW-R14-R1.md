# REVIEW-R14-R1 - an adversarial round on R14 itself

<!-- REVIEW-COVERS: 76bc497..6d8ad94 PATHS: docs/reviews/check-settings-are-read.py docs/reviews/probe-r14-manifest-marker.py docs/reviews/REVIEW-R14.md server.json pyproject.toml -->

Fresh reviewer, both lenses, one pass. I wrote none of this. Every number
below was re-measured; where my brief gave me a figure I say what I
actually got.

## Corrections to the brief I was given

| Brief claimed | Measured | Verdict |
|---|---|---|
| six commits on the branch | **five** (`git log --oneline main..review/r14-config \| wc -l` = 5) | WRONG |
| 4/4 probe arms pass | 4/4, exit 0 | CONFIRMED |
| `check-review-coverage.py` PARTIAL 7 -> 0 | `PARTIALLY covered ...: 0` | CONFIRMED |
| NONE is 15 | **NONE is 102** | WRONG - see M2 |
| 115 bare `DESIGN.md` continuations, exactly 1 live | could not reproduce 115; the live half holds, the "114 in records" half does not | UNSETTLED + WRONG - see M3, M4 |
| suite 887 passed / 0 skipped | `887 passed, 6 deselected in 55.24s` | CONFIRMED |
| M1 repoint `:1497-1506` is the fenced toml block | it is exactly that block | CONFIRMED - see "verified correct" |

**NONE is 102, not 15, and 15 is the instrument talking.**
`docs/reviews/check-review-coverage.py:298` reads `for sha in
untouched[:15]:`. The list is capped at fifteen rows for display; the
population is printed one line above it as `COVERED BY NOTHING: 102`.
Fifteen is how many the checker *prints*, not how many exist. Counting
the rows it chose to show is reading the instrument's behaviour as the
object's.

---

## R14-R1-H1 (High) - the JSON branch is an amputation SURVIVOR, and the argument that justifies it is false

`docs/reviews/check-settings-are-read.py:150-151`, `:156-189`
`docs/reviews/probe-r14-manifest-marker.py:17-24`
`docs/reviews/REVIEW-R14.md` ("Widening the tuple alone...")

The round's central claim, stated three times - in the checker's
comment, in the probe's docstring, and in the review document - is:

> Adding `server.json` to the list and nothing else would have produced
> a third artefact that reports a clean zero **whatever the manifest
> said**.

**That is false against the manifest this very round wrote.**

`server.json:108` reads:

    "description": "JOBVITE_OUTBOUND_RATE_LIMIT IS NOT YET IMPLEMENTED (ADR-0025): ..."

The description *begins with the variable name*. So the name and the
marker DO share one line, and the plain text rule matches. The premise
that the same-line rule is "structurally unsatisfiable" in JSON is
untrue for the file as authored - the fix's own wording defeated the
argument for the fix's own machinery.

**Measured, by amputating the fix a different way than the probe does.**
I rebuilt the checker's inputs in an isolated scratch repo
(`/tmp/r14-lab`: `src/`, `README.md`, `.env.example`, `server.json`,
the checker, `git init` + one commit) so nothing touched the review
checkout. Baseline reproduced: exit 0.

Then I deleted the JSON dispatch outright - both lines of

    if path.suffix == ".json":
        return _json_marker_lines(path, variable, marker)

leaving `_json_marker_lines` and `_walk_json` unreachable, 34 lines of
dead code:

    AMPUTATE-B  whole JSON branch deleted        exit 0   SURVIVOR

Nothing failed. Not the checker, not the probe, not the suite. The
probe's AMPUTATE arm only removes the string `"server.json"` from the
tuple; **no arm ever exercises the JSON reader it was built to justify.**

I then asked whether the branch does anything at all, two arms:

    A  line-rule-only + UNMARKED manifest       exit 1, names server.json   CORRECT
    B  line-rule-only + marker present, but the
       description does NOT repeat the variable
       name ("NOT YET IMPLEMENTED (ADR-0025):
       this knob is ...")                       exit 1                      FALSE POSITIVE

So the branch is not worthless - it prevents a false *failure* on a
prose-worded description. But that is the opposite of the harm the
docstring claims it prevents (a false *pass*), and nothing tests it.
The justification is inverted and the mechanism is unguarded.

Worth stating plainly: **all three artefacts carry the name and the
marker on one line today** - `README.md:82`, `.env.example:91`,
`server.json:108` - so the line rule alone would pass all three.

**Suggested fix**, two parts, both needed:

1. **Correct the claim in place** (do not append) at all three sites -
   the checker comment `check-settings-are-read.py:96-100`, the probe
   docstring `probe-r14-manifest-marker.py:17-24`, and the
   "Widening the tuple alone..." paragraph in `REVIEW-R14.md`. The true
   statement is narrower: *the line rule happens to work only because
   this description repeats the variable name; JSON is read
   structurally so the check does not depend on that accident.*

2. **Add the arm that makes the branch load-bearing.** Rewrite the
   manifest description so it carries the marker WITHOUT repeating the
   variable name, then assert the two halves disagree - the structural
   reader PASSES and a line-rule-only reader FAILS. That arm kills the
   amputation above; today's four do not. Both halves are already
   measured here, so the arm is a transcription, not a research task.

---

## R14-R1-H2 (High) - `_json_marker_lines` lets one marked entry launder an unmarked one

`docs/reviews/check-settings-are-read.py:166-174`

    entries = [
        node
        for node in _walk_json(json.loads(text))
        if isinstance(node, dict) and node.get("name") == variable
    ]
    ...
    if not any(marker in str(entry.get("description", "")) for entry in entries):

Two independent problems in four lines:

- `_walk_json` walks **the entire document**. Any dict anywhere with
  `name == variable` qualifies - it is not scoped to
  `packages[*].environmentVariables`.
- `any(...)` means **one** marked entry satisfies the check no matter
  what the others say.

**Measured, both cases, in the scratch repo:**

    duplicate JOBVITE_OUTBOUND_RATE_LIMIT entry, one marked
    and one not, both inside environmentVariables        exit 0

    real entry stripped of its marker, a marked look-alike
    {"name": ..., "description": "NOT YET IMPLEMENTED"}
    planted OUTSIDE environmentVariables                 exit 0

In both runs the published manifest tells a registry consumer the knob
works, and the gate that exists to prevent exactly that prints
`Unimplemented-marker artefacts checked: 3` and exits 0. This is the
R14-H1 defect surviving inside R14-H1's own fix.

The `description` cases the brief asked about are sound by comparison:
a missing `description` yields `""` and correctly reports MISSING; a
marker in a *differently named* entry is correctly excluded by the
`name ==` filter. The hole is duplicates and scope, not absence.

**Suggested fix** - scope the lookup and require every match, replacing
`_walk_json` (which then has no other caller and should be deleted):

```python
def _json_marker_lines(path, variable, marker):
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = [
        var
        for package in data.get("packages", [])
        for var in package.get("environmentVariables", [])
        if var.get("name") == variable
    ]
    if not entries:
        raise SystemExit(
            f"{path.name} declares no {variable} entry, so this cannot match"
        )
    if len(entries) > 1:
        raise SystemExit(
            f"{path.name} declares {variable} {len(entries)} times - a consumer "
            "reads one of them and this check cannot say which"
        )
    if marker not in str(entries[0].get("description", "")):
        return []
    ...
```

`all` rather than `any` would also close it, but refusing the duplicate
is the better answer: two entries with one name is a manifest defect in
its own right, and `check-committed-file-types.py` already establishes
that this repo refuses ambiguity rather than picking a winner.

Add both planted cases to the probe as arms - they are the positive
controls this function has none of.

---

## R14-R1-M1 (Medium) - a SIGKILL during the probe leaves CI GREEN on the exact defect

`docs/reviews/probe-r14-manifest-marker.py:100-151`

The restore is a `finally`. `SIGKILL` runs no `finally` - the project
has already recorded this once (task #100, #131). I did **not** test
this by killing anything; the state below is read off the source.

The dangerous window is `:120` to `:130`, between

    substitute(CHECKER, WIDE, NARROW)     # :120
    substitute(CHECKER, NARROW, WIDE)     # :130

At any point inside it the tree holds **both** halves of the original
defect at once:

- `server.json` with the marker stripped (from the POSITIVE arm at
  `:107`, never yet restored), and
- `check-settings-are-read.py` back on the two-artefact `NARROW` tuple.

That is precisely the pre-R14-H1 state, and `check-settings-are-read.py`
**exits 0 on it** - I measured that combination as the probe's own
AMPUTATE arm, which is the arm asserting exit 0. So a SIGKILL here does
not leave a loud broken tree; it leaves a quiet green one whose
published manifest lies. Both files are tracked, so
`git status` shows them - but no gate does.

The probe's own `tree_is_clean()` guard at `:93` catches this on the
NEXT probe run and returns 2 with a clear message. That is real
protection and worth crediting. It just is not the gate anybody runs
first.

**Suggested fix**, cheapest first:

- **Do not mutate the live checker at all.** The AMPUTATE arm needs a
  two-artefact checker, not *this* checker on disk. Copy it to a
  `tempfile.TemporaryDirectory()`, apply `NARROW` to the copy, and run
  the copy. `ROOT` is `Path(__file__).resolve().parent.parent.parent`,
  so a copy placed at `<tmp>/docs/reviews/` with symlinks (or copies) of
  `src`, `README.md`, `.env.example`, `server.json` resolves correctly -
  I did exactly this to produce H1 and H2, so it is known to work. That
  removes the checker from the abnormal-exit blast radius entirely and
  halves the window.
- **Write a sentinel before the first mutation** (e.g.
  `docs/reviews/.probe-r14-running`, gitignored), delete it in the
  `finally`, and have the probe refuse on a sentinel found at startup
  with instructions to `git checkout --` both paths. Unlike
  `tree_is_clean()` this survives the case where a later commit makes
  the mutated state look clean.
- **Say it in the docstring.** The file currently promises "Every arm
  mutates the working tree and restores it" with no abnormal-exit
  caveat. Add one sentence naming the window and the two files, so the
  next reader is not the one who discovers it. This is task #131's
  `--restore-only` class; cross-reference it.

---

## R14-R1-M2 (Medium) - the round reports a capped display as a population

`docs/reviews/REVIEW-R14.md`, Gates section and the "Why these files" table

Covered in the corrections table above; recorded as a finding because
it is a repeatable class, not a typo. `check-review-coverage.py` prints
`untouched[:15]` (`:298`) and `partial[:10]` (`:300`). Any future round
that counts printed rows will make the same mistake, and the two caps
differ, so the error is not even consistent.

**Suggested fix:** in `check-review-coverage.py`, make the caps
self-describing - print
`f"  ... and {len(untouched) - 15} more not listed"` when the list is
truncated. A display that says it is truncated cannot be miscounted.
Costs one line and removes the class.

---

## R14-R1-M3 (Medium) - the 115 is not reproducible from the document

`docs/reviews/REVIEW-R14.md`, "Scope, measured rather than assumed"

The round states "115 bare continuations of a `DESIGN.md` citation
exist across all tracked files" and "All 115 are in bounds", but records
no command. I tried five definitions over `git ls-files` and got
**0, 64, 77, 910 and 957**. None is 115. I am not claiming the figure is
wrong - I am claiming that neither I nor anyone else can check it, which
for a number carrying a scope argument is the same problem.

This is the prose-instead-of-probe shape: a measurement written down as
a sentence decays into a claim about one.

**Suggested fix:** paste the exact command and its output into the
document, the way the Gates section already does for exit codes. If the
scan is worth repeating, it belongs in `docs/reviews/` as a script
beside the other citation checkers, not in prose.

---

## R14-R1-M4 (Medium) - "114 sit in records" is wrong; at least five sit in live code

`docs/reviews/REVIEW-R14.md`, same paragraph

The claim is that of the 115, "114 sit in records - worklogs, reviews,
plans" and "Exactly one was in live config". Excluding
`docs/{worklogs,reviews,plans,briefs}/`, bare continuations on lines
that also name `DESIGN.md` appear at:

    pyproject.toml:10                                   (the M1 site)
    src/fast_mcp_jobvite/config.py:389                   :806-812
    src/fast_mcp_jobvite/services/jobvite_client.py:607  :373-375
    src/fast_mcp_jobvite/services/jobvite_client.py:1194 :618-620
    tests/test_config.py:211                             :778-782
    tests/test_resilience.py:1                           :373-375, :601-620
    docs/adr/0017-...:67, docs/adr/0028-...:61, :105

The "exactly one in **live config**" half survives - `pyproject.toml:10`
is the only one in a config file. The "**114 sit in records**" half does
not: `src/`, `tests/` and `docs/adr/` are none of them records, and the
`a1773e8` records-vs-load-bearing ruling that the sentence leans on does
not exempt them. Those sites are R11's declared paths, so they are
another round's to sweep - but the sentence as written tells the next
reader the class is closed outside one config file, and it is not.

**Suggested fix:** rewrite the sentence in place (not a rider) to
"**N sit in records; the remainder are in `src/`, `tests/` and
`docs/adr/`, which fall in R11's declared paths and are recorded here
rather than swept**", with N re-derived by the command M3 asks for. File
a task for the src/tests sites so the hand-off is on the board rather
than in a paragraph.

---

## R14-R1-N1 (nit) - `tree_is_clean()` is blind to a staged change

`docs/reviews/probe-r14-manifest-marker.py:82-88`

    ["git", "-C", str(ROOT), "diff", "--quiet", "--", str(MANIFEST), str(CHECKER)]

`git diff` without a commit compares the worktree to the **index**.
Measured in the scratch repo:

    modified + `git add`  ->  git diff --quiet       exit 0  (reports CLEAN)
    modified + `git add`  ->  git diff --quiet HEAD  exit 1  (reports dirty)

So a *staged* edit to `server.json` slips past the REFUSING guard at
`:93`, and the `finally`'s `git checkout --` then restores from the
index rather than HEAD. Not destructive - the operator's staged content
comes back - but the guard's message says "Commit or stash first" while
having failed to notice the thing it warns about, and the final
`tree_is_clean()` verdict at `:156` inherits the same blind spot.

**Suggested fix:** add `HEAD` to both calls -
`git diff --quiet HEAD -- <paths>`. One word, and it makes the message
true.

---

## R14-R1-N2 (nit) - the VACUITY arm keeps a manual snapshot the `finally` makes redundant

`docs/reviews/probe-r14-manifest-marker.py:135`, `:146`

    body = MANIFEST.read_text(encoding="utf-8")
    ...
    MANIFEST.write_text(body, encoding="utf-8")

`body` is captured *after* the POSITIVE arm already unmarked the
manifest, so the restore returns it to the unmarked state and the
`finally` does the real work. It is correct today and reads as if it
were the restore, which is the kind of line a later editor trusts.

**Suggested fix:** delete both lines; the arm is the last one and the
`finally` at `:147` restores unconditionally. If the snapshot is kept
for a future arm, name it `unmarked_body` so it cannot be read as the
committed content.

---

## What I verified and found CORRECT

Stated because a round reporting only findings makes the rest invisible.

- **The M1 repoint is right, and neither too wide nor too narrow.** Read
  from `git show "$(cat docs/DESIGN-FREEZE.txt)":docs/DESIGN.md` (freeze
  `5d17cd7`, derived not retyped), numbered: `1497` is the opening
  ```` ```toml ````, `1506` is the closing ```` ``` ````, with
  `dependencies = [` at `1498`, the three pins at `1499-1501`,
  `[tool.uv]` at `1504` and `prerelease = "explicit"` at `1505`. The
  range is the fenced block exactly. The inner `:1499-1501` still names
  the three pins correctly.
- **The REVIEW-COVERS declaration is honest.** All six declared paths
  (`pyproject.toml`, `.env.example`, `.pre-commit-config.yaml`,
  `server.json`, `README.md`, `docs/briefs`) are touched in
  `f699f74..dad014e`, and each gets substantive discussion, not a
  mention. I spot-checked two of the "found nothing wrong" claims
  against the diff and both hold: `.pre-commit-config.yaml`'s change
  over the range really is five citation repoints and nothing else, and
  `README.md`'s really is the per-second -> per-**minute** correction
  plus the new budget row. No manufactured coverage found.
- **The four probe arms do pass, and the AMPUTATE arm is not vacuous on
  its own terms.** It lands its mutation (the `substitute` helper
  asserts a unique anchor before writing, which is the right shape), the
  old tuple really does go green on a lying manifest, and I read WHICH
  arm reported what rather than scoring the exit code.
- **The tree really is restored** on a normal run: `tree_is_clean()`
  after the probe, and `git status --short` over the checkout,
  both clean.
- **`_json_marker_lines` handles the absent-entry and missing-description
  cases correctly** - it raises rather than returning a clean zero, which
  is the failure mode the file exists to avoid.
- **The suite and every gate.** Exit codes below.

## Gates - each on its own line, exit code as measured

    check-settings-are-read        0
    check-env-vars-are-declared    0
    check-design-citations         0
    check-design-citation-shape    0
    check-checkers-are-wired       0
    probe-142-exempt-controls      0
    probe-r14-manifest-marker      0   (4/4 arms, tree restored)
    check-committed-file-types     0
    ruff check .                   0
    ruff format --check .          0
    mypy .                         0
    check-review-coverage          1   (PARTIAL 0, NONE 102 - expected red, task #119)
    uv run --frozen pytest         0   887 passed, 0 skipped, 6 deselected, 55.24s

Suite floor derived from `ci.yml`, not retyped:
`grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1`
-> `check-suite-floor.sh 887`. The suite is AT the floor with no slack.

## What I could NOT settle

For what I could not settle, not what I did not try.

- **The 115.** Five definitions, five different numbers, none 115. I
  cannot reproduce the author's population without the author's command
  (M3). I did settle the half that carries the argument - the live-config
  count is 1 - and refuted the other half (M4).
- **Whether the 102 uncovered commits are a real gap or the checker's
  scope.** Out of my range and tracked as task #119; I confirmed the
  number and stopped.
- **Whether a fourth operator-facing artefact exists.** I verified R14's
  own unsettled claim is accurate as far as it goes - the three artefacts
  in `UNIMPLEMENTED_MARKER` are the three named in
  `check-env-vars-are-declared.py:18` - but nothing enumerates that set
  from a container, so neither of us can prove there is no fourth. R14
  was right to leave this open and right about why.
- **The abnormal-exit behaviour under an actual SIGKILL.** Read off the
  source, deliberately not executed: the brief forbade it and killing a
  process mid-mutation on the shared checkout is the destructive test
  this project does not run. M1 states the resulting state and its
  reasoning; it is not an observation.
