# CITATION-READ-SRC - the same read, over `src/` and `scripts/`

Agent: `citation-read-src`. Brief: `docs/briefs/CITATION-READ-SRC.md`. Measured against `main` at
**`90d68f6`**, targets read from **`git show c15b138:docs/DESIGN.md`** (2045 lines), never from the
working tree. Worktree `/tmp/citation-read-src-work`, branch `review/citation-read-src`, removed on
completion. **Nothing under `src/`, `tests/` or `scripts/` was edited** - `u7-resilience`, `r2-fixes`
and `r5-fixes` are live in those trees. Every fix below is text.

**Line numbers in the CITING files may have moved by the time anyone applies them. Anchor on the
SUBJECT quoted in each finding, not on the site line number** - every proposed target is quoted, and
every quoted subject was located with `grep -n` over `c15b138:docs/DESIGN.md`.

## The population, enumerated rather than inherited

```
$ grep -rnoE 'DESIGN\.md:[0-9]+(-[0-9]+)?' src/ scripts/ | wc -l
279
$ grep -rhoE 'DESIGN\.md:[0-9]+(-[0-9]+)?' src/ scripts/ | sort -u | wc -l
147
$ grep -rlE 'DESIGN\.md:[0-9]+(-[0-9]+)?' src/ scripts/ | wc -l
29
```

**279 occurrences, 147 distinct ranges, 29 files.** The brief's numbers were right; they are
restated here because they were re-derived, not carried. **All 147 distinct ranges were read** -
citing line plus enough surrounding context to learn the claim, then the target text in full.

## Tally

| Verdict | Ranges | Sites |
|---|---|---|
| **CORRECT** | 128 | 254 |
| **WRONG** | **19** | **25** |
| UNSETTLEABLE | 0 | 0 |
| *of the CORRECT, carrying a boundary nit* | *29* | *37* |

One of the 19 - `1338-1343` - is the range already on the board as task #54. **18 WRONG ranges at 24
sites are new.** The wrong-range rate over `src/` + `scripts/` is **12.9%** (19/147), against 8.7%
(10/115) over `tests/`. There was no reason to assume these trees were cleaner and they are not.

**The "right lines, wrong file" trap is NEGATIVE for this population.** I read all nineteen wrong
cited ranges against `c15b138:docs/plans/IMPLEMENTATION-PLAN.md` at the same numbers; none of them
reads plausibly there. The trap is nonetheless demonstrably real *in this tree*, and is disposed of
correctly in place - see the positive control in the negative-control section.

## The nineteen WRONG ranges

Grouped by range. **Every site of a range moves in one pass or none do.**

### W-1. `108-113` -> `88-90` - §1's in-process-state footnote, cited from §1.1

**1 site.** `src/fast_mcp_jobvite/server.py:21`:

> **Settings reach tools through the lifespan context, not a module global.** DESIGN.md:108-113
> records that **in-process state is per-connection on stdio** and that **nothing may depend on
> cross-call memory** from a module-level variable.

`108-113` is §1.1's evidence paragraph - `api-stg.jobvite.com` fails DNS, one genuine Jobvite `200`
exists, its body cannot be copied. It contains no mention of in-process state, stdio connections or
memory. The subject is **88-90**, and the docstring is nearly quoting it:

> **In-process state is per-connection on stdio**, generally and not just for any one mechanism:
> stdio spawns a fresh server process per connection, so anything held in memory resets between
> connections. **Nothing in this design depends on cross-call memory**, which is why that is a
> footnote.

**Fix:** -> `DESIGN.md:88-90`. Anchor phrase: *"In-process state is per-connection on stdio,
generally and not just for any one mechanism"* (unique). Do not anchor on *"stdio spawns a fresh
server process per connection"* alone - that clause occurs three times (89, 239, 404).

### W-2. `281` -> `282` - the citation lands on the directory name, not the module

**1 site.** `src/fast_mcp_jobvite/__main__.py:4`:

> **Logging is configured before anything else is imported** (DESIGN.md:281), and it goes to
> **stderr**.

Line `281` is `src/fast_mcp_jobvite/`, the first line inside §3's fenced block. The subject is the
next line, **282**:

> `  __main__.py                 entry; transport selection; signal handling; logging before imports`

**Fix:** -> `DESIGN.md:282`. Anchor phrase: *"logging before imports"* (unique).
**This is the only one of the nineteen a `+1` sweep would have corrected.**

### W-3. `289-291` -> `292-297` - the `utils/` package cites the `tools/` and `models/` lines

**1 site.** `src/fast_mcp_jobvite/utils/__init__.py:1`:

> `"""Cross-cutting helpers (DESIGN.md:289-291).`
> `U2 creates this package for `correlation.py`. `redaction.py` and `normalise.py` are owned by
> later units and are not written here."""`

