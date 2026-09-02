# REVIEW-R17: the complementary round, and the declaration channel that manufactures coverage

Round: R17. Reviewer: `review-r17`, Tier 1.
Brief: `docs/briefs/BRIEF-R17-complementary-round.md`.
Pinned at **`2eb2d2a`**. The trunk moved **three times** while I read
(`2eb2d2a` -> `c545ead`... -> `298ce89`); every number below is
re-derived at `2eb2d2a` unless it says otherwise.

<!-- REVIEW-COVERS: 8695101..2eb2d2a PATHS: docs/adr/0017-unmapped-errors-are-internal-error-not-about-blank.md docs/adr/0019-design-603-cites-a-section-that-does-not-exist.md docs/adr/0022-no-cookie-jar-is-a-disable-not-an-omission.md docs/README.md docs/DESIGN-FREEZE.txt CONTRIBUTING.md README.md .env.example .pre-commit-config.yaml pyproject.toml sweep.log scratch139 src/fast_mcp_jobvite/__main__.py src/fast_mcp_jobvite/approval.py src/fast_mcp_jobvite/errors.py src/fast_mcp_jobvite/services/jobvite_client.py src/fast_mcp_jobvite/utils/redaction.py tests/boot_process.py tests/test_spawn_orphan.py tests/test_audit_phase_sites.py tests/test_error_contract.py tests/test_resilience.py tests/test_tools_jobs.py tests/test_redaction.py -->

---

## 0. What this declaration claims, and what it deliberately does not

**It names 24 FILES, not five directories.** My brief and R15 §1c both
proposed `docs/briefs docs/adr docs/research src tests` plus root
config. Measured, that list claims **97 distinct files**. I did not read
97 files. Declaring the directories would have been a wide false
declaration, which §D of my brief calls a defect worse than the gap, and
which the checker cannot catch.

So the declaration is the file list I actually opened. Specifically **I
did NOT read**, and therefore do not claim:

- 30 of the 33 ADRs (I read 0017, 0019, 0022 in full - the three my
  population touches - plus 0001-0015 as authority, which the range does
  not touch);
- `docs/research/` (both files stay unclaimed);
- 25 of the 26 `docs/briefs/` files (only `BRIEF-R17` was read, and it
  is claimed by nobody);
- ~20 `tests/*.py` and ~14 `src/**.py` outside the list above.

**The honest cost:** `PARTIAL` does **not** go to 0. It was the round's
stated goal and it is not met. See §1.

---

## 1. Findings

### R17-H1 (High) - a declaration's RANGE alone clears `COVERED BY NOTHING`, so ONE file read reclassifies 26 commits

`docs/reviews/check-review-coverage.py:428-431`

```python
claiming = [r for r in rounds if sha in r.commits]
if not claiming:
    untouched.append(sha)
    continue
```

A commit is `NONE` **only when no round's RANGE contains it**. The path
filter is applied *afterwards*, to decide `PARTIAL`. So a round that
declares a wide range and a narrow path list moves every commit in that
range out of `NONE` **without having read one byte of most of them**.

**Measured, as a control.** A declaration over the whole container
range claiming exactly one file - `docs/DESIGN-FREEZE.txt`, a
seven-character file - against `main`:

```
baseline (no R17 declaration):   PARTIALLY covered 42   COVERED BY NOTHING 26
R17 claiming ONE file:           PARTIALLY covered 62   COVERED BY NOTHING  0
```

**One file. `COVERED BY NOTHING` 26 -> 0.**

And for my own real declaration, the split between reading and artifact:

```
was NONE, now PARTIAL because R17 read >=1 of its files:   2
was NONE, now PARTIAL as a PURE RANGE ARTIFACT:           24
```

This is the same shape as R12-H3, one column over. R12-H3 fixed a metric
that *improved when you deleted a declaration*; this one improves when
you **add** a declaration that reads nothing. The docstring refuses to
manufacture coverage from the inferrer's side and this manufactures it
from the author's side, which is exactly the hazard the PATHS mechanism
was introduced to close - closed for `covered`, left open for `NONE`.

It matters because `NONE` is the number a reader treats as *"nobody has
looked at these at all"*, and it is the number every recent handoff
quotes.

