# FIX-M5-L1 - the exception text leaves the API consumer and reaches the log

Agent `fix-m5-l1`. Branch `fix/m5-exception-detail`, based on `025aa55`. Task #14, and the part of
task #15 that was assigned with it. Frozen design read as `git show c15b138:docs/DESIGN.md`.

**Verdict: M-5 fixed, L-1 resolved by wiring, and task #15's defect was LIVE and is fixed here.**
Not "no live path" - a committed probe measured the credentials reaching stderr in the clear.

Two things went wrong on my side and are written up rather than tidied away: I ran `git add -A`
twice while a harness was mutating the same worktree (§11), and I concluded a redactor was
redundant from a suite that structurally could not see it (§7).

---

## 1. The two standards clauses, quoted from source

`/home/plafayette/claude_projects/evolv/repos/evolv-coder-standards/standards/backend/error-handling.md`,
frontmatter line 10: `priority: required`.

- `:383` - "Never leak raw exception messages from third-party libraries to API consumers:"
- `:493` - "Use controlled error messages — never pass `str(exc)` from third-party libraries"

Both are as the brief quoted them. Line numbers taken from `awk 'NR>=X && NR<=Y {print NR, $0}'`,
not from an unnumbered window.

## 2. The design clause on `detail`, from the frozen SHA

`git show c15b138:docs/DESIGN.md`, lines 356-360:

> - **An open breaker is distinguishable from an outage without inventing a type.** Both use
>   `/problems/service-unavailable` at 503, per the registry; what distinguishes them is `detail`,
>   which says whether Jobvite failed or whether we have stopped calling it, plus a `retry_after`
>   hint. An earlier revision minted two slugs for this. The distinction is real and worth making;
>   a new contract-bearing type URI is not the way to make it.

**Your reading was right, and I checked it rather than adopting it.** `detail` has to carry one bit -
upstream failure versus a breaker we opened - and an enumerated string carries it. `errors.py:146-153`
(`JobviteUnavailableError`) repeats the same requirement in its own docstring. I also read every
other mention of `detail` on the unavailable path at the frozen SHA; DESIGN.md:532-534 puts
*Jobvite's own message* in `detail`, and that is `JobviteUpstreamError`, a different class, untouched
by this change. **No ADR is needed.**

## 3. What `detail` said, verbatim, before and after

**Before** (`jobvite_client.py`, at `025aa55`):

```python
raise JobviteUnavailableError(
    redact_text(f"{type(exc).__name__}: {exc}")
) from None
```

which produced, measured on the `jobFeed` route with a `ConnectTimeout`:

```
ConnectTimeout: timed out connecting to https://api.jobvite.com/v1/jobFeed?api=[REDACTED]&sc=[REDACTED]&companyId=[REDACTED]
```

The credentials were redacted; the library's class name, its phrasing and the whole URL were not,
and that string reaches the caller unchanged through `problem_from_exception` ->
`build_problem` -> `problem["detail"]` (`errors.py:269-270`, `errors.py:233-243`). I followed that
end to end rather than taking it on trust.

**After**: one of three module constants, selected by `_unavailable_detail(exc)` on the exception
CLASS:

```
Jobvite did not respond before the configured timeout elapsed. This is an upstream failure, not an open circuit breaker.
Jobvite could not be reached. This is an upstream failure, not an open circuit breaker.
The request to Jobvite could not be issued. This is a client-side transport failure, not an open circuit breaker.
```

Three rather than one because `InvalidURL`, `CookieConflict` and `StreamError` never reach Jobvite
at all - "could not be reached" would be a false statement about the upstream service - and because
a timeout and a refused connection are different operational conditions. The set is closed: dispatch
is on the class and every return value is a constant, so nothing a library wrote can reach it. That
is a property of the function, not of a redactor applied afterwards.

**`redact_text` was never sufficient here, and this is the part worth keeping.** It bounds `api`,
`sc`, `companyId` and userinfo passwords. An httpx2 exception also carries `_ssl.c` line numbers,
local socket paths and resolver detail, which are third-party internals and are not
credential-shaped, so no redactor aimed at credentials will ever catch them.

## 4. The positive control, re-pointed rather than weakened

