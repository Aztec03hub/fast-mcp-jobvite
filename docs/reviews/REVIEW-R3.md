# REVIEW-R3 - a fresh round over the seven merged units

**Reviewer:** `code-review-r3`. **Base SHA:** `61d1171`. **Branch:** `review/r3`.
**Frozen design read as:** `git show c15b138:docs/DESIGN.md`.
**Worktree:** `/tmp/r3-work` (removed at the end - see the closing section).

This is a **re-derivation, not a reconstruction**. I did not read task #4's summary of round 1
before looking, and no finding below is carried over from it. `L6` (nothing floored the test count)
is excluded by the brief and is not re-reported.

Findings are ranked by severity. Every one carries a suggested fix.

---

## Summary

| ID | Sev | Subject | Status |
|----|-----|---------|--------|
| R3-H1 | **High** | `mirror.yml` has **never once run**: 117 runs, 117 failures, 0 jobs created | Proved from CI history |
| R3-M1 | Medium | `JOBVITE_HTTP_TOKENS` accepts an **empty-string bearer token** at boot | Proved at boot |
| R3-M2 | Medium | `check-u1-pid1-shutdown.sh` verifies PID-1 on the `http` arm only | Proved by read |
| R3-L1 | Low | `TOOL_REQUIREMENTS` may silently under-require a tool added to `KNOWN_TOOLS` | Latent, unguarded |
| R3-L2 | Low | `_token_map_problems` accepts a token mapped to **zero** scopes | Proved |
| R3-L3 | Low | `AuditEvent.to_record`'s `optional` dict is a hand-kept second list of fields | Latent, unguarded |
| R3-L4 | Low | The coverage step's "deferred to U1" comments are stale in two files | Proved by measurement |
| R3-L5 | Low | `test_server.py:69`'s source assertion survives commenting the line out | Proved |
| R3-N1 | Nit | Two tests share a name across files while belonging to different pairs | Confirmed |

Section "What I checked and did NOT find a defect in" records the seven candidates that came back
clean, because a reviewer who reports only hits gives no information about coverage.

---

## R3-H1 (High) - the mirror workflow has never mirrored anything, 117 runs, 117 failures

**This finding is outside the brief's stated scope, and that is the point.** The brief scopes me to
the seven units "plus `scripts/`, `docs/reviews/`, `ci.yml` and the suite". `mirror.yml` is in none
of those. It is also the exact file this repository has already been burned by, and says so in its
own test suite - `tests/test_workflow_pins.py:9-12`:

> **Why the miss was structural rather than careless.** The implementation plan's shared-file table
> named `.github/workflows/ci.yml` and nothing else, so `mirror.yml` and `pr-title.yml` were owned
> by nobody and read by nobody. A rule naming one file in a directory selects for the files it does
> not name.

That lesson was applied at the **pin** axis. The same file still carries an unread defect at the
**logic** axis, and a second scope line that names `ci.yml` and not the directory is what let it
stay there.

**Evidence.** `.github/workflows/mirror.yml:25` -

```
25	    if: ${{ secrets.MIRROR_TOKEN != '' }}
```

The `secrets` context is not available in a job-level `if:`. GitHub's context-availability table
allows `github`, `needs`, `vars` and `inputs` there and not `secrets`, so the expression fails to
evaluate and the run dies before any job is scheduled.

**Measured, not inferred.** Read from the repository's own Actions history:

```
$ gh run list --workflow=mirror.yml --limit 200 --json conclusion --jq '.[].conclusion' | sort | uniq -c
    117 failure
$ gh run list --workflow=mirror.yml --limit 200 --json conclusion --jq 'length'
117
```

**117 runs. 117 failures. Zero successes.** And the runs contain no jobs at all:

```
$ gh api repos/evolvconsulting/fast-mcp-jobvite/actions/runs/33235212551/jobs
{"total_count":0,"jobs":[]}
```

