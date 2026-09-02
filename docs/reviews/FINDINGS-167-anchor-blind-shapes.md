# FINDINGS — #167: the anchor checker's blind shapes, measured before widened

`suborch-167`, 2026-09-01 09:35 PM CDT.
Branch `fix/167-anchor-shapes`, from `origin/main` at `22c9873`. Not pushed,
not merged.

---

## 1. THE CONTAINER, MEASURED FIRST — the number nobody had

The brief's §D said to measure the container before touching the selector,
and to treat that number as the deliverable even if nothing else landed. It
is measured, and **it does not say what #156 and the task expected.**

Measured at `22c9873` by `docs/reviews/probe-167-mutation-site-census.py`,
which parses every `python3 -` heredoc in all 34 harnesses under `scripts/`
with `ast` and classifies every mutation-producing expression by KIND. It
shares no selector with the checker; that is the point.

| kind         | sites, repo-wide | in a heredoc the OLD checker even opened |
|--------------|------------------|------------------------------------------|
| `str.replace`| 32               | 32                                       |
| `re.sub`     | 9                | 9                                        |
| `re.subn`    | 1                | 0                                        |
| slice-splice | 2                | 0                                        |
| **total**    | **44**           | **41**                                   |

**Three sites were hidden, repo-wide, and all three are in one file:**
`scripts/check-u1-boot-amputation.sh` rows H (`re.subn`, :447), K
(slice-splice, :501) and M (slice-splice, :571).

### THE TASK EXPECTED THIS NUMBER TO BE BIGGER. IT IS NOT.

Task #167 says "expect the gap to be larger than three". **It is exactly
three heredocs, and no other harness contributes one.** The other 33
harnesses either anchor through shell helpers (shape A), a `@@` spec table
(shape C), `sed -i` (shape D), or use `.replace`/`re.sub` forms the old
selector already read. That is the honest answer to "how many does it hide
repo-wide", and it is a smaller answer than the task predicted.

### WHY THE COMPLETENESS CHECK COULD NOT SEE IT

`--self-check` prints "call sites seen" beside "anchors parsed" so a
selector that silently skips a site shows up. It could not show this one.
The skip happened at the HEREDOC level, at `check-harness-anchors.py:331`
(`22c9873`):

    if ".replace(" not in body and "re.sub(" not in body:
        continue

A heredoc failing that test was passed over WHOLE — before `seen` could
count anything in it. So a hidden shape contributed zero to both sides of
the comparison and the completeness check came out clean. **This is the
`self-tests share the author blind spot` shape**: the instrument that was
supposed to catch a missing selector was itself gated by the same missing
selector.

The `UNREAD MUTATION MECHANISMS` warning could not see it either: it fires
only for a harness contributing **zero** anchors. `check-u1-boot-amputation.sh`
contributed twelve, so a harness that was 80% covered looked identical to one
that was 100% covered.

---

## 2. A FOURTH HIDDEN ANCHOR THE TASK DID NOT NAME

Widening for the shapes above turned up one more live anchor nobody had
counted: `check-u1-boot-amputation.sh:387`

    opener = "TOOL_REQUIREMENTS: Final[dict[str, tuple[str, ...]]] = {"
    if s.count(opener) != 1:
        ... "AMPUTATION DID NOT LAND" ... sys.exit(1)

Row F guards its `re.sub` with a separate uniqueness assertion on the
table's OPENING LINE, because its regex carries no `count=`. That opener is
a real anchor — if the declaration is reformatted the row aborts — and no
selector read it, because it is attached to a `.count()` rather than to the
substitution. It was invisible for a reason unrelated to `re.subn` or the
splices.

---

## 3. WHAT LANDED

`scripts/check-harness-anchors.py`, four changes:

1. **The heredoc gate is derived from the invocation, not the body's prose.**
   `if "python3" not in head` replaces the `.replace(`/`re.sub(` body test.
   A predicate over a body's TEXT is a predicate that body's text decides.
   This also removes a latent parser gap in the other direction: under the
   old rule a `@@` spec row whose OLD text happened to contain `.replace(`
   would have been handed to `ast.parse` and reported as exit 2.
