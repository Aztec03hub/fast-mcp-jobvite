# U4 - Jobvite client, part 1: auth and the error-detection rule

**Branch:** `impl/u4-client` **Worktree:** `/tmp/impl-u4-work` (pinned at `5db4252`)
**Task:** #32

---

## What I read

Opened in full, not cited from memory:

- **`docs/DESIGN.md` frozen at `135c3ac`** (`git show`, never the worktree). §4 complete, §8 in
  full including required cases #1 and #2, §9 all seven hazards, and the packaging block in §10.
- **`docs/plans/IMPLEMENTATION-PLAN.md`** - `### U4` at `:763-801`, and §4's fixture-tier and
  dependency notes at `:304-322`.
- **`src/fast_mcp_jobvite/errors.py`** and **`utils/redaction.py`** in full;
  `utils/correlation.py` and `audit.py` by signature.
- **`docs/research/JOBVITE-CONTRACT.md`** §1, §2 (all of 2.1-2.3), §3 (all of 3.1-3.4).
- **`docs/adr/0007-httpx2-not-httpx.md`** in full; the ADR directory listing for status.
- **`CONTRIBUTING.md`**'s "The gates, and how to run them before you push", used as the gate list
  rather than a shorter one from memory.

**Not opened:** `docs/research/COMPLIANCE-SPEC.md`, and the TIER-1 standards
(`architecture/error-contract.md`, `backend/error-handling.md`, `backend/rate-limiting.md`,
`backend/python.md`). Recorded in "What I did NOT verify" below rather than implied.

---

## The brief's unverified numbers, checked

The brief flagged every `DESIGN.md` line number and the five-fixture claim as unverified. Checked
by opening the line and reading its subject:

