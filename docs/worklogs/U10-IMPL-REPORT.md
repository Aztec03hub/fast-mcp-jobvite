# U10 - the write: `approval.py` and `create_candidate`

**Branch** `feat/u10-write`, from `7bfe24b`. Worktree `/tmp/u10-write-work`, removed on completion.
Brief `docs/briefs/U10.md`; design read as `git show c15b138:docs/DESIGN.md` and never from the
working tree.

---

## The one sentence this unit is allowed to say

**The server requires an approval response from the host and refuses to write without one.**

It does not establish that a person was involved, and nothing in `approval.py`,
`tools/candidates.py`, `tests/test_approval_write.py` or this file may imply otherwise. A host may
auto-respond with no person present - that is **C4-S1**, a **High residual**, **not mitigable
server-side** (`DESIGN.md:1754`, ADR-0009).

**That rule is now enforced by a test rather than by review.**
`test_the_wording_rule_holds_across_every_file_this_unit_owns` scans all four files for a set of
assembled phrasings, reading each hit together with the text before it so a *denial* is not counted
as a claim. Its positive control shows the tripwire firing on a fabricated assertion and staying
silent on the two denials that broke its first two versions. **It is a tripwire, not a proof**: it
cannot see a claim made in words it does not know.

---

## THE ROW COUNTER AND THE APPROVED-WRITE CONTROL WERE WRITTEN FIRST. YES.

`tests/test_approval_write.py` was committed at **`8bc8012`**, alone, **before `approval.py` or
`create_candidate` existed**. Run against that tree it failed on both eras with
`Unknown tool: 'create_candidate'` - the red is the evidence, and the commit is the record of it.
Only then did `7d8021a` add the source.

`_JobviteRows` counts `POST`s on the server side of a `httpx2.MockTransport`, exactly as
`FASTMCP-SPIKE-4.md:2118-2143` ran it. `test_positive_control_an_approved_write_moves_the_row_counter_by_one`
is parameterised over both eras and asserts the counter moves **0 -> 1**.

**Why it is load-bearing, measured rather than asserted.** Harness row **M2** empties
`HANDSHAKE_PROTOCOL_VERSIONS`, which makes the handshake era refuse every call. Every refusal arm in
the file still passes against that tree - the row count did not move, exactly as they require. **The
positive control is the only thing that goes red.** That is the guard-that-refuses-everything of
`DESIGN.md:1370-1371`, reproduced deliberately and killed.

---

## Gate exit codes, read from the terminal, each on its own line

| Gate | Command | Exit |
|---|---|---|
| Format | `uv run --frozen ruff format --check .` | **0** |
| Lint | `uv run --frozen ruff check .` | **0** |
| Types | `uv run --frozen mypy src tests` | **0** (57 source files) |
| Suite | `uv run --frozen pytest` | **0** - **663 passed, 0 skipped**, 6 deselected |
| Anchors | `scripts/check-harness-anchors.py --self-check --floor 340` | **0** - 371 anchors, 27 harnesses |
| Design citations | `docs/reviews/check-design-citation-shape.py` | **0** |
| Obligations | `docs/reviews/check-obligations.py` | **0** |
| U10 controls | `ci-harness-gate.sh check-u10-write-controls.sh --controls-fired ...` | **0** - 21/21 |
| U10 amputations | `ci-harness-gate.sh check-u10-write-amputation.sh --amputation ...` | **0** - 10 rows, 10 applied, **0 vacuous** |

**`docs/reviews/check-standards-citations.py` exits 2 here and that is NOT a red.** It prints
`CORPUS ABSENT at /tmp/evolv-coder-standards/standards` and exits 2 deliberately, *"because a
checker that cannot find its subject has not checked anything, and a green from it would be a lie"*.
The corpus is not present on this machine. **It is unchanged by this branch and I could not run
it**; CI checks the corpus out and is where its verdict comes from.

**ShellCheck was NOT run locally: `command not found`, exit 127.** Both new harnesses are written
against the same skeleton as `check-u12-jobfeed-{controls,amputation}.sh`, which pass it, but that
is reasoning and not a measurement. **CI's ShellCheck step is the first real run of it.**

### The floors, DERIVED from `ci.yml`, never retyped

