# The authoritative repoint map for the 36 wrong-target `DESIGN.md` citations

`docs/reviews/check-design-citation-shape.py` named 36 citations in `src/ tests/ scripts/` whose
target cannot be their subject (task #37, measured at `4f4ae1d`). **This document resolves every one
of them by reading `git show c15b138:docs/DESIGN.md` and matching the SUBJECT**, so that two agents
fixing them in two different lanes cannot arrive at two different answers.

## Read this before you apply a single edit

**DO NOT ADD A CONSTANT OFFSET.** Twenty-five of the 36 are one line short, which makes `+1` look
like the whole answer. It is not, and this table contains its own counter-example:

- `constraints.py:4` cites **302-306** for *"Every input model imports its constraints from here. No
  input model defines its own"*. That sentence is at **300-301**. This citation is **one line LONG**.
  A `+1` sweep would move it further from its subject and the shape checker would go quiet, because
  303-304 is real prose - just somebody else's.
- `test_error_contract.py:162` cites **345-347** for *"the plain-text and Tomcat-HTML encodings carry
  no status"*. That is at **335-340**, in §4.2. The citation is **a whole section away**; 345-347 is
  §4.3 Resilience. No offset of any size finds it.
- `1793` and `1795` are both in C7's threat table and they resolve to **different rows** - 1799 and
  1797 - because the two sites cite different threats. An offset cannot split them.

**Three of the 36 are not off-by-one at all.** That is the argument against the mechanical fix,
stated as measurement rather than caution.

## The map

Every "new" below is the range whose text IS the quoted subject, verified against `c15b138`.

| Cited | Repoint to | The subject at the new range |
|---|---|---|
| `311` | `312` | "v2 credentials travel as headers, `x-jvi-api` and `x-jvi-sc`" |
| `311-312` | `312-313` | "**A URL containing a secret is never constructed**" |
| `311-316` | `312-318` | both: the header rule and the `jobFeed` exception |
| `312-316` | `312-318` | the same, plus "Enforced in one place, `utils/redaction.py`" - see the section below; 17 sites |
| `314-315` | `315-318` | "`GET /v1/jobFeed` is the exception ... never logged whole, never in an exception message, `sc=` redacted before any log line" |
| `302-306` | `300-301` | "Every input model imports its constraints from `utils/constraints.py`. No input model defines its own (ADR-0012)" |
| `302-303` | `303-304` | "No cache module, no bulk module, no custom logging module ... `loguru` cover the first and third" |
| `322-323` | `323-324` | "Credentials are `SecretStr` throughout, resolved with `.get_secret_value()` only when building a request" |
| `345-347` | `335-340` | "**Three error encodings are handled** ... plain text with no `Content-Type` header at all, and a Tomcat HTML page" |
| `692-705` | `693-705` | "That distinction is load-bearing ... Two different identities are in play" |
| `720-727` | `721-727` | "**What the caller receives** ... a `warnings` array in its structured content ... **Not a problem object.**" |
| `936-943` | `937-945` | "Fail-fast validates what each *enabled* tool requires, never the union", plus the requirements table |
| `959-960` | `960-961` | "`|` composition; startup in order, teardown in strict reverse, verified" |
| `984-988` | `985-986` | "**The verified implementation** installs an explicit handler rather than copying SIGINT's, and forces exit after teardown" |
| `1403-1407` | `1404-1407` | "**`mcp` is pinned explicitly**, not just `fastmcp`" |
| `1793` | `1799` | **C7-I1**, "Candidate PII written to logs in the clear", rated Critical |
| `1795` | `1797` | **C7-T1**, "A caller-supplied `X-Request-ID` carrying newlines forges log entries" |

## `312-316`, cited at seventeen sites, stops one sentence short

**Found by `shell-hygiene` while applying its three rows, and it is the map's own first miss.** The
range ends at 316, mid-specification. 317-318 is:

> `sc=` redacted before any log line. **Enforced in one place, `utils/redaction.py`**, with a test
> that fails if a secret can reach a log record.

*"Enforced in one place"* is the phrase four of the citing sites quote back, and the range cuts it
off. `redaction.py:1` opens *"Secret redaction - the single enforcement point (DESIGN.md:312-316)"*,
which is a citation that does not contain its own subject.

**No checker can see this**, because both endpoints are real prose. It is the class this document's
next section describes, and it was not in it.

**Repoint `312-316` -> `312-318`**, at all twelve sites under `src/ tests/ scripts/`. No new
derivation is needed: the table already sends `311-316` to `312-318` with the subject "both: the
header rule and the `jobFeed` exception". This citation has that same subject plus the enforcement
sentence, which is the part being quoted.

**The five hits under `docs/` are deliberately LEFT AS WRITTEN** - `U3-IMPL-REPORT.md` (x2),
`FIX-AUDIT-LOGGING-REPORT.md` (x2) and `REVIEW-CODE-R2.md`. They are dated records of what someone
measured on a particular day, and the same reasoning that excludes `docs/reviews/` from the checker's
scan applies to a worklog: repointing them edits history to agree with the present. shell-hygiene
flagged this call rather than making it; this is the call.

**Sweep all twelve in one pass.** Repointing one of seventeen is worse than repointing none, because
a reader who greps the string then finds two answers and no way to tell which is current.

## Two adjacent citations that RESOLVE and are still wrong

The shape checker cannot see these - both land on real prose - and they are in the same sentences as
rows above, so fix them in the same pass rather than leaving a neighbour wrong:

- `jobvite_client.py:526` cites **`313-316`** for the `jobFeed` route's structural requirement.
  Repoint to **`315-318`**, the same target as `314-315` above.
- `test_server.py:1` cites **`958-960`** for §7.4. Repoint to **`959-961`**; 958 is the heading.

## Who applies which

- **`src/` and `tests/`** - 33 shape rows, plus 11 of the 12 `312-316` sites - belong to `r4-fixes`.
- **`scripts/check-u4-client-*.sh`** - 3 shape rows - and **`scripts/check-u3-audit-controls.sh:185`**,
  one `312-316` site. Applied at `2e21aa7` and in the commit that adds this section; `shell-hygiene`
  had gone idle and its branch was merged, so reviving an agent for four comment lines was the more
  expensive option.

Whoever goes second re-runs the checker; it exits 1 while any remain and 0 when both lanes have
landed. **A zero from it does not mean the citations are correct**, only that none of them point at
a blank line, a fence, or the end of the file. R4 found ten wrong citations by reading that this
checker cannot see, and none of those ten are in the 36.
