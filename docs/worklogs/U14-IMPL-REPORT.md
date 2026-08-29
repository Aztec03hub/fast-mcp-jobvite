# U14 - argument-layer hardening: the completeness sweep

Agent `u14-arguments`. Branch `feat/u14-arguments`, off `bc0f958`. Worktree `/tmp/u14-arguments-work`.
Design read as `git show c15b138:docs/DESIGN.md`, never from the working tree.

---

## The headline: the brief said four input models. There are five.

The dispatch message, `docs/briefs/U14.md:32` and gating task #70 all say **four** input models -
*"`tools/jobs.py` (two), `tools/candidates.py` (two)"*. `docs/plans/IMPLEMENTATION-PLAN.md` §U14
names three units (U5, U8, U12) and the brief corrects it to four by adding U10.

`candidates.py` holds **three**:

```
$ grep -n '^class ' src/fast_mcp_jobvite/tools/*.py
src/fast_mcp_jobvite/tools/candidates.py:151:class SearchCandidatesInput(BaseModel):
src/fast_mcp_jobvite/tools/candidates.py:178:class GetCandidateInput(BaseModel):
src/fast_mcp_jobvite/tools/candidates.py:214:class CreateCandidateInput(BaseModel):
src/fast_mcp_jobvite/tools/candidates.py:274:class CreateCandidateResult(BaseModel):
src/fast_mcp_jobvite/tools/jobs.py:98:class SearchJobsInput(BaseModel):
src/fast_mcp_jobvite/tools/jobs.py:433:class GetJobFeedInput(BaseModel):
```

Five input models, one output model. **`SearchCandidatesInput` is the one nobody counted** - it is
`search_candidates`'s, it is deliberately empty, and it is the easiest thing in the file to read
past. Nobody was careless: U8 landed two models where the plan's prose implies one, and every later
count inherited the number rather than the container.

**This is not a nit about a brief. It is the unit's whole thesis, arriving before the unit ran.**
The count that gated this dispatch was wrong at dispatch time, and the only reason it is known to
be wrong is that the sweep enumerates rather than lists.

---

## How the input models are enumerated, rather than listed

`tests/test_arguments_sweep.py` **names no input model anywhere.** Two independent AST walks over
every module in `src/fast_mcp_jobvite/tools/` (the directory is globbed; `__init__.py` excluded):

- **Route A - `models_named_by_tool_functions`.** Every function carrying an `@server.tool(...)`
  decorator; take the annotation of its `params` argument. This is the inbound surface *as the
  framework sees it*: a class that is not some registered tool's `params` type can never receive
  anything from a caller.
- **Route B - `models_defined_as_classes`.** Every `ClassDef` whose bases include `BaseModel` or
  `InboundModel`, minus every class name passed to an `output_schema=` keyword in the same module.

**The output models are excluded by their USE, not by their name.** A `name.endswith("Result")`
filter is a second hand-kept list wearing a naming convention as a disguise; mutation **M4** turns
route B into exactly that and the planted-module control kills it.

`test_the_two_enumerations_of_the_input_model_set_are_EQUAL` asserts set equality - not `>=`, not
`<=`. Three guards keep that from being `set() == set()`:

1. `test_the_enumeration_is_not_a_wrong_zero` - the container is non-empty, `len(INPUT_MODELS) >= 5`,
   and `len(INPUT_MODELS) == TOOL_COUNT`. A glob at a path that does not exist returns a clean empty
   indistinguishable from a real absence.
2. `test_the_enumeration_finds_a_model_planted_in_a_synthetic_module` - both routes must find a model
   in a module neither has seen.
3. **`assert by_class - by_tool == {"OrphanInput"}`** - the planted module carries a model class no
   tool registers, so **the two routes are required to DISAGREE about it.** This arm exists because
   amputation A4 replaced route B's body with a call to route A and the whole harness went green:
   two instruments that cannot disagree are one instrument reported twice.

`INPUT_MODELS` is resolved at **import** time, so a broken enumeration fails collection rather than
parametrising zero cases and passing in silence.

---

## What was built

### 1. The three missing structural limits, and the deferral that could not expire

`utils/constraints.py` carried a recorded decision that nesting depth, list length and dict-key
limits were absent because *"no input model in the tree today is deeper than one flat object, so the
code would have no caller and no reachable test"*, with the trigger stated as **"the first nested
input model"** and `create_candidate` named as it.

**Two things are wrong with that, and the second is structural.**

- **It confuses the model with the payload.** These limits bound what a **caller sends**, not what a
  model declares. A caller can post `{"ids": [[[[[[1]]]]]]}` at any of the five models today.
