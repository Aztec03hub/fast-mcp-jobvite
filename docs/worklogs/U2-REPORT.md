# U2 - the error contract and the correlation ContextVar

**Agent:** `impl-u2-errors`. **Date:** 2026-08-28 05:55 PM CDT.
**Spec:** `docs/plans/IMPLEMENTATION-PLAN.md` §U2 (`:445-478`). **Design:** frozen revision 6,
read from `git show 135c3ac:docs/DESIGN.md`. Nothing in the design was edited.

**Not committed.** All work is left in the tree for the team lead to commit.

---

## 1. What was built

| File | Lines | What it is |
|---|---|---|
| `src/fast_mcp_jobvite/errors.py` | 266 | The exception hierarchy and RFC 9457 problem construction |
| `src/fast_mcp_jobvite/utils/__init__.py` | 5 | Package marker for `utils/` |
| `src/fast_mcp_jobvite/utils/correlation.py` | 54 | `request_id_var` and `request_id_scope` |
| `tests/test_error_contract.py` | 313 | 24 tests |
| `tests/test_correlation.py` | 155 | 10 tests |

No shared file was touched: `pyproject.toml`, `.github/`, `docs/plans/`, `tests/conftest.py`,
`config.py`, `server.py`, `__main__.py` and every tool, client and model are untouched.
`git status` at completion shows only the five paths above plus other agents' in-flight work.

### `errors.py`

- **The registry is mirrored as seven `ProblemKind` constants**, each a verbatim row of
  `error-contract.md:96-108`. Nothing is minted locally, per `DESIGN.md:510-511`.
- **The exception hierarchy carries its registry row**, so the mapping is fixed where the
  condition is *known* rather than re-derived from a status at the boundary - which is how
  Jobvite's status reached `status` in the revision `DESIGN.md:502-509` corrects.
  `JobviteUpstreamError` (502), `JobviteUnavailableError` (503), `ValidationError` (422),
  `ResourceNotFoundError` (404), `DuplicateCandidateError` (409), `ScopeDeniedError` (403),
  and anything else -> `about:blank`.
- **`JobviteUpstreamError` keeps Jobvite's status and message** on the instance (for the audit
  event) and reproduces both in `detail` (`DESIGN.md:532-534`). `upstream_status=None` is a first
  class case: the plain-text and Tomcat-HTML error encodings (`DESIGN.md:345-347`) carry no status.
- **`build_problem` and `problem_from_exception` return; they never raise a problem object**
  (`DESIGN.md:536-540`). The one `raise` in the module is a `ValueError` when an extension member
  would shadow one of the seven - a call-site programming error, and letting it silently overwrite
  `status` would reintroduce exactly the defect `DESIGN.md:502` corrects.
- **An unmapped exception's message never reaches the caller.** `detail` names the exception class
  instead; an arbitrary `str(exc)` can carry a URL, a credential fragment or an upstream body.

### `utils/correlation.py`

