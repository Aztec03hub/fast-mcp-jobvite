# BODY-CAP - `DESIGN.md:165`'s 1 MiB body cap, landed at the ASGI seat

Task **#81**, branch `feat/body-cap`, based at `27c6944`. Worktree `/tmp/body-cap-work`.

---

## 1. The question that could have ended the unit: could `uvicorn_config` have done this?

**No. Measured, not read.** `uvicorn 0.52.4` - the locked version - has **no request-body ceiling
of any kind**, so `uvicorn_config` cannot discharge `DESIGN.md:165` and the middleware was necessary.

The answer is committed as a runnable probe rather than as this paragraph, because prose about a
measurement decays into a claim about one: `scripts/probe-uvicorn-body-limit.py`. It serves a
counting ASGI application behind a real uvicorn and posts two megabytes twice. Verbatim:

```
$ uv run --frozen python scripts/probe-uvicorn-body-limit.py
uvicorn 0.52.4, h11_max_incomplete_event_size=1024
the cap DESIGN.md:165 asks for: 1048576 bytes

  A. Content-Length: 2097152 -> HTTP 200, the app saw 2097152 bytes
  B. chunked, NO Content-Length  -> HTTP 200, the app saw 2097152 bytes

FINDING: uvicorn passed BOTH oversized bodies through untouched.
         There is no request-body ceiling in `uvicorn.Config`, so
         `uvicorn_config` cannot discharge DESIGN.md:165 and the
         ASGI middleware seat is the answer.
$ echo $?
0
```

**`h11_max_incomplete_event_size=1024` is a positive control, not decoration.** It is the only
`uvicorn.Config` parameter whose name suggests a size ceiling on an inbound request, and setting it
to one kibibyte while a two-megabyte body sails through is what establishes that it is *not* one. It
bounds the buffer held for an **incomplete** h11 event - the request line and headers - and body
data arrives as complete events that are never held against it.

**Where I looked, so the absence is a claim about a place.** The full parameter list of
`uvicorn.Config.__init__` (55 parameters, read by `inspect.signature`), and a grep over the
installed `uvicorn` package for `max_body|body_size|MAX_BODY|content-length|content_length`. Every
`content_length` hit in that package is framing arithmetic - `expected_content_length` counting down
what remains of a body it has been told to expect - and none is a configurable maximum.
`ws_max_size` is a websocket frame limit and `limit_max_requests` is a request **count**.

---

## 2. What was built

`BodySizeLimitMiddleware` in `src/fast_mcp_jobvite/http_hardening.py`, mounted by `http_run_kwargs`
under the `middleware` key `FastMCP.run_http_async` already accepts. `__main__.py:438` already calls
`mcp.run(transport="http", **http_run_kwargs(settings))`, so nothing else had to change.

`ASGIMiddleware` is `starlette.middleware.Middleware` - imported under exactly the alias `fastmcp`
itself uses at `server/mixins/transport.py:15`, because an unqualified `Middleware` in
`http_hardening.py` already means the MCP-protocol one and the whole of ADR-0029's correction is
that the two are different layers.

**Two arms, because a body arrives two ways.**

1. **`Content-Length` declared** - refused on the header alone. `self.app` is never entered and not
   one byte of body is read. Measured: `app saw 0` in the table below.
2. **No `Content-Length`** (`Transfer-Encoding: chunked`) - `receive` is wrapped and the delivered
   bytes are summed, compared on **every** chunk. **This is the arm an attacker uses**, because
   omitting the header costs nothing and defeats any check that only reads it.

Arm 2 runs whatever arm 1 read, so a caller who lies about its length is still bounded: arm 1 is an
early exit and arm 2 is the bound.

**`middleware` is set on loopback too**, unlike `allowed_hosts` and `allowed_origins` in the same
function. Those address DNS rebinding, which a loopback bind makes moot; this does not - every
process on the host can open a socket to a loopback bind, so the set of callers able to send an
unbounded body is not empty there. A test asserts this specifically, because the two neighbouring
keys are loopback-conditional and the next reader will assume this one is.