**Suggested fix**, at `:428`:

```python
files = git("show", "--name-only", "--pretty=format:", sha).split()
claiming = [
    r for r in rounds
    if sha in r.commits and any(r.claims(f) for f in files if not is_record(f))
]
if not claiming:
    untouched.append(sha)
    continue
```

A round must claim at least one non-record file the commit touches
before it counts as having reached that commit. Add an arm to
`probe-coverage-ratchet.py`: a planted declaration over the full range
claiming one unrelated file must leave `COVERED BY NOTHING` unmoved.
That arm is the PLANT arm's missing sibling - the existing PLANT arm
perturbs the declaration's *existence*, not its *width*.

**The 24 range artifacts are named in §3** so the record is not
silently false while the fix is pending.

---

### R17-H2 (High) - the path list R15 §1c recommended, and my brief passed on, leaves 9 of 42 PARTIAL commits still PARTIAL

`docs/reviews/REVIEW-R15.md:107-112` proposes:

> *"one complementary round over `docs/briefs docs/adr docs/research src
> tests` plus the five root config files takes PARTIAL 39 -> 0."*

Measured against the real residual set at `2eb2d2a`:

```
R15 §1c proposal: PARTIAL would go 42 -> 9
  files it does NOT claim:
    CONTRIBUTING.md   docs/DESIGN-FREEZE.txt   docs/README.md
    scratch139/fix.py  scratch139/measure.py   sweep.log
```

**Four of those six are enumerated in §1c's own residual list**, ten
lines above the proposal that omits them - `docs/README.md` and
`sweep.log` and both `scratch139/` files appear in its "2 each" and "1
each" tallies, and `docs/DESIGN-FREEZE.txt` in the latter. §1c then
writes a *separate* paragraph saying `scratch139/` and `sweep.log` "are
not an obstacle", having left them out of the list that would have
claimed them. `CONTRIBUTING.md` entered after §1c was written and is a
genuine staleness, not an omission.

A fix that rebuilds its own defect one column over: §1c correctly
diagnosed that **touch counts over-promise because one stray file
demotes a whole commit**, then proposed a path list assembled from its
own touch table with six entries dropped.

**Suggested fix.** The correct list is §1c's plus those six. It is
recorded here rather than acted on, because R17-H1 means no path list
should be widened until the range/NONE hole is closed - widening it now
buys real coverage for the files read and manufactures `NONE` clearance
for everything else in the range.

---

### R17-M1 (Medium) - `measure-xref-population.py` excludes `docs/briefs/` against the ruling its own docstring invokes, and could not measure it anyway

`docs/reviews/measure-xref-population.py:48`

```python
EXCL_DIRS = ("docs/worklogs/", "docs/plans/", "docs/reviews/", "docs/briefs/")
```

The docstring at `:17-18` says it measures *"every tracked `*.md`
outside the RECORD paths ruled at `a1773e8`"*. The RECORD ruling names
**three** paths (`check-review-coverage.py:171-190`: `CHANGELOG.md`,
`docs/worklogs`, `docs/plans`) and refuses `docs/briefs` **by name**,
at `:161-170`, because *"a brief INSTRUCTS an agent and has carried
substantive rulings"*. `EXCL_DIRS` has five entries and carries no
reason for any of them, in a file whose sibling requires that *"a bare
path is refused: the reason IS the exemption"*.

**Two things follow, and the second is the one that matters.**

1. #139's headline "46 -> 1" was measured over a population that
   excluded briefs by policy.
2. **Removing the exclusion would not have helped**, because the script
   hard-codes `referent=None` for anything outside `docs/adr/` and not
   in `DEFAULT_TARGETS`. Measured:

   ```
   briefs tracked=62  MEASURED=0  SKIPPED(no numbered headings)=62  unresolved=0
   ```

   **62 of 62 skipped: a completely vacuous zero.** My first run of this
   reported "0 unresolved across 0 files" and I nearly published it -
   the `except ValueError: continue` swallowed the entire population.

   `docs/briefs/` carries **83 section references across 18 files**,
   none of which any instrument can resolve today.

The script's own comment at `:55-60` records this exact defect being
fixed once (hard-coded `referent=None` gave a false *count*); the
residual `None` fallback now gives a silent *skip*, which is the same
defect with the sign flipped.

**Suggested fix.** Drop `"docs/briefs/"` from `EXCL_DIRS`, give briefs
the `docs/adr/` treatment (`"docs/DESIGN.md"` as referent - most brief
§-refs are into the design), give the three surviving entries a reason
string each as `RECORD_PATHS` requires, and make the `ValueError` path
**print and count** rather than being swallowable, so a skipped
population can never read as a clean zero again.

---

### R17-M2 (Medium) - the audit-phase container compares a SET, so 7 of 13 call sites are indistinguishable from a sibling

`tests/test_audit_phase_sites.py:503-516`, `:521-540`

`_static_phase_sites()` returns `set[tuple[str, str]]` - (function,
phase). Measured against the tree:

```
AST call SITES in tools/:            13
distinct (function, phase) PAIRS:     6
   2x ('create_candidate', 'AFTER_WRITE')
   3x ('create_candidate', 'BEFORE_SIDE_EFFECT')
   2x ('get_candidate', 'READ')
   2x ('get_job_feed', 'READ')
   2x ('search_candidates', 'READ')
   2x ('search_jobs', 'READ')
