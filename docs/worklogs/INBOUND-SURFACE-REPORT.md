# INBOUND-SURFACE - R8-H1, and choosing a container that is not narrower than the claim

**Branch `fix/inbound-surface`, based at `5e439cc`. Worktree `/tmp/inbound-surface-work`.**
Design read as `git show c15b138:docs/DESIGN.md`, never from a working tree. Task **#88**.

---

## THE CONTAINER I CHOSE, AND WHAT IS OUTSIDE IT

**The container is the PACKAGE - every `*.py` under `src/fast_mcp_jobvite/`, walked with
`rglob` - and the selector inside it is a USE, not a name.**

`tests/test_arguments_sweep.py` now has three routes into one swept set:

| Route | Container | Selects by |
|---|---|---|
| A (U14) | `tools/` | being some `@server.tool` function's `params` annotation |
| B (U14) | `tools/` | being a model class, minus every class used as `output_schema=` |
| **C (new)** | **the whole package** | **being named as `response_type=` or `requested_schema=`** |

`INPUT_MODELS` is now the **union of A and C**, which is what that name has claimed since U14
wrote it. Route B stays scoped to `tools/` and stays asserted EQUAL to route A there: it is the
check that route A did not drift, and widening it is the thing R8 correctly said not to do,
because outside `tools/` it has no output-model exclusion that is not a name.

Route C reaches its model through two shapes, and it needs both: `response_type=ApprovalAnswer`
is a bare `Name`, but the MRTR leg passes `requested_schema=APPROVAL_SCHEMA` where
`APPROVAL_SCHEMA = ApprovalAnswer.model_json_schema()`. A route reading only bare names finds the
elicitation leg and not the sampling one. Today both name the same model, so that would have
looked correct; `_schema_aliases` resolves the module-level indirection so it stays correct when
they diverge.

### What is OUTSIDE this container, stated so nobody has to guess

1. **A path with no model at all.** No route over models can see one. That is the MRTR leg, and
   it has its own census - section below, and section 1c of the sweep.
2. **A model reached through a keyword nobody has written yet.** `OUTSIDE_RESPONSE_KEYWORDS` is
   `("response_type", "requested_schema")`. A future framework verb that hands a schema outward
   under a third name is invisible until that name is added. **This is the honest residual, and
   it is the same species as R8-H1 one level further out** - I have narrowed it, not abolished
   it. What I could do about it, I did: the keywords are a container-of-verbs, not a container of
   models, so adding one is a one-line edit at a named constant rather than a re-derivation, and
   `_resolve_outside_responses` goes RED rather than silent if a keyword names a non-model.
3. **Anything outside `src/fast_mcp_jobvite/`.** `tests/` and `scripts/` are not swept. That is
   deliberate: neither receives data from a host.
4. **A model that arrives as a nested field of a swept model.** Route C reads the keyword
   argument, not the transitive type graph. Nothing nests today - `tests/test_server.py`'s
   ADR-0032 arm asserts no input model's schema carries a `"$ref"` - so this is a hole with a
   tripwire in front of it rather than an open one, and the tripwire belongs to somebody else.