2. **`re.subn` is read alongside `re.sub`.** `attr in ("sub", "subn")`.
3. **Index-and-slice anchors are read.** Literal arguments to `.index`,
   `.find` and `.count` in a Python heredoc become anchors, deduplicated
   against literals the same heredoc already contributed.
4. **`.replace(old, new, 1)` is no longer dropped by arity.** `len(args) >= 2`.

Plus one defect found while reading, unrelated to the brief:

**`_shape_b` shadowed its own `name` parameter.** The local-binding scan did
`name = node.targets[0].id`, overwriting the harness filename. Every anchor
reported after the first assignment in a heredoc carried a Python variable
name where its harness name should be — so a `STALE ANCHOR` line would have
sent the reader to a file called `anchor` or `s`. Renamed to `bound_name`.

### The one weaker rule, named rather than hidden

`.index(x, start)` searches forward from a position the row already holds,
so file-wide uniqueness is not what the row needs. Row M's end anchor
`"    )\n"` occurs **4 times** in `src/fast_mcp_jobvite/__main__.py` and is
perfectly correct. Those anchors get their own shape, `py-scan`, checked as
**at least one hit** rather than exactly one. A weaker check that renders
identically to the strong one is worse than no check, so the verdict line
now says which rule it applied.

---

## 4. THE FLOOR: 458 → 464, AND IN THAT ORDER

`.github/workflows/ci.yml`: `--floor 458` → `--floor 464`.

**The floor was raised only after the widening, never before.** A floor set
from a blind instrument is #91's slack with the slack invisible.

    22c9873, before:  anchors resolved: 458
    after:            anchors resolved: 464   (+6)

All six are in `check-u1-boot-amputation.sh`, whose count goes 12 → 18.
Every other harness is unchanged, which is the evidence that the widening
did not accidentally start counting something it should not:

| line | shape       | target          | what it is                       |
|------|-------------|-----------------|----------------------------------|
| 387  | py-heredoc  | config.py       | row F's `opener` uniqueness guard|
| 450  | py-regex    | `__main__.py`   | row H's `re.subn` pattern        |
| 506  | py-heredoc  | `__main__.py`   | row K's start anchor             |
| 507  | py-scan     | `__main__.py`   | row K's end anchor               |
| 579  | py-heredoc  | `__main__.py`   | row M's start anchor             |
| 580  | py-scan     | `__main__.py`   | row M's end anchor               |

**The widening did NOT leave the floor unchanged.** The brief asked me to
say so rather than report a green if it had; it did not.

### #156's "15" is now 18, and neither figure was wrong

#156 read the file and counted 15 anchors against the checker's 12. Under the
widened selector the same file yields **18**. The extra three are row F's
opener (§2 above) and the two `py-scan` end anchors, which #156's
by-hand read counted as parts of rows rather than as anchors in their own
right. Both counts are defensible; the difference is a definition, and the
checker's definition is now written down in its docstring.

---

## 5. THE PROOF: three control PAIRS, all derived

`scripts/check-harness-anchors-controls.sh`, `ROW_FLOOR` 9 → 15.

Each widening gets two rows: break an anchor **only the new rule can see**,
require the real checker to report it (exit 1), then delete that one rule
from the same broken tree and require it to go green (exit 0). A rule whose
deletion leaves the count unchanged fails the row rather than passing it —
that is the vacuity guard the brief's "a widening that leaves 458 unchanged
did nothing" asks for, wired into the harness.

**WHICH anchor gets broken is computed, never named here.** The checker is
asked for its anchors, asked again with the rule under test deleted, and the
anchors that vanish are that rule's. A hand-named subject would rot the
first time a row moved.

    15/15 controls fired.
    HARNESS-RESULT name=check-harness-anchors-controls.sh rows=15 floor=15 fired=15/15 status=ok

### MY FIRST VERSION OF THAT CONTROL REPORTED THREE SURVIVORS, AND ALL THREE WERE FAULTS IN THE CONTROL