---

## 3. The registry row: `/problems/validation-error`, **422**

ADR-0029 declined to choose and left it here. I chose 422, and the first reason is not a preference:

**413 was not available.** `errors.py`'s registry says in its own header that *"every entry is a
verbatim row of `error-contract.md:96-108`; nothing here is minted locally"*, and
`DESIGN.md:510-511` makes a published `type` URI a contract owed forever. I read that table.
**It has no 413 row at all** - the thirteen rows are 404, 403, 401, 409, 400, 422 (twice), 400, 429,
502, 500, 405, 503. Choosing 413 therefore meant minting `/problems/payload-too-large`, which is
exactly the invention the registry is closed against. **ADR-0031 ruled this same shape already**, for
the refused-approval condition: *add the row's use, not a new slug.*

**422 is also right on the merits, not merely available.** `error-contract.md`'s own "When" column
for `/problems/validation-error` reads *"Request body/params failed validation"*, and an oversized
body is the fourth row of the same §2.1 table whose other three - depth, list items, dict keys - are
validation failures. `DESIGN.md:186-188` reached 422 independently from the other side, correcting an
earlier revision that said 400: *"had one done so its status would be 422, not 400, per the registry
mapping in §5.1."*

**The cost, stated rather than glossed.** 413 is the more precise HTTP status, and a client reading
only the status line loses the signal that the problem was *size*. That signal is in `detail`, which
names the limit and what arrived - the load-bearing role ADR-0031 gave `detail` for the same reason.
A caller distinguishing this from any other 422 reads `detail`, and the suite's
`_assert_is_the_cap_refusing` does exactly that rather than accepting a bare status code.

**Why a problem object at all**, when §2.1's other three limits produce none: `DESIGN.md:181-190` is
about checks *in the input models*, which run pre-dispatch and are **raised** by the framework -
§5.1's third exception. This middleware is on the other side of that boundary. It holds `send`, so
it **returns** a response, which is the property §5.1 says makes a problem object safe. The §8 #9
argument arms still assert `ValidationError` and are still right to; this arm asserts a problem
shape and is not in tension with them.

The refusal is served as `application/problem+json` (`error-contract.md:44`) and carries the
caller's own `X-Request-ID` through `resolve_request_id` - `RequestIdMiddleware` cannot do it,
because it is MCP-protocol middleware and the refusal happens before any message is parsed. A
refusal with an unjoinable correlation id is one an operator cannot trace to the caller who caused
it.

---

## 4. The boundary, both sides, both framings

Printed from a run, not restated from an assertion (the suite asserts every one of these):

```
cap = 1048576 bytes (DESIGN.md:165)

framing                       sent  status  app saw / high water
Content-Length             1048575     200  1048575
Content-Length             1048576     200  1048576
Content-Length             1048577     422  0
chunked (no C-L)           1048575     200  1048575
chunked (no C-L)           1048576     200  1048576
chunked (no C-L)           1048577     422  983040
chunked (no C-L)           8388608     422  917504
```

Three things in that table are the finding.

- **`1 MiB` is ACCEPTED and `1 MiB + 1` is refused**, in both framings. A cap that refused one byte
  early would look identical from every rejecting arm.
- **`app saw 0` on the declared-length refusal.** The application was never entered, so no body was
  read on its behalf. A cap that measured by reading would print 1048577 there and still return 422,
  and would have bounded nothing.
- **The last two rows are the "before buffering" claim, measured.** Eight megabytes arrive with no
  declared length and the application is handed **917504** bytes - *less* than the cap, because the
  chunk that crosses the line never reaches it. Memory is bounded by the LIMIT, not by what the
  caller chose to send. A cap that summed and compared once at the end would print 8388608 there.

The accepting arms assert the **byte count the application received**, not a 200. A 200 alone would
pass against a cap that silently truncated the body, which is worse than refusing it.

