"""The allow-listed output models for the candidate reads.

**Outputs are allow-listed models, not passthrough**
(DESIGN.md:192-195). A field Jobvite returns that is not declared here
does not reach the caller, and it fails closed: a new Jobvite field is
dropped until someone admits it deliberately.

**THE EEO FIELDS ARE NOT IN ANY MODEL AND THEREFORE NEVER LEAVE THE
SERVER** (DESIGN.md:853-856, ADR-0008). Our own fixtures show `gender`,
`race` and `veteranStatus` in candidate responses; they are
special-category personal data, and left alone they would flow straight
to a model. **The allow-list is the mechanism, and §8 #6 asserts it
against these models rather than by inspecting a result** - because a
grep of a result for those names passes on an empty page, and a test
that the model cannot carry them does not. C6-I1, Critical.

The point generalises: it is not "drop three fields" but "nothing
reaches the model that was not deliberately admitted".

**This is the attacker-authored data class** (DESIGN.md:811-818), which
is what makes these models different from `models/jobs.py`. There every
field takes an explicit *not free text* decision because job data is
recruiter-authored inside the operator's organisation. Here the answer
is genuinely different for most of the surface: a résumé body, a name,
a self-reported location and a current job title are all **input from
people outside the operator's organisation, fed directly to a model**.

**`title` is the field the path-keyed rule exists for.**
`candidates[].title` is a job title *the candidate typed into an
application form* and is fenced. `candidates[].application.job.title`
is a requisition title authored inside the operator org and is not -
the same decision `models/jobs.py` records for it. **A name-keyed
allow-list cannot express that and would collide here and nowhere
else** (DESIGN.md:820-822).

**Dates are the NORMALISED spelling, not Jobvite's**
(§9 hazard 2, DESIGN.md:1462). Jobvite answers in epoch milliseconds
and takes `yyyy-MM-dd` on the way in; `utils/normalise.py` converts at
the boundary so one concept has one spelling in the tool surface.
`models/jobs.py` deliberately did NOT do this and said so - the
normaliser is U8's file and did not exist when that model was written.
"""

from __future__ import annotations

from typing import Annotated, Final

from pydantic import BaseModel, ConfigDict, Field, computed_field

from .fencing import Fenced, FencingDecision

#: The Jobvite envelope key a v2 candidate search returns its page
#: under (`JOBVITE-API.md:397`, from the ONE observed success body).
#: §9 hazard 3 is why this is a named constant and not a literal in the
#: tool body: v2 jobs key on `requisitions`, the v1 feed on `jobs`, and
#: the create response nests under `application` - three names for one
#: concept.
CANDIDATES_ENVELOPE_KEY: Final = "candidates"

#: Jobvite's own key for the result-set total, read from the envelope.
#: `JOBVITE-API.md:398`: the recorded call requested 5 records and the
#: response reported a `total` in the hundreds of thousands, so this is
#: the FULL result-set size and never the page size - and never a loop
#: condition (DESIGN.md:525-526).
TOTAL_ENVELOPE_KEY: Final = "total"

#: The special-category fields §6.2 names, in **Jobvite's own casing**,
#: which is the casing they would arrive in.
#:
#: **This set is a TEST ORACLE, not a filter.** Nothing in this module
#: reads it to exclude anything - the exclusion is structural, and a
#: deny-list would fail open on the EEO field nobody thought of. It
#: exists so §8 #6 can assert the models cannot carry these, which is a
#: claim about the models and not about a list.
EEO_FIELD_NAMES: Final[frozenset[str]] = frozenset({"gender", "race", "veteranStatus"})

_FENCE = FencingDecision.FENCE
_NOT_FREE_TEXT = FencingDecision.NOT_FREE_TEXT

#: The reason every candidate-typed field carries. Written once because
#: it is one argument, not eleven: DESIGN.md:813-815 defines the class
#: as "input from people outside the operator's organisation, fed
#: directly to a model".
_CANDIDATE_TYPED: Final = (
    "free text the candidate typed; outside the operator org, so the "
    "attacker-authored class of DESIGN.md:811-818"
)


class CandidateJob(BaseModel):
    """The requisition an application is against.

    **`JOBVITE-CONTRACT.md:254` records that this MAY BE NULL** - a
    production integration marks the read `failSilently: true` for
    exactly that reason - so `CandidateApplication.job` is optional and
    the tool must not treat its absence as an error.

    Every field here is authored inside the operator's organisation or
    minted by Jobvite, so none of it is the attacker-authored class.
    That is the same answer `models/jobs.py` gives, reached
    independently for the same reason.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    eid: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "eId", "opaque 8-character Jobvite identifier"),
    ] = None
    title: Annotated[
        str | None,
        Fenced(
            _NOT_FREE_TEXT,
            "title",
            "requisition title, authored in the operator org - NOT the "
            "candidate-typed `title` one level up",
        ),
    ] = None
    department: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "department", "org unit name, from the operator org"),
    ] = None
    location: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "location", "place name from Jobvite's own taxonomy"),
    ] = None


class CandidateResume(BaseModel):
    """The inline résumé body.

    **DESIGN.md:813 names résumé bodies FIRST** in its definition of
    the attacker-authored class, so `content` is the archetypal fenced
    field and `candidate_list_injection.json` attacks precisely it.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    format: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "format", "enumerated format name from Jobvite"),
    ] = None
    content: Annotated[
        str | None,
        Fenced(_FENCE, "content", "the résumé body itself; DESIGN.md:813 names it"),
    ] = None