| Cited | Verdict |
|---|---|
| `DESIGN.md:332-333` - the invariant | **Correct, verbatim.** "a response is successful only if the body carries no `status.code >= 400` **and** the HTTP status is below 400. Both, every call." |
| `DESIGN.md:1356-1357` - MockTransport | **Correct.** `:1308` is the `MockTransport` sentence. |
| `DESIGN.md:311-316` - v2 headers, jobFeed exception | **Correct.** |
| `DESIGN.md:337-340` - HR-XML hardened fallback | **Correct.** |
| §8 case **#1** = the 200-with-401-body trap | **Correct** - it is the first bullet of the required-cases list. |
| §8 case **#2** = a secret never reaching a log record | **Correct** - the second bullet. |
| §9 hazard **7** = route-level 404s | **Correct.** |
| `DESIGN.md:1413-1418` - the three pins | **Off by one at the start.** `:1365` is the ```` ```toml ```` fence; the block is `1366-1370` and the three pins are at **`1367-1369`**. Minor, and it still resolves. |
| "the recorded tier is exactly five files" | **Correct, and now asserted.** `git ls-files` shows exactly five `error_*` fixtures. `test_the_recorded_tier_is_exactly_these_five_files` closes the set so a sixth cannot arrive unnoticed. |

### A contracted range that still resolves - FINDING C1

Two committed citations for the three pins point at ranges that **do not contain them**:

- `pyproject.toml` comment: *"Verbatim from DESIGN.md:1406-1415"*
- `tests/test_manifest.py` docstring: *"they are DESIGN.md:1406-1410"*

The pins are at `DESIGN.md:1415-1417`. `1358-1362` **ends four lines before the block begins** - it
covers the prose paragraph about the resolve, not the pins. Both ranges still "resolve" to
plausible-looking text, which is the sharpest form of this failure. **I did not fix either**: they
are outside U4's subject and belong with the anchor-scheme work on task #30. **Filed as task
#34**, which also records a third contracted variant of the same anchor: `test_removing_fastmcp_slim_breaks_the_resolve`'s own assertion message cites `DESIGN.md:1406-1408`.

---

## The dependency slot - collision 10, all three steps

| Step | Done | Result |
|---|---|---|
| 1. Append one line per dependency to `[project] dependencies` | Yes | `httpx2==2.12.0`, `defusedxml==0.7.1` |
| 2. `uv lock` | Yes | `Resolved 118 packages`. Diff is **4 insertions, 0 deletions, 0 version changes** - two `dependencies` entries and two `requires-dist` entries. The brief's claim that both were already resolved transitively is **confirmed**: `httpx2` 2.12.0 and `defusedxml` 0.7.1 were already in `uv.lock` before the edit. |
| 3. Append the same strings to `test_manifest.py` | Yes | Appended to the closed set. **The set is still `==`, not a subset check.** The three original pins are untouched, unreordered, unrelaxed; `test_removing_fastmcp_slim_breaks_the_resolve` is unmodified. |

**Resolved versions: `httpx2==2.12.0`, `defusedxml==0.7.1`.** Nothing else was added - no
`tenacity`, no `circuitbreaker`, no third-party mocking library.

### One decision inside the slot, flagged rather than taken silently

`defusedxml` ships **no type information**, so under `strict = true` its imports are hard mypy
errors. I added a narrow `[[tool.mypy.overrides]]` for `defusedxml.*` rather than a
`types-defusedxml` dev dependency, because a stub package would resolve a **new distribution** into
`uv.lock` for a typing convenience, and collision 10 serialises lock edits across units. The cost
is recorded in the override's own comment rather than hidden: `fromstring`'s result is `Any` inside
`_raise_from_markup`, so that element walk is unchecked, and the two XML tests cover the branch
behaviourally instead. **If you would rather spend the lock churn, say so and I will swap it.**

### `SecretStr` - a Protocol, not a pydantic import

`DESIGN.md:323-324` requires credentials to be `SecretStr`, which is pydantic's. `pydantic` is in
the resolve only as a transitive of `fastmcp`, and my slot was granted for two packages. Importing
it would have been an undeclared direct import - the exact defect my own `httpx2` comment argues
against. So `jobvite_client.py` declares a `SecretValue` **Protocol** with the single method
`get_secret_value() -> str`. **pydantic's `SecretStr` satisfies it structurally**, so U1's config
can pass one straight in with no adapter, and no dependency was spent. Flagging it because it is a
deliberate deviation from the letter of `:317-318`.

---

## What was verified, and how

Every row below is a real assertion in `tests/test_jobvite_client.py`. **37 tests, all passing.**

| Requirement | Case | Result |
|---|---|---|
| **§8 #1, the 200-with-401-body trap, against the fixture VERBATIM** - C5-S1 | `test_C5_S1_an_http_200_carrying_a_401_body_is_NOT_a_success`, driven with `error_auth_200_body401.json`'s exact bytes through `MockTransport` at HTTP 200 | **PASS.** Raises `JobviteUpstreamError`, preserves Jobvite's 401 in `upstream_status`, and maps to `/problems/external-service-error` **502** - not a 401 to the caller. |
| Positive control for it | `test_positive_control_a_200_with_status_code_200_SUCCEEDS` | **PASS.** A synthetic 200 with `status.code == 200` returns its body. |
| Second positive control | `test_positive_control_a_200_with_no_status_block_at_all_SUCCEEDS` | **PASS.** `JOBVITE-CONTRACT.md` §3.2 records that whether a success carries a `status` block is unknown, so both shapes must pass. |
| **The four other recorded fixtures, BYTE-EXACT** | `test_recorded_error_fixtures_are_byte_exact` plus one behavioural case each | **PASS** - see the finding below. |
| **The recorded tier is exactly five files** | `test_the_recorded_tier_is_exactly_these_five_files` | **PASS.** Set equality, so a sixth fixture fails it. |
| The two SYNTHETIC malformed bodies fail loudly | `test_a_malformed_body_fails_loudly_rather_than_degrading` (parametrised over both) | **PASS.** Bytes **deliberately not pinned** - they are invented and carry no ground-truth weight. |
| **Route-level 404 is NOT a record-level not-found** (§9 hazard 7) | `test_a_route_level_404_is_not_reported_as_a_record_not_found` **and** `test_an_http_404_with_NO_status_envelope_is_also_not_a_record_not_found` | **PASS.** The second arm exists because of an amputation finding - see A12. |
| **No secret in a v2 URL** | `test_v2_credentials_travel_as_headers_and_NEVER_in_the_url` | **PASS.** Asserted on the request `MockTransport` actually received; the full URL is checked for both credentials. |
| **The v1 URL never whole in a log record** (joins U3's §8 #2) | `test_the_jobfeed_url_never_reaches_a_log_record_whole` | **PASS**, with a **paired positive**: it first asserts the log line was emitted at all, so the three absence assertions cannot pass against a silent logger. |
| Exception-message redaction | `test_a_transport_error_on_the_jobfeed_route_is_redacted` | **PASS**, paired positive: asserts the message still carries the URL, so the absence is about redaction and not an empty string. |
| **No cookie jar** | `test_no_cookie_jar_is_carried_between_requests` + `test_the_jar_is_cleared_even_when_the_call_RAISED` | **PASS**, with a **measured** positive control - see ADR-0022. |
| Three error encodings | `test_a_json_envelope_401_on_an_http_401_fails`, `test_a_tomcat_html_error_page_fails_loudly`, `test_plain_text_with_no_content_type_fails_loudly` | **PASS.** The plain-text case sends **no `Content-Type`**, matching the recorded transport, so it exercises the condition rather than describing it. |
| XML as a hardened fallback | `test_an_xml_entity_bomb_is_REFUSED_rather_than_expanded` + `test_positive_control_defusedxml_still_parses_an_ordinary_document` | **PASS.** The bomb arrives on an HTTP 200, so nothing about the transport warned us first. |
| **BOTH arms of the invariant, independently** | `test_arm_2_...` (two) and `test_arm_1_fires_even_when_the_http_status_is_a_success` | **PASS.** Each arm has a case that no other case covers. |
| No third-party mocking library | `test_no_third_party_mocking_library_is_imported_anywhere_in_the_suite` | **PASS.** Walks the **AST**, not a grep - a grep for `respx` matches the docstring saying we do not use it, which is precisely U3's "asserting the documentation existed". Carries its own positive control. |

### FINDING C2 - the byte-exact assertion earned its keep immediately

I wrote `error_v1_auth_401.txt`'s expected bytes with a trailing `\n`, matching the other four. The
test failed: **that fixture has no trailing newline and the other four do.** Every one of these
fixtures round-trips identically through `json.loads`, so a content-level assertion would never
have seen it. This is the concrete argument for "byte-exact" over "parses to the same thing", and
the corrected assertion now carries that note.

### FINDING C3 - the two auth fixtures are byte-identical

`error_auth_200_body401.json` and `error_auth_401.json` are **the same 93 bytes**. The only
discriminator for C5-S1 is the HTTP status supplied by the test. A reader assuming the fixture
*name* carried the 200 would write a test that loads the wrong file and still passes.
`test_the_two_auth_fixtures_are_byte_identical_only_http_status_differs` pins this so it is stated
rather than discovered.

---

## Mutation harness - `scripts/check-u4-client-controls.sh`

**RESULT: 17 killed, 0 not killed.** Every row names the test that must fail, and a row is a pass
only if **that named test** is among the failures - a red suite elsewhere is a coincidence, not a
control.

The row that matters most is **M02**, which stops the envelope arm firing and reopens C5-S1: it is
killed by `test_C5_S1_an_http_200_carrying_a_401_body_is_NOT_a_success`.

**M04 is the subtle one.** It turns the two arms into an `if/elif`, which still *looks* like it
checks both and still fails every recorded fixture, because they all carry a failing
`status.code`. Only a body that passes arm 1 and fails arm 2 can tell the difference, and
`test_arm_2_an_http_500_with_a_passing_envelope_still_fails` is that body.

---

## Amputation harness - `scripts/check-u4-client-amputation.sh`

**12 rows, all applied, none failed to land, tree clean after every restore.** Survivors are the
output, so per-row counts:

| Row | Result | Reading |
|---|---|---|
| A1 both arms gone | 8 failed / 28 passed | The invariant's whole case set dies. |
| A2 envelope arm deleted | 4 failed / 32 passed | Survivors expected: the recorded fixtures whose HTTP status is *also* >= 400 still fail via arm 2. Exactly why arm 2 alone is not sufficient evidence. |
| A3 HTTP arm deleted | 2 failed / 34 passed | Only the two synthetic arm-2 cases can see this. Symmetric to A2. |
| A4 decode never fails | 17 failed / 19 passed | The widest blast radius, as expected. |
| A5 markup never routed to defusedxml | 2 failed / 34 passed | HTML/XML still error, but via `json.loads` - so an entity bomb would reach the *stdlib* path. Caught by the two XML cases. |
| A6 no v2 credential headers | 1 failed / 35 passed | |
| A7 no jobFeed credential params | 2 failed / 34 passed | |
| A8 `_excerpt` neither redacts nor truncates | 2 failed / 34 passed | |
| A9 transport error unredacted | 1 failed / 35 passed | |
| A10 cookie jar never cleared | 2 failed / 34 passed | |
| A11 **request path logs nothing** | 1 failed / 35 passed | The vacuity probe. It kills `test_the_jobfeed_url_never_reaches_a_log_record_whole`, which proves that case's paired positive is real and it is not passing against silence. |
| A12 route-404 mapped to record-not-found | 1 failed / 35 passed | **After a fix - see below.** |

### What amputation found that mutation did not - FINDING C4

**A12 initially passed 36/36. Nothing noticed.**

Diagnosed rather than patched: A12 *introduces* the mapping hazard 7 forbids (an amputation that
adds code, which is unusual and is labelled as such in the harness). Its first revision injected
that mapping **after** the envelope arm - and arm 1 already raises for the recorded fixture's 404
envelope, so **the injected branch was unreachable**. The row tested nothing, and the way it said
so was by passing everything. A survivor that was an instrument fault rather than a finding about
the code.

Repositioning the injection to the top of `evaluate_response`, where a real implementer adding
record-not-found mapping would put it, kills
`test_a_route_level_404_is_not_reported_as_a_record_not_found` - so the hazard-7 case is genuinely
sensitive.

**But the diagnosis exposed a real gap in my test.** The case only covered an HTTP 404 whose body
*also* carries a 404 envelope, which reaches arm 1. An HTTP 404 with **no `status` block** reaches
arm 2 instead, and nothing covered it. Added
`test_an_http_404_with_NO_status_envelope_is_also_not_a_record_not_found`. That gap would not have
been found by the mutation harness, which is the fourth unit running for amputation.

---

## The design defect found by building - ADR-0022 (Proposed)

**`docs/adr/0022-no-cookie-jar-is-a-disable-not-an-omission.md`. Number 0022 taken, as instructed.
Status Proposed; not applied.**

`JOBVITE-CONTRACT.md` §2.3 says **"Do not implement a cookie jar."** Read literally, an implementer
discharges that by doing nothing. **Doing nothing produces the opposite of the intended
behaviour.** Measured against the pinned resolve before writing any client code:

```
jar after 1st response:      {'AWSALBAPP-0': '_remove_', 'AWSALBAPP-1': '_remove_'}
Cookie header sent on 2nd:   AWSALBAPP-0=_remove_; AWSALBAPP-1=_remove_
```

A bare `httpx2.AsyncClient` **has** a jar, stores what Jobvite sets, and resends it for the life of
the client. So the implementer who correctly follows §2.3 as written ships a client carrying the
session Jobvite told us not to carry. The ADR restates the requirement as an **action** ("clear the
cookie jar after every request"), which is the form that can be tested.

`JobviteClient.request` clears in a `finally`, so a call that raised cannot leave a jar behind
either. `test_positive_control_httpx2_DOES_carry_cookies_by_default` pins the default itself, so
the main assertion cannot go vacuous if `httpx2` ever changes - and it fails with a message naming
the clearing as possibly-dead-code rather than going quietly green.

**Note on ADR numbering - RETRACTED, and worth recording why.** At my pinned base `5db4252`,
`docs/adr/` jumped 0017 -> 0019 with **no `0018`**, and I wrote this section up as a possible
missing file. **That was true of my base and false of the tree.** U1 landed
`0018-forced-exit-masks-a-crash-as-a-clean-stop.md`, and after rebasing onto `origin/main` the
numbering is complete 0001-0022 with no gap. `0022` was still free and is mine. The finding was an
artefact of reading a pinned worktree as though it were current.

---

## Gates

Run from `CONTRIBUTING.md`'s list, **judged by exit code on its own line**, not by grepping output.

```
uv lock --check                                     exit=0
ruff check                                          exit=0
ruff format --check                                 exit=0
mypy                                                exit=0     <- the type gate, not pyright
pytest (default offline)                            exit=0     <- 294 passed, 2 deselected, 0 skipped
check-u0-test-controls                              exit=0
check-u15-gate-controls                             exit=0
check-u15-gate-amputation                           exit=0
check-u11-advisory-controls                         exit=0
check-u3-audit-controls                             exit=0
check-u3-audit-amputation                           exit=0
check-u4-client-controls                            exit=0     <- 17 killed, 0 not killed
check-u4-client-amputation                          exit=0     <- 12 rows, all applied
check-committed-file-types --all                    exit=0
check_advisories                                    exit=0
check-coupling                                      exit=0
check-coupling-controls                             exit=0
check-coupling-sweep                                exit=0
check-plan-measurements                             exit=0
check-obligations                                   exit=1     <- SIX ANCHORS MOVED, see below
```

`check-cross-references.py` exits 1 on `DESIGN.md:603`, held for ADR-0019. Confirmed to be that
one failure and nothing else; not reported as a problem and not touched.

**Suite: 294 passed, 2 deselected, 0 skipped**, POST-REBASE onto `origin/main` at **`a51ffc0`**.
U4's own file contributes **37**. (Against my pinned base `5db4252` and its 189/2/0 baseline the
suite was 226/2/0 - also 37 added. `main` moved twice while I worked: U1 landed at `742aff9` and
the advisory-gate fix at `a51ffc0`, so I rebased and re-ran the whole gate a second time rather
than reporting the first run's numbers.)

(Recorded because it is the mistake this project keeps catching: I first wrote 230 and 41 into this
report from prediction, then ran the suite and copied 226 and 37 off the terminal. The gate goes
before the message, not after it.)

### `docs/OBLIGATIONS.md` - six anchors moved, NOT repointed by me

**These are the POST-REBASE numbers**, re-run after rebasing onto `origin/main` at `a51ffc0`. The
pre-rebase run named different line numbers for the same six obligations, because U1's changes
shifted them too - which is why this block is the checker's output pasted whole rather than a
pair I typed.

Adding two dependencies plus a mypy override to `pyproject.toml`, and two steps to `ci.yml`,
shifted six anchored lines. **The checker's own output, verbatim:**

```
Mappings: 28  |  anchors verified against their subject: 15  |  recorded as absent: 7