```
$ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
check-suite-floor.sh 621
$ grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml
check-harness-anchors.py --self-check --floor 340
```

**Measured on this branch:**

| Floor | In `ci.yml` today | This branch measures | New value for you |
|---|---|---|---|
| Suite | 621 | **663 passed, 0 skipped** | **663** |
| Anchors | 340 | **371** | **371** |

**`ci.yml` is yours and I did not touch it.** Both numbers are **branch-local** until you raise the
floors and wire the two new harness steps.

---

## What was built

### `src/fast_mcp_jobvite/approval.py` (new)

- **The discriminator is `ctx.request_context.protocol_version` and nothing else.**
  `MODERN_PROTOCOL_VERSIONS = ("2026-07-28",)` selects MRTR;
  `HANDSHAKE_PROTOCOL_VERSIONS = ("2025-11-25",)` selects `ctx.elicit()`.
- **The handshake tuple is deliberately NOT "everything that is not modern".** An `else` would hand
  a future era to `ctx.elicit()` on the strength of never having been measured. **An era in neither
  tuple refuses and logs the observed value** (`DESIGN.md:1126-1130`), asserted by reading the
  `observed_protocol_version` field back off the real log stream.
- **The conjunction, on BOTH mechanisms**: `action == "accept" and content.get("approve") is True`
  on the MRTR leg; `AcceptedElicitation` **and** `data.approve is True` on the elicit leg.
- `ApprovalMechanism` is closed at ADR-0021's three values; `ApprovalState` is `approved` /
  `refused` / `pending` / `unavailable`.

### `create_candidate` in `src/fast_mcp_jobvite/tools/candidates.py`

Registered only under `JOBVITE_ENABLE_WRITES=true` **and** a name in `JOBVITE_TOOLS`, both
directions tested. `send_email` defaults to `false`. Annotations `destructiveHint: true` /
`idempotentHint: false` / `readOnlyHint: false`, with `readOnlyHint` stated false rather than
omitted. A `409` becomes `/problems/conflict` with the duplicate named in `detail`. The elicitation
payload names **the candidate, the target job, and whether `send_email` is true**.

Audit: `BEFORE_SIDE_EFFECT` before the `POST` (no audit, no write), then `AFTER_WRITE` after it,
with `attach_audit_warnings` producing **success with a warning, never an error** - because an error
makes the model retry, and a retried write creates a second record and may email a second live
person.

### `ApprovalRefusedError` in `errors.py`

**No new slug is minted.** `DESIGN.md:509` makes a published `type` URI a promise owed forever and
the registry at `DESIGN.md:513-521` has no row for an approval refusal, so this reuses
`/problems/forbidden`. See *Findings* F1.

### Two harnesses, and ADR-0027

`scripts/check-u10-write-controls.sh` (21 rows) and `scripts/check-u10-write-amputation.sh`
(10 rows), both driven through `scripts/ci-harness-gate.sh` with no change to that script - its
vocabulary is derived from each harness's own source, and both print `COULD NOT APPLY`,
`ANCHOR NOT UNIQUE` and `DID NOT LAND`.

`docs/adr/0027-approval-mechanism-names-a-path-this-design-does-not-use.md`, **Proposed**. See F2.

---

## The mutation harness: 21 rows, 21 fired

| Row | Behaviour broken | Verdict |
|---|---|---|
| M1 | the modern tuple swallows the handshake era | KILLED |
| M2 | the handshake era is no longer recognised | KILLED |
| M3 | an unidentifiable era approves instead of refusing | KILLED |
| M4 | the discriminator is `ctx.transport`, a measured trap | KILLED |
| M5 | the MRTR leg checks the action and not the value | KILLED |
| M6 | the MRTR leg checks the value and not the action | KILLED |
| M7 | the elicit leg accepts any acceptance whatever it carries | KILLED |
| M8 | any answer in the container is read as the approval | KILLED |
| M9 | `send_email` defaults to true | KILLED |
| M10 | the `send_email` argument never reaches the body | KILLED |
| M11 | the approval request no longer discloses the email | KILLED |
| M12 | the request direction of the blank unification is dropped | KILLED |
| M13 | the write response is read with the READ casing only | KILLED |
| M14 | the duplicate status is the wrong number | KILLED |
| M15 | every upstream failure is dressed up as a conflict | KILLED |
| M16 | the `JOBVITE_ENABLE_WRITES` gate does not gate | KILLED |
| M17 | the write advertises itself as read-only | KILLED |
| M18 | the audit mechanism is hardcoded to one era's path | KILLED |
| M19 | a refusal is never audited | KILLED |
| M20 | a post-write audit failure fails the call instead of warning | KILLED |
| M21 | the successful write returns no `request_id` on the wire | KILLED |

