# R2-LEFTOVER-VERDICTS - the thirteen findings nobody had checked

**Agent:** `r2-verify` (task #13)
**Date:** 2026-08-29 04:26 AM CDT
**Pinned SHA: `1fef5be`** (`main`, "docs(brief): dispatch R2's thirteen unverified leftovers,
read-only beside r4-fixes"). Every verdict below is judged at that commit.
**Worktree:** `/tmp/r2-verify-work`, `git worktree add /tmp/r2-verify-work 1fef5be`, then
`git checkout -b review/r2-leftovers`. The shared checkout was never touched, no `git stash` and no
`git checkout` of a path was run, and `r4-fixes` (`/tmp/r4fix-work`, `fix/r4-findings`) and
`shell-hygiene` (`/tmp/shell-work3`) were both live throughout.

**Source under review:** `R2` (`docs/reviews/REVIEW-CODE-R2.md`) was pinned at
`3f313ceef63984498b4a569dd6b67b8e4ebc2230`. Eleven merges have landed between that SHA and this one.

## Baseline

```
$ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
check-suite-floor.sh 413
$ PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest -q
413 passed, 5 deselected in 40.11s          # exit 0
```

413 passed, **0 skipped**, at the floor. The 5 deselected are the `credentialed`/`network` marks
that `pyproject.toml:123-127` deselects by construction rather than skipping, so that CI reports
zero skips; they are collected (`413/418 tests collected`) so they cannot rot.

## Method

I read the module before the finding, for every item. Two of the thirteen changed verdict because of
that ordering: **M-4** is fixed by a test R2 asked for and nobody recorded, and **M-6** is **WRONG at
its own pinned SHA** - its supporting grep is falsifiable and I falsified it. Neither is visible if
you read the report first and go looking for what it tells you to look for.

Every mutation was applied to a file in this worktree, proven to have landed with `git diff --stat`
against a unique anchor asserted present with `grep -c` first, restored with `cp` from a `/tmp`
backup, and the restore proven with `cmp` plus a clean `git status --short`. `PYTHONDONTWRITEBYTECODE=1`
throughout.

## Tally

| Verdict | Count | Findings |
|---|---|---|
| STILL OPEN | 10 | M-1, M-2, M-3, M-8, L-4, L-6, nit-1, nit-2, nit-3, nit-4 |
| FIXED | 2 | M-4, L-5 |
| WRONG | 1 | M-6 |
| FIXED INCIDENTALLY | 0 | - |
| SUPERSEDED | 0 | - |

Thirteen in, thirteen out. **Two of the ten STILL OPEN are surviving mutations** measured against
the full suite at 413 passed: **M-3** (`EXIT_CONFIGURATION_REFUSED = 78 -> 1`) and **nit-4**
(`return inbound_request_id.lower() -> return inbound_request_id`). Both were filed as untested
behaviour and both are still untested, now demonstrated rather than inferred from a grep.

---

# M-1 - `AuditWriteError` rides the redacted-away exception on `__context__`

## STILL OPEN

`src/fast_mcp_jobvite/audit.py:348` still reads `raise AuditWriteError(` with no `from None`, and it
is reached from inside `except Exception as exc:` at `audit.py:336-337` (`emit` catches, then calls
`_on_audit_write_failure`). `grep -rn "__context__\|from None\|format_exception" src/ tests/` returns
three hits, all in `jobvite_client.py` (`:324`, `:365`, `:670`) - **no test in the repository
mentions `__context__` or `format_exception` at all.**

Reproduced with `/tmp/probe_m1b.py`, a redactable secret so the contrast is real:

```
AuditWriteError args        : leaks SUPERSECRET? False
e.__context__ (OSError)     : leaks SUPERSECRET? True
full traceback              : leaks SUPERSECRET? True
```

Identical to R2's table. `redact_text` at `audit.py:345` does its job on the message and the raw
exception travels beside it anyway.

**Note on reproducing this:** loguru's handler defaults to `catch=True` and swallows a sink
exception before `emit`'s `except` can see it. My first probe therefore showed nothing at all. The
sink has to be added with `catch=False` - which is what `__main__.py` does since H-2's fix - or the
policy silently cannot fire and you conclude wrongly that it can't leak.

**Suggested fix** (`src/fast_mcp_jobvite/audit.py:348-351`):

```diff
     if phase is AuditPhase.BEFORE_SIDE_EFFECT:
         # Fail the call. No audit, no write.
         raise AuditWriteError(
             f"audit write failed before the side effect of {event.tool_name}; "
             f"the call was not performed ({detail})"
-        )
+        ) from None
```

and an arm in `tests/test_audit.py` asserting on **bools**, per that file's secret-safe convention at
`:20-22`:

```python
    assert excinfo.value.__context__ is None
    tb = "".join(traceback.format_exception(type(v), v, v.__traceback__))
    assert SENTINEL not in tb, "the raw exception text reached a formatted traceback"
```

---

# M-2 - a pydantic validation failure exits 1 with a traceback, not 78

## STILL OPEN

`src/fast_mcp_jobvite/config.py:453` is still a bare `settings = Settings()` outside any `try`, and
`src/fast_mcp_jobvite/__main__.py:421` still catches only `except ConfigurationError as exc:`.

Reproduced against the real entry point in a real process, three of the seven constrained fields:

```
$ env -i ... JOBVITE_MCP_PORT=99999 uv run --frozen python -m fast_mcp_jobvite
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
mcp_port
  Input should be less than or equal to 65535 [type=less_than_equal, input_value='99999', input_type=str]
rc=1

$ ... JOBVITE_MCP_TRANSPORT=htp ...
mcp_transport
  Input should be 'stdio' or 'http' [type=literal_error, input_value='htp', input_type=str]
rc=1

$ ... JOBVITE_MAX_RESULTS=0 ...
max_results
  Input should be greater than or equal to 1 [type=greater_than_equal, input_value='0', input_type=str]
rc=1
```

`rc=1`, a traceback on stderr, and `input_value=` echoed back in every case. `__main__.py:62-65`
says 78 exists precisely so a supervisor can tell a misconfiguration from an ordinary failure, and a
mistyped port is the most ordinary misconfiguration there is.

**Suggested fix**, unchanged from R2 and still correct - one door for every boot-time refusal:

```python
def load_settings() -> Settings:
    try:
        settings = Settings()
    except PydanticValidationError as exc:
        raise ConfigurationError(
            [f"{env_name(str(e['loc'][0]))}: {e['msg']}" for e in exc.errors()]
        ) from None
    validate_settings(settings)
    return settings
```

`from None` is not cosmetic here: it is the same defect as M-1, and `exc.errors()` carries
`input_value`, so the reason list must be rebuilt from `loc` and `msg` rather than from `str(exc)`.
Add a `test_boot.py` process arm asserting `returncode == 78`, `"JOBVITE_MCP_PORT" in stderr` and
`"Traceback" not in stderr`.

---

# M-3 - the refusal exit status is asserted only against its own constant

## STILL OPEN - **and it is a surviving mutation at 413 passed**

Every assertion imports the constant from the module under test:

```
tests/test_boot.py:50,134,145,156,169   assert result.returncode == EXIT_CONFIGURATION_REFUSED
tests/test_server.py:179                assert main() == EXIT_CONFIGURATION_REFUSED
tests/test_shutdown.py:262              assert result.returncode != EXIT_CONFIGURATION_REFUSED
src/fast_mcp_jobvite/__main__.py:368    EXIT_CONFIGURATION_REFUSED = 78
```

`grep -rn '\b78\b' tests/ scripts/` returns three hits and **none of them is an assertion** - they
are the prose "78/78" in `tests/test_logging_process.py:452`,
`scripts/check-u1-boot-controls.sh:304` and `scripts/check-u1-boot-amputation.sh:400`. That is the
`grep` most likely to produce a false negative here and it is why I ran the mutation as well.

Measured. Anchor asserted unique first (`grep -c '^EXIT_CONFIGURATION_REFUSED = 78$'` → `1`),
mutation proven landed (`1 file changed, 1 insertion(+), 1 deletion(-)`):

```
EXIT_CONFIGURATION_REFUSED = 78  ->  = 1
413 passed, 5 deselected in 40.18s          # exit 0    *** SURVIVED ***
```

Restored, `cmp` clean, `git status --short` empty.

**The contrast that makes this concrete, and it is in the same repository:** its sibling constant
*is* held. `tests/test_shutdown.py:174` asserts `"EXIT_SOFTWARE = 70" in source`. `70` cannot be
changed without a test going red; `78` can. One of the two `sysexits.h` numbers this server exposes
to a supervisor is pinned and the other is not, and nothing records why.

**Suggested fix** - one test, in `tests/test_boot.py`, beside the arms that already import the
constant:

```python
def test_the_refusal_status_is_sysexits_EX_CONFIG_and_not_a_generic_failure() -> None:
    """78 is EX_CONFIG. A supervisor reads the NUMBER, not our constant's name."""
    assert EXIT_CONFIGURATION_REFUSED == 78
    assert EXIT_CONFIGURATION_REFUSED != 1
```

and a row in `scripts/check-u1-boot-controls.sh` mutating `EXIT_CONFIGURATION_REFUSED = 78` to
`= 1`, so the gate holds it and not just the suite.

---

# M-4 - the whitespace-only credential rule is implemented and untested

## FIXED, at `47c71c5` (2026-08-28), "test(config): hold the whitespace half of the empty-is-unset rule"

The test R2 asked for exists, parametrised, at `tests/test_config.py:499-526`:

```python
@pytest.mark.parametrize("blank", [" ", "   ", "\t", "\n", " \t \n "])
def test_a_whitespace_only_value_is_also_treated_as_unset(
```

and its docstring at `:508-510` records the finding in its own words ("**This was a surviving
mutation.** Deleting `.strip()` from the … uses `""` - which is falsy with or without the strip").
The parametrisation deliberately omits `""`, so every case it runs is one the old test could not
distinguish.

**It survives the amputation.** `src/fast_mcp_jobvite/config.py:236`,
`if not (isinstance(value, str) and not value.strip())` → `and not value)`:

```
5 failed, 408 passed, 5 deselected in 39.80s      # exit 1    *** KILLED ***
FAILED tests/test_config.py::test_a_whitespace_only_value_is_also_treated_as_unset[ ]
FAILED tests/test_config.py::test_a_whitespace_only_value_is_also_treated_as_unset[   ]
FAILED tests/test_config.py::test_a_whitespace_only_value_is_also_treated_as_unset[\t]
FAILED tests/test_config.py::test_a_whitespace_only_value_is_also_treated_as_unset[\n]
FAILED tests/test_config.py::test_a_whitespace_only_value_is_also_treated_as_unset[ \t \n ]
```

Restored, `cmp` clean.

**Residual, and it is the reason this is not a clean close:** R2's fix had two halves and only one
landed. It also asked for `not value.strip() -> not value` as a row in
`scripts/check-u1-boot-controls.sh`. `grep -n 'strip' scripts/check-u1-boot-controls.sh
scripts/check-u1-boot-amputation.sh` returns one hit and it is an unrelated comment at
`check-u1-boot-controls.sh:136`. The behaviour is held by the suite and not by the gate. **Suggested
fix:** add that row - the anchor is unique, and the mutation is the exact `sed` I ran above.

---

# M-6 - the timeout question

## WRONG - the finding's supporting evidence is false at R2's own pinned SHA

R2 wrote, of `resilience.md:74-76`:

> This server declares no inbound deadline anywhere - `grep -rn "deadline" src/ docs/DESIGN.md` finds
> none

That grep, run against the SHA R2 itself pinned, does not find none:

```
$ git show 3f313ce:docs/DESIGN.md | grep -n "deadline"
343:  inbound request's deadline, because there is no inbound deadline here - see the note below.
361:deadline** so a slow dependency surfaces as a fast, typed error rather than a hung request
362:worker."* **MCP gives us no inbound deadline to be shorter than.** There is no HTTP request worker
367:What the clause is *for* still applies, so we satisfy the intent by supplying the deadline the
1726:| C5-D1 | … The ceiling is ours because MCP supplies no inbound deadline to derive one from …
```

Five hits, one of which is a **bolded paragraph naming `backend/resilience.md:74-76` by citation and
answering it**. At the current SHA the same paragraph is `docs/DESIGN.md:364-374`, and it says:

> **`backend/resilience.md:74-76` has no referent on this transport, and saying so is the honest form
> of compliance with it.** … **MCP gives us no inbound deadline to be shorter than.** … What the
> clause is *for* still applies, so we satisfy the intent by supplying the deadline the transport
> does not: **a total outbound budget, configured, that bounds all attempts for one tool
> invocation** …

That is R2's own suggested remedy (b) - "record … stating that MCP tool calls carry no inbound
deadline" - already present in the frozen design, at the SHA R2 was reading, one section above the
timeout it was reviewing. The finding asked for something that was already there.

This is the same shape as R2-H-4: a real absence claimed from a search whose result was not what the
reviewer reported. I am recording it plainly rather than softening it, per the brief.

**What is NOT closed by this, and belongs to a different unit.** The **total outbound budget** the
design promises does not exist in `src/`. `grep -rni "budget\|ceiling" src/` returns
`errors.py:155` (a docstring), `config.py:203` `outbound_rate_limit: int = Field(default=6, ge=1)` -
a *rate* limit, not a time budget - and two unrelated `constraints.py` comments. There is no
per-invocation time bound. That is **U7's** work (`docs/adr/0022-*.md:95` assigns client-side
throttling to U7) and U7 is not built, so it is not a U4 defect and not a leftover of this report.
`read=30.0` at `services/jobvite_client.py:464` remains six times `resilience.md:84-87`'s exemplar,
which R2 correctly noted is an exemplar and not a mandate.

**Suggested action:** none against U4. Carry "the total outbound budget DESIGN.md:373-374 promises
is implemented by nothing" into the U7 brief as an obligation it must discharge, so the design's own
compliance argument is not left resting on a component that does not exist. **Do not** re-file it as
a U4 finding.

---

# M-8 - `__main__.py` coverage

## STILL OPEN - the number is stale, the defect is not

The brief said M-8's coverage figure is stale and to confirm it in a sentence. Confirmed, and the
sentence has to be longer than one, because the figure and the finding are not the same thing.

```
src/fast_mcp_jobvite/__main__.py    88   27   14   3   69%   163->165, 191, 226-232, 287-288, 292-293, 393, 398, 426-458
TOTAL                              714   41  138  12   94%
Required test coverage of 80.0% reached. Total coverage: 93.54%
413 passed, 5 deselected in 48.52s
```

`__main__.py` is **69%**, not 58%, and the total is 93.54%. Every per-module figure R2 quoted has
moved. But **the mechanism R2 named is untouched**: `pyproject.toml:167-173` `[tool.coverage.run]`
still sets only `source`, `branch` and `omit` - **no `parallel`, no `sigterm`, no `concurrency`, no
`COVERAGE_PROCESS_START`** - so the subprocess arms in `test_boot.py` and `test_shutdown.py` are
still invisible, and the missing range `426-458` is still the shutdown handler, the transport
selection and the `finally`. And R2's separate note stands verbatim: `[tool.coverage.report]` sets
`fail_under = 80` and nothing enforces ADR-0010's per-module floors.

The 69% is a wrong number with a plausible story, which is the whole reason R2 filed it. The next
reader still sees the most safety-critical file in U1 well under every other module and can still
"fix" it by adding an `omit`.

**Suggested fix** - the cheap half, which the report itself offers as the acceptable alternative and
which I would take now rather than wiring subprocess measurement:

```toml
[tool.coverage.run]
source = ["src/fast_mcp_jobvite"]
branch = true
# `__main__.py` reads low because its shutdown, transport-selection and
# `finally: os._exit` arms run OUT OF PROCESS - `test_boot.py` and
# `test_shutdown.py` drive them through subprocess.run/Popen and no
# `parallel`/`COVERAGE_PROCESS_START` is set, so the child's execution is
# not measured. The arms exist. Do NOT add an `omit` row for it: that
# makes the number look right by measuring less.
omit = [
```

---

# L-4 - a local configuration fault is reported as a Jobvite upstream error

## STILL OPEN

`src/fast_mcp_jobvite/services/jobvite_client.py:539-544` is unchanged:

```python
        if self._company_id is None:
            raise JobviteUpstreamError(
                None,
                "the jobFeed route requires a companyId credential and none is "
                "configured",
            )
```

Reproduced end to end through the real mapping (`/tmp/probe_l4.py`):

```
str   : Jobvite returned status none: the jobFeed route requires a companyId credential and none is configured
type   : /problems/external-service-error
status : 502
title  : External Service Error
detail : Jobvite returned status none: the jobFeed route requires a companyId credential and none is configured
```

`errors.py:72` maps the slug to **502** and `errors.py:149` renders `"Jobvite returned status none:"`.
Jobvite returned nothing and was never called. The caller is told the upstream failed when the
deployment is misconfigured.

Note the docstring at `:532-537` now argues *for* raising rather than sending the call without the
credential - which is right, and orthogonal. The finding is the **type**, not the raise.

**Suggested fix**, unchanged from R2 (`errors.py` has no configuration row and `DESIGN.md:510-511`
forbids minting a slug, so `about:blank`/500 via ADR-0017's `problem_from_exception` is the honest
answer):

```diff
         if self._company_id is None:
-            raise JobviteUpstreamError(
-                None,
-                "the jobFeed route requires a companyId credential and none is "
-                "configured",
-            )
+            msg = "the jobFeed route requires a companyId credential and none is configured"
+            raise RuntimeError(msg)
```

Repoint `test_the_jobfeed_route_refuses_without_a_company_id` at `RuntimeError` and assert
`problem_from_exception(exc, request_id)["type"] == "about:blank"`. Update the `Raises:` block at
`:532-537` in the same edit - it names `JobviteUpstreamError` and would otherwise become a
docstring that describes the defect it used to have.

---

# L-5 - non-`HTTPError` httpx2 exceptions escape uncaught

## FIXED, at `0fe965a`, "fix(client): catch the httpx2 exceptions that are not HTTPError subclasses"

`src/fast_mcp_jobvite/services/jobvite_client.py:617-637` now catches the tuple:

```python
        except (
            httpx2.HTTPError,
            # NOT SUBCLASSES OF HTTPError, measured at httpx2 2.12.0
            ...
            httpx2.InvalidURL,
            httpx2.CookieConflict,
            httpx2.StreamError,
        ) as exc:
```

and `raise JobviteUnavailableError(_unavailable_detail(exc)) from None` at `:670` now covers all
four, so the module's documented contract is true.

Tests exist and are not the same test twice: `tests/test_jobvite_client.py:881-910`
(`test_an_invalid_url_becomes_a_typed_error_not_an_escape`, driven by a real NUL-byte path rather
than a mock), `:924` (the header-redaction arm reusing that trigger) and `:967-970`, which asserts
the *taxonomy claim itself* - that those three names are outside `HTTPError` at the installed
version, so the comment cannot rot silently if httpx2 reparents them.

**It survives the amputation.** Deleting the single line `httpx2.InvalidURL,` (anchor asserted
unique, `git diff --stat` = `1 file changed, 1 deletion(-)`):

```
2 failed, 40 passed in 3.68s        # exit 1    *** KILLED ***
FAILED tests/test_jobvite_client.py::test_an_invalid_url_becomes_a_typed_error_not_an_escape
FAILED tests/test_jobvite_client.py::test_the_v2_credential_headers_are_redacted_in_the_failure_log
```

Restored, `cmp` clean.

---

# L-6 - the shutdown case asserts on source substrings where its sibling uses the AST

## STILL OPEN

`tests/test_shutdown.py:141-174`, `test_the_shipped_entry_point_is_what_the_case_exercises`:

```
161:    assert "signal.signal(signal.SIGTERM, _term)" in source
162:    assert "os._exit(status)" in source
167:    assert "os._exit(status)" in finally_block
172:    assert "os._exit(0)" not in source
173:    assert "status = EXIT_SOFTWARE" in source
174:    assert "EXIT_SOFTWARE = 70" in source
```

and the next test, `test_the_handler_does_not_read_ambient_state` at `:177`, still uses `ast.parse`
at `:195` and still carries the paragraph explaining why a substring search is the wrong instrument
for this file. The assertions moved (ADR-0018 turned `os._exit(0)` into `os._exit(status)`, and
`:172` is now a *negative* substring assertion) but the instrument did not.

R2's own judgement that these are not vacuous today still holds: `scripts/check-u1-boot-controls.sh`
M11 (`:210-218`) and M12 (`:221-229`) kill both mutations through the behavioural arms, and M12
asserts its anchor is unique first (`:225`).

**Suggested fix**, unchanged: walk the AST for a `signal.signal` `Call` whose second argument is
`Name(id="_term")`, and for an `os._exit` `Call` inside a `Try.finalbody`, mirroring `:195`. Keep
`:152-153` (`MARKER_ENTRY`) as substring assertions - those are checking a string literal and are
the correct instrument for that.

**One thing to keep when you rewrite it:** `:174`'s `assert "EXIT_SOFTWARE = 70" in source` is the
*only* thing in the repository pinning either `sysexits.h` number to its value (see M-3). It is a
poor instrument and it is currently load-bearing. Replace it with a real assertion
(`assert EXIT_SOFTWARE == 70`) in the same edit rather than deleting it.

---

# nit-1 - `enabled_tools`' docstring says "registers nothing"

## STILL OPEN

`src/fast_mcp_jobvite/config.py:261-262`, verbatim and unchanged:

```
261:        writes-on with `JOBVITE_TOOLS` unset registers nothing, and
262:        naming it without the flag registers nothing either.
```

The first clause is still wrong: with `JOBVITE_TOOLS` unset and `JOBVITE_ENABLE_WRITES=true`,
`READ_TOOLS` is registered and only the write is withheld.

**Suggested fix** (`config.py:261-262`):

```diff
-        writes-on with `JOBVITE_TOOLS` unset registers nothing, and
-        naming it without the flag registers nothing either.
+        writes-on with `JOBVITE_TOOLS` unset registers **no write**, and
+        naming it without the flag registers no write either.
```

---

# nit-2 - `_empty_is_unset` only strips `str`

## STILL OPEN

`src/fast_mcp_jobvite/config.py:233-237`:

```python
        return {
            key: value
            for key, value in data.items()
            if not (isinstance(value, str) and not value.strip())
        }
```

`isinstance(value, str)` is still the only branch, so `Settings(api_key=SecretStr(""))` reaches
`_check_required_variables` as a present, empty credential. Environment variables are always `str`,
so this cannot fire from the environment - it is correctly a nit - but the direct-construction shape
is in live use in the suite (`test_config.py:450-457`, `test_server.py:45-50`).

**Suggested fix**, in `validate_settings` rather than in `_empty_is_unset`, because that is where a
refusal belongs and it catches the shape regardless of how the value arrived:

```python
    for name in _REQUIRED_SECRET_FIELDS:
        value = getattr(settings, name)
        if value is not None and not value.get_secret_value().strip():
            failures.append(f"{env_name(name)} is present but empty")
```

---

# nit-3 - `redact_text` deletes punctuation attached to a redacted value

## STILL OPEN

`src/fast_mcp_jobvite/utils/redaction.py:213` (`def redact_text`). Reproduced, two shapes:

```
in : "connect failed for url 'https://api.jobvite.com/api/v2/job?api=AAA&sc=BBB' after 3 tries"
out: "connect failed for url 'https://api.jobvite.com/api/v2/job?api=[REDACTED]&sc=[REDACTED] after 3 tries"
                                                                                            ^ the closing quote is gone

in : 'see "https://x/y?sc=BBB", then stop.'
out: 'see "https://x/y?sc=[REDACTED] then stop.'
                                    ^ the closing quote AND the comma are gone
```

It never un-redacts anything, so it stays a nit. It matters for the reason `redaction.py:104-108`
gives about preserving parameter order: a redacted log line that is not a faithful rendering of the
original is one people stop trusting.

**Suggested fix:** strip a trailing run of `'"),.;` off the matched token before `redact_url` and
re-append it to the result. Add an arm asserting the closing delimiter survives, parametrised over
`'`, `"`, `)`, `,` and `.` - and note that a naive fix must not strip characters that are legally
part of a query value, so the test should also assert that a value ending in a real `.` or `)`
inside the URL is still fully redacted.

---

# nit-4 - a valid inbound `X-Request-ID` is echoed lower-cased

## STILL OPEN - **and it is a surviving mutation at 413 passed**

`src/fast_mcp_jobvite/audit.py:234-235`:

```python
    if inbound_request_id is not None and _UUID4_RE.match(inbound_request_id):
        return inbound_request_id.lower()
```

and the test, `tests/test_audit.py:597-599`, uses an all-numeric lower-case literal that cannot
distinguish the two behaviours:

```python
def test_a_valid_inbound_uuid4_is_echoed() -> None:
    inbound = "11111111-1111-4111-8111-111111111111"
    assert resolve_request_id(inbound) == inbound
```

Measured. `return inbound_request_id.lower()` → `return inbound_request_id`:

```
413 passed, 5 deselected in 39.93s          # exit 0    *** SURVIVED ***
```

Restored, `cmp` clean. R2's claim that "at this SHA that test passes whichever behaviour is intended"
is confirmed by amputation, at the current SHA, unchanged.

**Suggested fix.** Decide the behaviour, then hold it either way. I would return the caller's string
unchanged - `_UUID4_RE` is already `IGNORECASE`, `error-contract.md:83-85` requires no case, and an
exact-match join across two systems is the whole point of echoing it:

```diff
-        return inbound_request_id.lower()
+        return inbound_request_id
```

and in `tests/test_audit.py:597`, a row that goes red on the other choice:

```python
@pytest.mark.parametrize(
    "inbound",
    [
        "11111111-1111-4111-8111-111111111111",
        "A1B2C3D4-1111-4111-8111-111111111111",   # upper case: NOT the same string lower-cased
    ],
)
def test_a_valid_inbound_uuid4_is_echoed_unchanged(inbound: str) -> None:
    assert resolve_request_id(inbound) == inbound
```

The upper-case row must contain a letter. The existing literal is all digits and hyphens, which is
why it is invisible to `.lower()` - that is the actual mechanism of this nit and any replacement
test that keeps an all-numeric literal reproduces it.

---

# Gates

Run in `/tmp/r2-verify-work` on `review/r2-leftovers`, each judged by its own exit code on its own
line. This change is documentation-only; the code gates are here to prove the tree I mutated and
restored is byte-identical to `1fef5be`.

| Gate | Result | Exit |
|---|---|---|
| `uv run --frozen ruff check .` | `All checks passed!` | 0 |
| `uv run --frozen ruff format --check .` | clean | 0 |
| `uv run --frozen mypy` | `Success: no issues found in 44 source files` | 0 |
| `uv run --frozen pytest` | `413 passed, 5 deselected in 38.67s` - 0 skipped, at the 413 floor | 0 |
| `uv run --frozen python docs/reviews/check-quickstart.py` | clean | 0 |
| `python3 scripts/check-committed-file-types.py --all` | clean | 0 |
| `python3 scripts/check-harness-anchors.py --self-check` | clean | 0 |
| `git status --short` after every restore | empty | - |
| `cmp` backup vs restored, 4 files | identical | 0 |

Not run: `scripts/check-u1-pid1-shutdown.sh` (needs Docker) and `actionlint` (needs actionlint and
shellcheck on PATH). Neither can be affected by a documentation-only change, and neither is claimed
above.

# What I could NOT settle

1. **Whether `r4-fixes` changes any of these verdicts.** All thirteen are judged at `1fef5be` on
   `main`. `fix/r4-findings` was at `97eb93b` in `/tmp/r4fix-work` throughout and I did not read it -
   the brief made `src/` and `tests/` read-only and reading another agent's mid-sweep branch to
   predict a verdict would be worse than saying so. **M-1 (`audit.py`), L-4 and L-6 are the ones at
   risk**: R4 is sweeping `services/jobvite_client.py`, which is L-4's file. Re-check L-4 after the
   r4-fixes merge before dispatching a fix for it.

2. **Whether M-2's `input_value=` echo can leak a secret.** The three fields I reproduced are
   integers and a `Literal`. Every secret-class field is `SecretStr`, and pydantic renders those as
   `SecretStr('**********')` in an error - but I did not construct a case that makes a `SecretStr`
   field fail *pydantic* validation (they carry no constraints today), so I have not demonstrated it
   either way. It does not change M-2's verdict; it changes how carefully the fix must be written,
   which is why the suggested fix builds the reason list from `loc`/`msg` and not from `str(exc)`.

3. **Two gates I did not run:** `scripts/check-u1-pid1-shutdown.sh` needs Docker and `actionlint`
   needs actionlint plus shellcheck on PATH. Neither is reachable from a documentation-only change,
   so this is a statement of what the Gates table does not cover rather than a verdict I could not
   reach.

Worktree `/tmp/r2-verify-work` is removed after the push; the branch `review/r2-leftovers` carries
this report.