class CandidateApplication(BaseModel):
    """One application, allow-listed.

    **`JOBVITE-CONTRACT.md:236`: a single object, not an array**, in
    the observed mapping - and it may itself be absent.

    **`gender`, `race` and `veteranStatus` live on this object in every
    fixture we have and are not declared here.** That absence is §6.2's
    whole mechanism, and `extra="forbid"` is what makes it unsettable
    rather than merely undeclared.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    eid: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "eId", "opaque Jobvite application identifier"),
    ] = None
    workflow_state: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "workflowState", "enumerated workflow state"),
    ] = None
    disposition: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "disposition", "recruiter-set outcome, operator org"),
    ] = None
    source: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "source", "sourcing channel recorded by Jobvite"),
    ] = None
    source_type: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "sourceType", "value from Jobvite's source taxonomy"),
    ] = None
    #: NORMALISED to `yyyy-MM-dd` (§9 hazard 2). The wire carries epoch
    #: milliseconds; the fencing path below still names Jobvite's key,
    #: because the registry is generated in Jobvite's key space and the
    #: decision is about the value that ARRIVES.
    sent_date: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "sentDate", "date, normalised from epoch ms"),
    ] = None
    last_updated_date: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "lastUpdatedDate", "date, normalised from epoch ms"),
    ] = None
    resume: Annotated[
        CandidateResume | None,
        Fenced(_NOT_FREE_TEXT, "resume", "container; its members decide separately"),
    ] = None
    job: Annotated[
        CandidateJob | None,
        Fenced(_NOT_FREE_TEXT, "job", "container; may be null, and its members decide"),
    ] = None


class Candidate(BaseModel):
    """One candidate, allow-listed and fenced.

    **Most of this surface is the attacker-authored class**, which is
    the difference from `models/jobs.py`. A name, an email address, a
    phone number, a self-reported location and a current job title are
    all typed by someone outside the operator's organisation into a
    form, and every one of them is fed to a model.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    eid: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "eId", "opaque 8-character Jobvite identifier"),
    ] = None
    first_name: Annotated[str | None, Fenced(_FENCE, "firstName", _CANDIDATE_TYPED)] = (
        None
    )
    last_name: Annotated[str | None, Fenced(_FENCE, "lastName", _CANDIDATE_TYPED)] = (
        None
    )
    email: Annotated[str | None, Fenced(_FENCE, "email", _CANDIDATE_TYPED)] = None
    home_phone: Annotated[str | None, Fenced(_FENCE, "homePhone", _CANDIDATE_TYPED)] = (
        None
    )
    work_phone: Annotated[str | None, Fenced(_FENCE, "workPhone", _CANDIDATE_TYPED)] = (
        None
    )
    city: Annotated[str | None, Fenced(_FENCE, "city", _CANDIDATE_TYPED)] = None
    state: Annotated[str | None, Fenced(_FENCE, "state", _CANDIDATE_TYPED)] = None
    country: Annotated[str | None, Fenced(_FENCE, "country", _CANDIDATE_TYPED)] = None
    #: THE PATH-KEYED CASE (DESIGN.md:820-822). The candidate's OWN job
    #: title, typed by them. `candidates[].application.job.title` is a
    #: requisition title and takes the opposite decision.
    title: Annotated[str | None, Fenced(_FENCE, "title", _CANDIDATE_TYPED)] = None
    work_status: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "workStatus", "enumerated status from Jobvite"),
    ] = None
    application: Annotated[
        CandidateApplication | None,
        Fenced(
            _NOT_FREE_TEXT,
            "application",
            "container; one object not an array, and its members decide",
        ),
    ] = None


class CandidateSearchResult(BaseModel):
    """One capped page of candidates, with the cap reported not hidden.

    **`request_id` is deliberately NOT a field here**
    (DESIGN.md:689-697). `additionalProperties: false` is set below and
    the client validates structured content against the cached output
    schema unconditionally, so an undeclared top-level `request_id` is
    rejected. `_meta` is the protocol's own channel.

    **This model and `Candidate` are two return schemas, which is why
    there are two tools.** `get_candidate` returns one record and
    `search_candidates` a page; under `strict=True` one tool cannot
    have two return schemas.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    candidates: Annotated[
        list[Candidate],
        Fenced(_NOT_FREE_TEXT, "candidates", "container; each element decides"),
    ] = Field(default_factory=list)

    #: Jobvite's own reported total, from the envelope. **Reported,
    #: never trusted as a loop condition** (DESIGN.md:525-540).
    total: Annotated[
        int, Fenced(_NOT_FREE_TEXT, "total", "integer from the envelope")
    ] = 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def showing(
        self,
    ) -> Annotated[
        int, Fenced(_NOT_FREE_TEXT, "showing", "integer derived from len(candidates)")
    ]:
        """How many candidates this result actually carries.

        Derived rather than stored, so it cannot disagree with the
        page beside it.

        Returns:
            The page length.
        """
        return len(self.candidates)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def summary(
        self,
    ) -> Annotated[
        str,
        Fenced(
            _NOT_FREE_TEXT,
            "summary",
            "derived by this server from two integers; no Jobvite content",
        ),
    ]:
        """The caller-facing `showing N of total` line.

        DESIGN.md:513-515 uses `showing 50 of 1,240` as its own worked
        example, and a capped result **reports** rather than truncating
        silently.

        Returns:
            The summary line.
        """
        return f"showing {self.showing:,} of {self.total:,}"