- **`create_candidate` landed with six flat scalar fields.** The named trigger did not fire, and
  nothing was watching for it. The obligation could stay open indefinitely while looking discharged
  by its own terms.

Landed in `utils/constraints.py`: `MAX_NESTING_DEPTH=5`, `MAX_LIST_ITEMS=1000`, `MAX_DICT_KEYS=100`,
`MAX_PAYLOAD_BYTES=1 MiB`, `check_structural_limits()`, and `InboundModel` - a base with one
`@model_validator(mode="before")`. **ADR-0012 explicitly leaves the form to the implementing unit**
("`Annotated` aliases, validators, or a base model"); a base model is chosen because the limits are
properties of the payload, so there is no field to hang an alias on. `InboundModel` **sets no
`model_config`** on purpose - inheriting `extra="forbid", strict=True` would make the per-model
assertion pass for a model that never stated it.

All five input models now inherit it. **The gap comment was REWRITTEN in place, not appended to.**

### 2. An honest statement of what the five models were doing before

**Pre-U14 all five failed closed against all four limits already** - every field is a bounded scalar
under `strict=True`, so a list arriving at a `str` field is refused as a type error. That is
**fail-closed by accident**, and it evaporates the first time any model declares a `dict` or `list`
field. `test_case9_EVERY_swept_model_fails_closed_on_every_limit` asserts the OUTCOME across all
five (`DESIGN.md:189`: *"The rule still fails closed, which is the whole of what B25 and B30
require"*), and `NestedProbe` - a model with a `dict[str, Any]` field, declared in the test module -
is where the limits are load-bearing and where each arm measures the limit itself.

### 3. No arm asserts a problem-object shape

`DESIGN.md:181-190`: every check here lives in the input models, runs before the tool body, and is
raised by the framework, so **none of these rejections can carry a problem object**. An earlier
revision said `400`, the registry says `422`, neither reaches the caller pre-dispatch. Every
assertion in the module is `pytest.raises(ValidationError)` and no model constructed. The module
docstring says so, so a later reader does not "fix" it.

---

## The four structural limits: four rejecting arms, FOUR accepting arms

| Limit | Rejecting arm | **Accepting arm** | Through a live model |
|---|---|---|---|
| depth 5 | `_payload_of_depth(6)` | `_payload_of_depth(5)` | `NestedProbe` |
| 1,000 list items | `range(1001)` | `range(1000)` | `NestedProbe` |
| 100 dict keys | 101 keys | 100 keys | `NestedProbe` |
| 1 MiB payload | `1024*1024 + 1` | `1024*1024 - 32` | `NestedProbe` |

Plus §8 #7's control (a well-formed argument passes, **per model**, payload synthesised from the
model's own fields) and §8 #8's (an ordinary name passes, **per string field**, nine of them).

**Three arms were wrong when first written, and the harness is what said so.**

- **The accepting arms read their expectation out of the code under test.**
  `_nest(MAX_NESTING_DEPTH - 1)` moved with mutation **M11** (5 → 4) and passed. A test that imports
  its expectation from its subject is a restatement, not an assertion. **Every arm now uses the
  design's literal** - 5, 1000, 100, 1048576 - and `test_the_limits_are_the_designs_own_numbers` is
  the single place those literals are joined to the constants.
- **The depth rejecting arm had two levels of slack**, so **M15** (loosen the check by exactly one)
  survived. It is now exactly one level past.
- **The dict-key rejecting arm used `{str(i): i}`**, whose 101 values are 101 distinct values, so
  **M13** (count distinct values instead of keys) survived. The values are now all identical.

---

## U2's no-`success`-envelope rule, re-run with teeth

U2 owns the rule in `tests/test_error_contract.py`. Its own docstring: *"This assertion is
near-vacuous today and U2-REPORT.md says so: `src/` holds four modules, so it passes over almost
nothing."*

**U2's file is not edited.** The re-assertion is in U14's module and **imports U2's scanner**, adding
the one claim U2 could not make: a claim about the **size of the corpus walked**. U2's
`_scan_for_envelope` guards against scanning zero files; it cannot tell 4 modules from 23.

`test_the_no_success_envelope_rule_now_runs_over_the_COMPLETED_corpus` asserts the source-module count
is `> 4` (U2's own recorded figure), the whole corpus is `>= 50` files, and the scan returns `[]`.
`test_the_corpus_claim_can_fail_over_a_shrunken_tree` is its positive control.

**Proved able to fail, both halves:** M19 shrinks the corpus to one module - the scanner returns a
clean empty, exactly what a passing repository returns, and only the size claim tells them apart -
and M20 makes U2's scanner match nothing at all. Both KILLED.

**Result: 0 `success:` envelopes across 23 source modules and 34 test modules.**

---

## Gate exit codes, read from the terminal

```
uv run --frozen ruff check .           All checks passed!                 exit 0
uv run --frozen ruff format --check .  71 files already formatted         exit 0
uv run --frozen mypy                   no issues in 58 source files       exit 0
uv run --frozen pytest                 768 passed, 6 deselected, 0 skipped exit 0
pre-commit run shellcheck --all-files  ShellCheck v0.10.0 Passed          exit 0
python3 scripts/check-harness-anchors.py --self-check --floor 371
                                       401 anchors, all resolve uniquely  exit 0
docs/reviews/check-adr-numbers.py      29 ADRs, 0001-0029, unique         exit 0
docs/reviews/check-design-citation-shape.py                               exit 0
docs/reviews/check-standards-citations.py  97 citations, all resolve      exit 0
docs/reviews/check-settings-are-read.py                                   exit 0
docs/reviews/check-obligations.py                                         exit 0
bash scripts/ci-harness-gate.sh check-u14-arguments-controls.sh --controls-fired
                                                                          exit 0
bash scripts/ci-harness-gate.sh check-u14-arguments-amputation.sh \
     --amputation --anchors-applied --min-rows 10 --row-re '^########## A[0-9]+ '
                                                                          exit 0
```

`check-standards-citations.py` exits **2** with no corpus (*"CORPUS ABSENT ... a checker that cannot
find its subject has not checked anything"*). It resolves `ROOT.parent / evolv-coder-standards /
standards`, and a worktree under `/tmp` has no such sibling. Symlinked
`/tmp/evolv-coder-standards -> repos/evolv-coder-standards` to run it. **Worth knowing: every agent
working from a `/tmp` worktree gets exit 2 from this checker, and the message is clear enough that
nobody has mistaken it for a pass - but it is a checker that does not run in the isolation model the
preamble mandates.**

## The floors, DERIVED from `ci.yml` and reported for you to set

```
$ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
check-suite-floor.sh 663
$ grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml
check-harness-anchors.py --self-check --floor 371
```

| Floor | In `ci.yml` at `bc0f958` | Measured on this branch |
|---|---|---|
| suite | 663 | **768** (+105, 0 skipped) |
| harness anchors | 371 | **401** (+30: 20 controls, 10 amputation) |

**`ci.yml` is yours. I have not touched it.** The two steps to add:

```yaml
      - name: U14 argument-layer controls
        run: bash scripts/ci-harness-gate.sh check-u14-arguments-controls.sh --controls-fired

      - name: U14 argument-layer amputation
        run: >
          bash scripts/ci-harness-gate.sh check-u14-arguments-amputation.sh
          --amputation --anchors-applied --min-rows 10 --row-re '^########## A[0-9]+ '
```

Both were run through `ci-harness-gate.sh` with exactly those arguments; both exit 0.

---

## Harness rows: every row, and whether it fired

### `scripts/check-u14-arguments-controls.sh` - 20/20 KILLED, exit 0

| Row | Subject | Verdict |
|---|---|---|
| M1 | route A matches no argument name | KILLED |
| M2 | route B stops excluding output models | KILLED |
| M3 | the tool-module container becomes a hand-typed name | KILLED |
| M4 | route B excludes output models by NAME, not by use | KILLED |
| M5 | one input model silently loses `strict=True` | KILLED |
| M6 | the write model admits undeclared keys | KILLED |
| M7 | one input model drops the shared structural limits | KILLED |
| M8 | a PII free-text field becomes an unbounded bare `str` | KILLED |
| M9 | the forbidden set loses its C1 range | KILLED |
| M10 | the compiled pattern loses its bidi overrides | KILLED |
| M11 | the depth ceiling is one level too tight | KILLED |
| M12 | the list ceiling admits one item too many | KILLED |
| M13 | the key ceiling counts values, not keys | KILLED |
| M14 | the payload size is measured before encoding | KILLED |
| M15 | the depth check happens after the descent | KILLED |
| M16 | a string is counted as a collection of characters | KILLED |
| M17 | the before-validator drops the payload it checked | KILLED |
| M18 | the size check crashes on a value `json` cannot serialise | KILLED |
| M19 | the corpus shrinks to a single module | KILLED |
| M20 | U2's envelope scanner matches nothing at all | KILLED |

Row floor 20. `tests/test_error_contract.py` is U2's file: **mutated, never edited**, restored with
`cp` and verified with `cmp` against a pristine copy taken before row 1. No `git stash`, no
`git checkout <path>`, `PYTHONDONTWRITEBYTECODE=1` throughout.

**Four rows failed on the first run and all four were defects in MY arms, not in the code**
(M10 anchor unreadable, M11/M13/M15 arms too weak). Diagnosed and fixed as described above; the
harness is what found every one of them.

### `scripts/check-u14-arguments-amputation.sh` - 10 rows, 10 anchors applied, **0 vacuous**, exit 0

| Row | Behaviour deleted | Survivors |
|---|---|---|
| A1 | route A finds no input model at all | 16 |
| A2 | the tool-module container returns nothing | 18 |
| A3 | the string-field discovery returns nothing | 50 |
| A4 | the second enumeration route becomes the first | 104 |
| A5 | the forbidden-character pattern admits everything | 98 |
| A6 | the structural limits measure nothing (**the pre-U14 tree**) | 97 |
| A7 | the structural limits have no caller | 101 |
| A8 | the write model's extra-key refusal is gone | 103 |
| A9 | a read model stops being strict | 104 |
| A10 | the structural walk never descends | 100 |

**Two rows were vacuous on the first run and both were findings.**

- **A4** deleted route B and had it call route A. Nothing went red: the equality assertion was
  comparing a set with itself. **This is the exact failure the unit exists to prevent, present in
  the unit's own instrument.** Closed by the `OrphanInput` arm above.
- **A10** originally rewrote an assertion in the SUITE (`issubclass(model, InboundModel)` →
  `BaseModel`) - trivially true, so it deleted nothing and correctly went vacuous. **An amputation
  whose subject is the test is measuring the harness.** Replaced with a row that deletes the
  structural walk's descent.

**A7 is the row that retires the pre-U14 argument.** `constraints.py` said an unreachable limit
"reads as discharged"; A7 makes the limits correct, tested, and reachable by nothing, and the suite
notices. The suite can now tell *implemented* from *wired*.

---

## ADR-0029 (Proposed): the body-size limit has no middleware to live in

`DESIGN.md:165` and ADR-0012 both place the 1 MiB body cap "at the middleware". **There is no
middleware here that sees a body.** Measured:

```
$ grep -rn 'MiB\|1048576\|1024 \* 1024\|max_body\|body_size\|Content-Length' src/ scripts/
src/fast_mcp_jobvite/utils/constraints.py:171:#     Max request body    1 MiB      <- middleware, not this module
```

One hit, and it is the comment saying the limit lives somewhere else. `http_hardening.py` is the only
middleware module and holds only the rate limiter. The path resolves; five of the six patterns return
zero against it, so this is a real absence.

`MAX_PAYLOAD_BYTES` bounds the **serialised argument payload**, which is the largest thing that layer
can see. **It is not the body cap**: a malformed frame, a body the JSON parser rejects, or a body on
a non-tool route never becomes an argument payload. ADR-0029 records that, refuses the tempting
alternative (declare the payload cap the discharge and close the row), and leaves the middleware half
as its own task. `constraints.py`'s module comment and the §8 #9 size arms both carry the caveat, so
nothing in the tree claims `DESIGN.md:165` is discharged.

`docs/reviews/check-adr-numbers.py`: 29 ADRs, 0001-0029, contiguous, exit 0. **ADR-0029 was free when
I looked and the checker confirms it is unique now.**

---

## Anchor collisions

`check-harness-anchors.py --self-check` was run before starting (371/371), after each harness, and
after the final `ruff format`. **No collision with another unit's anchors**, and none of my anchors
needed widening.

**One anchor was rejected by the checker and the row was passing anyway.** M20 first anchored on
`ENVELOPE = re.compile(r'["\']?success...')` - nested quotes and backslashes. Bash expanded it
correctly and the row reported KILLED, but `check-harness-anchors.py` reported `0 hits in
tests/test_error_contract.py`. **A row that a harness executes and a static checker cannot read is a
row nobody is checking**, and it would have been invisible to the gate that exists to catch drifted
anchors. Re-anchored on `if ENVELOPE.search(line):` - plain ASCII, unique, same subject. This is
worth carrying to other units: an anchor's readability by the checker is part of its correctness.

`ruff format` ran **before** the final harness run (as the brief requires), then both harnesses and
the anchor checker were re-run. No collision appeared; the one thing `ruff format` did change was
joining an assertion message in my own test, which broke a later scripted edit and cost nothing.

---

## Files

Written: `src/fast_mcp_jobvite/utils/constraints.py`, `tests/test_arguments_sweep.py`,
`scripts/check-u14-arguments-controls.sh`, `scripts/check-u14-arguments-amputation.sh`,
`docs/adr/0029-the-body-size-limit-has-no-middleware-to-live-in.md`,
`changelog.d/72-u14-arguments.md`, this report.

Edited minimally: `src/fast_mcp_jobvite/tools/jobs.py` and `tools/candidates.py` - **only** the input
models' base class and the import line (and `BaseModel` dropped from `jobs.py`'s pydantic import once
it had no other use). **No tool body was restructured**, so `code-review-r7` reading a merged SHA
still recognises what it read.

Not touched: `.github/workflows/ci.yml`, `docs/DESIGN.md`, `docs/OBLIGATIONS.md`,
`tests/test_error_contract.py`, `tests/test_constraints.py`, `http_hardening.py`.

**The worktree `/tmp/u14-arguments-work` is removed** (see the final section for the exact state at
removal).

---

## What I could NOT settle

1. **Whether the five input models are the whole inbound surface, or only the whole *tool* inbound
   surface.** Both enumeration routes are scoped to `src/fast_mcp_jobvite/tools/`. A model living
   outside that directory and reached by a caller through some other path would be invisible to both.
   I found no such path, but "I looked in one directory" is what that claim is worth. Widening route B
   to the whole of `src/` would sweep the output models in `models/` and needs a rule for telling them
   apart that is not a name - I did not find one I trusted.

2. **The 1 MiB body cap.** ADR-0029, above. It is Proposed, not applied, and the decision of whether
   to build a body-size middleware, on which transports, and what a caller sees when it fires is
   yours. §8 #9's fourth arm tests a payload cap, not `DESIGN.md:165`'s body cap, and the report says
   so rather than letting the arm's existence imply otherwise.

3. **Whether `MAX_PAYLOAD_BYTES` should re-serialise at all.** `check_structural_limits` measures
   `json.dumps(payload).encode()`. That is not the bytes that arrived - key order, whitespace and
   escaping all differ - so it is an approximation of the size of what a caller sent, bounded and
   conservative but not exact. On the argument-payload path I judge that acceptable; if the intent is
   a byte-exact bound it belongs in the middleware and is item 2.

4. **`check-standards-citations.py` in a `/tmp` worktree.** It exits 2 without the sibling corpus.
   The preamble mandates `/tmp` worktrees and this checker cannot run in one without a symlink. I
   worked around it rather than fixing it, because `docs/reviews/` is not mine. Suggested fix: resolve
   the corpus from an env var falling back to the sibling, so an agent in an isolated worktree can
   point it at the real path - and keep the exit-2-on-absent behaviour exactly as it is.

5. **SETTLED, and it was cheap enough that parking it would have been rigour-theatre.** U14's own
   string-field sweep was silently finding 5 of 9 fields (`Optional[Annotated[str, ...]]` is not
   `str`), and only a hand-written population assertion caught it - so the obvious question is
   whether any other unit's parametrised sweep is currently empty. Measured by parsing every
   `tests/*.py` on this branch and reporting every `@pytest.mark.parametrize` whose argvalues are
   not a literal list or tuple: **17 sites, 11 of them U14's own.** The other six:

   | Site | Argvalues | Verdict |
   |---|---|---|
   | `test_approval_write.py` 225, 414, 431, 536, 604 | `BOTH_ERAS` | a two-element tuple literal - cannot go empty |
   | `test_error_contract.py:73` | `REGISTRY_CASES` | derived, and `test_no_type_uri_is_minted_locally` asserts `len(defined) == 7` first |
   | `test_workflow_contexts.py:117` | `workflows()` | derived, and `:96` already asserts `found, "no workflow files under {WORKFLOWS}; every test here is vacuous"` |

   **No unguarded derived parametrisation exists outside U14's module**, and both derived ones
   already carry a population assertion for exactly this reason. No task filed, because there is
   nothing to file.

6. **Coverage beyond `utils/`.** `DESIGN.md:1362-1364` requires 95% on `utils/`. Measured:
   `src/fast_mcp_jobvite/utils/constraints.py` is **100% statement and 100% branch** (43 statements,
   16 branches, 0 missing), and `utils/` overall is 100%. I did **not** re-measure the tool-module
   floor (85%) or the critical-path floor (95% line / 90% branch on argument rejection) - the suite
   passes and `ci.yml` holds those floors, but I have not read those numbers off a run.