```

The file's docstring (`:33-38`) says a later call site *"with a phase no
case exercises fails that assertion rather than joining the silent
twelve"*. That is true as written. But the equality is over 6 pairs, so
**a call site added inside an already-covered function with an
already-covered phase changes `static` not at all.**

The ordered-sequence assertion in each case catches such an addition on
a **driven** branch (the sequence gets longer). It does not catch one on
a branch no case drives - and error branches nobody drives are precisely
where the original twelve survivors lived.

To be fair to the file: this is the strongest test in my population. The
container check has a vacuity guard (`:534`), the phase spy delegates to
the real `emit`, and the "no audit, no write" case runs both arms with
the control first. This is a gap in one layer, not a vacuous test.

**Suggested fix.** Key the pair by call site rather than by identity -
`(function, phase, lineno)` from the `ast` node, compared as a
`Counter` of `(function, phase)`; the CASES side already knows its
expected multiplicity because it pins ordered sequences, so
`Counter(covered) == Counter(static)` is the assertion, and an added
site on an undriven branch fails it.

---

### R17-L1 (Low) - "Eleven decision records" in two files, against 33 ADRs

`docs/README.md:22` - *"Eleven decision records, each citing the clause
it deviates from"*
`docs/adr/README.md:7` - *"eleven ADRs exist against a design that is..."*

```
ADR files (excl README): 33
```

A count beside a growing container, twice - the defect
`.pre-commit-config.yaml` had corrected out of it at `ee84ab7`, whose
commit message is literally *"a count beside a growing container"*. And
`docs/README.md`'s own opening paragraph says a count was removed from
that very file because *"both were true when written and neither
survived the afternoon"*, then keeps this one nine lines later.

I checked the siblings: `"Seven reports"` for `docs/research/` is
correct (7), and `"Six further gates"` matches its own enumeration (6).
Only the ADR count is wrong, and it is wrong in both files.

**Suggested fix.** Delete the number from both, as `ee84ab7` did:
*"Decision records, each citing the clause it deviates from"* and
*"ADRs exist against a design that..."*. `ls docs/adr/[0-9]*.md | wc -l`
answers it whenever anyone needs it. Do not replace 11 with 33 - the
container is still growing.

---

### R17-L2 (Low, latent) - the audit-phase container is scoped to `tools/` by path

`tests/test_audit_phase_sites.py:511` walks
`pathlib.Path(candidates_module.__file__).parent`, i.e. `tools/` only.

Measured today the scope is complete - all 13 non-dispatcher sites are
in `tools/`, and `audit.py`'s 2 are the dispatcher's own branches, which
are well tested and correctly excluded. So this is latent, not live.

But it is #153 and #155's shape - a container selected by path rather
than by the property - and an `AuditPhase` emission added in
`approval.py` or `services/` would be invisible while the test still
prints a clean equality.

**Suggested fix.** Walk the package root
(`.parent.parent`) and exclude `audit.py` **by name with a reason**, so
the exclusion is one named file rather than an unnamed everything-else.

---

### R17-L3 (nit) - `redaction.py` reaches into `httpx2`'s private module

`src/fast_mcp_jobvite/utils/redaction.py:54`

```python
from httpx2._client import logger as _httpx2_logger  # noqa: SLF001
```

ADR-0026 requires the logger name be **derived, never retyped**, and
this correctly discharges it (R11-M1 fixed the retyped literal). There
is no public accessor, so the private import is the only way to obey the
ADR - the trade is right and I am not asking for it to be reverted.

The nit is that nothing states the failure mode: a `httpx2` minor
upgrade that moves `logger` out of `_client` is an **ImportError at
import time**, which is loud and safe. That is the good outcome and it
should be said, because the reader's fear is the silent one.

**Suggested fix.** One line on the import: *"private on purpose
(ADR-0026 forbids the literal). A rename upstream is an ImportError at
module load, not a silently detached filter - which is the failure this
is chosen for."*

---

## 2. WITHDRAWN: "ADR citations into DESIGN.md have drifted"

**I nearly published this and it is wrong.** Recording it because the
method that produced it is the reportable part.

I observed that ADR-0017 cites `DESIGN.md:515` for the unmapped-error
registry row, and that `:515` today is pagination prose; the row is at
`:573`. Same for `:1756` (C4-R1, actually `:1844`), `:1725` (C2 stack,
actually `:1812`), `:1763` (C8-I1, actually `:1899`), `:373-375` (the
outbound budget, actually `:393`). Three of them resolve to **blank
lines**. `check-design-citations.py` passes on all of them because it
checks bounds, not subject, and says so.

I then built a quote-containment heuristic and it reported **27 of 28
citations wrong**. That number is garbage: the matcher grabbed the
nearest emphasised run in a 4-line window, which is usually the ADR's
own bold heading, not a quote of the design. "no threat model row
changes" and "the cap is http only by construction" are ADR prose.

**Then I checked the thing I should have checked first.** ADR citations
are pinned to the DESIGN blob contemporary with the ADR:

```
git show 135c3ac:docs/DESIGN.md | sed -n 603p
  -> line carries the URL, because the v1 `jobFeed` URL is itself a secret (§5.4)
     (exactly what ADR-0019 says :603 reads, and 135c3ac is the blob ADR-0019 names)