**TWO OF THEM SURVIVED ON THE FIRST RUN AND BOTH SURVIVORS WERE REAL.** They are recorded as F3 and
F4 below rather than quietly fixed, because the fix in each case was a change to the *subject*, not
to the row.

## The amputation harness: 10 rows, 10 applied, 0 vacuous

| Row | Behaviour deleted | Suite result | Survivors |
|---|---|---|---|
| A1 | the approval guard does not exist at all | 15 failed | 27 |
| A2 | there is one mechanism, not two | 19 failed | 23 |
| A3 | any response whatsoever authorises the write | 4 failed | 38 |
| A4 | an unrecognised era falls through instead of refusing | 2 failed | 40 |
| A5 | the approval request names neither the person nor the email | 3 failed | 39 |
| A6 | a duplicate is indistinguishable from any other failure | 1 failed | 41 |
| A7 | the successful write carries no `_meta` at all | 3 failed | 39 |
| A8 | the approved write emits no audit event before or after | 1 failed | 41 |
| A9 | the `send_email` flag is disclosed and then dropped | 1 failed | 41 |
| A10 | the deploy-time write gate does not exist | 1 failed | 41 |

**370 surviving assertions, and they are the output rather than a failure.** Every row went red, so
no behaviour here can be deleted unnoticed. **A1 is the row that matters**: with the approval guard
gone entirely, 15 assertions go red - including all four `#22` arms, both `#25` arms and both
audit-state arms. **The 27 that survive A1 are the ones that were never about approval** - the
casing readers, the wire body, the registration gates, the message builder - and that is the correct
answer, not a gap.

---

## Findings, each with a suggested fix

### F1 (Medium) - the error registry has no row for an approval refusal

`DESIGN.md:513-521`'s registry names seven conditions and none of them is *"the host returned no
approval"*. Its catch-all row sends anything unmapped to `/problems/internal-error`, **500** - which
would tell a caller this server is broken when a refusal is the control working exactly as designed.

`ApprovalRefusedError` therefore reuses `/problems/forbidden`, **403**, which is the closest fit and
is **a deliberate widening of that row past the "caller's token lacks the scope" condition its table
names**. No new slug is minted, because `DESIGN.md:509` makes a published `type` a promise owed
forever.

**Suggested fix (hypothesis, not an instruction):** add a registry row - *"an approval was required
and none was returned"* -> `/problems/forbidden`, 403 - so the widening is a decision rather than an
implementer's judgement. That is a `DESIGN.md` edit and therefore an ADR. **I did not raise one**,
because ADR-0027 is already open against this same paragraph's neighbourhood and ADR-0021 records
what happens when one ADR resolves two things.

### F2 (Medium) - `approval_mechanism`'s closed set names `sampling`, a path this design never uses

ADR-0021 closed the vocabulary at `elicitation`, `sampling`, `no_handler`. **This server has no
sampling path.** The sessionless era uses MRTR - `InputRequiredResult` plus `ctx.input_responses` -
which is a different protocol facility. ADR-0021's own context paragraph describes §7.5 as
*"elicitation on one era, **sampling** with `ctx.input_responses` on the other"*, and the closed set
was drawn from that sentence.

So the audit record's most informative field is **wrong on one of the two eras it exists to
distinguish**, and a checker asserting the value is one of the three passes.

**Suggested fix:** rename the sessionless value to `mrtr`, keeping the set closed at three. Raised as
**ADR-0027 (Proposed)**, which carries the full argument. **U10 emits `sampling` in the meantime**,
because the set is closed by an applied ADR against a frozen design and a unit that invents a fourth
string is a unit that decided a contract on its own.