`total_count: 0` with a `failure` conclusion and a 0s duration is the signature of a workflow that
failed at **expression evaluation**: the run was created, the expression could not be resolved, and
no runner was ever scheduled. Every push since `7a95a38` ("Host on evolvconsulting with an automatic
mirror to the personal fork") has failed this way.

**The failure it produces.** The mirror described at `mirror.yml:3-8` does not exist. Every push
that does not originate from the maintainer's machine - "web edits, other maintainers, merged PRs",
the precise cases the file says it covers - has never reached `Aztec03hub/fast-mcp-jobvite`. The
comment at `:7-8` says the job "is inert until the repository defines a `MIRROR_TOKEN` secret"; it is
in fact inert unconditionally, and the two states are indistinguishable from the outside, which is
why 117 red runs went unread.

**Alternative hypothesis, checked.** Line 25 is the only expression in the file evaluated outside a
step: `on:`, `concurrency.group` (a literal), and `permissions` are all static, and
`${{ secrets.MIRROR_TOKEN }}` at `:34` is inside a step `env:`, where the context *is* available.
So the `if:` is the only candidate.

**Suggested fix.** Move the emptiness test into the step, where `secrets` is legal, and drop the
job-level `if:` entirely:

```yaml
jobs:
  mirror:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0

      - name: Push to mirror
        env:
          MIRROR_TOKEN: ${{ secrets.MIRROR_TOKEN }}
        run: |
          set -euo pipefail
          if [ -z "${MIRROR_TOKEN:-}" ]; then
            echo "MIRROR_TOKEN is not defined; nothing to mirror."
            exit 0
          fi
          git push --prune --force \
            "https://x-access-token:${MIRROR_TOKEN}@github.com/Aztec03hub/fast-mcp-jobvite.git" \
            "+refs/remotes/origin/*:refs/heads/*" "+refs/tags/*:refs/tags/*"
```

This preserves the intended "inert without the secret" behaviour while keeping the run **green**, so
a future real failure is visible instead of being the 118th red in a row.

**And add the guard, or this recurs at a third axis.** The pins test already walks the directory;
nothing evaluates the workflows. Either install `actionlint` as a CI step (it flags
`secrets`-in-`if` directly, and no workflow linting exists today - `grep -n "actionlint\|yamllint"
.github/workflows/ci.yml` returns nothing), or add to `tests/test_workflow_pins.py`:

```python
def test_no_job_level_if_reads_the_secrets_context() -> None:
    """`secrets` is unavailable in `jobs.<id>.if`; the expression never evaluates."""
    offenders = [
        f"{p.name}:{n}" for p in sorted(WORKFLOWS.glob("*.yml"))
        for n, line in enumerate(p.read_text().splitlines(), 1)
        if re.match(r"\s*if:", line) and "secrets." in line
    ]
    assert not offenders, f"job-level `if:` reading secrets: {offenders}"
```

I would take `actionlint`: it is the version that catches the case nobody thought of, which is the
whole subject of `test_workflow_pins.py`'s docstring.

---

## R3-M1 (Medium) - an empty-string bearer token passes every boot refusal

**Evidence.** `src/fast_mcp_jobvite/config.py:375` -

```
375	    for scopes in parsed.values():
```

`_token_map_problems` iterates `parsed.values()` and never examines a single **key**. The keys are
the bearer tokens. The function validates that the map is a non-empty object (`config.py:370`) and
that every value is a list of strings (`config.py:376-382`), and stops there.

**Proved against the shipped code**, `load_settings()` with a clean environment:

```
$ JOBVITE_MCP_TRANSPORT=http JOBVITE_MCP_HOST=127.0.0.1 JOBVITE_TOOLS=search_jobs \
  JOBVITE_API_KEY=k JOBVITE_API_SECRET=s \
  JOBVITE_HTTP_TOKENS='{"": ["jobs:read"]}' python -c 'from fast_mcp_jobvite.config import load_settings; ...'
BOOT ACCEPTED. transport= http
token map keys = ['']
```

A whitespace-only key (`{"   ": ["jobs:read"]}`) is accepted the same way.

**Why it is a defect.** `DESIGN.md:828-829` defines the value as "a JSON object mapping each
**bearer token** to the scopes it holds". The empty string is not a bearer token. `config.py:9-10`
states the module's own rule as "fail closed, loudly, before serving anything", and `config.py:19-20`
justifies the unset-tokens refusal as "The alternative is an open server". A map whose only key is
the empty string is the same condition wearing a different shape: it satisfies the
"non-empty object" check while holding no usable credential.

**Honest bound on the impact.** `StaticTokenVerifier` is **not wired yet** - `grep -rn
"StaticTokenVerifier\|auth=" src/` returns nothing, U9 owns it. So this is today a
**config-validation gap, not a live authentication bypass**, and I am not claiming otherwise.
It matters now because the refusal is specified as a boot-time one and boot is exactly where this
value is checked; the gap is cheapest to close before the verifier lands on top of it.

**Suggested fix.** In `_token_map_problems`, before the value loop:

```python
    if any(not token.strip() for token in parsed):
        return [
            "JOBVITE_HTTP_TOKENS maps an empty or whitespace-only bearer token; "
            "every key must be a usable token"
        ]
```

Keep the existing discipline of `config.py:356-358`: the message must not echo the key. Pair it with
a `test_config.py` arm for `{"": [...]}` and one for `{"   ": [...]}`, asserting
`ConfigurationError` and asserting the message does **not** contain the raw value.

---

## R3-M2 (Medium) - the PID-1 harness proves PID-1 on one arm of two

**Evidence.** `scripts/check-u1-pid1-shutdown.sh:128-131` -

```
128	  if [ "$transport" = "http" ]; then
129	    printf '%s' "$logs" | grep -q 'process \[1\]' || {
130	      echo "    FAIL: no 'Started server process [1]' in the log - this was NOT pid 1"; FAILED=1; }
131	  fi
```

The PID-1 assertion is inside an `http`-only branch, because it keys off a uvicorn log line
(`Started server process [1]`) that the stdio arm never emits.

The script's own headline claim is not scoped that way. `scripts/check-u1-pid1-shutdown.sh:2-3`:

> `# PID 1 receives SIGTERM, the lifespan tears down, and the process exits inside the`
> `# grace period - on BOTH transports.`

and `:14` - "It **DOES** put the interpreter at PID 1."

**The failure it produces.** The `stdio` arm asserts only that the marker reached `closed` and that
`docker stop` returned inside the grace period. Both of those hold for a process that is **not**
PID 1 - for instance if a future edit adds `--init`, switches the image to one with an entrypoint
shim, or wraps the command in `sh -c`. The arm would stay green while testing a different thing
from the one the file is named for. This is shape 3 from the brief at the file level: the name is a
claim about the body, and for `stdio` the body does not make it.

**Corroborating read.** `tests/boot_process.py:27-52` - `MARKER_ENTRY` writes `opened` and `closed`
and never records a PID, so nothing downstream of the shared entry can recover it either.

**Suggested fix.** Make the assertion transport-independent by putting the PID in the marker, at the
one source of truth the script already deliberately shares (`check-u1-pid1-shutdown.sh:58-60`). In
`tests/boot_process.py`'s `MARKER_ENTRY`, change the open write to:

```python
        fh.write(f"opened pid={os.getpid()}\\n")
```

(with `import os` added), then in the script replace the `http`-only block with an unconditional:

```sh
  grep -q 'pid=1' "$marker" || {
    echo "    FAIL: the entry was not pid 1"; FAILED=1; }
```

That also removes the dependency on a uvicorn log string, which is a third-party format this
project does not control. Note `boot_process.py` is imported by the in-process U1 tests too, so the
`opened` substring check at `boot_process.py:150` keeps working unchanged (`"opened" in ...`).

---

## R3-L1 (Low) - a tool added to `KNOWN_TOOLS` and forgotten in `TOOL_REQUIREMENTS` requires nothing

**Evidence.** `src/fast_mcp_jobvite/config.py:275` -

```
275	            for field in TOOL_REQUIREMENTS.get(tool, ())
```

`missing_for` resolves an unlisted tool to the empty tuple, so it reports **no** missing variables,
so `_check_required_variables` (`config.py:316-322`) appends no refusal and the tool boots with no
credential requirement at all. This is the brief's shape 6 (a rule that NAMES its members) sitting
directly on top of shape 7 (the fail-closed branch fails open on empty).

**Measured today: the map is complete**, so this is latent rather than live -

```
KNOWN_TOOLS - TOOL_REQUIREMENTS = set()
coverage equal today: True
```

**Why report a latent one.** The invariant is unguarded. `tests/test_config.py:472-477` is the test
that looks like it covers this and does not:

```
472	def test_the_tool_names_are_the_five_of_the_design() -> None:
473	    """The allow-list is the design's tool surface, not a superset."""
474	    design = (REPO_ROOT / "docs" / "DESIGN.md").read_text()
475	    for tool in KNOWN_TOOLS:
476	        assert f"`{tool}`" in design
477	    assert len(KNOWN_TOOLS) == 5
```

It checks `KNOWN_TOOLS` against the **design prose** and its own cardinality. It says nothing about
`TOOL_REQUIREMENTS`. U5 (`search_jobs`) and the remaining tool units are the changes that would
exercise this.

**Suggested fix.** Two lines, in `tests/test_config.py`:

```python
def test_every_known_tool_declares_its_required_variables() -> None:
    """An unlisted tool would boot requiring no credential at all."""
    assert set(TOOL_REQUIREMENTS) == set(KNOWN_TOOLS)
```

Optionally harden the source too, by replacing `.get(tool, ())` with `TOOL_REQUIREMENTS[tool]` so
the omission is a `KeyError` at boot rather than a silent pass - the module's stated direction is
"fail closed, loudly" (`config.py:9-10`).

---

## R3-L2 (Low) - a token mapped to zero scopes is accepted

**Evidence.** `src/fast_mcp_jobvite/config.py:375-382`. `[]` is a `list`, and `all(...)` over an
empty list is `True`, so `{"tok": []}` produces no refusal. Proved:

```
'{"tok": []}' -> refusals: []
```

**The failure it produces.** A token that authenticates and carries no scope. Under the
`require_scopes` model of `DESIGN.md:835` this fails closed at authorisation, so it is not a
privilege hole - it is a deployment that starts, accepts a bearer token, and then denies every tool
call, which is the "green start-up having done less than the operator asked" condition
`config.py:16-17` already refuses in the `JOBVITE_TOOLS` case. Reporting it as Low for that reason,
not as a security issue.

**Suggested fix.** Extend the existing value check in the same `return`:

```python
        if not isinstance(scopes, list) or not scopes or not all(
            isinstance(scope, str) and scope.strip() for scope in scopes
        ):
```

and widen the message to "a non-empty list of scope strings".

---

## R3-L3 (Low) - `to_record`'s optional-field list is a second hand-kept enumeration

**Evidence.** `src/fast_mcp_jobvite/audit.py:186-194` names six optional fields in a dict literal.
`AuditEvent` is a dataclass (`audit.py:134-159`); its fields are the container, and the literal is
an allow-list over that container. A field added to the dataclass and not to the literal is simply
absent from every audit record, silently - the record still validates, still parses, still looks
well-formed. That is the brief's shape 6, and `audit.py:34-37` shows the project already reasoning
about "a field that looks like a join and is not one".

Nothing enumerates the container. `grep -rn "dataclasses.fields" tests/` returns nothing.

**Suggested fix.** In `tests/test_audit.py`, assert the two lists agree:

```python
def test_every_event_field_reaches_the_record() -> None:
    """A field added to AuditEvent and not to to_record vanishes silently."""
    import dataclasses
    event = AuditEvent(tool_name="t", request_id="r", transport=Transport.HTTP,
                       client_id="c", trace_id="a" * 32, span_id="b" * 16,
                       approval_state="s", approval_mechanism="m")
    emitted = set(event.to_record())
    declared = {f.name for f in dataclasses.fields(event)} - {"started_at"}
    assert declared - emitted == set(), f"fields never recorded: {declared - emitted}"
```

`started_at` is excluded deliberately: it is the input to `latency_ms`, not a wire field.

---

## R3-L4 (Low) - the coverage gate is live, and two files still say it is deferred

**Evidence.** `.github/workflows/ci.yml:32-33`, inside the header's `DEFERRED with an owning unit`
list:

```
32	#     coverage floors -> U1 (src/fast_mcp_jobvite holds only __init__.py, so a
33	#       coverage run reports "No data collected" or a vacuous 100%)
```

and `pyproject.toml:155-160`:

```
155	# NOT wired into addopts, and the CI coverage step is commented out with a U1
156	# reference, for the same reason the plan gives for the pip-audit step
157	# (IMPLEMENTATION-PLAN.md:206-211): src/fast_mcp_jobvite holds only __init__.py
158	# today, so a coverage run here reports either "No data collected" (red from the
159	# first run) or a vacuous 100% over an empty package. U1 lands the first real
160	# module and turns the step on.
```

**All three factual claims are false at `61d1171`:**

1. The CI step is **not** commented out. `ci.yml:655-656` -
   `- name: Coverage` / `run: uv run --frozen pytest --cov --cov-report=term-missing`.
2. The package does **not** hold only `__init__.py`. It holds eight modules and 515 statements.
3. The run is neither "No data collected" nor a vacuous 100%. **Measured** -

```
TOTAL                                               515     33    100      9    93%
Required test coverage of 80.0% reached. Total coverage: 92.85%
====================== 333 passed, 2 deselected in 23.10s ======================
EXIT=0
```

**Why this is worth a finding rather than a shrug.** The same comment block has already produced
this exact defect once, and says so five lines above, at `ci.yml:21-24`:

> `scripts/check_advisories.py -> LANDED by U11 (f4f69f9). The step runs and enforces the expiry`
> `half. This entry stayed here saying "the script does not exist" after it did, which U11 flagged`
> `and could not fix`

So the `DEFERRED` list is a structure that has now gone stale twice in the same way. A reader
consulting `ci.yml`'s header to learn what is enforced is told coverage is not, when it is - and the
next reader to act on that belief may "turn the step on" a second time or, worse, treat the 80%
floor as unenforced when planning a change.

**Suggested fix.** Delete both entries and state the enforcement where it is true. In `ci.yml`
replace lines 32-33 with nothing (the list is for deferrals, and this is not one), and replace
`pyproject.toml:155-160` with:

```
# Wired: `ci.yml`'s Coverage step runs `pytest --cov`, and `fail_under` below is
# the floor it enforces. --cov-fail-under is deliberately NOT passed there, so the
# floor lives in this file alone - see ci.yml:651-654.
```

**And close the class, not the instance.** Both stale entries are of the form "X is deferred to unit
U" where U has since merged. That is checkable: `check-plan-measurements.py` already reproduces plan
measurements and is wired into CI. Add an assertion that no `DEFERRED`/`-> U<n>` entry in `ci.yml`'s
header names a unit that appears in `CHANGELOG.md`/`changelog.d/` as landed. Without it, this recurs
at the third entry - `fastmcp inspect capability-drift diff -> U1` (`ci.yml:34-37`) is already
half-stale: the step exists at `ci.yml:631-643` and is named "Capability drift report", though it
genuinely still performs no diff, so I am not counting it as a fourth false claim.

---

## R3-L5 (Low) - the `mask_error_details` source guard survives commenting the line out

**Evidence.** `tests/test_server.py:61-69` -

```
61	    server = build_server(_settings())
62	    assert server._mask_error_details is True
...
69	    assert "mask_error_details=True" in source
```

The docstring at `tests/test_server.py:56-59` states precisely why line 69 exists:

> Asserted on the built instance AND on the source, because **a framework whose default happened to
> be True would satisfy the first alone** - and the point of this case is that a dependency bump must
> not be able to change it silently.

**The failure it produces.** Line 69 is a substring match over the raw file, so it passes on a
commented-out line. Proved:

```
as shipped       -> "mask_error_details=True" in source == True
commented out    -> "mask_error_details=True" in source == True
```

Line 62 covers the omission **today**, because the framework default is currently `False` - measured:

```
FastMCP.__init__ mask_error_details param: mask_error_details: 'bool | None' = None
omitted  -> _mask_error_details = False
explicit -> _mask_error_details = True
```

So the pair holds right now. But line 62 is exactly the assertion the docstring says is
insufficient in the scenario line 69 was written for. **In the one world where line 69 is
load-bearing - a dependency bump flips the default to True - line 62 passes on the default and line
69 passes on a comment, and `server.py` could carry the setting commented out with both green.**
The guard is inoperative precisely in its own stated threat model.

**Suggested fix.** Assert on the parsed source rather than the text, so a comment cannot satisfy it:

```python
    import ast
    tree = ast.parse(source)
    kwargs = [
        kw
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        for kw in node.keywords
        if kw.arg == "mask_error_details"
    ]
    assert kwargs, "mask_error_details is not passed in server.py at all"
    assert all(isinstance(k.value, ast.Constant) and k.value.value is True for k in kwargs)
```

That keeps the property the docstring actually wants - the value is *stated in our source* - and is
immune to both comments and string reflow. The same shape applies to `tests/test_correlation.py:48`
(`assert "request_id_var: ContextVar[str | None]" in source`), which is additionally brittle to
whitespace and would break on a reformat that changes nothing semantically; an `ast` check for a
module-level assignment named `request_id_var` is the durable form.

---

## R3-N1 (Nit) - two tests share a name across modules and belong to different pairs

**Evidence.** `tests/test_config.py:319` and `tests/test_boot.py:54` both define
`test_the_default_loopback_bind_starts`. Both are collected - `tests/__init__.py` exists, so the
modules are a package and the basenames do not collide - so this is **not** a shadowing bug and
nothing is silently skipped (my 333-passed run includes both).

It is still worth one line, because the docstrings make them read as one pair when they are two:

- `tests/test_boot.py:55` - `"""Positive control 1 of 2 (DESIGN.md:1323, IMPLEMENTATION-PLAN.md:504)."""`
- `tests/test_config.py:320` - `"""Positive control 2 of 2 for the refusal."""`

A reader grepping the name finds "1 of 2" and "2 of 2" under one identifier and reasonably concludes
they are the matched pair. They are not: `test_boot.py`'s partner is
`test_off_loopback_with_the_assertion_declared_starts` (`test_boot.py:72`, the real-process pair),
and `test_config.py`'s partner is the in-process validator pair.

**Suggested fix.** Rename by level, which the file names already imply:
`test_boot.py` -> `test_the_default_loopback_bind_starts_a_real_process`, and
`test_config.py` -> `test_the_default_loopback_bind_passes_validation`. Then say which pair each
belongs to in the docstring rather than only its ordinal.

---

## What I checked and did NOT find a defect in

Reporting only hits would say nothing about where I looked. Each of these was a live hypothesis
under one of the brief's seven shapes, and each came back clean **on evidence**, not on reading.

1. **The 21 harnesses and checkers, against a real runner.** I resolved every file in `scripts/` and
   `docs/reviews/*.py` to the thing that executes it (`.github/workflows/`, `.pre-commit-config.yaml`,
   `pyproject.toml`, `tests/`, and other scripts), rather than to a `CONTRIBUTING.md` line. Four are
   run by nothing, and **all four are defended**: `probe-exception-redaction.py` (task #15, owned by
   `fix-m5-l1`), `classify-w505.py` (`b49b-sweep`), `repoint-design-citations.py` (a one-shot repair
   tool, `CONTRIBUTING.md:136`), and `check-u1-pid1-shutdown.sh`, whose non-wiring is argued at
   `scripts/check-u1-pid1-shutdown.sh:35-38` ("CI has no Docker daemon"). I accept all four.
   `check-resweep-verdicts.py` is referenced by nothing at all, including CONTRIBUTING.md - see the
   open question below.
2. **`check-design-citations.py` being unwired.** I expected shape 1 and was wrong:
   `CONTRIBUTING.md:130` says "**`check-design-citations.py` is NOT a gate, and that is deliberate**",
   and with `DESIGN.md` frozen the citations cannot move without an ADR. Correctly defended.
3. **The suite-floor guard masking a red pytest through a pipe.** This is the preamble's own warning
   and `check-suite-floor.sh:17-21` explicitly delegates failure detection to the exit code, so a
   pipeline that swallowed it would be a real defect. `ci.yml` gets it right at both call sites:
   `out=$(...); rc=$?` then `[ "$rc" -eq 0 ] || { echo "$out"; exit "$rc"; }` **before** the pipe
   (`ci.yml:281-282` and `:311-312`). The script also fails closed on an absent passed-count
   (`check-suite-floor.sh:40-44`), which is shape 7 handled correctly.
4. **The `DESIGN.md` freeze.** Verified by object hash rather than by trusting the SHA:
   `c15b138:docs/DESIGN.md`, `61d1171:docs/DESIGN.md` and the working tree are all
   `8988e8cd7d9284157eeb8e0cef122732ced2ef4a`. The freeze holds.
5. **Coverage being a vacuous or absent gate.** It is real: 92.85% against an enforced
   `fail_under = 80`, exit 0. **I nearly reported the opposite.** My first run measured 0% with
   "No data was collected" and exit 1, which is a red that explains itself - and it was my own
   artifact: the venv's editable install points at the shared checkout
   (`_editable_impl_fast_mcp_jobvite.pth` -> `/home/.../fast-mcp-jobvite/src`), so imports resolved
   there while coverage's relative `source = ["src/fast_mcp_jobvite"]` resolved inside my worktree.
   Re-run with `PYTHONPATH=/tmp/r3-work/src`, it is 92.85%. Only the comments about it are wrong
   (R3-L4).
6. **`enabled_tools` mutating a module constant.** `config.py:259-260` does `selected -= WRITE_TOOLS`
   where `selected` may be the module-level `READ_TOOLS`. `frozenset` has no `__isub__`, so `-=`
   rebinds rather than mutating, and `READ_TOOLS` is intact. No defect.
7. **`is_loopback`'s name allow-list** (`config.py:79`, `{"localhost"}`) under shape 6. Unlisted
   loopback aliases such as `localhost.localdomain` are treated as **non**-loopback, which refuses
   the boot. That is the fail-closed direction and `config.py:122-124` states it deliberately. Not a
   defect.

## Two beliefs the brief asked me to challenge

**"The seven merged units are the whole reviewable surface."** Wrong, and it cost a High.
`.github/workflows/mirror.yml` is in no unit and in no scope line, and it has failed 117 times out
of 117 (**R3-H1**). `tests/test_workflow_pins.py:9-12` had already diagnosed this exact structural
cause for this exact file - "a rule naming one file in a directory selects for the files it does not
name" - and the R3 brief then scoped me to "`ci.yml`" rather than to `.github/workflows/`. The guard
the project built covers the pin axis only. **Suggested fix: scope future briefs to the directory,
and add `actionlint` so the logic axis has a runner too** (see R3-H1).

**"The out-of-scope areas are covered by the agents I assigned them to."** Mostly true, one gap.
`fix-m5-l1` owns `__main__.py`, `jobvite_client.py`, `redaction.py` and their tests; `b49b-sweep`
owns docstring line lengths. I stayed out of both and report the two observations below in the
message instead of as findings. The gap is not in those assignments but between them: **nobody owns
`.github/`**, which is how R3-H1 survived.

## What I did NOT verify

Kept for what I could not settle, not for what I did not try.

1. **That `secrets` in a job-level `if:` is the specific cause of the 117 mirror failures.** I proved
   the effect conclusively (117/117 failures, `total_count: 0` jobs, 0s duration - a run that never
   scheduled a runner) and I eliminated every other expression in the file as a candidate. I could
   not read GitHub's evaluation error itself: `gh run view --log-failed` returns "log not found" and
   the check-runs annotations endpoint 404s, because no job was ever created to carry a log. **One
   push after the suggested fix settles it** - that is the cheapest possible confirmation and I would
   take it before anything else.
2. **Whether an empty-string key would actually authenticate under `StaticTokenVerifier`** (R3-M1).
   It is not wired yet (`grep -rn "StaticTokenVerifier|auth=" src/` -> nothing; U9 owns it), so I
   proved only that the boot refusal accepts it. Whether it becomes an auth bypass or an inert bad
   config depends on U9's construction, and I deliberately did not guess.
3. **The `credentialed` arm.** Two tests, deselected by design and empty today
   (`tests/credentialed/README.md`); `ci.yml:325-333` collects them and treats pytest's exit 5 as a
   notice. I read the wiring and confirmed it is honest, but I ran nothing against a real Jobvite
   tenant and cannot speak to those two tests' behaviour.
4. **`check-resweep-verdicts.py`.** Referenced by no runner, no CI step and no `CONTRIBUTING.md`
   line - unlike the other three unwired scripts, which each have a stated reason. I did not read it
   closely enough to say whether it is a spent one-shot (like `repoint-design-citations.py`) or a
   control that was meant to be wired. **It is a five-minute question for whoever wrote it**, and it
   is the one loose end I would not want dropped.
5. **The `network`-marked arm end to end.** `ci.yml:308-313` runs it with its own floor of 2. I did
   not run it: it performs a real resolve against the network, and the brief's isolation rules plus
   the risk of a flaky external dependency made a local run worth less than reading it.

## Housekeeping

- **Worktree removed.** `git worktree remove /tmp/r3-work` after the final commit; `git worktree
  list` then shows only the shared checkout and the two live agents' trees.
- **I edited nothing in `src/`, `tests/` or `scripts/`.** This report is the only file I created.
  Verified: `git diff --stat 61d1171 review/r3` lists `docs/reviews/REVIEW-R3.md` and nothing else.
- **`docs/OBLIGATIONS.md` untouched**, so no anchor moved. `check-obligations.py` verbatim:
  `Every mapped anchor still contains its subject. OK.` (exit 0).
- **Suite at base, unchanged by me:** `333 passed, 2 deselected` in 22.59s, **0 skipped**, exit 0.
  The preamble's baseline of "322 passed, 2 deselected, 0 skipped" was measured at `0d34c66`; the
  growth to 333 is commits landing since, and `ci.yml:296` already floors at 333 "measured at
  025aa55". Consistent, not stale.