Recorded because the fix is only trustworthy because the control failed
first:

- **The break did not break anything.** It spliced `ZZ` into the middle of
  the matched text. Row H's anchor is a regex containing `.*?`, so the
  insertion landed inside the wildcard and the pattern still matched — the
  checker correctly reported 464 with nothing stale, and the row read as a
  survivor. The insertion point is now SEARCHED for, and a candidate whose
  anchor cannot be invalidated at all is passed over rather than declared
  broken.
- **The break was not isolated.** The first lost anchor under the
  index-and-slice rule was `"TOOL_REQUIREMENTS: ... = {"` — which is also
  the opening of the `re.sub` pattern at :391 that the OLD selector already
  read. Breaking it broke both, so the amputated checker stayed red and the
  row read as a survivor while the widening was fine. A subject is now only
  usable if no anchor that SURVIVES the amputation matches the same text.
- Those two faults produced three survivors between them.

### A LIMIT OF W3, stated

W3 (the heredoc gate) and W1 (`re.subn`) both select `:450` as their
subject, because restoring the prose gate hides row H's heredoc entirely and
`:450` is the first candidate that passes the isolation filter. W3 therefore
proves the gate change is load-bearing, but it does not distinguish the gate
from the `subn` rule. W2 is the row that exercises a splice anchor
specifically (`:506`).

---

## 6. GATES, each exit code on its own line