**One arm is measured at the unit rather than over the wire, deliberately.** A `Content-Length: 10`
followed by two megabytes cannot be produced by `httpx2`: `httpcore2` raises out of
`_send_request_body` before a byte leaves the process. A wire arm there would be measuring the
client's honesty and would pass with arm 2 deleted, so it drives the middleware directly instead and
the reason is written in the test.

---

## 5. Amputation

`scripts/check-body-cap-amputation.sh`, 5 rows, `5/5 ROWS`, exit 0. Survivors are the output.

| row | what was removed | red | survived |
|---|---|---|---|
| A | `__call__` is a bare passthrough - the class exists, is mounted, and caps nothing | 8 | 13 |
| B | the `Content-Length` arm never fires | **1** | 20 |
| C | the streaming bound never fires - a header-only cap | 4 | 17 |
| D | `http_run_kwargs` mounts nothing | 4 | 17 |
| E | the refusal is an empty body, not a problem object | 8 | 13 |

**Row A is the answer to the brief's question: amputate the cap and the refusing arms go red.** They
do - eight of them. The thirteen survivors are every accepting arm plus the constant and mount arms,
and they are *supposed* to survive: a passthrough accepts everything, so an accepting arm passing
against it is correct, not vacuous. There is no assertion in this file that survives A and claims to
be about refusal.

**Row B is the most interesting result and it is a finding about the design, not a defect.** Removing
the declared-length arm entirely takes down exactly **one** test. Everything else survives, because
the streaming sum catches the same request a moment later and returns the same 422. **So arm 1 is not
the bound - arm 2 is.** Arm 1's unique contribution is that the application is never entered at all,
and the single test that goes red is precisely the one asserting `high_water == 0`. The instrument is
pointed at the right thing; I am recording the shape because a reader could otherwise conclude arm 1
is load-bearing for correctness, and it is not - it is load-bearing for *cost*.

Row D is the "reads as discharged" shape ADR-0029 refused for `MAX_PAYLOAD_BYTES`: a correct control
that nothing constructs. Seventeen arms survive it, which is right, and four hold the wiring up.

---

## 6. Mutation

`scripts/check-body-cap-controls.sh`, **12/12 controls fired**, exit 0. No survivors.

```
########## 12/12 controls fired.
```

The rows, and why each exists:

| row | mutation | killed by |
|---|---|---|
| M1 | declared-length `>` becomes `>=` - refuses exactly 1 MiB | the declared accepting arm |
| M2 | streaming `>` becomes `>=` - same off-by-one, other framing | the chunked accepting arm |
| M3 | the declared-length arm never fires | the declared rejecting arm |
| M4 | **the streaming bound never fires - header-only, the attacker's case** | the chunked rejecting arm |
| M11 | the running sum becomes a per-chunk comparison | the chunked rejecting arm |
| M5 | the cap is 2 MiB, not the design's number | the transcription arm |
| M6 | `http_run_kwargs` stops mounting it | the mount arm |
| M7 | the status line stops matching the registry row (writes 413 under a 422 problem) | the refusing arm |
| M8 | the refusal is not `application/problem+json` | the refusing arm |
| M9 | the caller's correlation id is discarded | the echo arm |
| M10 | a negative `Content-Length` is trusted instead of ignored | the malformed-header arm |
| M12 | a websocket scope is answered with an HTTP response | the non-HTTP arm |

M1 and M2 are the pair that only an accepting arm at the boundary can see. M4 and M11 are the same
defect from two directions and are the rows that matter most: a header-only cap passes M1 and M3 and
looks entirely correct.

**M12 caught a weak test of mine and I rewrote the test rather than the row.** The first version of
the non-HTTP arm used a *lifespan* scope, and deleting the `scope["type"] != "http"` guard changed
nothing observable - a lifespan scope carries no `content-length` and its messages are not
`http.request`, so arm 1 found nothing and arm 2 never incremented. The guard was real and the test
could not see it. A **websocket** scope can carry a `content-length`, and without the guard the cap
answers it with `http.response.start` - writing an HTTP response onto a websocket handshake, a
protocol violation and a worse outcome than the body it was trying to refuse. That is what the arm
measures now, and M12 kills it.