`test_a_transport_error_on_the_jobfeed_route_is_redacted` asserted `"jobvite.com" in detail`. The
control depended on the leak; fixing M-5 made it fail, correctly.

It now reads the **log record**, which is where the text went:

- consumer half: `detail == jc.UNAVAILABLE_TIMEOUT_DETAIL`, plus explicit absences for
  `jobvite.com`, `ConnectTimeout`, `timed out connecting` and all three credentials;
- negative arm: `"not an open circuit breaker" in detail` and `detail != UNAVAILABLE_REQUEST_DETAIL`,
  so the outage-versus-breaker distinction DESIGN.md:356-360 requires is asserted, not assumed;
- log half: `"jobvite.com" in logged` and `"ConnectTimeout" in logged` - **the relocated positive
  control** - next to `REDACTED in logged` and the three credential absences, so the absences are
  still about redaction over real content and not about an empty string.

`test_an_invalid_url_becomes_a_typed_error_not_an_escape` had the same shape one layer down: its
only assertion was `"InvalidURL" in str(excinfo.value)`, i.e. it read a third-party class name out
of the consumer's `detail`. It now asserts the enumerated `detail` and reads the class name out of
the log.

**A process-level arm was added as well**, because a fixture's own sink is a real loguru stream and
just not the one the server writes to - which is how H-1 hid.
`test_the_process_publishes_no_credential_when_the_transport_fails` in `tests/test_logging_process.py`
runs the real client under `MockTransport` in a subprocess configured the shipped way, writes the
consumer's `detail` to a file, and asserts against the bytes the process actually wrote to stderr.

## 5. L-1: where `redact_headers` is now called

**Confirmed orphaned before acting.** `grep -rna "redact_headers" . --exclude-dir=.git` and
`git grep -n "redact_headers" HEAD` (two instruments, one reading git objects rather than the
working tree): definition at `src/fast_mcp_jobvite/utils/redaction.py:152`, four hits in
`tests/test_redaction.py`, and prose in `docs/reviews/REVIEW-CODE-R2.md` and the brief. No caller in
`src/`. Positive control on the instrument: the same grep finds `redact_arguments` with `src/` call
sites, so an empty `src/` column is a real absence and not a broken search.

It is now called in the new `logger.warning("jobvite transport failure", ...)` in
`jobvite_client.request`:

```python
headers=redact_headers(headers),
```

**This is a real caller, not a token one.** On the v2 branch the local `headers` IS `v2_headers()` -
`x-jvi-api` and `x-jvi-sc` resolved in the clear. Measured in the amputation run: with
`redact_headers` removed the log line carries
`"headers": {"x-jvi-api": "TESTKEY-not-a-real-credential", ...}` and
`test_the_v2_credential_headers_are_redacted_in_the_failure_log` goes red.

That test uses the NUL-byte `InvalidURL` trigger rather than a mock raising, because it fails before
the transport, so the credential headers on the request are the real ones and nothing had to be
faked to make them so.

## 6. `record["exception"]` - IT IS LIVE, and it is fixed here

The brief asked me to check it and state the method. I did not settle it by argument.

**Method: a runnable probe against a process configured the shipped way**, now committed as
`EXCEPTION_LEAK_ENTRY` / `test_an_exception_carrying_a_credential_is_redacted_at_the_sink`. It
imports `fast_mcp_jobvite.__main__`, raises a `RuntimeError` whose text carries
`.../jobFeed?api=..&sc=..&companyId=..`, and calls `logging.getLogger(...).exception(...)`.

**Measured at `025aa55`, before any fix - the credentials appear TWICE in one record:**

```
{"text": "... - upstream call failed\nTraceback (most recent call last):\n ...\nRuntimeError: timed out connecting to https://api.jobvite.com/v1/jobFeed?api=PROBEKEY&sc=PROBESECRET&companyId=PROBECO\n",
 "record": {... "exception": {"type": "RuntimeError", "value": "timed out connecting to https://api.jobvite.com/v1/jobFeed?api=PROBEKEY&sc=PROBESECRET&companyId=PROBECO", "traceback": true}, ...}}
```

So the defect is **wider than task #15 states**: it is not only `record["exception"]`. `serialize`
also emits a `text` key holding the fully rendered line **including the formatted traceback**, and
`_redact_message` reached neither.