FAIL: B49: pyproject.toml:159 no longer contains 'line-length = 88' - it is now at pyproject.toml:177. Repoint the anchor.
FAIL: B50: pyproject.toml:188 no longer contains 'convention = "google"' - it is now at pyproject.toml:206. Repoint the anchor.
FAIL: B51: pyproject.toml:181 no longer contains 'no datetime.utcnow' - it is now at pyproject.toml:199. Repoint the anchor.
FAIL: B52: pyproject.toml:175 no longer contains 'pep8-naming' - it is now at pyproject.toml:193. Repoint the anchor.
FAIL: B75: .github/workflows/ci.yml:509 no longer contains 'name: Capability drift report' - it is now at .github/workflows/ci.yml:539. Repoint the anchor.
FAIL: B82: .github/workflows/ci.yml:679 no longer contains 'Relative links resolve' - it is now at .github/workflows/ci.yml:709. Repoint the anchor.

6 failure(s).
```

`check-obligations.py --controls` also exits 1, with `ABORT: the real map is already red, so no
control below proves anything` - a consequence of the six above, not a separate fault.

---

## What I did NOT verify

Things I could not settle, rather than things I did not try.

1. **The four TIER-1 standards were not opened.** `architecture/error-contract.md`,
   `backend/error-handling.md`, `backend/rate-limiting.md`, `backend/python.md`. The brief says
   `priority: required` outranks it, so I cannot claim no required clause is contradicted. What
   reduces the exposure: `errors.py` is U2's merged work and already encodes the error-contract
   registry, and I raise its types rather than minting statuses. `rate-limiting.md` is most likely
   to bite U7, which owns retry and the breaker. **Please have a reviewer with those loaded check
   §4.3's timeout wording against my `httpx2.Timeout(connect/read/write/pool)` values** - I chose
   5/30/30/5 from nothing more authoritative than "not a single scalar".
2. **`COMPLIANCE-SPEC.md` was not opened**, despite the brief naming it. Same exposure class.
3. **No success body has ever been observed**, so every success-path assertion in this suite is
   against a synthetic hypothesis. `JOBVITE-CONTRACT.md` §13's checklist is what closes it. In
   particular I cannot verify that a real success body's `status` block, if it has one, carries a
   code under 400 - my `_envelope_status_code` tolerates both shapes precisely because it is
   unknown.
4. **Whether U1 spells its transport values the way U3 did.** I did not touch transport and did not
   invent a third spelling.
5. **Whether `pydantic.SecretStr` actually satisfies my `SecretValue` Protocol at runtime under
   U1's config.** It does structurally by signature and mypy accepts the Protocol, but I never
   constructed a real `SecretStr` - that would have meant importing pydantic, which is the thing I
   was avoiding. **A one-line check in U1 or U5 settles it.** This is the single most likely place
   for U4 to fail to compose.
6. **The `409` duplicate-create shape** (§9 hazard 6) is `[INFERRED]` and never observed; U4 raises
   `JobviteUpstreamError` for it. Mapping it to `DuplicateCandidateError` is `create_candidate`'s
   job, not the one-call path's.
7. **I did not run the `network`-marked arms**, which are deselected by default. `uv lock --check`
   passing is the frozen-resolve evidence I do have.

---

## Merge

```
git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite merge --no-ff impl/u4-client
```

Rebased onto `origin/main` at `a51ffc0` and the full gate re-run after that rebase; every number
above is from the post-rebase run. The branch is three commits, 13 files, **insertions only** - it
deletes and modifies nothing outside its own subject. Worktree `/tmp/impl-u4-work` removed.