`289-291` is `tools/candidates.py`, `tools/jobs.py` and `models/`. Every module the docstring names
is at **292-297**:

```
292	  utils/correlation.py        request_id_var, the per-invocation correlation ContextVar (§5.3)
293	  utils/redaction.py          log redaction; untrusted-content fencing
294	  utils/normalise.py          casing, dates, empty-string/null unification
295	  utils/constraints.py        the shared inbound constraint types every input model reuses:
```

**Fix:** -> `DESIGN.md:292-297`. Anchor phrase: *"utils/correlation.py        request_id_var"*
(unique). 295-297 is one wrapped entry, so the range should not stop at 295.

### W-4. `291` -> `293`, **at one of its two sites** - the same off-by-two, one line at a time

**1 of 2 sites is wrong; do not move the other.**

- **WRONG** - `src/fast_mcp_jobvite/utils/redaction.py:3`: *"**This module holds the SECRET half
  only.** DESIGN.md:291 gives `utils/redaction.py` two jobs, **"log redaction; untrusted-content
  fencing"**"*. That quoted string is line **293**. Line 291 is `models/`.
- **CORRECT, leave it** - `src/fast_mcp_jobvite/models/__init__.py:1`: *"Allow-listed OUTPUT models,
  one file per tool (DESIGN.md:291)."* Line 291 is exactly that.

**Fix:** `utils/redaction.py:3` -> `DESIGN.md:293`. Anchor phrase: *"log redaction;
untrusted-content fencing"* (unique). **This is the one range in the set where "every site moves or
none do" is the wrong rule**, because the two sites cite the same number for two different modules
and only one of them is at 291. Stated explicitly so nobody sweeps it.

### W-5. `313` -> `315-316` - the three query parameters are named one paragraph down

**1 site.** `src/fast_mcp_jobvite/utils/redaction.py:18`:

> **Three parameters are redacted, not one.** DESIGN.md:313 names `api`, [`sc` and `companyId`]

`313` is *"constructed**, even though Jobvite's own published sample code does exactly that."* - the
tail of the never-build-a-URL sentence. It names no parameter. The subject is **315-316**:

> `GET /v1/jobFeed` is the exception: it **structurally requires `api`, `sc` and `companyId` as query
> parameters**. Its URL is classified sensitive - never logged whole, never in an exception message,

**Fix:** -> `DESIGN.md:315-316`. Anchor phrase: *"structurally requires `api`, `sc` and `companyId`
as query parameters"* (unique).

### W-6. `317-319` -> `320-321` - the credential-class claim is in the next paragraph, and 319 is blank

**1 site.** `src/fast_mcp_jobvite/utils/redaction.py:20`:

> DESIGN.md:317-319 makes `companyId` **a credential class of its own** ("the [job feed's separate
> `companyId` credential]")

`317-318` is *"`sc=` redacted before any log line. Enforced in one place, `utils/redaction.py`..."*
and **`319` is blank**. The parenthetical the comment quotes is at **320-321**:

> **This gives three credential/data classes, which is also the token-scoping axis (§7.2):**
> candidate PII, public job data, and **the job feed's separate `companyId` credential**.

**Fix:** -> `DESIGN.md:320-321`. Anchor phrase: *"the job feed's separate `companyId` credential"*
(unique). Note `redaction.py:122`, eighty lines below, already cites `321` for the same quoted
string - **one file, two citations of one sentence, two different answers.**

### W-7. `339-344` -> `332-333` - a §4.2 invariant cited by §4.3's heading

**1 site.** `src/fast_mcp_jobvite/errors.py:144`, the `upstream_status` argument:

> `upstream_status: The status Jobvite reported - **the HTTP status or the `status.code` of its JSON
> envelope** (DESIGN.md:339-344). `None` when Jobvite gave no status at all.`

`339-344` is the `defusedxml` sentence, a blank line, the `### 4.3 Resilience` heading, another
blank, and *"Ordered timeout, then retry, then circuit breaker."* **Two of its six lines are blank
or a heading, and none of the six mentions a status.** The subject is the §4.2 invariant at
**332-333**:

> **Invariant:** a response is successful only if the body carries no **`status.code >= 400`** and
> **the HTTP status is below 400**. Both, every call.

**Fix:** -> `DESIGN.md:332-333`. Anchor phrase: *"a response is successful only if the body carries
no `status.code >= 400`"* (unique).

### W-8. `632-638` -> `624-627` - the `_meta` key's justification is eight lines up

**1 site.** `src/fast_mcp_jobvite/tools/jobs.py:68`, on `REQUEST_ID_META_KEY`:

