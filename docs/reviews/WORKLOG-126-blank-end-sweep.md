# WORKLOG #126 - the blank-END citation sweep

Swept 2026-09-01, on `fix/blank-end-citations` off `main` at `0751016`.
Design read at the freeze, `docs/DESIGN-FREEZE.txt` -> `5d17cd7`, 2133 lines.

**The population was re-measured, not trusted.** A fresh run of
`docs/reviews/check-design-citation-shape.py` on this branch reported
**47** sites, which matches `docs/briefs/EVIDENCE-126-blank-end-citations.md`
and confirms the task title's **46** is stale. The sweep script parsed the
checker's own output rather than the evidence file, so no range was retyped.

47 sites -> 26 distinct ranges -> **19 distinct END lines**, and the END
LINE is the decision unit. Every line number below was read from
`git show 5d17cd7:docs/DESIGN.md | cat -n`, never counted inside a window.

## The nineteen decisions

Legend: **TRIM** = `end - 1` applied, the claim survives in the trimmed
range. **FINDING** = the claim is NOT in the trimmed range; argued in its
own section below.

| # | END | ranges (sites) | decision | the claim it was checked against |
|---|---|---|---|---|
| 1 | 213 | `207-213` (1) | TRIM -> `207-212` **+ FINDING F1** | `config.py:67` "the only write ... and the only one gated by `JOBVITE_ENABLE_WRITES`". Half the claim is at 209; the `JOBVITE_ENABLE_WRITES` half is at 227, outside the range either way. |
| 2 | 238 | `207-238` (1) | TRIM -> `207-237` | `candidates.py:13` "gated behind an explicit deploy-time opt-in **and** a per-invocation approval guard". Both gates are at 225-237 ("Two gates, deliberately not three"). Survives. |
| 3 | 314 | `312-314` (1) | TRIM -> `312-313` | `test_tools_job_feed.py:544` "forbids building a URL containing a credential **everywhere else**". That sentence is exactly 312-313. Survives. |
| 4 | 319 | `312-319` (1) | TRIM -> `312-318` | `redaction.py:96` "query parameters on the `jobFeed` URL that carry a credential". The jobFeed exception and the `sc=` redaction are 315-318. Survives. |
| 5 | 383 | `373-383` (6), `354-383` (1) | TRIM -> `373-382` / `354-382`, **one site EXEMPT** | 429 retried then mapped to 503 honouring `Retry-After` (373-375), plus ADR-0030's passed-on hint (376-382). `354-382` is the whole of §4.3, which is what `test_resilience.py:1` claims. Survives. The seventh site is a RECORD - see F5. |
| 6 | 391 | `386-391` (1) | TRIM -> `386-390` | `jobvite_client.py:624` "MCP gives us no inbound deadline to be shorter than - there is no HTTP request worker to hang and no caller-supplied timeout". Verbatim at 387-390. Survives. |
| 7 | 654 | `649-654` (1) | TRIM -> `649-653` | `audit.py:6` "`StructuredLoggingMiddleware` runs with `include_payloads=False`, which emits *no* arguments where the mandated field is *redacted* arguments". At 650-653. Survives. |
| 8 | 680 | `674-680` (2), `678-680` (2) | TRIM -> `674-679` / `678-679` | `674-679`: "retries and breaker transitions are logged, each carrying `request_id`" - at 674-677. `678-679`: the quoted "a retry line is exactly where an unredacted URL would otherwise reach a log" - at 678-679 verbatim. Both survive. |
| 9 | 698 | `692-698` (2) | TRIM -> `692-697` **+ FINDING F2** | `test_tools_jobs.py:312`/`:380` "the two arms travel by DIFFERENT channels and are different assertions". The success/error channel split is at 681-687, one paragraph EARLIER; 692-697 is the "not a field on the output models" paragraph. |
| 10 | 877 | `873-877` (1) | TRIM -> `873-876` | `test_config.py:375` "the off-loopback TLS refusal". At 873-876 ("binding a non-loopback address without `JOBVITE_TLS_TERMINATED_BY_PROXY=true` is a startup failure"). Survives. |
| 11 | 907 | `901-907` (1), `905-907` (2), `906-907` (1) | TRIM -> `901-906` / `905-906`; **`906-907` REPOINTED -> `908-910`, FINDING F3** | `901-906`: "the HTTP transport" / `JOBVITE_HTTP_TOKENS` - survives. `905-906`: "an open server is the alternative" - verbatim at 905-906, survives. `906-907`: "candidate PII, public job data, job feed" is the SCOPES sentence at 908-910, which the trim would have excluded entirely. |
| 12 | 1009 | `1004-1009` (1), `992-1009` (2) | TRIM -> `1004-1008` / `992-1008` | `1004-1008`: "an unrecognised tool name exits naming it" - at 1004-1006. `992-1008`: `JOBVITE_TOOLS`, the AND-ing, and what does and does not register - 992-1008. Both survive. |
| 13 | 1030 | `984-1030` (1), `1028-1030` (1) | TRIM -> `984-1029` / `1028-1029` | `984-1029`: "U1's configuration refusals", i.e. all of §7.3 - survives. `1028-1029`: "`server.json` declares EVERY variable" - verbatim at 1028. Survives. |
| 14 | 1144 | `1134-1144` (5), `1143-1144` (1) | TRIM -> `1134-1143`; **`1143-1144` REPOINTED -> `1142-1143`, FINDING F4** | `1134-1143`: "an approver shown a database row authorises an email nobody named" - at 1136-1141. Survives. `1143-1144` quotes "names the candidate, the target job, and **whether `send_email` is true**, in those terms", which BEGINS at 1142; the trim would have left the fragment "is true**, in those terms." |
| 15 | 1313 | `1310-1313` (3) | TRIM -> `1310-1312` | "CI has **zero skips** - a skip counts as a failure, so credential-dependent tests are excluded by *selection*". Verbatim 1310-1312. Survives. |
| 16 | 1323 | `1318-1323` (1) | TRIM -> `1318-1322` | `test_markers.py:6` "a typo in the exclusion marker's name selects nothing and the run goes green having tested less than it claimed". Verbatim at 1318-1319, and `--strict-markers` turning it into a collection error at 1320-1321. Survives. |
| 17 | 1338 | `1332-1338` (1) | TRIM -> `1332-1337` | `test_fixture_path.py:16` "three tiers: recorded, structural, synthetic". The heading is 1332 and the three bullets are 1333-1337. Survives. |
| 18 | 1453 | `1451-1453` (6) | TRIM -> `1451-1452` | "A guard that refuses everything is not a guard ... every refusal-path test is paired with a positive control". Verbatim 1451-1452. Survives at all six sites. |
| 19 | 1669 | `1663-1669` (1) | TRIM -> `1663-1668` | `config.py:230` "§4.3 requires the total outbound budget to be **configured** ... the default is a choice, not a measurement". At 1663-1668. Survives. |

