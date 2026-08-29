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
| R3-M1 | Medium | `JOBVITE_HTTP_TOKENS` accepts an **empty-string bearer token** at boot | Proved at boot |
| R3-M2 | Medium | `check-u1-pid1-shutdown.sh` verifies PID-1 on the `http` arm only | Proved by read |
| R3-L1 | Low | `TOOL_REQUIREMENTS` may silently under-require a tool added to `KNOWN_TOOLS` | Latent, unguarded |
| R3-L2 | Low | `_token_map_problems` accepts a token mapped to **zero** scopes | Proved |
| R3-L3 | Low | `AuditEvent.to_record`'s `optional` dict is a hand-kept second list of fields | Latent, unguarded |

_(more below; this file is committed incrementally)_

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