- `request_id_var: ContextVar[str | None] = ContextVar("request_id_var", default=None)` - the name
  mandated verbatim by `ai/tool-calling.md:173-175` (subject-verified: that line reads *"the
  canonical triple verbatim: HTTP header `X-Request-ID`, log field `request_id`, ContextVar
  `request_id_var`"*).
- `request_id_scope(request_id)` - a context manager that sets the var and **resets it in a
  `finally`**, using `reset(token)` rather than `set(None)` so a nested scope restores the
  enclosing id instead of erasing it.

**`request_id_scope` is an addition to what the design names, and it needs a ruling - see §5, N1.**

---

## 2. The full gate, real output

```
$ uv run --frozen pytest -q
======================= 90 passed, 2 deselected in 1.44s =======================

$ uv run ruff check
All checks passed!

$ uv run ruff format --check
21 files already formatted

$ uv run --frozen mypy src tests
Success: no issues found in 14 source files
```

**Zero skips.** The 2 deselected are the pre-existing `credentialed` arm. Baseline before U2 was
`56 passed, 2 deselected`; U2 adds 34 tests.

Coverage of the two new modules, against the 95% `utils/` floor in `[tool.coverage]`:

```
$ uv run --frozen pytest -q --cov=fast_mcp_jobvite --cov-report=term-missing \
    tests/test_error_contract.py tests/test_correlation.py
Name                                        Stmts   Miss Branch BrPart  Cover   Missing
src/fast_mcp_jobvite/errors.py                 56      0      4      0   100%
src/fast_mcp_jobvite/utils/correlation.py      11      0      0      0   100%
TOTAL                                          67      0      4      0   100%
```

100% line and 100% branch on both. The coverage step in `ci.yml` is still commented out and is
U1's to enable; nothing here changes it.

---

## 3. Harness 1 - mutation. 17 designed, 17 killed, 0 survived

Each mutation was applied to the real module, the suite was run, and the module restored.

```
KILLED  M1  Jobvite 401 passed through as status               4 failed, 30 passed
KILLED  M2  validation is 400 not 422                          3 failed, 31 passed
KILLED  M3  minted slug /problems/jobvite-auth-failed          5 failed, 29 passed
KILLED  M4  registry title drifts (Conflict -> Duplicate)      1 failed, 33 passed
KILLED  M5  instance URN prefix changed                        1 failed, 33 passed
KILLED  M6  timestamp member dropped                           3 failed, 31 passed
KILLED  M7  request_id member dropped                          3 failed, 31 passed
KILLED  M8  Jobvite message discarded from detail              2 failed, 32 passed
KILLED  M9  Jobvite status discarded from detail               1 failed, 33 passed
KILLED  M10 unmapped becomes about:blank (INVERTED, ADR-0017)  2 failed, 32 passed
KILLED  M11 problem object RAISED instead of returned         18 failed, 16 passed
KILLED  M12 unmapped exception message leaked to caller        1 failed, 33 passed
KILLED  M13 naive (non-UTC) timestamp                          1 failed, 33 passed
KILLED  M14 ContextVar renamed to correlation_id               1 failed, 33 passed
KILLED  M15 reset moved out of the finally                     4 failed, 30 passed
KILLED  M16 reset(token) replaced by set(None)                 2 failed, 32 passed
KILLED  M17 scope never sets the var                           5 failed, 29 passed

17 killed / 0 survived of 17
```

Named killers for the load-bearing ones:

- **M1** killed by `test_a_jobvite_401_is_a_502_and_not_a_401`,
  `test_every_registry_row_maps_to_its_registry_type_and_status[any Jobvite failure, including
  its 4xx]`, `test_the_registry_constants_match_the_standards_table_verbatim`.
- **M11** killed by 18 tests including `test_no_problem_construction_function_raises_a_problem_object`,
  the static AST arm.
- **M15** killed by `test_the_reset_is_lexically_in_a_finally`,
  `test_the_id_does_not_leak_when_the_invocation_raises`, and the concurrency test.
- **M17** (the leak trap: the var is never set, so `get()` is always `None`) killed by
  `test_the_positive_arm_the_var_reads_back_the_id_inside_the_scope` **and** by the four leak
  tests, because each leak test carries its positive arm inline. **This is the mutant the brief
  warned about and it is the reason every leak assertion here is paired.**

### The harness itself was defective on its first run, and that is worth recording

The first sweep reported M2 as killed by M1's test set. Cause, verified: `.pyc` invalidation is
`(mtime, size)`. M1 changes `502` to `401` - **same byte count**, applied and reverted inside one
second - so `src/fast_mcp_jobvite/__pycache__/errors.cpython-312.pyc` was treated as current and
the M2 run imported **M1's bytecode**. Every mutant still showed `exit=1`, so the summary line was
right and the attribution was wrong: a green-looking harness measuring the previous mutant.

Fixed by clearing `__pycache__` and setting `PYTHONDONTWRITEBYTECODE=1` before every run. **Any
unit running an in-place mutation harness on this repo must do the same**; a same-size,
same-second edit is the normal shape of a mutation, not an unusual one.

---

## 4. Harness 2 - amputation. What still passes when the subject is gone

Subject absent / empty / truncated to its module docstring. `-rA` used so passes are listed.

| Case | Result |
|---|---|
| **A1** `errors.py` deleted | `exit=2, 1 error` - collection fails at import. Nothing passes. |
| **A2** `errors.py` empty | `21 failed, 13 passed` |
| **A3** `errors.py` truncated to docstring | `21 failed, 13 passed` (identical set to A2) |
| **A4** `correlation.py` deleted | `exit=2, 1 error`. Nothing passes. |
| **A5** `correlation.py` empty | `9 failed, 25 passed` |
| **A6** `correlation.py` truncated | `9 failed, 25 passed` (identical set to A5) |

Cross-module passes (the `test_correlation.py` tests surviving A2/A3, and vice versa) are a
different subject, not vacuity. **Within its own subject, exactly three assertions survive
amputation. One is a genuine vacuity; two are controls that are supposed to.**

### V1 - genuinely vacuous: the repo-wide "no `success` envelope" assertion

`test_no_success_true_false_envelope_exists_anywhere_in_the_repository` passes with `errors.py`
empty, truncated, or holding nothing but a docstring.

**It is vacuous for the reason the brief predicted, and I confirm it rather than counting it.**
`src/` holds four modules and none of them returns a tool result, so the assertion sweeps a tree
where the defect it forbids cannot yet exist. It is a placeholder for a future check, not present
evidence. **It must be re-asserted, and its result re-read, once `tools/` exists (U6-U8).**

Two things were done rather than shrugging at it:

1. **The scanner has a positive control** (`test_the_envelope_scanner_finds_an_envelope_when_one_is_present`):
   a planted `{"success": true}` in a tmp tree must be found. Without it, a broken regex reads
   exactly like a clean repository.
2. **The scanner fails loudly on a wrong zero** (`test_the_envelope_scanner_reports_a_wrong_zero_on_an_empty_tree`):
   if it walks zero `.py` files it returns a `WRONG ZERO` marker instead of an empty list.

   The first draft used `git grep`, which searches **tracked** files only. Every file in this unit
   is untracked. That draft would have reported a clean zero over its own subject and explained
   itself perfectly. It was replaced with a `pathlib.rglob` walk before this report was written.

### V2, V3 - controls that survive by design, and must not be counted as coverage

- `test_the_concurrency_test_would_catch_a_module_global` survives every amputation of
  `correlation.py`. It is the positive control for the concurrency test: it runs the identical
  interleaving against a module-global holder and asserts the corruption **does** appear. If it
  passed against a ContextVar it would prove the concurrency test is a test of `asyncio.gather`.
  It never touches `src/` and is not evidence about `src/`.
- The two envelope-scanner control tests in V1 above are the same shape.

### One assertion was vacuous and is now fixed

`test_no_type_uri_is_minted_locally` iterates the `ProblemKind` constants in `errors.py`. Deleting
every constant makes the loop iterate zero times and the test pass. Mutation had already passed it
(M3 kills it), which is exactly the pattern U0 and U15 hit: **mutation cannot see an assertion that
iterates over nothing, because a mutant leaves the collection populated.** `assert len(defined) ==
7` was added ahead of the loop.

---

## 5. Findings - design, standards and scope

### D1 (design defect): the unmapped row specified no `status`, and `status` is required - DECIDED, ADR-0017

`DESIGN.md:495-496` makes `status` one of seven **required** members. `DESIGN.md:515`'s registry
table gives the unmapped row `about:blank` and a literal `-` in the Status column. Those cannot
both hold: an unmapped condition must produce a `status` and the design says which value it is
nowhere.

**Implemented at the time:** `about:blank` with **500** and title `"Internal Server Error"`, per
RFC 9457 §4.2.1 (with `about:blank` the title is the status phrase). That was my reading, not the
design's instruction, and it was reported rather than edited in - **a defect in the design is an
ADR, not an edit**.

**ADR-0017 replaced that reading.** The row is now `/problems/internal-error`, 500, "Internal
Server Error", and every problem object carries a `status` without exception, which is what makes
the seven-member requirement checkable. D2 below is the argument, and it is the one that decided
this. The design line is now `DESIGN.md:521`; `DESIGN.md:515` above is where it stood in the
frozen object this report was written against.

### D2 (standards vs design, related to D1): `about:blank` was the wrong row - DECIDED, ADR-0017

`error-contract.md:115` scopes the `about:blank` fallback to *"unmapped **HTTP** errors"*, and
`error-contract.md:106` already carries `/problems/internal-error` **500** *"Unhandled exception
(generic safe message)"*. An unhandled exception raised inside our own tool body is precisely that
row - it is not an unmapped HTTP status. `DESIGN.md:515` routes it to `about:blank` instead, which
declines a registry row that exists for the case.

**DECIDED by ADR-0017, in favour of the standard.** `problem_from_exception` now returns
`/problems/internal-error`, 500, for an exception outside this module's hierarchy, and
`FastMcpJobviteError.kind` defaults to it. `INTERNAL_ERROR` was defined in `errors.py` and reached
by no code path, exercised only by the registry-mirror test; it is now the answer, and **the dead
constant was the symptom**. `UNMAPPED` keeps `about:blank` for its actual scope - an unmapped HTTP
status received from Jobvite - and is reached by no path today, which ADR-0017 accepts on the
grounds that an unreachable fallback that is correct beats a reachable one that is wrong.

**Mutation M10 inverted.** As written here it read *"unmapped becomes `/problems/internal-error`"*
and the harness killed it; that is now the shipped behaviour. The row above is the mutation in its
new direction - *"unmapped becomes `about:blank`"* - re-run against the current tree: **2 failed,
32 passed**, killed by
`test_every_registry_row_maps_to_its_registry_type_and_status[anything unmapped]` and
`test_a_problem_object_is_returned_never_raised`. The row's numbers changed with its direction and
are measured, not carried forward.

### D3 (design, minor): `retry_after` and the "seven members"

`DESIGN.md:496` names seven members; `DESIGN.md:358` attaches a `retry_after` hint to the 503, and
`error-contract.md:86` defines an `errors` array for 422s. Read strictly, "seven members" and an
eighth hint are in tension. **Implemented** as RFC 9457 extension members: the seven are always
present, extensions are additive and may not shadow a required member. This is the reading RFC
9457 §3.2 supports, but the design does not say it.

### N1 (scope, needs the team lead's ruling): `request_id_scope` is not in the design

`DESIGN.md:604-606` places the set and the `finally`-reset in **`audit.py`**, which is U3's.
`utils/correlation.py` is described as holding *"a single `ContextVar[str | None]` named
`request_id_var`"* - which it still does; there is exactly one `ContextVar(` in the file, asserted
by `test_correlation_declares_exactly_one_contextvar`.

**Why I added the context manager anyway:** without it, U2's leak test can only wrap a
`try/finally` written **inside the test**, and then the assertion tests the test's own code.
Amputating `correlation.py` would leave that `finally` intact and the leak test green. Putting the
`finally` in shipped code is what makes M15 ("reset moved out of the finally") a killable mutant at
all.

**The risk this creates, stated plainly:** if U3 writes its own `try/finally` in `audit.py` and
never calls `request_id_scope`, then `request_id_scope` is a shipped function with a test suite
and no caller, and U2's leak evidence describes a code path production does not take. **U3 must
either call `request_id_scope` or this function should be deleted and the `finally` asserted in
`audit.py` instead.** I have not verified what U3 intends; U3 was not written when this ran.

### T1 (tooling, affects other units): CI does not check out `evolv-coder-standards`

`grep -rn "standards" .github/workflows/*.yml` returns only prose comments - no checkout step. A
test that reads `error-contract.md` from the sibling checkout therefore **hard-fails in CI**, and a
test that tolerates its absence is a wrong zero. A `skipif` is unavailable: this suite's CI
contract is zero skips.

My first draft did read the standards file (with a `pytest.fail` if absent). It was replaced: the
registry table is now **pinned as data in `tests/test_error_contract.py`** with the
`error-contract.md:96-108` citation, and `errors.py`'s constants are compared against that pin.
**The limit this leaves is real: nothing in CI compares the pin to the standard.** Drift between
them is caught only by the project's citation audit. Any other unit planning to assert against a
standards file hits the same wall.

---

## 6. Not verified

- **`request_id_scope` has no caller.** U3 owns `audit.py`. See N1.
- **The pinned registry table is not machine-compared to `error-contract.md` in CI.** See T1. I
  read the file by hand at `architecture/error-contract.md:96-108` and transcribed seven rows; a
  transcription error would pass every test in this suite.
- **The envelope assertion proves nothing today.** See V1.
- **Nothing here is asserted on the wire.** `DESIGN.md:615-616` requires the problem object's
  `request_id` to match the audit event's id **on the wire**; that is U5's and needs a server.
- **The 422 row's reachability is unexercised.** `DESIGN.md:563` records it is unreachable on the
  pre-dispatch path and serves in-body validation only. Nothing in the tree yet produces either,
  so the class exists and no caller raises it.
- **Timestamp format vs consumers.** `_timestamp()` emits microseconds (`...T14:32:00.123456Z`),
  matching `error-contract.md:62`'s example. Whether any consumer parses it was not checked.
- **The mutation harness lives in `/tmp/u2_harness.py`, not in the repo.** It is not a committed
  gate and will not run again unless someone re-creates it. If mutation coverage should be
  standing rather than one-shot, that is a decision above this unit.