At the branch tip, worktree `fmj-worktrees/w167`:

    uv run --frozen ruff check .                                    0
    uv run --frozen ruff format --check .                           0
    uv run --frozen pytest -q                    887 passed, 6 deselected, 0 skipped, 0
    python3 scripts/check-harness-anchors.py --self-check --floor 464   0   (464 resolved)
    bash scripts/ci-harness-gate.sh check-harness-anchors-controls.sh --controls-fired  0  (15/15)
    uv run --frozen python docs/reviews/check-checkers-are-wired.py 0   (125 members)
    python3 docs/reviews/check-row-floors.py                        0
    python3 docs/reviews/check-row-floor-exactness.py               0
    python3 docs/reviews/check-no-errexit.py                        0
    python3 docs/reviews/check-no-sigpipe-pipelines.py              0
    bash   docs/reviews/check-harness-result.sh                     0
    python3 docs/reviews/check-landing-published.py                 0
    python3 docs/reviews/check-design-freeze.py                     0
    python3 docs/reviews/check-design-citations.py                  0
    python3 docs/reviews/check-design-citation-shape.py             0
    python3 docs/reviews/check-cross-references.py                  0
    python3 docs/reviews/check-clause-citations.py                  0
    python3 docs/reviews/check-standards-citations.py               0
    python3 docs/reviews/check-obligations.py                       0
    python3 docs/reviews/check-coupling.py docs/DESIGN.md           0
    uv run --frozen python docs/reviews/probe-docs-lint-amputation.py  0
    python3 scripts/check-committed-file-types.py                   0
    shellcheck --severity=warning scripts/*.sh scripts/lib/*.sh docs/reviews/*.sh  0
    uv run --no-project --with detect-secrets==1.5.0 python scripts/check-secrets-baseline.py  0
      (audited=22 found=22 new=0 stale=0 files=13)
    uv run --frozen python docs/reviews/probe-167-mutation-site-census.py  0

`887 passed, 6 deselected` — the 6 deselections are the standing
configuration, not a skip. **0 skipped.**

---

## 7. DELIBERATE DEVIATIONS FROM §B, declared

§B says I own `ci.yml`'s floor number ONLY. Three edits go beyond that, each
because leaving it would ship a number that contradicts a run:

1. **`ci.yml`'s comment above the floor said "deleting one shape drops 201
   to 186".** Row F1 of the controls harness now measures 464 → 449. The
   sentence was rewritten in place with the live figures and a pointer to
   the row that produces them, and it now records why 458 was not a number
   to raise blind.
2. **R16-N3, handed to me by #166 because it lives in `ci.yml`.** "43
   tracked .sh" against `check-no-errexit.py`'s own live 55. **Deleted, not
   refreshed** — the checker prints its count every run, so it belongs in
   one place. Same ruling #166 applied to three stale doc counts.
3. **R16-N4, same source.** The lychee comment's "27 relative markdown links
   across 63 files"; I re-walked the tree and it is 56 across 244, 0
   dangling (one apparent hit is `[x](y)` inside prose ABOUT the link form,
   in `REVIEW-R16.md:468`). Counts deleted, property kept.

Fourth: **`docs/reviews/check-checkers-are-wired.py` gained one exemption
entry** for the census probe. That file is not in my §B list. It was
unavoidable: the wiring container is "tracked .py, .sh under docs/reviews/,
scripts/", so committing the probe makes it a member and CI goes red without
an entry — and §F says do not add a red step. **This is #163's shape, live:
the probe was invisible to the wiring gate until it was tracked, so the
gate's green while it sat untracked said nothing.** The probe is exempt
rather than wired because it always exits 0; a step that cannot fail guards
nothing.

---

## 8. REPORTED, NOT FIXED

**R3 / §F — bare `python3` in the U1 mutators.** All 13 heredocs in
`scripts/check-u1-boot-amputation.sh` invoke bare `python3` where CI uses
`uv run --frozen python`. Harmless today (stdlib only) but it is the #46
shape. **NOT FIXED, and the reason is not cost:** that file is not in my §B
list, and #156 has unmerged commits on it (`b84b77d`, `76863bb`). Editing
all 13 invocations under those two conditions is how a merge resolution puts
damage back. It should be one sweep, on one branch, by whoever lands #156.

The same shape is in my OWN `check-harness-anchors-controls.sh` (7 sites)
and it is deliberately left: the harness runs the checker inside a scratch
`git ls-files` copy, and `uv run --frozen` there would build a venv per row.
The checker is stdlib-only. Recorded so the zero is not read as absence.

---

## 9. COULD NOT SETTLE

- **`actionlint` is not installed on this machine** (`command not found`),
  so ci.yml was not lint-checked. My change to it is one integer plus
  comment text, but I did not run the gate and will not claim it passed.
- **The census covers Python heredocs only.** Shapes A (shell helpers), C
  (`@@` tables) and D (`sed -i`) were cross-checked for *presence* — only
  `check-u0-test-controls.sh` and this harness's own controls contain
  `sed -i`, only `check-u15-gate-controls.sh` contains `@@`, and the
  checker's per-harness `seen` tallies match its anchor counts for all of
  them — but I did not build an independent enumerator for those three the
  way I did for shape B. If a shape-A helper anchors by a mechanism its
  `local` line does not name, this measurement would not see it.
- **Whether the three previously-hidden rows ever silently tested an intact
  tree.** They all carry their own `assert`/`sys.exit` guards at HEAD (#156
  put them there), so they fail loudly now. What happened before those
  guards existed is not recoverable from the tree.

---

## 10. WHERE THE BRIEF WAS WRONG

Thirteen of thirteen found one; this is the fourteenth.

- **§C and §D: "expect the gap to be larger than three".** Measured
  repo-wide, the gap is **exactly three heredocs, all in one file**. Widening
  found a fourth ANCHOR (§2) inside one of the already-visible heredocs, but
  no other harness hides anything. The brief's expectation was the reasonable
  one and the measurement refutes it — which is why §D said to measure first.
- **§C: "Two independent selector limits".** There are **three**, and the
  third is the load-bearing one: the `:331` body gate skipped rows K and M's
  heredocs WHOLE, before any per-call selector ran. Fixing `attr == "sub"`
  and adding a splice reader without touching that gate would have recovered
  row H only, and K and M would have stayed invisible at exit 0 — with the
  floor freshly raised over them.
- **§B: "the anchor floor ONLY" in ci.yml.** Not survivable as written; see
  §7. Two of the three extra edits are findings #166 explicitly routed to me
  because I hold the file.