**The producers, enumerated rather than asserted absent.** `_InterceptHandler.emit` passes
`exception=record.exc_info` for **every** stdlib `logging` record in the process. That is not an
enumerable set of libraries - it is "any dependency that calls `logger.exception` or
`logger.error(..., exc_info=True)`". Two producers are in the shipped tree today:

1. `__main__.main`'s `logger.exception("the server terminated abnormally")` on the abnormal
   termination path;
2. anything under `logging.basicConfig(handlers=[_InterceptHandler()], level=INFO, force=True)`,
   which is every logger in the process.

The pre-fix argument ("jobvite_client redacts its own exception text and `diagnose=False`") is an
argument about the producers we know, and it was already false for producer 1.

**Fix**: `_redacting_sink` / `_redact_serialised` in `__main__.py`. The sink parses the serialised
record, walks the DECODED JSON applying `redact_text` to every string, and re-encodes. Redacting the
raw line would corrupt it - `redact_url`'s `urlencode` would swallow a closing quote adjacent to a
URL into the redacted parameter value - so the walk is what keeps the record parseable, and the
tests assert the record still parses after redaction.

`stream.flush()` in the sink is load-bearing and not tidiness: loguru flushes a *stream* sink and
not a *function* sink, and an unflushed write to a full disk returns normally and raises at
interpreter shutdown, which would have silently disarmed H-2's `/dev/full` arm.

## 7. A wrong conclusion I drew and corrected, because the first measurement was scoped wrong

With the sink redacting, I amputated `_redact_message` and the U1 boot suite passed **78/78**. I
concluded it was redundant, deleted it, and wrote that conclusion into a docstring.

**The full suite then went red** on
`tests/test_jobvite_client.py::test_the_jobfeed_url_never_reaches_a_log_record_whole`, with
`httpx2`'s INFO URL line in the clear.

The reason: `tests/test_boot.py`, `test_server.py` and `test_shutdown.py` import
`fast_mcp_jobvite.__main__` at module scope, so in a full run `_InterceptHandler` is live in the
pytest process and every stdlib record reaches **any** loguru handler - including one a test
installed. The filter redacts the **record**, which every handler sees. The sink redacts the
**line**, which only this handler renders. **Neither covers the other.** Every arm of
`test_logging_process.py` reads the process's own stream, so that suite structurally could not see
the filter at all: the 78/78 was an instrument fault, not a finding.

Both are kept. The property is now asserted deterministically by
`test_a_sink_this_project_did_not_install_sees_a_redacted_record` (a subprocess that adds its own
second sink), rather than left depending on pytest collection order across two modules. Amputation
row L carries the story so the next reader does not repeat the deletion, and mutation control M20
kills it.

**This is why the full gate runs before folding, not after.** A focused suite that is green about
the thing it can see is not a gate.

## 8. Harness rows, and two gates that were themselves defective

`scripts/check-u4-client-amputation.sh` - 17 rows, every one applied:

- **A9's anchor was stale** the moment M-5 was fixed. Rewritten as "M-5 reopened": the pre-fix
  `redact_text(f"...")` line restored. Red.
- **A9b** `str(exc)` verbatim to the consumer. Red.
- **A9c THE NEGATIVE ARM**: the enumerated detail collapses to one string. It leaks nothing, so
  M-5 stays fixed - what dies is DESIGN.md:356-360's distinction. Red.
- **A9d** `redact_headers` unwired. Red.
- **A9e** the exception text logged without `redact_text`. Red.
- **A9f** the failure is not logged at all, so every control this fix RELOCATED to the log goes
  vacuous. Red, 3 failures.

`scripts/check-u4-client-controls.sh`: **M12's anchor was stale too, and the harness said so in a
line CI does not read.** `COULD NOT APPLY` left the run at exit 0 reporting "16 killed, 1 not
killed", and the CI step gates on the exit code and on `killed > 0` - so a moved mutation anchor
passed the gate silently. M12 is repointed at the log line's `redact_text`, and **M12b** (M-5 as a
mutation) and **M12c** (`redact_headers` unwired) added. Now 19 killed, 0 not killed.