5. **A FOURTH enumeration, in another file, which I did not fix.** `tests/test_server.py:316`
   `_input_models()` discovers input models by `pkgutil` over `tools/` AND by
   `attr.endswith("Input")` - R8-H1's container error plus the name filter U14's route B refuses.
   It asserts a different property (ADR-0032's no-`$ref` claim) and may be correctly scoped, but
   nothing says so. **Recorded as task #90 with a suggested fix**, not silently changed.

---

## PROOF THE NEW ROUTE FAILED BEFORE THE FIX

Route C was written and run **before** `ApprovalAnswer` was touched. From the terminal:

```
$ PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest tests/test_arguments_sweep.py -q
...
_ test_every_input_model_carries_the_shared_structural_limits[ApprovalAnswer] __
tests/test_arguments_sweep.py:444: in test_every_input_model_carries_the_shared_structural_limits
    assert issubclass(model, InboundModel), (
E   AssertionError: ApprovalAnswer does not inherit InboundModel, so §2.1's four
E   structural limits do not apply to what its callers send

FAILED tests/test_arguments_sweep.py::test_the_enumeration_is_not_a_wrong_zero
FAILED tests/test_arguments_sweep.py::test_every_input_model_carries_the_shared_structural_limits[ApprovalAnswer]
FAILED tests/test_arguments_sweep.py::test_the_string_field_sweep_covers_what_the_models_actually_declare
======================== 3 failed, 108 passed in 0.89s =========================
PYTEST_EXIT=1
```

Route C sees `ApprovalAnswer` - `6 = len([... , <class 'fast_mcp_jobvite.approval.ApprovalAnswer'>])`
in the same run - and the arm it lands on goes red on the property that was genuinely missing.
Two of those three are bookkeeping the wider container moves (a count and a named exception
list); one is the finding.

**After the fix**: `117 passed` in that file, and the full suite is below.

## THE FIX, AND WHY IT IS NOT A CONTRACT CHANGE

`ApprovalAnswer` now inherits `InboundModel` instead of `BaseModel`
(`src/fast_mcp_jobvite/approval.py`), which is the one §2.1 property it was missing: it already
declared `extra="forbid"` and, since `fd1057a`, `strict=True`. **I did not touch `strict=True` or
`tests/test_approval_strictness.py`**, and I stayed away from the module docstring at the top of
that file, which `r7-fixes` is editing.

It changes no outcome today, and that is the argument for it rather than against it: with one
`bool` field under `strict=True` and extra keys forbidden, every payload the structural limits
would refuse is already refused for another reason. That is exactly the "fail-closed by accident"
that `NestedProbe`'s docstring was written about, and it evaporates the first time this model
grows a `dict` or a `list` field. No contract moves: §2.1's limits are stated for an argument
payload, and applying them to a response this server asked its host for adds a refusal, never an
acceptance. **No ADR raised.** (`check-adr-numbers.py` says `NEXT FREE ADR NUMBER: 0033` across
9 local branches, unused by me.)

---

## THE SEVENTH PATH: THE MRTR LEG, WHICH HAS NO MODEL AT ALL

`resolve_approval` reads `ctx.input_responses` and `_approved_by_conjunction` takes
`content.get("approve")` off a **raw dict**. No model, so no `extra="forbid"`, no `strict=True`,
no structural limits. **Routes A, B and C are blind to it by construction.**

### The decision: no model is introduced there. Here is why that is acceptable.

1. **Its acceptance rule is already the strictest available.** `is True` is applied to the WIRE
   value - which is precisely what `strict=True` was added to `ApprovalAnswer` (R8-H2) to
   reproduce on the other leg. The unsafe direction here was the *modelled* leg, not this one.
   `tests/test_approval_strictness.py` pins the two legs to agree on every plausible answer, so a
   regression on either goes red.
2. **The four structural limits have nothing to bound there.** That code reads one key and
   compares identity: it never recurses, never re-serialises, never stores. A model placed there
   would validate a body the transport has already accepted in full, so the bound that actually
   matters for this path is the **1 MiB body cap at the middleware seat** - ADR-0029 as corrected
   by task #77, built by task #81 - and no model can stand in for it.
3. **Putting a model there is a new contract** - it decides what shape a host response must have
   before this server will read one key out of it - and inventing that inside a fix is what an ADR
   exists to prevent. This path needs no new contract to be safe today.

### What WAS missing, and is now there: the enumeration

Nothing told a reader that this path exists and is outside every route. So the sweep now runs a
**census** (`MODELLESS_INBOUND_READS`): an AST walk over the same package container for every read
of `ctx.input_responses`, each anchored to **the function that performs it** rather than to a line
number, asserted equal to exactly:

```
["fast_mcp_jobvite.approval:resolve_approval"]
```

This is an expected-VALUE list, not a search space - the container is the package and the
selector is an attribute read, so a second modelless path cannot be missed by anyone forgetting
to add it here. It appears, and the assertion goes red. It is an AST census and not a grep on
purpose: `approval.py` mentions `ctx.input_responses` in four places and *reads* it in one, so a
grep answers a different question and answers it wrongly.

---

## MEASUREMENTS, EACH FROM THE TERMINAL, EXIT CODE ON ITS OWN LINE

Floors DERIVED from `ci.yml`, never retyped:

```
$ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
check-suite-floor.sh 782
$ grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml
check-harness-anchors.py --self-check --floor 401
```

| Gate | Result | Exit |
|---|---|---|
| `uv run --frozen pytest -q` | **794 passed, 6 deselected, 0 skipped**, 63.72s | 0 |
| `uv run --frozen ruff check .` | All checks passed | 0 |
| `uv run --frozen ruff format --check .` | 71 files already formatted | 0 |
| `uv run --frozen mypy` | Success: no issues found in 59 source files | 0 |
| `check-harness-anchors.py --self-check --floor 401` | **407 anchors**, all resolve to one hit | 0 |
| `check-harness-anchors-controls.sh` | 9/9 controls fired | 0 |
| `check-u14-arguments-controls.sh` | 20/20 controls fired | 0 |
| `check-u14-arguments-amputation.sh` | **16 rows, 16 anchors applied, 0 vacuous**, 1587 survivors | 0 |
| `check-quickstart.py` | - | 0 |
| `check-coupling.py` / `-controls` / `-sweep` | - | 0 |
| `check-cross-references.py` | - | 0 |
| `check-obligations.py` / `--controls` | - | 0 |
| `check-plan-measurements.py` | - | 0 |
| `check-resweep-verdicts.py` | - | 0 |
| `check-adr-numbers.py` | 32 ADRs, next free 0033 | 0 |
| `check-committed-file-types.py --all` | 322 files, none refused | 0 |
| `check_advisories.py` | - | 0 |

**794 >= the 782 floor, 0 skipped. NEW SUITE FLOOR FOR `ci.yml`: 794.** Anchor count moved
401 -> **407**; the floor is a minimum so the existing 401 stays green, and **407 is the ratchet
if you want it**. `ci.yml` is yours - I changed nothing in it. No new CI step is needed: the six
new amputation rows live in `check-u14-arguments-amputation.sh`, which CI already runs.

### The six new amputation rows, and what killed each

Applied one at a time, anchor asserted unique before mutating, LANDED proved by `cmp` against a
backup taken first, RESTORED proved by `cmp` after. `PYTHONDONTWRITEBYTECODE=1` throughout.

| Row | Amputation | Exit | Killed by |
|---|---|---|---|
| **A11** | route C returns an empty set | 1 | `..._is_not_a_wrong_zero`, `test_route_C_reaches_a_model_route_A_structurally_cannot`, route C's synthetic-module control, the string-field population arm |
| **A12** | route C's container narrows back to `tools/` - **R8-H1 itself** | 1 | the same three, plus the modelless census (it stops seeing `approval.py` at all) |
| **A13** | `extra="forbid"` gone from `ApprovalAnswer` - **R8's surviving mutation, byte for byte** | 1 | `test_every_input_model_forbids_extra_keys_and_is_strict[ApprovalAnswer]`, `test_case7_an_undeclared_argument_key_FAILS_CLOSED[ApprovalAnswer]` |
| **A14** | `strict=True` gone | 1 | `test_every_input_model_forbids_extra_keys_and_is_strict[ApprovalAnswer]` |
| **A15** | `InboundModel` swapped for a plain `BaseModel` | 1 | `test_every_input_model_carries_the_shared_structural_limits[ApprovalAnswer]` |
| **A16** | the modelless census finds nothing | 1 | `test_the_modelless_inbound_paths_are_exactly_the_reasoned_one`, and its own synthetic-module control |

**A13 is the one the brief asked for**: R8's mutation, which left all 768 tests green, now takes
two arms down. **A14 is worth reading twice**: the only thing that catches it inside this file is
the *config* assertion. `test_case7_a_wrongly_typed_argument_FAILS_CLOSED[ApprovalAnswer]` does
NOT catch it, because pydantic's lax mode still refuses `"not_an_int"` for a `bool` - the values
that actually coerce are `"yes"`, `1`, `"on"`, and those live in
`tests/test_approval_strictness.py`, which the harness does not run. The two files are
complementary and neither is redundant.

**A15's anchor is on the IMPORT, not the class statement.** Removing `BaseModel` from
`approval.py`'s imports (ruff F401, once `ApprovalAnswer` stopped using it) meant a row rewriting
the base to `BaseModel` would go red on a `NameError` - red for a reason that measures the
harness rather than the property. It now amputates
`from fast_mcp_jobvite.utils.constraints import InboundModel` to
`from pydantic import BaseModel as InboundModel`, which deletes the behaviour and binds the name.

### Positive controls written for the new machinery

- **Route C** is planted with a synthetic module where the two keywords name *different* models,
  one of them reached through a `X.model_json_schema()` alias, with an `output_schema=` model and
  an entirely unused class that must NOT be picked up. Both directions of the exclude-by-USE rule.
- **`_resolve_outside_responses`** is asserted to go RED on a response type that is not a model
  (`response_type=bool` is legal and would be an inbound path with nothing on it).
- **The census** is planted with a read in a differently-named function, so its one-element
  expected list is not a hand-kept list with extra steps.
- **`test_route_C_reaches_a_model_route_A_structurally_cannot`** exists because R8's literal
  suggestion - "assert route C's set is a subset of the swept set" - is **true by construction**
  once the swept set is their union, and would pass against a route C that found nothing. The
  non-tautological property is that route C reaches outside route A's container, and that is what
  is asserted, without naming the model.

---

## ONE THING FIXED THAT WAS NOT MINE

`uv run --frozen mypy` was **RED at my branch point**. Measured in a pristine worktree at
`5e439cc`, not inferred:

```
tests/test_server.py:308: error: "type" has no attribute "model_json_schema"  [attr-defined]
Found 1 error in 1 file (checked 59 source files)
```

`_input_models()` was annotated `list[tuple[str, type]]`, and a bare `type` has no
`model_json_schema`. The annotation was the defect, not the call. It is now
`type[BaseModel]` and mypy is clean. **The type gate is red on whatever `5e439cc` descends from -
somebody should check main.** Recorded on task #90 alongside the enumeration finding in the same
function.

---

## WHAT I DID NOT VERIFY

1. **Whether `main` is red on mypy.** I measured `5e439cc`, my base, and it is red there. I did
   not fetch or check out `main` to see whether it shares that commit, because the brief says not
   to touch the shared checkout and I had no pinned `main` SHA.
2. **ShellCheck over the modified harness.** `shellcheck` is not installed on this machine
   (`command not found`) and `ci.yml` has no step that runs it over `scripts/` - only
   `actionlint`, which runs it over workflow `run:` blocks. My edits to
   `check-u14-arguments-amputation.sh` are new rows in the existing `amputate` call form and one
   variable, so I expect nothing new, but I have not run the tool and cannot claim it.
3. **Whether `ApprovalAnswer` belongs in `tests/test_server.py`'s ADR-0032 population.** I argued
   above that `requested_schema=` is not the tool-schema path `DereferenceRefsMiddleware`
   rewrites, and I did not measure that middleware. Task #90 carries it.
4. **Whether a real host sends an elicitation payload that the structural limits would now
   refuse.** They can only refuse what `extra="forbid"` plus a strict `bool` already refuses, so I
   believe the answer is no by construction - but "by construction" is an argument, and I did not
   run a live host. R8's own unsettled item 2 (whether `strict=True` breaks a field host) is the
   same question and is still open.
5. **`check-clause-citations.py` and `check-design-citations.py`.** The first needs the
   `evolv-coder-standards` sibling checkout, which a `/tmp` worktree does not have; I did not
   symlink around it. The second is not a gate and I edited no design text.
6. **The coverage floors.** Unchanged since U14 and R8 both declined to read them; I did not read
   them either.

## Worktrees

`/tmp/inbound-baseline` - the pristine worktree at `5e439cc` I used to prove the mypy failure
pre-dates me - **is removed**, verified by `git worktree list`.

`/tmp/inbound-surface-work` **is still there**, and the PREAMBLE asks me to remove it. I have
not, for one reason: it is the directory this process is running in, and removing it under
myself is how a report gets written to a path that no longer exists. Everything is committed on
`fix/inbound-surface`, so nothing is lost by removing it - `git worktree remove
/tmp/inbound-surface-work` when you have read this. Leaving it also means every measurement above
can be re-run as written.