---

## 7. The stale prose, rewritten in place

Nothing was appended. Four sites:

- **`utils/constraints.py` module docstring** - the paragraph beginning *"The 1 MiB body limit of
  DESIGN.md:165 is still not discharged here"* now says it is discharged **elsewhere**, names
  `http_hardening.BodySizeLimitMiddleware` and `http_run_kwargs`, and adds the sentence that matters:
  the two caps are **not duplicates** and neither may be deleted as one.
- **`utils/constraints.py` §2.1 limits block** - the table line reads `<- NOT HERE, SEE BELOW`, and
  the paragraph under it records that the residue *is now bounded*, by what, and that
  `MAX_PAYLOAD_BYTES` remains the only inbound bound on stdio.
- **`utils/constraints.py` `MAX_PAYLOAD_BYTES` docstring (R8-M2)** - *"Left as-is deliberately"*
  stands, and now says the exact bound **exists**: HTTP-side the 6x under-measurement is bounded at
  the right layer, stdio-side it is not and this constant is all there is.
- **`tests/test_arguments_sweep.py`** - the §8 #9 size arm's docstring and the census comment at the
  approval path both now say the cap is landed, and both carry the do-not-delete-this-arm sentence.

**On R8-M2 specifically: yes, this cap is byte-exact.** Nothing is re-serialised. The number compared
is either the caller's own `Content-Length` or a running sum of the bytes ASGI delivered, so a client
that `\u`-escapes printable ASCII gains nothing. It is exact on the **entity body**; it does not
count request-line, header or chunk-framing bytes, which is stated in the code rather than left for
someone to assume either way.

**ADR-0029's "What I did not settle" section is rewritten in place** with the uvicorn measurement and
the 413-or-422 ruling, following #93's precedent that a stale ADR claim is corrected at the site, not
annotated with a rider.

---

## 8. Gates - every floor derived from `ci.yml` by grep, none retyped

```
$ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
check-suite-floor.sh 801
$ uv run --frozen pytest 2>&1 | bash scripts/check-suite-floor.sh 801
====================== 822 passed, 6 deselected in 49.59s ======================
suite floor OK: 822 passed, floor 801
$ echo $?
0

$ grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml
check-harness-anchors.py --self-check --floor 415
$ python3 scripts/check-harness-anchors.py --self-check --floor 415
  check-body-cap-amputation.sh         anchors=  5  (shell call sites=5, python edits=1, ...)
  check-body-cap-controls.sh           anchors= 12  (shell call sites=12, python edits=1, ...)
harnesses scanned: 31
anchors resolved: 432
OK: all 432 anchors resolve to exactly one hit in their target file (floor 415).
$ echo $?
0
```

**822 passed, 6 deselected, ZERO skipped.** The baseline at `27c6944` was 801 passed, so this branch
adds 21. Deselection is by `-m` selection in `addopts`, never `skipif`.

```
$ uv run --frozen ruff check .          -> All checks passed!            exit 0
$ uv run --frozen ruff format --check . -> (clean)                       exit 0
$ uv run --frozen mypy                  -> Success: no issues found in 60 source files   exit 0
```

**`uv run --frozen mypy`, not `mypy src`** - `ci.yml:422` is the authority, and the narrower command
is the one that hid a real error on main for a day. It reports 60 source files, one more than the 59
before this branch.

**`scripts/check-harness-anchors.py` found a real defect in my first draft and I fixed the harness,
not the checker.** It refused both new harnesses with `PARSER GAP: helper amputate takes an 'old'
anchor but names no target - neither a 'file' parameter nor a 'python3 - "..."' invocation`. Both
helpers now take an explicit `file` parameter, as `check-u12-jobfeed-controls.sh` does, so a static
reader can resolve every anchor to the file it is checked against. An anchor whose target nothing can
resolve is an anchor nothing defends.

