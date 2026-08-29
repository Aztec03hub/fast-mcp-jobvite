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

## Two adjacent citations that RESOLVE and are still wrong

The shape checker cannot see these - both land on real prose - and they are in the same sentences as
rows above, so fix them in the same pass rather than leaving a neighbour wrong:

- `jobvite_client.py:526` cites **`313-316`** for the `jobFeed` route's structural requirement.
  Repoint to **`315-318`**, the same target as `314-315` above.
- `test_server.py:1` cites **`958-960`** for §7.4. Repoint to **`959-961`**; 958 is the heading.

## Who applies which

- **`src/` and `tests/`** - 33 rows - belong to `r4-fixes`.
- **`scripts/check-u4-client-amputation.sh:249` and `scripts/check-u4-client-controls.sh:184,195`** -
  3 rows - belong to `shell-hygiene`.

Whoever goes second re-runs the checker; it exits 1 while any remain and 0 when both lanes have
landed. **A zero from it does not mean the citations are correct**, only that none of them point at
a blank line, a fence, or the end of the file. R4 found ten wrong citations by reading that this
checker cannot see, and none of those ten are in the 36.