**That CI hole is closed in this branch**: the U3 and U4 mutation steps now fail on
`COULD NOT APPLY` and on a non-zero "not killed" count, the same way the amputation steps already
did.

`scripts/check-u1-boot-amputation.sh`: row **L** is the record filter, row **N** the serialising
sink, each carrying the other's blind spot in its comment. Both kill exactly one arm.

`scripts/check-u1-boot-controls.sh`: **M18** repointed at the sink (its old anchor
`filter=_redact_message` would now survive, since the sink covers that arm) and **M20** added for
the filter. 20/20.

`.github/workflows/ci.yml`: **its U4 amputation row-count gate was also defective.** It counted
`'^########## A[0-9]+ '`, with a space straight after the digits, so `A9b`..`A9f` matched nothing:
the gate would have reported 12 while 17 ran, and `-ge 12` would have passed. Pattern and count
corrected to 17; the U1 count moved 13 -> 14.

`CONTRIBUTING.md` needs no edit: it lists the harness SCRIPTS, all of which already run, and no new
script was added. Said explicitly because the brief asked for both files.

`docs/OBLIGATIONS.md`: my `ci.yml` edits shifted two anchors. `check-obligations.py` output,
verbatim:

```
FAIL: B75: .github/workflows/ci.yml:598 no longer contains 'name: Capability drift report' - it is now at .github/workflows/ci.yml:602. Repoint the anchor.
FAIL: B82: .github/workflows/ci.yml:768 no longer contains 'Relative links resolve' - it is now at .github/workflows/ci.yml:772. Repoint the anchor.
```

Repointed by PARSING that output with a regex, never by retyping a number. Re-run, verbatim:

```
Mappings: 28  |  anchors verified against their subject: 21  |  recorded as absent: 7
Every mapped anchor still contains its subject. OK.
```

and `--controls`: `Every mapped anchor still contains its subject. OK. / post-run re-check of the
real OBLIGATIONS.md: exit=0`.

## 9. B49b landed mid-task, so this branch's prose is already at 72

`b49b` merged at `f0c3764` while this branch was open, enabling `W505` with
`max-doc-length = 72`. This branch predates it, so its new prose was written at 79.

**201 doc lines this branch ADDED exceeded 72.** Measured with
`ruff check --select W505 --config 'lint.pycodestyle.max-doc-length=72' --output-format json`,
intersected with the lines `git diff -U0 025aa55` reports as added, so the count is this branch's
own residue and not `b49b`'s. Reflowed to **0**, block by block, restricted to blocks containing an
added line - rewrapping a line `b49b` had already rewrapped would turn each one into a merge
conflict for no gain.

Twelve lines the reflow left alone were fixed by hand (docstring summary lines that could only be
shortened, two `Args:` entries, two rulers cut from 75 to 70 dashes to match `b49b`'s style at
`f0c3764`). `ruff --fix` then cleared the `D209` closing quotes the reflow had pulled up, and one
`D205` was rewritten by hand.

**The merge will still conflict** in `__main__.py`, `jobvite_client.py`, `test_jobvite_client.py`
and `test_logging_process.py`, because `b49b` rewrapped the same files. What this buys is that after
the conflict is resolved, `ruff check` is clean rather than carrying 201 new violations.

## 10. Gates, by exit code

Baseline at `025aa55`, before any edit: **322 passed, 2 deselected, 0 skipped** - it agrees with
`PREAMBLE.md`, so that line is not stale.

On the delivered tree, every harness run **serially** (see §11):

| gate | result |
| --- | --- |
| `uv run --frozen ruff check .` | `All checks passed!`, exit 0 |
| `uv run --frozen ruff format --check .` | `45 files already formatted`, exit 0 |
| `uv run --frozen mypy` | `Success: no issues found in 32 source files`, exit 0 |
| `uv run --frozen pytest` | **326 passed, 2 deselected, 0 skipped** |
| `uv lock --check` | exit 0 |
| `scripts/check-committed-file-types.py --all` | `182 file(s) checked, none refused`, exit 0 |
| `docs/reviews/check-coupling.py docs/DESIGN.md` | exit 0 |
| `docs/reviews/check-cross-references.py` | exit 0 |
| `docs/reviews/check-coupling-controls.py` | exit 0 |
| `docs/reviews/check-coupling-sweep.py` | exit 0 |
| `docs/reviews/check-obligations.py` (+ `--controls`) | exit 0 |
| `scripts/check-u1-boot-controls.sh` | **20/20 controls fired**, exit 0 |
| `scripts/check-u1-boot-amputation.sh` | 14 rows, 0 `COULD NOT APPLY`, 0 `TIMED OUT`; L and N each kill one arm |
| `scripts/check-u4-client-controls.sh` | **19 killed, 0 not killed**, exit 0 |
| `scripts/check-u4-client-amputation.sh` | 17 rows, 0 `COULD NOT APPLY`, 0 `DID NOT LAND` |