---

## 9. `ci.yml` steps - yours to add, and `check-row-floors.py` is RED until you do

`docs/reviews/check-row-floors.py` exits **1** on this branch, and correctly:

```
Harnesses: 30
  not referenced by ci.yml at all : 2
  wired but no floor at either layer: 0
    UNWIRED  check-body-cap-amputation.sh
    UNWIRED  check-body-cap-controls.sh
```

Both harnesses carry an internal `ROW_FLOOR` (12 and 5), both **derived** - each read off its own
run's own closing counter (`12/12 controls fired.` and `5/5 ROWS`), never counted by reading the file
for `mutate`/`amputate` calls, which is the count that goes stale the moment a row stops applying.

Three steps, in the shape the other harness steps take:

```yaml
      - name: Body cap controls
        run: bash scripts/ci-harness-gate.sh scripts/check-body-cap-controls.sh

      - name: Body cap amputation
        run: bash scripts/ci-harness-gate.sh scripts/check-body-cap-amputation.sh --min-rows 5
```

and the suite floor raised from `801` to `822` at `.github/workflows/ci.yml:446`.

**Two numbers I could not reconcile and you should check.** Task #92 records the floors moved to
`810/421` on main after my base at `27c6944`. This branch's `ci.yml` still says `801/415`, so **my
822 and my 432 anchors are branch-local numbers measured against a `ci.yml` that has since moved**.
The merged floor is whatever main's `ci.yml` says plus this branch's additions - derive it after the
merge from a run, do not add my delta to #92's number.

---

## 10. What I could NOT settle

- **Whether `_BodyTooLarge` can ever escape as a 500 in production.** It does not in the suite: the
  chunked end-to-end arm drives a real `FastMCP.http_app` over a real socket and gets a 422, so the
  unwind does survive Starlette's `ExceptionMiddleware` and every layer `http_app` mounts. What I
  could not exercise is the one branch that re-raises - the case where the application had already
  begun a response when the bound tripped. Under MCP's request/response shape I could not construct
  a request that reads its body *after* starting to write, so that branch is reasoned about and
  never run. It is three lines and it fails closed by closing the connection, but it is untested and
  I am not going to call it covered.

- **Behaviour under HTTP/2 or HTTP/3.** Everything here was measured over HTTP/1.1 with `h11`.
  ASGI normalises framing, so the streaming arm should be unaffected and `Content-Length` remains a
  pseudo-header, but I did not run it and the design does not say which protocols the transport is
  expected to serve.

- **Whether any other route on the mounted app is now capped that should not be.** The middleware
  sits outside the router, so it caps every request on the transport, including ones that would 404
  or redirect. That is what ADR-0029 asked for - it names *"a body on a non-tool route"* as part of
  the residue - and I believe it is correct, but I did not enumerate the app's routes to confirm
  none of them legitimately needs a body over 1 MiB. `FastMCP.http_app` mounts more than `/mcp`.

- **The `Content-Length`-lie case on the wire.** Measured at the unit and NOT over a socket, because
  `httpx2`/`httpcore2` refuse to emit that framing. What a *hostile* client does with it - one
  writing raw bytes to the socket - is bounded by h11's own framing before reaching us, and I did
  not build a raw-socket client to establish exactly where. The unit arm proves our sum runs
  regardless of the header, which is the part that is ours.

- **Whether 422 will read correctly to a real MCP client.** The choice is defended from the registry
  and the design, and no client was consulted, because none exists to consult on this project yet.

---

## Housekeeping

The worktree at `/tmp/body-cap-work` is **not** removed - task #91 is still measuring row floors and
this branch is unmerged, so removing it would destroy the only copy of the harness runs above. Say
the word and I will remove it; per the brief's own rule I am saying what I did rather than what I
should have.

Nothing merged, nothing pushed. `git -C /tmp/body-cap-work log --oneline main..feat/body-cap` is the
whole of it.