**ADR-0026 was NOT free** despite the brief saying so - `docs/adr/0026-log-redaction-is-a-property-of-the-entry-point-not-the-client.md`
exists on another ref (task #68, landed while U10 was in flight). The brief also said to check
`docs/adr/` first, and checking the *working tree* would have missed it: `git log --all --name-only`
is what found it.

### F3 (Medium, FIXED here) - `send_email` had TWO defaults and the one a mutation could reach was inert

`CreateCandidateInput` declared `send_email: Annotated[bool, Field(default=False, ...)] = False`.
Pydantic takes the **assignment**; the `Field(default=...)` copy does nothing. Harness row **M9**
flipped the inert copy to `True` and `test_send_email_defaults_to_false_on_the_wire` **passed
against it** - a surviving row on the one field in this server that decides whether a live person
receives an email.

**Fixed at the source, not at the row**: the `Field(default=...)` copy is removed from all three
optional fields, so the default is declared once. M9 now mutates the declaration that decides, and
fires. **This is the two-lists defect at the width of a single field**, and only amputating the
wrong copy exposed it.

### F4 (Medium, FIXED here) - nothing exercised the ACTION half of the conjunction on the MRTR leg

Every arm of `test_case22_the_second_leg_actually_consumes_ctx_input_responses` sent
`action="accept"`, so deleting the action check changed nothing any of them could see. Harness row
**M6** survived.

**Fixed by adding the missing arm**, `test_case22_a_declined_answer_carrying_approve_true_refuses` -
a *declined* response carrying `approve: true` must refuse. M6 is pointed at it and fires.
`DESIGN.md:1075-1078` requires both halves; the suite had one.

### F5 (Low) - `ctx.input_responses` is not the shape the spike recorded

`FASTMCP-SPIKE-4.md:2103` reads the answers as `answers.root.get(...)`, a pydantic `RootModel`. At
the `fastmcp` version this repository pins it arrives as a **plain mapping**, and the spike's line
raises `AttributeError: 'dict' object has no attribute 'root'`. `_answer_for` accepts both forms,
with the reason at the call site.

**Suggested fix:** none in code - both are accepted deliberately. **The spike line should carry a
note** that the container type moved, so the next reader does not copy it. That is a
`docs/research/` edit and is yours.

### F6 (Low) - the audit-failure policy has three branches and a failed write is not one of them

`DESIGN.md:711-718` defines the policy over *before the side effect*, *a read tool*, and *after a
**successful** write*. A write that was attempted and **failed** matches none of them. `AFTER_WRITE`'s
*policy* is right for it - never raise, never fail the call, because a timeout after a successful
create is indistinguishable from a refused one - but its returned warning text asserts *"the write
succeeded"*, which is not known on that path.

`create_candidate` uses `AFTER_WRITE` there and **discards its return value**, with the reason at the
call site. The stderr line it also writes is generic and correct, so nothing false is emitted.

**Suggested fix:** give `AuditPhase` a fourth member, or reword the `AFTER_WRITE` warning to *"the
write may already have been performed; do not retry"*, which is true on both paths. `audit.py` is
not mine.

### F7 (nit) - `ApprovalState`'s vocabulary is this implementer's, not the design's

ADR-0021 explicitly leaves `approval_state`'s contents unsettled and declines to fold it in. U10
emits four values - `approved`, `refused`, `pending`, `unavailable` - named in `approval.py` so they
are visible as a choice.

**Suggested fix:** an ADR of its own. **Deliberately not folded into ADR-0027**, for the reason
ADR-0021 gives about itself.

### F8 (nit, FIXED here) - U8's amputation anchor A13 went stale the moment I touched the gate

`check-u8-candidates-amputation.sh:308` anchored on
`wanted = {SEARCH_CANDIDATES, GET_CANDIDATE} & settings.enabled_tools`. Adding `CREATE_CANDIDATE`
made it **0 hits**, and `ruff format` then wrapped the set across four lines, moving it again.
`check-harness-anchors.py` caught both in milliseconds.

**Fixed by REPOINTING, not shortening**, exactly as the brief requires: the new anchor is the wrapped
four-line set and the replacement still removes the whole gate including the write, so the row
deletes the same behaviour it always did.

---

## Two traps, and what I did about them

**Trap 1 - neither `ctx.transport` nor `session_id` may be the discriminator.**
`observed_protocol_version` reads `protocol_version` and nothing else.
`test_the_discriminator_is_protocol_version_and_not_transport_or_session_id` builds two contexts
whose `transport` and `session_id` are **byte-identical** and asserts they are, so only
`protocol_version` separates them - and harness row **M4** swaps the discriminator to `transport`
and is killed by that test.

**Trap 2 - §8 #25 must not assert an error shape.**
`test_case25_no_client_handler_fails_closed_on_both_eras` catches whichever shape arrives and
asserts **the row count did not move**. A separate case,
`test_case25_the_two_eras_refuse_in_DIFFERENT_shapes`, pins the asymmetry itself - and I re-measured
it rather than trusting the spike:

```
auto   RAISED   MCPError Elicitation not supported
legacy RETURNED is_error= True  "Error calling tool 'create_candidate'"
```

Exactly `FASTMCP-SPIKE-4.md:2153-2165`. That second case is **not** §8 #25; it is the measurement
#25's wording depends on, and it goes red if the two eras ever agree.

---

## What must go in the README - it is yours, not mine

Three residuals, all in `DESIGN.md`'s Residual Risks, and one behaviour:

1. **No approval attests to a person (C4-S1, High).** The server requires an approval response from
   the host and refuses to write without one. **A host may auto-respond with no person present**, and
   the MCP specification places human-in-the-loop on the host. The README must not say a human
   approved anything, and must say why it cannot.
2. **An abandoned approval hangs the call (C4-D1, Medium).** There is **no server-side bound** - the
   elicitation handler runs in the client's own process, so a client-side timeout is the only one
   there is. The write stays safe with the row count unchanged; the call does not return.
3. **An authorised write can be made twice (C4-D2, Medium).** Neither gate stops it. The write is
   never retried by this server, and a `409` surfaces as `/problems/conflict` with the duplicate
   named in `detail` - **detection, not prevention**, and the `409` shape is `[INFERRED]` rather than
   observed, so even the detection rests on a hypothesis until a credential exists. **The remedy the
   standard names cannot be built**: nothing establishes that Jobvite accepts an idempotency key on
   this endpoint (B108, `DESIGN.md:245-258`).
4. **`create_candidate` requires a host that can elicit**, and there is no fallback since the
   confirmation token was cut. On a host that can elicit on neither era, the tool refuses - which is
   correct and surprising if undocumented (`DESIGN.md:1595-1597`).

I would also disclose that **`send_email` defaults to `false` and setting it `true` mails a real
person**, and that the approval request names the candidate, the job and that flag - because an
integrator who does not know that will not know what they are approving.

---

## What I could NOT settle

- **ShellCheck on the two new harnesses.** `command not found`, exit 127 on this machine. CI's step
  is the first real run.
- **`check-standards-citations.py`.** Exits 2 - corpus absent at `/tmp/evolv-coder-standards`. It is
  unchanged by this branch, but *unchanged* is not *green*, and I did not see it green.
- **Everything about the live route.** `POST /api/v2/candidate`'s body, its `201` shape, the `EId`
  casing and the `409` are **all `[INFERRED]`** (`JOBVITE-CONTRACT.md:260`). Every fixture here is
  synthetic. **A suite passing against synthetic fixtures proves this client is self-consistent, not
  that it speaks Jobvite.** Checklist row 10 - one write in a customer-agreed window - is what
  settles all four, and nothing in this unit can.
- **Whether a fourth approval path exists.** If a host answers some way that is neither
  `ctx.elicit()` nor MRTR, the closed set is wrong. It would fail rather than absorb it, which is
  ADR-0021's intended direction, but nobody has seen one.
- **The dual-era behaviour on stdio.** Every era arm here runs over the in-memory client with
  `mode=auto` / `mode=legacy`. `DESIGN.md:1108-1114` records that a default stdio install lands on
  the handshake era and marks that claim **documentation-sourced, not executed**. I did not change
  that, and driving Claude Code against this server is still unrun.
- **`server.py` needed no line from me.** `candidates.register` already dispatches all three tools,
  and `build_server` calls it unchanged. **Nothing in `server.py`, `ci.yml`, `README.md`,
  `config.py`, `audit.py`, `http_hardening.py` or `services/jobvite_client.py` was edited.**
  `errors.py` gained one exception class (F1) and `scripts/check-u8-candidates-amputation.sh` had one
  anchor repointed (F8).