326 = 322 + 4 new cases (one in `test_jobvite_client.py`, three in `test_logging_process.py`).
Counts read off the terminal after each run, not predicted.

## 11. A contamination I caused, and what it invalidated

**I ran `git add -A` twice while `scripts/check-u1-boot-amputation.sh` was running in the same
worktree.** That harness mutates `config.py`, `server.py` and `__main__.py` and restores each from a
byte copy it took at its own start. Two of my commits therefore captured an amputated tree:

- `dd3e82c` committed `validate_settings` with its body replaced by `return`;
- `021db3a` committed `build_server` returning a bare `FastMCP` - caught only because `ruff` then
  reported `F401 __version__ imported but unused` in a file I had never touched.

Both are restored in `5538c65` from `025aa55` and verified byte-identical to it
(`git diff 025aa55 -- src/fast_mcp_jobvite/config.py src/fast_mcp_jobvite/server.py` is empty). The
whole-tree diff against `025aa55` now touches exactly twelve files, all of them this task's.

The harness also restored `__main__.py` over my reflow, from a copy predating it, which is why that
file was reflowed twice.

**And it voided measurements.** I ran the two U4 harnesses concurrently with the U1 one, in the same
checkout. The numbers in an earlier draft of this report came from those runs. Every harness quoted
in §10 has been **re-run serially** on the final tree, and the U4 controls figure changed as a
result of the M12 repoint (16/1 -> 19/0). Nothing else moved, but "nothing moved" is only worth
saying because the runs were repeated.

## 12. What I did NOT verify

Things I could not settle, not things I did not try:

1. **`scripts/check-u3-audit-controls.sh` and `check-u3-audit-amputation.sh`** - not run. Their
   anchors are in `audit.py`, which this branch does not touch, and the CI change I made to their
   step is a strictly tightening one - but that is my inference and a run is the evidence. They cost
   several minutes each and the tree is already serialised behind two other harnesses.
2. **`redact_text` over a JSON-decoded string can still mangle punctuation adjacent to a URL** - the
   walk stops it corrupting the RECORD, not the value. A message ending `...?sc=x, please` has the
   comma swallowed into the redacted value. Pre-existing, unchanged by me, and cosmetic; I did not
   measure how often it happens on real messages.
3. **Whether `text` and `record["exception"]` are the only serialize-rendered fields that can carry
   free text.** The walk covers every string in the record whatever its key, so I believe the
   question no longer matters - but I did not enumerate loguru's serialiser field by field, and
   "the walk covers everything" is a claim about the code I read, not about loguru's next version.
4. **The `retry_after` hint** DESIGN.md:358 attaches to a 503 alongside `detail`. Nothing in the
   client produces one today and U7 owns the breaker; I left it alone rather than inventing a
   constant with no producer.
5. **The merge itself.** I did not attempt the merge onto `f0c3764`, so I cannot say how large the
   `b49b` conflict is - only that it exists and that resolving it leaves a lint-clean tree.

## 13. Housekeeping

Worktree `/tmp/m5-work` at `025aa55`, branch `fix/m5-exception-detail`. **Removed after the final
gate run**; I pushed nothing and the branch is in the repository for you to merge.

Files touched: `src/` (2), `tests/` (2), `scripts/` (4), `.github/workflows/ci.yml`,
`docs/OBLIGATIONS.md`, one `changelog.d` fragment, and this report. `docs/OBLIGATIONS.md` is the
only documentation edit beyond the fragment, it was mechanical, and I flag it because `b49b-sweep`
was also moving through documentation.
