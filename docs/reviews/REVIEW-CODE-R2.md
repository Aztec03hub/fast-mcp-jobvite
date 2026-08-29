# REVIEW-CODE-R2 - U1, U3 and U4

**Reviewer:** `code-review-r2` (task #10)
**Date:** 2026-08-28 10:29 PM CDT
**Pinned SHA: `3f313ceef63984498b4a569dd6b67b8e4ebc2230`** (`main`, "Brief round 2 at U1, U3 and U4,
which nobody has reviewed"). Every finding below is judged at that commit.
**Worktree:** `/tmp/code-review-r2-work`, created with `git worktree add -b review/code-r2 … 3f313ce`,
never the shared checkout. `adr-batch` was concurrently on `adr/batch` at `371fe3b`; nothing it
touched was read from the shared tree.

**Scope:** `config.py`, `server.py`, `__main__.py`, `audit.py`, `utils/redaction.py`,
`services/jobvite_client.py`, and `tests/test_config.py`, `test_server.py`, `test_boot.py`,
`test_shutdown.py`, `boot_process.py`, `test_audit.py`, `test_redaction.py`,
`test_jobvite_client.py`, `conftest.py`, plus `scripts/check-u{1,3,4}-*.sh`.

---

## Tally

| Severity | Count |
|---|---|
| Critical | 0 |
| High | 6 |
| Medium | 8 |
| Low | 7 |
| nit | 4 |
| **Total** | **25** |

**Six of these are surviving mutations or measured runtime behaviour, not readings.** Five mutations
that the authors' own 45 control rows do not contain survived the entire 294-test suite. Every
finding carries a suggested fix, marked as a suggestion to be verified rather than applied blindly.

**Gates at this SHA, each judged by its own exit code on its own line:**

| Gate | Exit |
|---|---|
| `uv run --frozen pytest -q` | **0** - `294 passed, 2 deselected`, **0 skipped** |
| `uv run --frozen ruff check .` | **0** |
| `uv run --frozen ruff format --check .` | **0** |
| `uv run --frozen mypy src tests` | **0** - `no issues found in 31 source files` |
| `pyright src/fast_mcp_jobvite` | **0** - `0 errors, 0 warnings` |
| `bash scripts/check-u1-boot-controls.sh` | **0** - `13/13 controls fired` |
| `bash scripts/check-u3-audit-controls.sh` | **0** - `15 killed, 0 not killed` |
| `bash scripts/check-u4-client-controls.sh` | **0** - `17 killed, 0 not killed` |

The 2 deselected are the `credentialed` and `network` marker arms, deselected by
`pyproject.toml:132` on purpose. `check-cross-references.py` on `DESIGN.md:603` is red on purpose
for ADR-0019 and is not reported.

---

# Findings

## H-1 - The audit event's mandated fields never reach the log in production

**File:** `src/fast_mcp_jobvite/audit.py:313`; nothing in `src/` configures loguru.

`emit` writes `logger.bind(**event.to_record()).info(AUDIT_EVENT_NAME)`. `bind` puts the record into
loguru's `extra`. **Nothing in `src/` ever calls `logger.add`, `logger.remove`, `logger.configure`
or sets `serialize=True`** - the only `logger.add` calls in the repository are in
`tests/test_audit.py:90` and `tests/test_jobvite_client.py:533`. `__main__.py:45-50` configures the
**stdlib** `logging` module, which is a different library from the one `audit.py` and
`jobvite_client.py` import.

So in production the only sink is loguru's autoinit handler #0, whose format is
`loguru/_defaults.py` `LOGURU_FORMAT` - `{time} | {level} | {name}:{function}:{line} - {message}`.
**It contains no `{extra}` and `LOGURU_SERIALIZE` is `False`.** Measured, run at this SHA:

```
$ python -c 'from loguru import logger; logger.bind(tool_name="get_candidate",
      request_id="abc", result_status="success").info("tool_invocation")'
2026-08-28 22:15:26.268 | INFO | __main__:<module>:5 - tool_invocation
```

Every mandated field is gone. The same run also caught `jobvite_client.py:475`'s own line emitting
as bare `... - jobvite request` with `method` and `route` dropped.

This breaches `ai/tool-calling.md:171-179` (`priority: required`), which mandates "tool name,
validated arguments (PII redacted), result status, latency, and the request correlation id" and
"Tool logs are wire-shaped **snake_case** (`tool_name`, `request_id`, `result_status`)". It also
removes the entire justification ADR-0011 gives for keeping a third log producer: that producer
exists *because* `StructuredLoggingMiddleware` "emits **no** arguments where the mandated field is
*redacted* arguments" (`docs/adr/0011-…:31-33`). At this SHA the third producer emits no arguments
either.

**Why no test sees it.** `tests/test_audit.py:78-94` installs its own sink and reads
`message.record["extra"]`. That channel exists only inside the fixture. This is the harness sharing
its author's blind spot exactly as the brief predicts: it is a real loguru stream, but not the one
the server writes to unattended.

**Suggested fix (verify, do not apply blindly).** Configure the audit sink in the one place that
owns process-wide logging, `__main__.py`, before `build_server`, and pin it in a test that asserts
against the **rendered output** rather than against `record["extra"]`:

```python
# __main__.py, beside logging.basicConfig
from loguru import logger as _loguru
_loguru.remove()                       # drop autoinit handler #0
_loguru.add(sys.stderr, serialize=True, catch=False, level="INFO")
```

`serialize=True` emits one JSON object per record carrying `extra`, which is what
`ai/tool-calling.md:178-179`'s snake_case wire shape asks for; `sys.stderr` keeps the JSON-RPC
channel clean on stdio; `catch=False` is H-2's fix. Add a test that captures the **string** a sink
receives (`logger.add(records.append)` then `json.loads(str(records[0]))`) rather than the record
object, so a format that drops `extra` goes red.

---

## H-2 - The audit-write-failure policy cannot fire in production

**File:** `src/fast_mcp_jobvite/audit.py:312-316`; `tests/test_audit.py:398-427`.

`emit` wraps the write in `try: … except Exception`. **Loguru handlers default to `catch=True`**
(`loguru/_defaults.py` `LOGURU_CATCH = env("LOGURU_CATCH", bool, True)`): a sink that raises is
caught *inside* loguru, printed to stderr as `--- Logging error in Loguru Handler #N ---`, and
`.info()` returns normally. Measured at this SHA:

```
$ # a sink that always raises, added with logger.add(boom)
RESULT: .info() did NOT raise -> audit.emit's except is unreachable with a real sink
```

Therefore, with a real sink, `except Exception` never runs and `_on_audit_write_failure` is dead
code. The branch that matters is `AuditPhase.BEFORE_SIDE_EFFECT` (`audit.py:324-329`): its whole job
is "no audit, no write" before `create_candidate` emails a live human. **In production a failed
audit write returns `[]` and the write proceeds.**

The three arm tests pass because `_ExplodingLogger` (`test_audit.py:398-413`) raises from `bind`.
`bind` is a pure local call that constructs a bound logger; it is not the thing that fails when a
disk fills, a file handle is revoked, or a network sink is unreachable. The fake mirrors the call
signature (which its docstring claims, correctly) but not the **failure mode**.

**Suggested fix.** Add every sink with `catch=False` (see H-1's snippet) so a sink failure really
does propagate into `emit`'s `except`. Then add one arm that installs a *raising sink* rather than
patching `audit.logger`:

```python
def test_arm1_fires_when_the_SINK_fails_not_only_when_bind_does() -> None:
    sink_id = logger.add(lambda _m: (_ for _ in ()).throw(OSError("disk full")),
                         catch=False, level="DEBUG")
    try:
        with audit_scope("create_candidate", Transport.HTTP) as event:
            with pytest.raises(AuditWriteError):
                emit(event, AuditPhase.BEFORE_SIDE_EFFECT)
    finally:
        logger.remove(sink_id)
```

Keep the `_ExplodingLogger` arms as well - they cover a different failure and cost nothing.

---

## H-3 - `follow_redirects` is not pinned, so a 30x would forward the v2 credential headers

**File:** `src/fast_mcp_jobvite/services/jobvite_client.py:358-362`. **SURVIVING MUTATION.**

`httpx2.AsyncClient` is constructed with `transport` and `timeout` only. `follow_redirects` is left
to the library. Today `inspect.signature(httpx2.AsyncClient.__init__)` reports
`follow_redirects` default `False` at `httpx2 2.12.0`, so the behaviour is currently safe **by a
dependency's default and nothing else**.

I added `follow_redirects=True` to that constructor and ran the whole suite:

```
R7 the client follows redirects, forwarding its credential headers: *** SURVIVED ***
```

294 tests stayed green while the client would follow a `Location` to any host, carrying
`x-jvi-api` and `x-jvi-sc` (httpx does not strip custom headers across hosts) - and on the
`jobFeed` route, carrying `api`, `sc` and `companyId` in the query string to that host.

`server.py:3-9` states this repository's own lesson: "The default is what a dependency bump changes
silently … the `ResponseLimiting` regression arrived through the transitive SDK with zero change to
the code that broke." `mask_error_details` was pinned for that reason. This one was not, and it is
a credential-exfiltration property rather than a detail-masking one.

**Suggested fix.**

```python
self._client = httpx2.AsyncClient(
    transport=transport,
    follow_redirects=False,   # never forward x-jvi-* to a Location we did not choose
    timeout=timeout or httpx2.Timeout(connect=5.0, read=30.0, write=30.0, pool=5.0),
)
```

plus a behavioural test: a `MockTransport` handler returning `302` with
`Location: https://evil.example/` and asserting the second request never happens
(`assert len(seen) == 1`) and that `evaluate_response` raises on the 302 body. Add the mutation
`follow_redirects=True` as a row in `check-u4-client-controls.sh`.

---

## H-4 - The inbound `request_id` regex is untested at the canonical log-forging shape

**File:** `src/fast_mcp_jobvite/audit.py:82-85`; `tests/test_audit.py:571-588`. **SURVIVING MUTATION.**

`_UUID4_RE` correctly anchors with `\Z`. I changed the trailing `\Z` to `$`:

```
R8 the inbound request-id anchor allows a trailing newline: *** SURVIVED ***
```

In Python `$` matches immediately before a trailing newline, so the mutant accepts
`"11111111-1111-4111-8111-111111111111\n"` and `resolve_request_id` echoes it into the audit record
- which is precisely C7-T1 (`DESIGN.md:1795`), "a value carrying a newline writes a second,
attacker-authored line into the audit stream" (`audit.py:80-81`).

Measured, at this SHA:

```
 trailing-newline id, shipped \Z : False (rejected -> correct)
 trailing-newline id, mutant  $  : True  (ACCEPTED -> forges a log line)
 every parametrised row in test_audit.py still rejected by the mutant: True
```

The last line is the defect. `test_an_invalid_inbound_request_id_is_replaced_rather_than_used`'s
newline row is `"…111111111111\ninjected=audit_bypass"` - content **after** the newline, which `$`
also rejects. The one shape that separates `\Z` from `$` is a **trailing** newline, and it is the
canonical form of the attack (a header value copied with its line terminator). The test name is a
claim its body does not exercise.

**Suggested fix.** Add two rows to the existing `@pytest.mark.parametrize` at
`tests/test_audit.py:571-581`:

```python
        "11111111-1111-4111-8111-111111111111\n",      # trailing newline: \Z vs $
        "11111111-1111-4111-8111-111111111111\r\n",    # CRLF, as a header would carry it
```

and add `\Z -> $` as a row in `check-u3-audit-controls.sh` so the anchor stays pinned.

---

## H-5 - `companyId` is allow-listed for audit output while the same file treats it as a credential

**File:** `src/fast_mcp_jobvite/utils/redaction.py:64` vs `:80-93`.

The same module holds both:

- `SECRET_QUERY_PARAMS = frozenset({"api", "sc", "companyid"})` (`:64`), because
  `DESIGN.md:317-319` makes `companyId` "a credential class of its own", and
- `NON_SENSITIVE_ARGUMENT_KEYS` containing `"companyId"` (`:91`), whose docstring says every member
  is there because it is "structurally an identifier, a bound or a page cursor rather than anything
  a candidate typed or that identifies one".

`config.py:169` types the same value `company_id: SecretStr | None`, and `config.py:31-34` cites
`DESIGN.md:320` for it being "the job feed's separate credential, not … a public identifier".

Measured at this SHA:

```
>>> redact_arguments({"companyId": "REAL-COMPANY-CREDENTIAL", "eId": "abc"})
{'companyId': 'REAL-COMPANY-CREDENTIAL', 'eId': 'abc'}
```

The single enforcement point fails **open** on a value it redacts everywhere else. Reachability
today is low - no shipped tool takes `companyId` from the caller, it comes from configuration - so
this is a latent fail-open in the one module DESIGN.md:312-316 designates as the single enforcement
point, not a live leak. It becomes live the moment any tool accepts a `companyId` argument, which
is exactly the "a tool added later contributes its arguments … redacted" property `:75-76` claims
for this list. No test covers it: `test_redaction.py` has
`test_the_allow_list_does_not_contain_query` but no `companyId` equivalent.

**Suggested fix.** Remove `"companyId"` from `NON_SENSITIVE_ARGUMENT_KEYS`, and pin the invariant
so the two lists cannot contradict each other again:

```python
def test_no_secret_query_parameter_name_is_also_an_allow_listed_argument_key() -> None:
    """The same file must not call one name both secret and non-sensitive."""
    overlap = {k for k in NON_SENSITIVE_ARGUMENT_KEYS if k.lower() in SECRET_QUERY_PARAMS}
    assert overlap == set(), f"allow-listed keys that are also redacted as credentials: {overlap}"
```

That test is red at this SHA and green after the removal, so it is its own positive control.
Consider whether `"eId"` belongs either - it is Jobvite's candidate identifier and the only
camelCase member of an otherwise snake_case set.

---

## H-6 - Credentials in a URL's userinfo survive redaction and reach the caller

**Files:** `src/fast_mcp_jobvite/utils/redaction.py:96-135`;
`services/jobvite_client.py:489-497`; `errors.py:259-260`.

`redact_url` redacts query **parameters** only. It does not touch RFC 3986 userinfo. Measured:

```
>>> redact_text("ProxyError: unable to connect via http://proxyuser:proxypassword@proxy.internal:8080/path?x=1")
'ProxyError: unable to connect via http://proxyuser:proxypassword@proxy.internal:8080/path?x=1'
```

`jobvite_client.py:495-497` puts `redact_text(f"{type(exc).__name__}: {exc}")` into
`JobviteUnavailableError.detail`, and `errors.py:259-260` returns that `detail` **verbatim** as the
problem object's `detail` member. A deployment behind an authenticating egress proxy
(`HTTPS_PROXY=http://user:pass@proxy:8080`, which httpx reads from the environment) publishes the
proxy credential to the MCP caller on any `ProxyError`, and into the log line that formats it.
`DESIGN.md:314-315`'s rule is "never in an exception message"; this is an exception message.

**Suggested fix.** Redact userinfo inside `redact_url`, where the single enforcement point already
is, so both the log arm and the exception arm inherit it:

```python
    split = urllib.parse.urlsplit(url)
    if split.username or split.password:
        host = split.hostname or ""
        netloc = f"{REDACTED}@{host}" + (f":{split.port}" if split.port else "")
        split = split._replace(netloc=netloc)
        # fall through: a userinfo URL must be reassembled even with no query
```

and relax the `if not split.query: return url` early return so a userinfo-only URL is still
rewritten. Add `test_a_url_with_credentials_in_its_userinfo_is_redacted` and a
`check-u3-audit-controls.sh` row deleting the userinfo branch.

---

## M-1 - `AuditWriteError` is raised inside `except`, so the redacted-away exception rides on `__context__`

**File:** `src/fast_mcp_jobvite/audit.py:323-329`.

`_on_audit_write_failure` computes `detail = redact_text(...)` specifically so the raw exception text
does not travel. It then raises `AuditWriteError(...)` **from inside the `except` block with no
`from None`**, so Python attaches the original exception as `__context__` and any traceback
formatting prints it in full. Measured:

```
 AuditWriteError args        : leaks SUPERSECRET? False
 full traceback              : leaks SUPERSECRET? True
 e.__context__ (OSError)     : leaks SUPERSECRET? True
```

`jobvite_client.py:232`, `:269` and `:497` all use `from None` correctly for exactly this reason.
`audit.py` is the sibling that was missed.

**Suggested fix.** `raise AuditWriteError(...) from None` at `audit.py:326`. Add an arm asserting
`excinfo.value.__context__ is None` and that `traceback.format_exception(...)` carries no credential
- the assertion must be on a bool, per this file's own secret-safe failure convention
(`test_audit.py:20-22`).

---

## M-2 - A configuration value that fails pydantic validation exits 1 with a traceback, not 78

**Files:** `src/fast_mcp_jobvite/config.py:386-397`; `__main__.py:107-112`.

`load_settings` calls `Settings()` outside any `try`, and `main` catches only `ConfigurationError`.
Seven of the fifteen variables carry constraints that pydantic - not `validate_settings` - enforces:
`mcp_port` (`ge=1, le=65535`), `mcp_transport` (`Literal`), `max_results` and `outbound_rate_limit`
(`ge=1`), the two booleans, and `pagination_start_base` (`int`). Measured, running the real entry
point in a real process:

```
JOBVITE_MCP_PORT=99999      -> returncode = 1, ValidationError traceback on stderr
JOBVITE_MCP_TRANSPORT=htp   -> returncode = 1, ValidationError traceback on stderr
```

`__main__.py:62-65` says 78 exists so "a supervisor can tell 'this deployment is misconfigured,
retrying will not help' from an ordinary failure". A mistyped port is the most ordinary
misconfiguration there is and it produces the ordinary-failure code plus a traceback, where §8 #10
asks for the process to exit naming the reason. No test covers any of these seven.

**Suggested fix.** Wrap the construction so every boot-time refusal leaves through one door:

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

`from None` matters: pydantic's `errors()` carries `input_value`, and building the reason list by
hand keeps the value out while `str(exc)` would put it in. Add a `test_boot.py` process arm
asserting `returncode == 78`, `"JOBVITE_MCP_PORT" in stderr` and `"Traceback" not in stderr`.

---

## M-3 - The distinct refusal exit status is asserted only against its own constant

**Files:** `src/fast_mcp_jobvite/__main__.py:65`; `tests/test_boot.py:44,110,118,126,138`;
`tests/test_server.py:156`. **SURVIVING MUTATION.**

```
R3 the distinct refusal exit status becomes 1: *** SURVIVED ***
```

Every assertion is `result.returncode == EXIT_CONFIGURATION_REFUSED`, importing the constant from
the module under test, so changing `78` to `1` keeps 294 tests green. `grep -rn "\b78\b" tests/`
returns nothing. The value is the entire point of the constant - 78 is `EX_CONFIG` from
`sysexits.h`, which is what makes it legible to a supervisor - and nothing holds it.

**Suggested fix.** One line, in `tests/test_boot.py`, beside the arms that already exist:

```python
def test_the_refusal_status_is_sysexits_EX_CONFIG_and_not_a_generic_failure() -> None:
    """78 is EX_CONFIG. A supervisor reads the NUMBER, not our constant's name."""
    assert EXIT_CONFIGURATION_REFUSED == 78
    assert EXIT_CONFIGURATION_REFUSED != 1
```

Add `EXIT_CONFIGURATION_REFUSED = 78 -> 1` as a row in `check-u1-boot-controls.sh`.

---

## M-4 - The whitespace-only credential rule is implemented and untested

**File:** `src/fast_mcp_jobvite/config.py:216-222`. **SURVIVING MUTATION.**

`_empty_is_unset` filters on `not value.strip()`, so `JOBVITE_API_KEY="   "` is correctly treated as
absent. I removed the `.strip()`:

```
R2 empty-is-unset stops stripping whitespace: *** SURVIVED ***
```

With the mutant, a whitespace-only credential is a *present* credential that satisfies
`_check_required_variables` and then fails at Jobvite as a 401 - the exact confusion
`DESIGN.md:913-917` and this function's own docstring exist to prevent. `test_config.py:366-379`
covers `""` only. The behaviour at this SHA is correct; the guard holding it is absent.

**Suggested fix.** Parametrise the existing case:

```python
@pytest.mark.parametrize("blank", ["", " ", "\t", "\n", "   "])
def test_a_blank_or_whitespace_only_value_is_treated_as_unset(clean_env, blank) -> None:
    clean_env.setenv("JOBVITE_TOOLS", "search_jobs")
    clean_env.setenv("JOBVITE_API_KEY", blank)
    clean_env.setenv("JOBVITE_API_SECRET", "s")
    with pytest.raises(ConfigurationError) as excinfo:
        load_settings()
    assert "JOBVITE_API_KEY" in str(excinfo.value)
```

and add `not value.strip() -> not value` to `check-u1-boot-controls.sh`.

---

## M-5 - A third-party exception's `str()` reaches the API consumer

**Files:** `services/jobvite_client.py:495-497`; `errors.py:259-260`.

`backend/error-handling.md` is `priority: required` and says at `:383` "Never leak raw exception
messages from third-party libraries to API consumers", with the BAD exemplar at `:386-396` being
literally `raise BadRequestException(str(exc))`, and at `:493` "Use controlled error messages -
never pass `str(exc)` from third-party libraries". `jobvite_client.py:496` passes
`f"{type(exc).__name__}: {exc}"` for an `httpx2` exception into `JobviteUnavailableError.detail`,
and `problem_from_exception` returns that `detail` unchanged to the caller.

`errors.py:246-249` already states the correct rule for the *unmapped* path - "an arbitrary
exception's `str()` can carry a URL, a credential fragment or an upstream body, and this value
reaches the caller" - and then declines to apply it to the mapped path. `redact_text` bounds the
credential classes it knows about; it does not bound library internals (H-6 is one instance,
`_ssl.c` line numbers and local socket paths are others).

**Suggested fix.** Keep the full redacted string for the log, send a controlled string to the
caller:

```python
        except httpx2.HTTPError as exc:
            logger.warning("jobvite transport failure",
                           kind=type(exc).__name__,
                           reason=redact_text(str(exc)))
            raise JobviteUnavailableError(
                f"Jobvite could not be reached ({type(exc).__name__})."
            ) from None
```

The class name alone satisfies `DESIGN.md:355-358`'s "what distinguishes them is `detail`".
`test_a_transport_error_on_the_jobfeed_route_is_redacted` would need repointing at the log record
rather than at `detail`; note that its current positive half (`assert "jobvite.com" in detail`)
**asserts the leak** as the thing that makes the absence non-vacuous.

---

## M-6 - The timeout question: the brief's named authority does not govern, and the clause that does is unmet

**File:** `src/fast_mcp_jobvite/services/jobvite_client.py:360-361`. **Open question 1, settled.**

The brief asked for `httpx2.Timeout(connect=5, read=30, write=30, pool=5)` to be checked against
`backend/rate-limiting.md`. **That document says nothing about outbound client timeouts.** It exists
(391 lines, `priority: required` at `:10`) and the grep instrument works on it (`grep -cn "Rate"` =
38), and `grep -ni` for each of `timeout`, `connect`, `read_timeout`, `write`, `pool`, `httpx`,
`aiohttp`, `outbound`, `budget`, `backoff`, `deadline`, `upstream`, `egress` returns **zero**. Its
`retry` hits (`:190,193,203,284,309,360`) are all the inbound `Retry-After` response header. It
governs inbound admission only. **A finding phrased as "violates rate-limiting.md's timeout mandate"
would be uncitable.**

The authority is `backend/resilience.md`, also `priority: required` (`:9`):

> `:71-73` "**Every** outbound call MUST set an **explicit connect and read (or total) timeout**. No
> call may rely on the client/SDK default"
> `:74-76` "Timeouts MUST be **shorter than the inbound request's own deadline** so a slow dependency
> surfaces as a fast, typed error rather than a hung request worker."
> `:84-87` `client = httpx.AsyncClient(timeout=httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=2.0))`

**What U4 got right:** `:71-73` and `:249-250` ("**No timeout** on an outbound call … The root
resilience defect") are satisfied - the timeout is explicit and per-phase, and
`check-u4-client-controls.sh` M16 kills the single-scalar mutation. `:84-87` is an **exemplar**, not
a mandate, so `read=30` is not a breach of a number.

**What is unmet:** `:74-76`. This server declares no inbound deadline anywhere -
`grep -rn "deadline" src/ docs/DESIGN.md` finds none, and neither MCP transport imposes one on a
tool body. A `read=30` on the `jobFeed` route with no inbound bound means one slow Jobvite response
pins a worker for 30 seconds, and `resilience.md:95-105` then requires the *retry budget* (U7's) to
fit inside a deadline that does not exist. `read=30` is six times the standard's own exemplar with
no recorded reason.

**Suggested fix.** This is a decision, not a defect to patch silently. Either (a) declare the
inbound deadline - a `JOBVITE_TOOL_DEADLINE_SECONDS` with the per-phase timeouts derived from it, so
`:74-76` is checkable - or (b) record an ADR under this project's own convention ("a deviation from
a `priority: required` standard clause is recorded as an ADR with a `Type:` field") stating that MCP
tool calls carry no inbound deadline and that `read=30` is chosen against Jobvite's observed latency
rather than against a deadline. **(b) needs one number nobody has: Jobvite's observed p99.** Until
U4 has seen a real response (open question 5, still open), I would take (b) and set `read=10.0`,
which is `ai/resilience.md`-shaped and still four times the exemplar. Add a
`check-u4-client-controls.sh` row mutating `read=30.0` to `read=300.0` and a test asserting an upper
bound, so the number is held by something.

---

## M-7 - `redact_arguments` walks a `list` but not the `Sequence` its own type says it takes

**File:** `src/fast_mcp_jobvite/utils/redaction.py:51-53, 203-205`.

`JsonValue` is declared as `… | Mapping[str, JsonValue] | Sequence[JsonValue]`. The walk tests
`isinstance(arguments, list)`. A tuple is a `Sequence` and in contract; it falls through to
`return arguments`. Measured:

```
>>> redact_arguments(({"email": "a@b.c"},))     # tuple
({'email': 'a@b.c'},)                            # UNREDACTED
>>> redact_arguments([{"email": "a@b.c"}])      # list
[{'email': '[REDACTED:str]'}]
```

A pydantic model field typed `tuple[...]`, or any caller that passes a tuple, defeats the
fail-closed walk at the top level. Note the nested case is safe by accident: a tuple under an
*unlisted* key hits `_redacted_value` and becomes `[REDACTED:tuple]`; only an *allow-listed* key or
the top level leaks.

**Suggested fix.** Match the declared type and keep `str`/`bytes` out of it:

```python
    if isinstance(arguments, Sequence) and not isinstance(arguments, str | bytes):
        return [redact_arguments(item) for item in arguments]
```

`Sequence` is already imported at `:43`. Add `test_a_tuple_is_walked_like_a_list` and a
`check-u3-audit-controls.sh` row reverting it to `list`.

---

## M-8 - `__main__.py` reports 58% coverage because its arms run in subprocesses

**Files:** `pyproject.toml:152-178`; `tests/boot_process.py:87-159`. **Open question 6, measured.**

Coverage was never measured by U3. Measured now, at this SHA:

```
src/fast_mcp_jobvite/__main__.py                     36     15      4      0    58%   82, 87, 114-135
src/fast_mcp_jobvite/audit.py                        89      1     14      1    98%
src/fast_mcp_jobvite/config.py                      109      3     28      3    96%
src/fast_mcp_jobvite/server.py                       21      0      2      0   100%
src/fast_mcp_jobvite/services/jobvite_client.py     110      3     26      2    96%
src/fast_mcp_jobvite/utils/correlation.py            11      0      0      0   100%
src/fast_mcp_jobvite/utils/redaction.py              47      0     18      1    98%
TOTAL                                               479     22     96      7    95%
```

**ADR-0010's `utils/` 95% floor is MET** (`redaction.py` 47/47 statements, 17/18 branches;
`correlation.py` 100%), and the client's 90% is met at 96%. That closes open question 6 with a
number.

The defect is `__main__.py` at 58%: lines `114-135` are `_install_shutdown_handler`, the transport
selection, the `except KeyboardInterrupt` and the `finally: os._exit(0)`. Those **are** tested, by
`test_boot.py` and `test_shutdown.py` - but through `subprocess.run`/`Popen`
(`boot_process.py:100,140`), and `[tool.coverage.run]` sets no `concurrency`/`parallel` and no
`COVERAGE_PROCESS_START`, so the child's execution is invisible. The overall `fail_under = 80` is
met only because six other modules carry it. This is a wrong number with a plausible story: the next
reader sees the most safety-critical file in U1 at 58% and either adds an exclusion or deletes the
process arms to "fix" it.

**Suggested fix.** Turn on subprocess measurement so the number reflects the arms that exist:

```toml
[tool.coverage.run]
parallel = true
sigterm = true          # coverage.py writes data when the child takes SIGTERM
```

with `COVERAGE_PROCESS_START=pyproject.toml` propagated in `boot_process.clean_env` and a
`sitecustomize.py` calling `coverage.process_startup()`; then `coverage combine` before the report.
`sigterm = true` matters specifically here because `test_shutdown.py` signals the child.
**If that is judged too much machinery for the value**, the honest alternative is a comment in
`pyproject.toml` naming `__main__.py` as measured out-of-process, so the 58% is not read as a gap -
but do not add `omit`, which would make the number *look* right while measuring less.

Separately: ADR-0010's per-module floors (tool modules 85%, client 90%, utils 95%, critical paths
95% line / 90% branch) are enforced by **nothing**. `ci.yml:560-564` deliberately does not pass
`--cov-fail-under`, and `pyproject.toml:152-153` says the per-module floors "are enforced by the
units that create those modules" - which is a plan, not a gate. Suggest a small
`tests/test_coverage_floors.py` that parses `coverage.json` and asserts the ADR's rows, or the
`coverage.py` `[tool.coverage.paths]`-per-module pattern.

---

## L-1 - `redact_headers` is called by nothing in `src/`

**File:** `src/fast_mcp_jobvite/utils/redaction.py:138-152`.

`grep -rn "redact_headers" --include=*.py .` returns three hits in `tests/test_redaction.py` and the
definition. `jobvite_client.v2_headers()` builds the two credential headers and no code path
redacts them, because no code path logs headers. The function is inoperative shipped code, and
`test_the_client_and_the_redactor_name_the_SAME_two_headers`
(`test_jobvite_client.py:510-517`) pins the two constant lists together while the redactor they
name is never invoked - the pin is real, the consumer is not.

**Suggested fix.** Either call it at the one place headers could reach a log - add
`headers=redact_headers(headers)` to the `logger.debug` at `jobvite_client.py:475-479`, which makes
the belt-and-braces claim in that comment true of headers as well as of the route - or delete it and
the two tests, and note in the docstring that headers are never logged. I lean to the first: it is
one argument and it makes the existing pin load-bearing.

---

## L-2 - `ci.yml`'s own status header is stale about two obligations it says are deferred

**File:** `.github/workflows/ci.yml:20-37` vs `:525-564`.

The header block says under "DEFERRED with an owning unit, NOT silently omitted":

```
32:#     coverage floors -> U1 (src/fast_mcp_jobvite holds only __init__.py, so a
33:#       coverage run reports "No data collected" or a vacuous 100%)
34:#     fastmcp inspect capability-drift diff -> U1
```

Both landed: `:546` runs `uv run --frozen fastmcp inspect` and `:564` runs
`uv run --frozen pytest --cov --cov-report=term-missing`. `pyproject.toml:155-160` carries the same
stale sentence ("the CI coupling step is commented out with a U1 reference … U1 lands the first real
module and turns the step on"). This is the file whose own opening line says the alternative is "a
workflow that reads as tested and is not", and its status block now reads as less tested than it is.
The same block already carries a precedent: `:21-24` records an entry that "stayed here saying 'the
script does not exist' after it did".

I checked this against `3f313ce` only. **`adr-batch` is rewriting `ci.yml`**, so confirm before
editing.

**Suggested fix.** Move both entries out of DEFERRED into the EXECUTED/wired list with their line
numbers, and rewrite `pyproject.toml:155-160` in place rather than appending a correction. Consider
a small check that fails when a `-> U<n>` deferral names a unit whose files exist, which is the
generalisation of the two instances now on the record.

---

## L-3 - The checklist mandates `pyright` and the project declares only `mypy`

**Files:** `docs/CODE-REVIEW-CHECKLIST.md:57`; `pyproject.toml:72-74`.

The Type-safety row is "`pyright` is clean on the delta, and new files are clean outright".
`pyproject.toml`'s dev group declares `pytest-cov`, `ruff` and `mypy`; there is no pyright anywhere
in the lock. I discharged the row with `uv run --frozen --with pyright pyright src/fast_mcp_jobvite`
(exit 0, `0 errors, 0 warnings`), but `--with` resolves **outside the lock**, which is exactly the
defect ADR-0015 records for `pip-licenses` and `ci.yml:30-31` forbids for `pip-audit`. So the row
cannot currently be discharged by a reproducible tool.

**Suggested fix.** Add `pyright>=1.1` to the dev dependency group and `uv lock`, then a CI step
`uv run --frozen pyright src/fast_mcp_jobvite`; or amend the checklist row to name `mypy`, which is
what CI actually gates on. Either resolves it; leaving the row naming a tool the project cannot run
under `--frozen` does not.

---

## L-4 - A local configuration fault is reported as a Jobvite upstream error

**File:** `src/fast_mcp_jobvite/services/jobvite_client.py:415-420`.

A missing `company_id` raises `JobviteUpstreamError(None, "the jobFeed route requires a companyId
credential and none is configured")`, which `errors.py:122` maps to
`/problems/external-service-error` **502** and renders as `"Jobvite returned status none: …"`.
Jobvite returned nothing; the call was never made. The caller is told the upstream failed when the
deployment is misconfigured, which is the same inversion `DESIGN.md:502-509` corrects for Jobvite's
own 401.

Note also that `config.py:310-322` refuses to boot when `get_job_feed` is enabled without
`JOBVITE_COMPANY_ID`, so in a validated deployment this branch is unreachable and its test
(`test_the_jobfeed_route_refuses_without_a_company_id`) exercises a client constructed outside that
guarantee. That is fine as defence in depth; the wrong *type* is the finding.

**Suggested fix.** Raise the internal condition instead. `errors.py` has no configuration row, and
`DESIGN.md:510-511` forbids minting a slug, so `about:blank`/500 via a plain exception is the
honest answer - which is what `problem_from_exception` already does for anything outside the
hierarchy (ADR-0017):

```python
            msg = "the jobFeed route requires a companyId credential and none is configured"
            raise RuntimeError(msg)
```

Repoint the test at `RuntimeError` and assert `problem_from_exception(...)["type"] == "about:blank"`.

---

## L-5 - Non-`HTTPError` httpx2 exceptions escape uncaught and unredacted

**File:** `src/fast_mcp_jobvite/services/jobvite_client.py:489`.

`except httpx2.HTTPError` does not cover the whole library. Measured at `httpx2 2.12.0`:

```
InvalidURL             subclass of HTTPError? False
CookieConflict         subclass of HTTPError? False
StreamError            subclass of HTTPError? False
```

An `InvalidURL` - reachable from a `path` a later unit interpolates - escapes `request()` without
passing through `redact_text` and without becoming a typed error, so it reaches the tool boundary as
an unmapped exception. `errors.py:261-266` does contain it (`about:blank`, class name only), so
there is no leak today; the gap is that the module's stated contract ("Raises:
`JobviteUnavailableError`: If Jobvite could not be reached at all") is not what happens.

**Suggested fix.** `except (httpx2.HTTPError, httpx2.InvalidURL, httpx2.CookieConflict,
httpx2.StreamError) as exc:` - or `except Exception` narrowed by re-raising `FastMcpJobviteError`,
if a future edit is expected to add more. Add a `MockTransport`-free arm calling
`c.request("GET", "/candidate\x00")` and asserting `JobviteUnavailableError`.

---

## L-6 - The shutdown case asserts on source substrings where its sibling uses the AST

**File:** `tests/test_shutdown.py:134-159`.

`test_the_shipped_entry_point_is_what_the_case_exercises` asserts
`"signal.signal(signal.SIGTERM, _term)" in source` and `"os._exit(0)" in finally_block`. The very
next test, `test_the_handler_does_not_read_ambient_state`, explains why that is the wrong
instrument - "this module's own prose NAMES the defect in order to warn about it, and a substring
search cannot tell the warning from the thing it warns against" - and uses `ast.parse`.
`__main__.py:15-16` does carry a near-miss of that shape in its docstring. This is the exact failure
U3's amputation harness found (`A7`, a test asserting its own documentation).

The substring assertions are not vacuous today - `check-u1-boot-controls.sh` M11 and M12 kill both
mutations through the *behavioural* arms - so this is a nit-adjacent Low about instrument choice.

**Suggested fix.** Walk the AST for a `signal.signal` `Call` whose second argument is `Name(id="_term")`,
and for an `os._exit` `Call` inside a `Try.finalbody`, mirroring the sibling test. Keep the
`MARKER_ENTRY` string assertions, which are checking a string literal and are correct as they are.

---

## L-7 - The two ADRs governing these units predate the `Type:` convention and were never backfilled

**Files:** `docs/adr/0010-coverage-targets-remapped.md`,
`docs/adr/0011-three-log-producers-not-one.md`.

`docs/CODE-REVIEW-CHECKLIST.md:41-42` requires that a deviation from a `priority: required` clause be
"recorded as an ADR with a `Type:` field, not left as an undocumented difference". Measured:
**ADR-0001 through ADR-0011 carry no `Type:` field; ADR-0012 through ADR-0022 all do**
(`Design change` x7, `Deviation` x3, one long-form). The convention was clearly adopted at 0012 and
never backfilled.

That is a repository-wide gap, but it lands on this review because **both ADRs in scope are among the
eleven, and both are deviations rather than design changes**: ADR-0010 loosens
`backend/testing.md:583-589`'s per-category coverage targets, and ADR-0011 deviates from
`backend/request-middleware.md:145`'s "One log per request". Each states its clause and its reasoning
in prose - the reasoning is good - but neither is machine-classifiable as a deviation, so a sweep for
"which required clauses do we deviate from" finds three of them and misses these two.

**Suggested fix.** Add `**Type:** Deviation` under the `**Status:**` line of ADR-0010 and ADR-0011,
matching the three that already use that value, and backfill the other nine as `Design change` or
`Deviation` as each warrants. Then hold it: a test that fails when any `docs/adr/*.md` lacks `Type:`
is four lines and belongs beside the existing `docs/reviews/check-*.py` gates.
`adr-batch` is in flight over the ADR set; coordinate before editing.

---

## nit-1 - `enabled_tools`' docstring says "registers nothing" where it registers the four reads

**File:** `src/fast_mcp_jobvite/config.py:243-247`. "so writes-on with `JOBVITE_TOOLS` unset
registers nothing, and naming it without the flag registers nothing either." The first clause is
wrong: with `JOBVITE_TOOLS` unset and `JOBVITE_ENABLE_WRITES=true`, `READ_TOOLS` is registered and
only the write is withheld - which is what `test_enable_writes_true_with_tools_unset_does_not_
register_the_write` asserts.
**Fix:** "so writes-on with `JOBVITE_TOOLS` unset registers **no write**, and naming it without the
flag registers no write either."

## nit-2 - `_empty_is_unset` only strips `str`, so a programmatic `SecretStr("")` is a present empty credential

**File:** `src/fast_mcp_jobvite/config.py:220-221`. Environment variables are always `str`, so this
cannot fire from the environment; `Settings(api_key=SecretStr(""))` reaches
`_check_required_variables` as present. `test_config.py:450-457` and `test_server.py:45-50` both
construct `Settings(...)` directly, so the shape is in use.
**Fix:** also drop a value whose `get_secret_value()` is blank, or assert in `validate_settings`
that no `SecretStr` field is empty.

## nit-3 - `redact_text` deletes punctuation attached to a redacted parameter value

**File:** `src/fast_mcp_jobvite/utils/redaction.py:155-173`. Measured:
`redact_text("… for url 'https://…?sc=BBB'")` returns `… for url 'https://…&sc=[REDACTED]` - the
closing quote was inside the value and is gone. Cosmetic, and it never un-redacts anything, but a
redacted log line that is not a faithful rendering of the original is one people stop trusting,
which is the argument `:104-108` makes for preserving parameter order in the first place.
**Fix:** strip a trailing run of `'"),.;` off the token before `redact_url` and re-append it after.

## nit-4 - A valid inbound `X-Request-ID` is echoed lower-cased, so it is not the caller's string

**File:** `src/fast_mcp_jobvite/audit.py:219`. `return inbound_request_id.lower()`. A caller sending
an upper-case UUIDv4 gets a different string back in `request_id` and in the problem `instance` URN
than the one they logged, so an exact-match join across the two systems fails.
`test_a_valid_inbound_uuid4_is_echoed` uses a lower-case literal and cannot see it.
**Fix:** either return `inbound_request_id` unchanged (the regex is already `IGNORECASE`, and
`error-contract.md:83-85` does not require a case), or keep the normalisation and document it - but
add an upper-case row to `test_a_valid_inbound_uuid4_is_echoed` either way, because at this SHA that
test passes whichever behaviour is intended.

---

# The six open questions the authors could not settle

| # | Question | Answer |
|---|---|---|
| 1 | U4's timeouts vs `backend/rate-limiting.md` | **Wrong authority.** That document says nothing about outbound timeouts (searches and positive control in M-6). The governing clause is `backend/resilience.md:71-76`, `priority: required`. The **shape** is compliant; the "shorter than the inbound deadline" clause is unmet because no inbound deadline exists. See **M-6**. |
| 2 | U3's `"stdio"`/`"http"` vs `config.py` | **They agree, and the agreement is now held.** `audit.py:101-102` `StrEnum` renders `"stdio"`/`"http"`; `config.py:176` `Literal["stdio","http"]`; `__main__.py:118-128` passes the same strings to `mcp.run`. I mutated `str(self.transport)` to `self.transport.name` (`"STDIO"`): **killed**, 3 tests. Nothing structural ties them, though - see the suggestion below. |
| 3 | U3's `ctx.request_context.meta` vs a live FastMCP context | **`parse_trace_context` is correct.** At `fastmcp 4.0.0b4`, `BaseContext.meta` returns `RequestParamsMeta \| None` (`mcp/shared/context.py:58-60`), and `RequestParamsMeta` is `class RequestParamsMeta(TypedDict, extra_items=Any)` (`mcp_types/_types.py:80`) - a plain `dict` at runtime, with `.get`, satisfying `Mapping[str, object]`, and an open map so a wire `traceparent` round-trips. **No call site exists yet**, so the binding is still unwired; see the note below. |
| 4 | U3 vs ADR-0011 (three producers) | **No conflict, but the ADR's premise is unrealised.** `audit.py` is producer #3 exactly as ADR-0011:15 specifies. Producers #1 and #2 - `TimingMiddleware` and `StructuredLoggingMiddleware` - are **not installed**: `server.py:113-120` registers no middleware, and `IMPLEMENTATION-PLAN.md:1566` assigns the middleware block to **U9**, so this is scheduled work and not a U1/U3 defect. What *is* a defect is that producer #3 emits none of its fields - **H-1**. |
| 5 | U4 has never seen a real success body | **Still open, and not closeable from here.** No credential exists in this environment; the `credentialed` arm is deselected by `pyproject.toml:132` and collected only with `--collect-only`. Both success shapes are tolerated (`test_positive_control_a_200_with_status_code_200_SUCCEEDS`, `…_with_no_status_block_at_all_SUCCEEDS`), which is the right hedge for an unknown. It feeds **M-6**: the `read=30` figure has no observed latency behind it. |
| 6 | Coverage vs ADR-0010's 95% for `utils/` | **MET, measured.** `utils/redaction.py` 47/47 statements, 17/18 branches; `utils/correlation.py` 11/11. Overall 95% against a floor of 80. The finding is elsewhere: `__main__.py` at 58% and nothing enforcing the per-module floors - **M-8**. |

**Suggestion for question 2** (nit-level, no finding filed because nothing is wrong today): derive
the audit enum from the configuration type so the two cannot drift -
`Transport = enum.StrEnum("Transport", {v.upper(): v for v in get_args(Settings.model_fields["mcp_transport"].annotation)})`
is one option; a test asserting
`{t.value for t in Transport} == set(get_args(...))` is the cheaper one.

**Note on question 3.** `parse_trace_context` and `audit_scope` have **no production caller** at this
SHA (`grep -rn "audit_scope" src/` returns only `audit.py` itself). The wire contract is right, but
"U3's parse call site" does not exist yet, so the first tool unit must pass
`meta=ctx.request_context.meta` and nothing currently fails if it forgets. Worth a row on U5's
checklist.

---

# What I checked and found clean

So the absence of a finding is bounded, here is what I looked at and did not report.

- **`evaluate_response`'s two arms** (`jobvite_client.py:125-164`). Both fire independently; the
  boundary is tested at 399/400; `bool` is excluded from `int`; five recorded fixtures are pinned
  byte-exact and the *count* of the recorded tier is asserted, so a sixth cannot appear unnoticed.
  `check-u4-client-controls.sh` kills 17/17. I found nothing to add.
- **The HR-XML hardening.** I hypothesised that `defused_fromstring` would raise `ValueError` on a
  document carrying an encoding declaration (`<?xml version="1.0" encoding="UTF-8"?>`), which
  `except (DefusedXmlException, SyntaxError)` would not catch. **Measured and false** - it parses
  cleanly, and end to end through `JobviteClient.request` it produces `JobviteUpstreamError`. Not a
  finding.
- **`follow_redirects` default.** `False` at `httpx2 2.12.0` (measured from the signature), so H-3
  is a pinning finding and not a live exposure.
- **The no-cookie-jar property.** Cleared in a `finally`, and
  `test_positive_control_httpx2_DOES_carry_cookies_by_default` measures the default it is defending
  against rather than asserting it from memory. This is the best control in the three units.
- **The stdio attribution marker.** `ATTRIBUTION_UNAVAILABLE` never contains `"global"`, the client
  id is discarded on stdio, and both the marker and its absence on HTTP are asserted. M1/M2 kill it.
- **`_redacted_value` and the path-keyed allow-list.** I mutated it to pass unlisted **strings**
  through in the clear: **killed**, 5 tests. The container-redacted-whole property (`M14`'s story)
  holds.
- **`is_loopback`'s fail-closed direction.** Unrecognisable is not loopback; `127.0.0.1.evil.example`
  and `""` are covered; `[::1]` is handled.
- **Every-reason-collected.** `validate_settings` accumulates and
  `test_every_reason_is_named_not_just_the_first` asserts `len(reasons) == 2`, not just membership.
- **`_token_map_problems` discards the parse exception**, and
  `test_a_malformed_token_map_is_refused_without_echoing_it` asserts the secret's absence from the
  message. Correct, and the sibling `audit.py` case that is *not* correct is M-1.
- **Logging is on stderr, on the refusal path.** I mutated `stream=sys.stderr` to `sys.stdout`:
  **killed** by `test_a_refusal_writes_nothing_to_stdout`. I also confirmed loguru's autoinit
  handler is stderr, so the serving path does not corrupt JSON-RPC either - though **nothing tests
  the serving path's stdout**, and `spawn_marker_server` redirects it to a file without asserting on
  it. Not filed as a finding because the behaviour is right; worth a row when U5 lands a tool.
- **`mask_error_details=True`** is asserted on the built instance *and* in the source, and M10 kills
  it.
- **Lifespan composition order** is asserted with **two** composed lifespans, which is the only shape
  that can tell "strict reverse" from "same order".
- **The `os._exit` interlock.** `test_server.py:147-151` stubs `build_server` to turn "the refusal
  did not fire" into a red test instead of a 22-minute hang. Good.
- **The three-cycle shutdown arm** is a measured correction to a one-cycle coin flip, and M12 kills
  the amputation.
- **`redact_url` returns byte-identical output when there is nothing to redact**, which is why
  `test_a_url_carrying_no_secret_is_untouched` is meaningful.
- **`errors.py`** was not in scope (U2, round 1) and I read it only to trace where `detail` goes.

---

# The checklist, row by row

`docs/CODE-REVIEW-CHECKLIST.md`, worked in order. **A row I could not verify is not ticked.**

### Functionality
| Row | Verdict |
|---|---|
| Accomplishes the stated task requirements | **PASS with findings.** U1's four refusals, U3's event and redaction, and U4's invariant are all present and behave as specified. H-1 means U3's event does not *reach* anything. |
| Edge cases properly handled | **FINDING** - M-2 (pydantic-validated values), M-4 (whitespace), M-7 (tuple), L-5 (non-`HTTPError`). |
| Error handling appropriate and user-friendly | **FINDING** - M-5 (`str(exc)` to the caller), L-4 (a local fault reported as 502). |
| No obvious bugs or logic errors | **FINDING** - H-1, H-2. |

### Architecture
| Row | Verdict |
|---|---|
| Separation of concerns | **PASS.** `server.py` holds the instance and lifespan only and registers no tool; redaction is one module; `errors.py` owns the registry. |
| Changes respect FROZEN `DESIGN.md` | **PASS.** `git diff 3f313ce~N -- docs/DESIGN.md` shows no U1/U3/U4 commit editing it; the ADRs are numbered. |
| Deviation from a `priority: required` clause recorded as an ADR with a `Type:` field | **FINDING.** M-6 (`resilience.md:74-76`) and M-5 (`error-handling.md:383`) are undocumented deviations; and the two in-scope ADRs that *are* written both lack the `Type:` field - **L-7**. |

### Code quality
| Row | Verdict |
|---|---|
| Follows `backend/python.md` | **PASS.** ruff exit 0, format exit 0. `python.md` mandates no logging library, no `os._exit`/signal rule, no redaction rule (verified by grep, in the standards report). |
| No duplication | **PASS.** `ERROR_STATUS_THRESHOLD` is named once for both arms; `env_name` is the single mapping. |
| Focused functions | **PASS.** |
| Naming clear and consistent | **PASS**, except nit-1's docstring. |
| No hardcoded values | **PASS with M-6** - the timeout numbers are literals with no recorded derivation. |
| No debug code or stray `print` | **PASS.** `sys.stderr.write` is used deliberately at `audit.py:348-355` with the T20 reason stated; ruff T20 is on for `src/`. |

### Type safety
| Row | Verdict |
|---|---|
| Type hints on all functions | **PASS.** |
| Pydantic models for request/response shapes | **PASS** for configuration; no tool request/response shapes exist yet. |
| `pyright` clean on the delta, new files clean outright | **PASS** - `0 errors, 0 warnings` - but see **L-3**: pyright is not a declared dependency, so I ran it outside the lock. |

### Security
| Row | Verdict |
|---|---|
| No secrets or credentials in code | **PASS.** Test literals are prefixed `FAKE-`/`TEST` with `# noqa: S105`; `.secrets.baseline` is present. |
| Authentication checked before privileged operations | **N/A at this SHA** - the HTTP auth block is U9's (`IMPLEMENTATION-PLAN.md:1566`). `config.py` refuses to start `http` without `JOBVITE_HTTP_TOKENS`, which is the boot half. |
| Authorization verified | **N/A** - scope checking is U9/U10's. |
| Input validation present (Pydantic) | **PASS** for configuration; M-2 is about what happens when it *fails*. |
| Audit logging for sensitive operations | **FINDING - H-1, H-2.** The record is built correctly and neither reaches a sink with its fields nor fails closed. |
| Secret-class `.env.example` values empty, `.env` gitignored | **PASS.** `test_the_whole_committed_template_loads` and `tests/test_repo_hygiene.py` cover both. |
| No vendor document / PDF / unlicensed specification added | **PASS.** `.file-type-allowlist` and `scripts/check-committed-file-types.py` are wired; `git diff --stat` over the U1/U3/U4 commits adds `.py`, `.md`, `.json`, `.txt`, `.html` only. |

### Testing
| Row | Verdict |
|---|---|
| Unit tests cover new functionality | **PASS.** 294 tests, 95% overall. |
| Tests are meaningful (not just for coverage) | **PASS in the main, with H-4, M-3, M-4 as the exceptions** - three assertions whose names claim more than their bodies exercise. |
| Integration tests for behaviour changes | **PASS.** `test_boot.py` and `test_shutdown.py` run the real entry point in real processes and assert the teardown side effect, never the exit code. |
| Tests deterministic | **PASS.** Ran the full suite four times across this review; 294 passed each time. The one known race (single-cycle shutdown) is already mitigated to three cycles. |
| Edge cases have test coverage | **FINDING** - M-2, M-4, M-7, H-4. |

### Performance
| Row | Verdict |
|---|---|
| Large result sets paginated | **N/A** - paging is U6's; `request` is deliberately the one-call path. `evaluate_response` returns an unbounded decoded body, and `ai/tool-calling.md:153` requires "**Bound result size** before returning it to the model" - **flagged for U6**, not filed against U4. |
| Appropriate caching | **N/A** - `ResponseCachingMiddleware` is excluded by design and its absence is asserted (`IMPLEMENTATION-PLAN.md:1091-1099`). |

### Documentation
| Row | Verdict |
|---|---|
| Public functions have docstrings | **PASS** - every public callable in all six modules. |
| Complex logic has explanatory comments | **PASS**, unusually so. |
| README updated if needed | **N/A** - README is U13, task #8. |
| CHANGELOG fragment present | **PASS** - `changelog.d/22-…`, `27-…`, `32-…` for U1, U3, U4. |

### Project additions
| Row | Verdict |
|---|---|
| Gate judged by exit code | **DONE.** Every gate above ran on its own line with `EXIT=` printed; no `\| tail` or `\| grep` stood in for a status. |
| Zero skips, passed-count quoted | **DONE.** `294 passed, 2 deselected`, **0 skipped**. The 2 deselected are the `credentialed` and `network` markers, deselected by `pyproject.toml:132` with `--strict-markers` on so a typo cannot silently select nothing. |
| Citations verified by subject | **DONE.** Every `file:line` in this report was produced by `grep -n`, by a numbered `Read`, or by a tool's own output. I did not count offsets inside a `sed -n X,Yp` window. |
| New test checked for vacuity by amputation, not only mutation | **PARTIAL.** I re-ran the three **control** harnesses (13/13, 15/15, 17/17, exit 0) and added seven mutations of my own, five of which survived. I did **not** re-run the three amputation harnesses - see "What I did not verify". |
| A claimed absence states where the search looked | **DONE.** Each absence below names its search. |

---

# Absences, and where I looked

- **No loguru configuration exists in shipped code.** `grep -rn "loguru\|logger\.add\|logger\.remove\|logger\.configure" --include=*.py .` over the whole worktree: 4 hits in `src/` (two `from loguru import logger`, two comments), 5 in `tests/`, 1 in `test_manifest.py`'s pin. Positive control: the same grep finds the `logger.add` calls in both test files, so the pattern works.
- **`redact_headers` has no caller in `src/`.** `grep -rn "redact_headers"` over the whole worktree: definition + 3 test hits. Positive control: the same grep finds `redact_arguments`' two `src/` call sites.
- **No test asserts the literal `78`.** `grep -rn "\b78\b" tests/` returns nothing; the same pattern finds three hits in `docs/`, so the instrument works.
- **`backend/rate-limiting.md` contains no outbound-timeout clause.** Thirteen `grep -ni` patterns, each zero; positive control `grep -cn "Rate"` = 38 on the same path. The file resolves (391 lines).
- **No inbound deadline is declared.** `grep -rn "deadline" src/ docs/DESIGN.md` returns nothing; the same grep over `evolv-coder-standards` finds `resilience.md:74`, so the pattern works.
- **ADR-0001 through ADR-0011 carry no `Type:` field; ADR-0012 through ADR-0022 do.** Per-file loop
  `for f in docs/adr/0*.md; do grep -q "^\*\*Type:\|^Type:" "$f" || echo "$f"; done`, which lists
  exactly 0001-0011. Positive control: `grep -h "^\*\*Type:"` over the same glob returns 11 lines
  (`Design change` x7, `Deviation` x3, one long-form). **I first wrote this absence as "none of the
  22 carry it", from a misused `grep -Ln`. That was wrong and is corrected here rather than
  appended to** - the clean zero explained itself, which is exactly when to hand-check one case.

---

# What I did NOT verify

Not "did not try" - these are the things I could not settle at this SHA.

1. **Whether the three amputation harnesses still pass, and what survives them.** I ran the three
   **control** harnesses (all exit 0). I did not re-run `check-u1-boot-amputation.sh`,
   `check-u3-audit-amputation.sh` or `check-u4-client-amputation.sh`: each spawns real servers per
   row with a 20-second grace, and the U1 one signals processes, so a full pass is a long serial run
   I judged a worse use of the budget than the seven targeted mutations that produced H-3, H-4, M-3
   and M-4. **Their survivor lists are the output** and nobody has read them since the units landed.
   Recommend running all three before this branch merges.
2. **Whether Jobvite's real success body carries a `status` block, and its observed latency.**
   No credential is available here and the `credentialed` arm is deselected by design. This is open
   question 5 and it is the input M-6's `read=30` needs.
3. **Whether `mcp.run(transport="http", …)` actually serves under the settings U1 passes it beyond
   opening a port.** `test_boot.py` asserts `wait_for_port`; nothing performs an MCP handshake over
   HTTP. That is U9's arm and I did not attempt it.
4. **Whether `fastmcp inspect` at `ci.yml:546` produces a stable artefact.** The step exists; I did
   not run it, and `ci.yml:35-37` already records that standing it up is not the same as executing
   it against a real capability change. Note `adr-batch` is rewriting `ci.yml`.
5. **Whether H-1's suggested `serialize=True` sink interacts with `StructuredLoggingMiddleware` when
   U9 installs it.** ADR-0011 keeps three producers; two of them are the framework's and I have not
   read how FastMCP configures its own logging. The fix should be re-reviewed when U9 lands.
6. **The `docs/` prose that cites these modules.** I read `DESIGN.md`, `IMPLEMENTATION-PLAN.md`,
   ADR-0010 and ADR-0011 only where a finding needed them. `adr-batch` is rewriting `DESIGN.md` and
   its citations concurrently, so a citation sweep from this SHA would be judged against a tree that
   no longer exists.

---

**Report written at `3f313ce`, committed on `review/code-r2`. Worktree `/tmp/code-review-r2-work`
removed after commit.**