Sixteen end lines were a clean `end - 1`. Three were not, and one site inside
end 383 must never move at all.

## FINDINGS - what was not a trim

### F5 (applied) - `check-design-citation-shape.py:45` is a RECORD, not a citation

The checker's own docstring names `DESIGN.md:373-383` as one of the TWO
instances R12 had read before writing the check. Trimming it to `373-382`
would falsify the record: 383 is where the defect WAS, and the sentence is
about that fact. Marked `REPOINT-EXEMPT` on the line instead - the same
mechanism the same docstring already uses for the `DESIGN.md:311` record one
paragraph up, and the mechanism `repoint-design-citations.py` honours.

The surrounding paragraph was REWRITTEN in place rather than appended to,
because it also carried two stale numbers: it said the sweep found **46**,
and the merged trunk measures **47**. It now records both numbers and that
the backlog is zero.

`REPOINT-EXEMPT` lines went 22 -> 23, exactly the one line added.

### F1 (reported, NOT repointed) - `config.py:67` names a gate outside its range

`src/fast_mcp_jobvite/config.py:67` claims the write tool is "the only one
gated by `JOBVITE_ENABLE_WRITES`" and cites what was `DESIGN.md:207-213`.
`JOBVITE_ENABLE_WRITES` first appears at `DESIGN.md:227` ("Not registered
unless `JOBVITE_ENABLE_WRITES=true`"), which is outside 207-213 *and*
outside the trimmed 207-212. The trim neither creates nor worsens this; the
citation was already short of half its claim.

**Left as `207-212` and reported rather than repointed**, because widening a
range is a correctness decision, not the shape fix this task owns.
**Suggested fix:** `DESIGN.md:207-229` - the section heading through the
deploy-time gate bullet, which is where both halves of the claim live.

### F2 (reported, NOT repointed) - `test_tools_jobs.py` cites the paragraph after its claim

Both `tests/test_tools_jobs.py:312` and `:380` claim the two `request_id`
arms "travel by DIFFERENT channels and are therefore different assertions".
That split is stated at `DESIGN.md:681-687`: *"The error half is the problem
object's own `request_id` member ... The success half goes in the result's
`_meta`"*. The cited 692-698 is the NEXT paragraph, "Not a field on the
output models", which explains why `_meta` rather than a model field. It
supports half the claim and states none of the error half.

This is the R4 off-by-one-paragraph shape in the other direction, and the
blank-end check cannot see it - it only sees the trailing blank line.

**Left as `692-697` and reported. Suggested fix:** repoint both sites to
`DESIGN.md:681-687`.

### F3 (repointed, loudly) - `test_http_hardening.py:506` was one line short of its sentence

`tests/test_http_hardening.py:506` reads
`"""DESIGN.md:906-907: candidate PII, public job data, job feed."""`.
`DESIGN.md:906` is *"§7.3 applies to every required variable."* - the tail of
the fail-fast sentence, about something else entirely - and 907 is blank. The
scopes claim is at **908-910**: *"**Scopes follow the three data classes of
§4.1**: candidate PII, public job data, and the job feed."*

`end - 1` here would have produced `DESIGN.md:906`, a single line that
RESOLVES, passes both citation gates forever, and names an unrelated
sentence. That is exactly the #114 class. Trimming would have made the
citation worse, so it was **repointed to `DESIGN.md:908-910`**, not trimmed.
Recorded here rather than folded silently into the 46.

### F4 (repointed, loudly) - `redaction.py:149` quotes a sentence starting one line before its range

`src/fast_mcp_jobvite/utils/redaction.py:149` quotes the elicitation payload
sentence verbatim. That sentence spans `DESIGN.md:1142-1143`; the citation
said `1143-1144`. `end - 1` would have left `DESIGN.md:1143`, the fragment
*"is true**, in those terms."*, which does not contain the quoted claim.

**Repointed to `DESIGN.md:1142-1143`.** Same reasoning as F3: the trim was
available and would have been wrong.

## Gates, each exit code read on its own line

Run from the worktree at the swept tree.

```
ruff check .                                        0
ruff format --check .                               0   (110 files already formatted)
mypy                                                0   (no issues in 110 source files)
pytest                                              0   873 passed, 0 skipped, 6 deselected
check-quickstart.py                                 0
check-suite-floor.sh floor (ci.yml)               873   met exactly by 873 passed
check-harness-anchors.py --self-check --floor 458    0   458 anchors resolve
check-coupling.py docs/DESIGN.md                    0
check-cross-references.py                           0
check-coupling-controls.py                          0
check-coupling-sweep.py                             0
check-obligations.py                                0
check-obligations.py --controls                     0
check-plan-measurements.py                          0
check-resweep-verdicts.py                           0
check-clause-citations.py                           0
check-design-citations.py                           0   1902 citations, 200 files, all resolve
check-design-citation-shape.py                      0   881 citations, 160 files, 0 findings
check-design-citation-shape.py --controls           0   7/7 controls fired
```

**The zero is not vacuous.** The `--controls` run's detector arm still prints
`DETECTOR ends on a blank line -> FIRED`, so the branch that found these 47
is alive against a citation built to trip it, and the negative control still
returns no finding. A detector nothing can reach prints the same clean run.

`check-review-coverage.py` exits **1** (150 trunk commits, 81 fully covered,
0 partial). That is the pre-existing #119 backlog, it is NOT wired in
`ci.yml`, and this sweep is not a code review, so it declares no
`REVIEW-COVERS` range.

## Not wired, on purpose

`check-design-citation-shape.py` is now green and ready to wire. Wiring is
**#125** and belongs to the team lead; nothing in `.github/workflows/ci.yml`
was touched here.

## What I did NOT verify

- **F1 and F2 are reported, not fixed.** I read the design at the freeze and
  the citing sites, and I am confident the ranges are short of their claims -
  but I did not repoint them, so nothing here proves the suggested ranges are
  the ones the team lead wants.
- **I did not re-check the ~834 citations that were NOT in this population.**
  The blank-end shape is one detector; a citation landing on real prose one
  paragraph off looks clean to every gate here. F2 is one such, and it was
  only visible because the same range happened to also end on a blank line.