> `#: (DESIGN.md:632-638). **`io.modelcontextprotocol/*` is reserved**, and the spec's own
> **`SERVER_INFO_META_KEY` is the precedent**: server stamped, and documented as display and
> debugging only, never behaviour or security - which is exactly this value's class.`

That comment is a near-verbatim copy of **625-627**:

> `com.evolvconsulting.fast-mcp-jobvite/requestId` - **`io.modelcontextprotocol/*` is reserved**, and
> the spec's own **`SERVER_INFO_META_KEY` is the precedent**: server-stamped, and documented as
> display and debugging only, never behaviour or security, which is exactly this value's class.

`632-638` is the *"Not a field on the output models"* paragraph - `additionalProperties: false` and
the validator - a different claim, which W-9 below cites correctly nowhere and wrongly twice.

**Fix:** -> `DESIGN.md:624-627`. Anchor phrase: *"`io.modelcontextprotocol/*` is reserved"* (unique).

### W-9. `639-650` -> `629-637` - the validator argument, cited from the two paragraphs after it

**2 sites**, in two different files, making the same claim.

- `src/fast_mcp_jobvite/tools/jobs.py:35` - *"**`request_id` is stamped into `_meta`, not into the
  model** (DESIGN.md:639-650). `_meta` is the protocol's own channel and the result validator never
  inspects it, whereas an undeclared top-level key in structured content is rejected outright."*
- `src/fast_mcp_jobvite/models/jobs.py:153` - *"**`request_id` is deliberately NOT a field here**
  (DESIGN.md:639-650). `additionalProperties: false` is set below and
  `ClientSession.validate_tool_result` validates structured content against the cached output schema
  unconditionally, so an undeclared top-level `request_id` is *rejected*."*

Both are paraphrases of **629-637**:

> **Not a field on the output models, and the reason is executed rather than reasoned.** §2.1's
> models set `additionalProperties: false`, and `ClientSession.validate_tool_result` validates
> `structured_content` against the cached output schema unconditionally ... An undeclared top-level
> `request_id` in structured content is **rejected** ... **`_meta` is the protocol's own channel for
> this, and the validator never inspects it.**

`639-650` is *"One way to set `meta` and have it silently discarded"* plus *"A caller reads it as a
normal field on the result"* - the `_raw_mcp_result` short-circuit and the caller-facing key. Real
prose, somebody else's.

**Fix:** both sites -> `DESIGN.md:629-637`. Anchor phrase: *"Not a field on the output models, and
the reason is executed rather than reasoned"* (unique).

### W-10. `656-662` -> `664-666` - the range stops two lines before the reason it is cited for

**1 site.** `src/fast_mcp_jobvite/audit.py:243`:

> Read from `ctx.request_context.meta` directly rather than through **FastMCP's span plumbing**
> (DESIGN.md:656-662): **`telemetry_mode()` may be `"off"`**, in which case FastMCP's extractor
> returns the ambient context unchanged while the wire `_meta` still carries the header.

`656-662` establishes that trace context is *reachable* on the pinned stack (SEP-414, the
`opentelemetry-api` dependency, FastMCP's server-side extractor). The reason for reading `_meta`
directly is **664-666**:

> **We read `ctx.request_context.meta` directly rather than depending on FastMCP's span plumbing,
> because `telemetry_mode()` may be `"off"`**, in which case the extractor returns the ambient
> context unchanged while the wire `_meta` still carries the header.

**Fix:** -> `DESIGN.md:664-666`. Anchor phrase: *"because `telemetry_mode()` may be `\"off\"`"*
(unique). **This citation and W-11's are five lines apart in the same docstring and both are wrong**
- `audit.py:243` and `audit.py:248`.

### W-11. `663-665` -> `668-669` - the never-synthesised rule, cited from the paragraph above it

**4 sites**, and this is the most-repeated error in the set.

- `src/fast_mcp_jobvite/audit.py:38` - *"**`trace_id` and `span_id` are recorded when present,
  omitted when absent, and never synthesised** (DESIGN.md:663-665, `ai/tool-calling.md:176-177`). A
  locally minted id in a field named for the host's trace joins nothing while looking like it does"*
- `src/fast_mcp_jobvite/audit.py:99` - *"Accepting them would put a field in the event that looks
  like a join and is not one, which is exactly what DESIGN.md:663-665 forbids."*
- `src/fast_mcp_jobvite/audit.py:248` - *"**Returns `None` rather than a synthesised pair** when the
  header is missing or malformed (DESIGN.md:663-665)."*
- `scripts/check-u3-audit-controls.sh:132` - *"`# --- trace context, both arms (DESIGN.md:663-665,
  :1287-1292) ---`"*

`663-665` is the tail of the reachability paragraph - `fastmcp/server/telemetry.py:95`, the public
helper, its export line. The subject is **668-669**, which two of the four sites quote almost
verbatim:

> `trace_id` and `span_id` are **recorded when present, omitted when absent, and never synthesised**:
> a locally-minted id in a field named for the host's trace joins nothing while looking like it does.

**Fix:** all four sites -> `DESIGN.md:668-669`. Anchor phrase: *"recorded when present, omitted when
absent, and never synthesised"* (unique).

**Rider on `check-u3-audit-controls.sh:132`, which carries a SECOND wrong range on the same line.**
Its `:1287-1292` continuation is labelled *"trace context, both arms"*. `1287-1292` is §8 cases
**#6, #7 and #8** - EEO fields, argument-schema violation, control-character rejection. The
trace-context case is §8 **#17** at **1335-1339**. Fix that half to `:1335-1339` in the same edit.
It is not counted in the tally because the bare `:N-N` continuation form is outside the population
the brief's `grep` defines - **which is itself worth knowing: two live citations in `src/` and
`scripts/` use that form and no checker and no sweep, including this one, can see them.** Both are
listed under "not in scope" at the end.

### W-12. `676-680` -> `688-690` - a §5.3 closed-set argument cited twelve lines early

**1 site.** `src/fast_mcp_jobvite/models/fencing.py:61`, on `FencingDecision`:

> A closed set, for the reason `error-contract.md`'s registry is closed (DESIGN.md:676-680): **a
> value that governs a security control is a contract, and an open string invites a second spelling
> of the first answer.**

`676-680` is *"What this does not do"* (the stdio within-invocation correlation limit) plus the
opening of *"The audit event includes `approval_state`"*. Neither mentions a closed set. The subject
is **688-690**:

> The set is closed **for the reason `error-contract.md`'s registry is closed**: a value emitted into
> an audit record **is a contract, and an open string invites a fourth spelling of the first three**.

**Fix:** -> `DESIGN.md:688-690`. Anchor phrase: *"The set is closed for the reason
`error-contract.md`'s registry is closed"* (unique).

### W-13. `745-748` -> `747-749` - the example key it names is on the line after the range

**1 site.** `src/fast_mcp_jobvite/models/fencing.py:49`:

> `#: Separator between path segments, matching DESIGN.md:745-748's own`
> `#: example key **`candidates[].application.job.title`**.`

`748` is *"`eId` each appear at multiple depths in our own fixtures, and `customField[]` is
open-ended."* The example key is at **749**:

> Keys are paths like **`candidates[].application.job.title`**.

**Fix:** -> `DESIGN.md:747-749`. Anchor phrase: *"Keys are paths like
`candidates[].application.job.title`"* (unique).

### W-14. `747-750` -> `744-745` - and it is W-13's neighbour, wrong in the opposite direction

**1 site.** `src/fast_mcp_jobvite/models/fencing.py:68`, on `FencingDecision.FENCE`:

> `#: Attacker-authored free text. U8 fences it, and **strips delimiter tokens occurring inside the
> content so the content cannot close its own fence** (DESIGN.md:747-750).`

`747-750` is the path-keying paragraph plus a blank line - **W-13's correct target.** The subject is
**744-745**:

> Every such field is fenced before it reaches a tool result, and **delimiter tokens occurring inside
> the content are stripped so content cannot close its own fence**.

**Fix:** -> `DESIGN.md:744-745`. Anchor phrase: *"delimiter tokens occurring inside the content are
stripped so content cannot close its own fence"* (unique). **W-13 and W-14 are nineteen lines apart
in one file and their answers are almost each other's** - `747-749` and `744-745`. Fix them in the
same pass or the second reader will assume the first was the typo.

### W-15. `826-829` -> `828-831` - "secret-class" is on line 830

**1 site.** `src/fast_mcp_jobvite/config.py:387`:

> **No token, key or fragment of the value appears in any message here.** The value is
> **secret-class** (DESIGN.md:826-829), and a parse error's own text quotes the input, so the
> exception is deliberately discarded.

`826` is the `### 7.2 Authentication and scopes` heading, `827` is blank, and `828-829` is the
`StaticTokenVerifier` sentence. The word the citation exists for is at **830-831**:

> It is **secret-class**: unset by default, absent from `.env.example`'s filled values like every
> other credential, and redacted wherever configuration is echoed.

**Fix:** -> `DESIGN.md:828-831`. Anchor phrase: *"It is **secret-class**: unset by default"*
(unique). Two of the four cited lines are a heading and a blank - the same shape the repoint map's
own `959-961` miss had, and the shape checker exits 0 on it because 828-829 is real prose.

### W-16. `877` -> `1388-1393` - the largest miss in the set, and it crosses two sections

**1 site.** `src/fast_mcp_jobvite/errors.py:185`:

> `"""Duplicate candidate on create (DESIGN.md:519, DESIGN.md:877)."""`

`519` is right and stays - it is the registry row *"| Duplicate candidate on create |
`/problems/conflict` | 409 |"*. `877` is inside §7.2's ambient-authority disposal: *"paragraph rots
silently on the day the assumption changes, which is precisely how the conditional"*. Nothing about
duplicates, conflicts or 409. The second reference the docstring needs is §9 hazard 6 at
**1388-1393**:

> **Duplicate creates return `409`, and none of §2.2's gates prevent one.** ... So `create_candidate`
> surfaces a `409` as `/problems/conflict` with the duplicate named in `detail`, rather than as a
> generic failure, and never retries (§4.3).

**Fix:** -> `DESIGN.md:519, DESIGN.md:1388-1393`. Anchor phrase: *"Duplicate creates return `409`,
and none of §2.2's gates prevent one"* (unique). **Delta +511**, larger than either of round 1's
~306-line §8-for-§7.4 misses, and like those it crosses a section boundary (§7.2 -> §9).

### W-17. `958` -> `960-961` - two sites citing the §7.4 HEADING, the exact miss the map records

**2 sites**, both in `src/fast_mcp_jobvite/server.py`.

- `server.py:33` - *"This parameter is the composition point DESIGN.md:958 already requires (`|`
  composition)"*
- `server.py:117` - *"`extra_lifespan`: A lifespan composed after the base one with `|`, so
  **teardown runs in strict reverse** (DESIGN.md:958)."*

Line `958` is `### 7.4 Lifespan and shutdown`. Line `959` is blank. The subject is **960-961**:

> `from fastmcp.server.lifespan import lifespan` with **`|` composition; startup in order, teardown
> in strict reverse, verified.**

`CITATION-REPOINT-MAP.md` already sends `959-960` -> `960-961` and records that *"958 is the heading
and 959 is BLANK"* - the map's own self-correction. **These two `src/` sites cite the heading alone
and were not in the 36 the shape checker found**, because a heading is real prose.

**Fix:** both sites -> `DESIGN.md:960-961`. Anchor phrase: *"`|` composition; startup in order,
teardown in strict reverse, verified"* (unique).

### W-18. `1338-1343` -> `1335-1339` - CONFIRMED, already on the board as task #54

**1 site in my trees.** `src/fast_mcp_jobvite/audit.py:190`:

> **Optional fields are OMITTED, never emitted as `None`.** A `trace_id` of `None` is a field that is
> always present, and **§8's trace case exists because a field that is always there passes a
> single-arm test** (DESIGN.md:1338-1343).

**Independently re-derived and I agree with round 1.** §8 #17 is **1335-1339** in full; the claim
this docstring makes is at **1336-1337** - *"**Both arms are required**: a field that is always
absent and a field that is always synthesised each pass a single-arm test"* - which the cited range
starts three lines past. 1340-1343 is the lifespan-teardown bullet, §8 #18, a different case.

**Fix:** -> `DESIGN.md:1335-1339`, with the two `tests/` sites, in one pass. **Do not apply
separately from task #54.**

### W-19. `1517` -> `1515-1516` - a verbatim quote whose whole subject is one line up

**2 sites**, both in `scripts/check_advisories.py`.

- `:69` - `"""DESIGN.md:1517 - `an expiry date no more than 30 days out`."""`
- `:300` - `f"more than the {MAX_IGNORE_DAYS} DESIGN.md:1517 allows"`

`1517` is *"required CI step:** it reads that table, emits the `--ignore-vuln` flags `pip-audit`
actually takes"*. The quoted string spans **1515-1516**:

> ... with the advisory id, the date, the reason it is unreachable, and **an expiry
> date no more than 30 days out**.

**Fix:** both sites -> `DESIGN.md:1515-1516`. Anchor phrase: *"an expiry date no more than 30 days
out"* (unique). `:69` is a docstring that quotes the design in backticks and cites a line that does
not contain the quoted words - the cheapest kind of finding to verify and the kind no checker sees.

## Why no constant offset would have found these

| Range | Repoint | Delta (start) |
|---|---|---|
| `877` | `1388-1393` | **+511** |
| `676-680` | `688-690` | +12 |
| `639-650` | `629-637` | -10 |
| `656-662` | `664-666` | +8 |
| `632-638` | `624-627` | -8 |
| `339-344` | `332-333` | -7 |
| `663-665` | `668-669` | +5 |
| `747-750` | `744-745` | -3 |
| `1338-1343` | `1335-1339` | -3 |
| `108-113` | `88-90` | **-20** |
| `289-291` | `292-297` | +3 |
| `317-319` | `320-321` | +3 |
| `313` | `315-316` | +2 |
| `745-748` | `747-749` | +2 |
| `826-829` | `828-831` | +2 |
| `958` | `960-961` | +2 |
| `291` (one site) | `293` | +2 |
| `1517` | `1515-1516` | -2 |
| `281` | `282` | **+1** |

Eleven positive, eight negative, magnitudes from 1 to 511. **Three cross a section boundary** -
§1.1 -> §1, §4.3 -> §4.2, §7.2 -> §9. **A `+1` sweep would have corrected exactly one of nineteen**
(`281`) and would have pushed `1517`, `747-750`, `339-344`, `639-650`, `632-638` and `1338-1343`
further from their subjects while the shape checker stayed silent, because every one of these
nineteen already lands on real prose today.

## Two patterns round 1 named, and what they found here

**"A copied citation is never re-derived" - confirmed three times, and it is the highest-yield rule
in the brief.**

- `audit.py:243` and `audit.py:248` are five lines apart in one docstring. **Both are wrong** (W-10,
  W-11), in opposite directions, and W-11's number was then copied to `audit.py:38`, `audit.py:99`
  and a shell script - **one mis-derivation, four sites.**
- `models/fencing.py:49` and `:68` are nineteen lines apart. **Both are wrong** (W-13, W-14), and
  each one's correct target is close to the other's cited range.
- `utils/redaction.py` cites the same §4.1 sentence twice, eighty lines apart, and **gets two
  different answers**: `:20` cites `317-319` (W-6) and `:122` cites `321` (correct). Reading that
  file's other citations after finding `:20` wrong is what found `:3` (W-4) as well.

**"Verify the numbering base independently" - done, and it holds.** Six `§8 #N` claims live in
`src/` and `scripts/`. Counting §8's required-case list with **1265 as #1** - which means the
`1264` bullet, *"the 200-with-401-body trap"*, is **not** counted - all six land on the right case:

| Site | Claims | Lands on |
|---|---|---|
| `check-u4-client-controls.sh:217` | #2, no secret reaches a log record | 1270, *"a secret never reaching a log record"* |
| `check-u3-audit-amputation.sh:132` | #2 and #5, arguments unredacted | 1270 and 1283, *"candidate PII never reaching a log or audit record"* |
| `check-u5-jobs-controls.sh:176` | #16, `request_id` on the wire | 1328, *"`request_id` is present on every result"* |
| `check-u3-audit-amputation.sh:146` | #17, trace context, two arms | 1335, *"trace context is recorded when the caller supplies it"* |
| `__main__.py:67`, `:413` | #18, teardown / exit status | 1340, *"lifespan teardown runs on SIGTERM"* |
| `config.py:29`, `:316` | #10, off-loopback refusal | 1297, *"an off-loopback bind without TLS refuses to start"* |

**All six §8 `#N` claims in this population are CORRECT.** Six independent landings here agree with
round 1's four in `tests/`, so the base is settled by ten sites and not by assumption. **Counting
from 1264 instead - which is what a reader who simply counts bullets does - shifts every number by
one and would have made all six look wrong.** That is worth writing down: the off-by-one is in the
counting convention, not in the citations.

## Negative control

**128 of 147 ranges were read and judged CORRECT**, covering 254 of the 279 occurrences. Naming
them, because a sweep that finds something wrong with everything it reads proves nothing:

`133-139`, `137`, `152-154`, `162-164`, `172-179`, `176-183`, `178-179`, `192-195`, `197-200`,
`202-205`, `207-213`, `227-229`, `270-274`, `280-293`, `289-290`, `295-297`, `300-301`, `308-340`,
`312`, `312-313`, `312-318`, `312-319`, `315-318`, `320`, `320-321`, `321`, `323-324`, `328-333`,
`332-333`, `335-337`, `337-340`, `342-358`, `346`, `355-358`, `356-360`, `358`, `434`, `434-436`,
`436-438`, `451`, `455`, `455-464`, `455-487`, `463-464`, `465-466`, `465-468`, `469-472`,
`469-473`, `469-477`, `471-473`, `474`, `474-476`, `478-480`, `486`, `486-487`, `487`, `487-489`,
`491-540`, `495-496`, `502`, `502-509`, `502-534`, `510-511`, `515`, `518`, `519`, `520`, `521`,
`532-534`, `536-540`, `548-568`, `589-594`, `595-597`, `597-599`, `597-606`, `601-604`, `601-606`,
`601-612`, `604-606`, `608-612`, `693-705`, `698-700`, `698-703`, `711-727`, `712-718`, `713-715`,
`717-718`, `721-727`, `738-744`, `798-802`, `826-832`, `828-833`, `909-955`, `911-915`, `917-934`,
`919-921`, `923-927`, `929-934`, `937-945`, `938-943`, `938-944`, `946-951`, `956-1046`, `960-1023`,
`979-981`, `985-986`, `990-1023`, `1026-1034`, `1039-1046`, `1280-1282`, `1338-1344`, `1359-1360`,
`1483-1488`, `1505-1524`, `1507-1510`, `1513-1518`, `1520-1522`, `1523-1524`, `1546-1550`,
`1569-1573`, `1572-1575`, `1574-1580`, `1630-1637`, `1633-1634`, `1635-1637`, `1788`, `1797`,
`1799`.

That list holds exactly 128 entries and was emitted by a script over the enumerated population minus
the nineteen WRONG rows, not typed by hand. **`291` is not in it** even though one of its two sites
is correct - see W-4; the range is counted WRONG and `models/__init__.py:1` must not move.

Four of the 128 are worth naming as *positive* evidence that earlier repoint work landed correctly:
`312-318` (10 sites) and `315-318` (7 sites) are exactly where `CITATION-REPOINT-MAP.md` sent the
twelve-site `312-316` sweep, `300-301` is the map's own `302-306` counter-example row, and `985-986`
is its `984-988` row. **Those repoints are verified landed by reading, not by the checker's exit
code.**

**A positive control on the "right lines, wrong file" trap, which is the strongest single piece of
evidence in this report.** `src/fast_mcp_jobvite/models/fencing.py:24-25` cites
`DESIGN.md:828-833` **in order to say it is wrong**:

> It was cited here as `DESIGN.md:828-833`, which was the right LINES in the wrong FILE:
> `DESIGN.md:828-833` at the frozen `c15b138` is the `JOBVITE_HTTP_TOKENS` paragraph, a different
> subject entirely.

I checked both halves. `c15b138:docs/DESIGN.md:828-833` **is** the `JOBVITE_HTTP_TOKENS` /
`StaticTokenVerifier` paragraph, and `c15b138:docs/plans/IMPLEMENTATION-PLAN.md:826-833` **is**
*"Why the fencing-decision registry lands here and not in U8"*, the heading the comment now cites
instead. **The claim is CORRECT in both directions**, the trap is real and is disposed of in place
by heading rather than by number, and this is the falsifiable half of my negative report on the
trap: I did not merely fail to find it, I found the one confirmed instance and it is already fixed.

### Boundary nits inside the CORRECT set

Twenty-nine of the 128 contain their subject - a reader landing there gets the right claim, so they
are not WRONG - but a boundary line is off. **Each is worth one edit and none is worth an argument.**
They are listed so the negative control stays falsifiable: **I did not grade a range CORRECT without
reading both of its endpoints.**

| Range | Site(s) | Nit | Suggested |
|---|---|---|---|
| `176-183` | `constraints.py:25`, `check-u5-jobs-amputation.sh:283` | clips *"A candidate name carrying a NUL or a bidi override"*, which opens at 175; runs on into §2.1's rejection-shape paragraph | `175-179` |
| `280-293` | `__init__.py:4` | *"every module ... lists"* - the listing runs to 297; `normalise.py` and `constraints.py` fall outside | `281-297` |
| `312-319` | `redaction.py:83` | 319 is blank; 312-318 is the canonical target the twelve-site sweep used | `312-318` |
| `320` | `config.py:37` | 320 is the topic sentence; *"the job feed's separate `companyId` credential"* is on 321 | `320-321` |
| `355-358` | `errors.py:158` | opens on the previous bullet's tail; the `retry_after` hint finishes on 359 | `356-359` |
| `358` | `errors.py:227` | *"plus a `retry_after`"* is on 358 and *"hint."* on 359 | `358-359` |
| `436-438` | `tools/jobs.py:175` | `min(transport_cap, ...)` is on 436; 437-438 is the start-base paragraph | `434-436` |
| `471-473` | `constraints.py:117` | *"`eId` is an opaque"* opens on 470; the range starts mid-sentence | `470-471` |
| `487-489` | `models/jobs.py:178`, `tools/jobs.py:167` | 488 is blank and 489 is `---`; the sentence is 486-487 | `486-487` |
| `491-540` | `errors.py:1` | §5.1 runs to 568; stops before *"Three honest exceptions to uniformity"* (round 1 raised the identical nit for `test_error_contract.py:1`) | `491-568` |
| `589-594` | `audit.py:6` | paragraph opens at 588; 594 is blank | `588-593` |
| `713-715` | `tools/jobs.py:344` | the read branch is 713-714; 715 opens the *write* branch, a different case | `713-714` |
| `798-802` | `config.py:24`, `config.py:355` | opens two lines into the previous paragraph; the refusal sentence finishes on 803 | `800-803` |
| `826-832` | `config.py:22` | the startup-failure sentence finishes on 833 | `828-833` |
| `909-955` | `config.py:3` | §7.3 is 911-956 | `911-956` |
| `917-934` | `server.py:107`, `tools/jobs.py:197` | 917-918 is §7.3's opening; the enable-surface sentence finishes at 935 | `919-935` |
| `929-934` | `config.py:19`, `config.py:329` | the subject sentence is 931-935; 929-930 are the two preceding bullets | `931-935` |
| `938-943` | `config.py:286` | *"the order ... 's row lists them"* - the matrix is 940-946; the `get_job_feed` and `create_candidate` rows fall outside | `940-946` |
| `938-944` | `config.py:15`, `config.py:70` | same matrix; and `:70`'s own comment discusses *"the `http` row"*, which is line 946, outside the range it cites | `937-946` |
| `956-1046` | `server.py:1` | §7.4 is 958-1047 | `958-1047` |
| `979-981` | `__main__.py:50`, `:405`, `:455` | 981 is the topic line; *"a non-daemon AnyIO worker thread blocks interpreter shutdown"* is 982-983 | `981-983` |
| `1039-1046` | `server.py:12`, `server.py:66` | the paragraph is 1042-1047; the range opens in the §8-test paragraph | `1042-1047` |
| `1338-1344` | `server.py:28` | opens two lines inside §8 **#17**; the teardown case it cites is **#18**, 1340-1343 | `1340-1343` |
| `1483-1488` | `check-u0-test-controls.sh:12` | the quoted sentence is 1487-1488; 1483-1485 is the stale-count paragraph | `1487-1488` |
| `1505-1524` | `check_advisories.py:2`, `:327` | clips policy step 4, which finishes at 1525 (round 1 raised the identical nit) | `1505-1525` |
| `1523-1524` | `check_advisories.py:243` | 1523 is step 3's tail; *"Never a blanket ignore"* finishes at 1525 | `1524-1525` |
| `1546-1550` | `config.py:153` | subject opens at 1548 and finishes at 1552 (round 1 raised the identical nit for `1546-1552`) | `1548-1552` |
| `1569-1573` | `config.py:197` | the `JOBVITE_MAX_RESULTS` bullet is 1572-1575; 1569-1571 is the previous bullet | `1572-1575` |
| `1574-1580` | `config.py:200` | the rate-limit bullet is 1576-1581; the range opens inside the `MAX_RESULTS` bullet | `1576-1581` |

Five of these are nits round 1 raised in `tests/` on the same or an adjacent range - `491-540`,
`1505-1524`, `1523-1524`, `1546-1550` and `979-981`. **The same range is clipped the same way in two
different trees**, which is what a copied citation looks like across a file boundary rather than
within one.

## What I could NOT settle

**Nothing. There is no UNSETTLEABLE row in this population, and one item came close enough to state.**

`scripts/check-u6-paging-controls.sh:201` reads:

> The short-page test reads the DE-DUPLICATED count instead of the raw page. A full page that is
> entirely duplicate then looks short, and **the scan stops early on exactly the clamping hypothesis
> the seen set exists to absorb** (DESIGN.md:486).

The referent is arguable. *"The scan stops early"* is `486` - *"Paging terminates on a short page
(`len(items) < count`), never on `total`"* - and the citation is correct on that reading. *"the
clamping hypothesis the seen set exists to absorb"* is `465-468`. **I graded it CORRECT** because the
mutation the comment introduces breaks the short-page loop condition and nothing else, so 486 is the
rule the control defends. The clean repair, if anyone wants one, is `DESIGN.md:465-468 and
DESIGN.md:486` - I am not filing it as a finding because the citation as written supports the claim
its own mutation tests, and a repoint made on a guess is the failure this exercise exists to catch.

## What is NOT in scope here, stated so nobody reads a false absence

- **`tests/`** - round 1's population, at `docs/reviews/CITATION-READ-VERDICTS.md`. I did not
  re-derive it, and W-18 is its finding confirmed rather than re-filed.
- **`docs/`** - not read. Following `CITATION-REPOINT-MAP.md`'s call on the five `312-316` sites, a
  dated worklog or review is left as written even when its citation is now known wrong; repointing a
  dated record edits history to agree with the present. **If any of the nineteen ranges above is
  quoted under `docs/`, it stays.** I did not enumerate which.
- **The bare `:N-N` continuation form** - `DESIGN.md:798-802, :806-812` and `DESIGN.md:663-665,
  :1287-1292`. Exactly two occurrences, at `src/fast_mcp_jobvite/config.py:355` and
  `scripts/check-u3-audit-controls.sh:132`. **They are outside the population the brief's `grep`
  defines, outside `check-design-citation-shape.py`'s regex, and outside every count in this
  report.** I read both: `806-812` is correct for `config.py:355`'s TLS-refusal claim;
  `:1287-1292` is **wrong** and is filed as a rider on W-11. **A hand-written citation form that no
  instrument matches is a population nobody is counting**, and the honest recommendation is to
  normalise both to the full `DESIGN.md:N-N` spelling in the same pass, so the next sweep sees them.
- **`docs/OBLIGATIONS.md`** - untouched; this report moves no anchor, so
  `docs/reviews/check-obligations.py` was not run and its output is not quoted. Nothing here edits a
  file it indexes.
- **Gates** - none were run. This unit edits no code, so there is no delta to type-check or test,
  and reporting a passed-count from a tree three other agents are editing would attribute their
  state to me.