git show <ADR-0017's own commit>:docs/DESIGN.md | sed -n 515p
  -> | Anything unmapped | `about:blank` per `:212` | - |
     (exactly what ADR-0017 says :515 reads)
```

Two of two headline citations resolve **exactly**. `scratch139/fix.py`
section D confirms the convention is deliberate: it repointed ADR-0019's
title from `:605` to `:603` *against the blob the ADR itself names*.

**So the citations are correct and the finding is withdrawn.** What
survives is smaller and I record it as an observation rather than a
finding, because I have not established it is unwanted:

> ADR-0019 names its blob (`135c3ac`) in prose. **The other 32 do not.**
> A reader resolving ADR-0017's `:515` against today's design lands on
> pagination and would "correct" it - the same destructive-correction
> shape ADR-0014 was written about. And `check-design-citations.py`
> validates ADR citations against **today's** file, which is a category
> error that passes only because `DESIGN.md` has grown rather than
> shrunk; the highest line any ADR cites is `:1763` against 2133 today.

If Tier 0 wants it closed, the cheap form is a `Blob:` field beside
`Status:` and `Type:`, and `docs/adr/` either exempted from the citation
checker or resolved against that field.

---

## 3. The 24 range artifacts, named

These commits move `NONE -> PARTIAL` under my declaration **because my
range contains them, not because I read anything in them.** They are
recorded in the backlog as `PARTIAL` because that is what the instrument
measures; this section is the record that the move is not progress.

```
298ce89 76863bb 96249f5 e5c7aeb 03da258 2eb2d2a c545ead b050b4b
3a5dbe9 e61a668 2d886a4 3cf6fa4 6e07131 5fb7a6f d0fce2a a3fc38f
0256438 b84b77d 401689e 4aca097 ffd36c7 c276a45 3aad1a3 3d7a82f
```

Six of these (`298ce89 76863bb 96249f5 e5c7aeb 03da258 b84b77d`) landed
**after** my pinned sha and fall outside the declared range, so they
stay `NONE` - correctly, since I read none of them.

The two that are **not** artifacts, where I did read a file:

```
a00d2ac  <- CONTRIBUTING.md
0b90c2a  <- .pre-commit-config.yaml
```

---

## 4. Credit, because a round that only reports defects misreports the tree

- **ADR-0022 is applied and controlled correctly.** The clearing is in a
  `finally` (`jobvite_client.py:1927-1940`) so a raising call cannot
  leave a jar; both `test_no_cookie_jar_is_carried_between_requests` and
  `test_positive_control_httpx2_DOES_carry_cookies_by_default` exist,
  and the positive control is the thing that stops the first going
  vacuous if `httpx2` changes its default.
- **ADR-0017 is applied in both halves** - `DESIGN.md:573` carries
  `/problems/internal-error`, and `errors.py:92-93` makes
  `INTERNAL_ERROR` the answer rather than dead code, with `UNMAPPED`
  (`about:blank`) kept for its actual scope at `:110`.
- **ADR-0019 is applied**: `grep -n '§5.4' docs/DESIGN.md` returns
  nothing.
- **R11-H1 and R11-H2 are model fixes.** `5e45709` moved the
  `retry_after` attachment into `problem_from_exception` rather than to
  six call sites, and rewrote a test whose docstring claimed a caller
  property its body could not exercise - it had been handed the value it
  asserted. `afd2937` turned two negative-only PDEATHSIG guards into
  pairs with arms **measured to fire before being written**.
- **`ece3dbd`** replaced `HTTPX_LOGGER_NAME: Final = "httpx2"` with the
  library's own `logger.name`, and gave three bail-out exit codes a
  second reader so they stop rendering as one blank body.

---

## 5. Corrections to my brief

1. **§B/§F: "the trunk is `2d886a4` on `origin/main`" was wrong when
   written.** `origin/main` was 4 commits behind local `main`, which
   already carried R16's merge, R16's review document and the rewritten
   backlog. Measured both ways at the time I started:

   ```
   --ref origin/main : recorded 86, measured 101, ENTERED 15, exit 1
   --ref main        : recorded 57, measured  62, ENTERED  5, exit 1
   ```

   The brief's own "the backlog holds 57" is the `main` number, so the
   brief mixed the two refs in one paragraph. The checker warns about
   exactly this (`WHAT IT STILL CANNOT DO` / *"the ref it reads can be
   stale"*), and it is the reason I re-pinned to `main`.
   **Fix: push `main`, or have every brief quote the ref beside the sha.**

2. **§B: "R15 §1c names the complement" - it names an incomplete one.**
   See R17-H2. The brief was right to tell me to read §1c first-hand
   rather than trust the summary; reading it first-hand is how the six
   missing files were found.

3. **§E: "THE BACKLOG EDIT IS UP TO THREE PARTS" is right, and there is
   a fourth.** Deletions, additions and KIND corrections are all
   present. The fourth is that a KIND correction can be an **artifact of
   a range** rather than a fact about reading (R17-H1), and nothing in
   the backlog format can express the difference - which is why §3 of
   this document exists.

4. **§D: "R16 declared three paths where its brief's example showed
   four" - I could not confirm the four.** `REVIEW-R16.md`'s
   declaration reads `PATHS: docs/reviews scripts .github`, three, as
   stated. I did not locate the four-path example in `BRIEF-R16`, and I
   am not claiming it is absent - I did not read that brief in full.
   Recorded as unverified rather than confirmed.

---

## 6. What I did NOT verify

- **CI.** I ran no workflow and added no run. `.github/` is outside my
  declaration entirely.
- **`.secrets.baseline`.** 9 touches in my population and I read only
  its shape (27 plugins, 13 files with results, `generated_at`
  2026-09-01T20:33:41Z). #163 is open on this and I did not re-file.
- **Whether `check-review-coverage.py`'s `probe-coverage-ratchet.py`
  arms still pass with my suggested H1 fix applied.** I am read-only
  and did not apply it; the suggested arm is proposed, not measured.
- **The 30 ADRs, 2 research documents, 25 briefs and ~34 src/tests
  files** listed in §0. Not read, not claimed.
