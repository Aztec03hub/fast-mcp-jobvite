"""The allow-listed output model for `search_jobs` (DESIGN.md:192-195).

**Outputs are allow-listed models, not passthrough.** A field Jobvite
returns that is not declared here does not reach the caller, and it
fails closed: a new Jobvite field is dropped until someone admits it
deliberately. That is *containment*, and DESIGN.md:192-195 is explicit
that it is a different control from fencing - a field can be correctly
admitted and still carry an injection payload, which is why every
field below also carries a `Fenced` decision.

**Public job data, not candidate PII** (DESIGN.md:137). This is the
least dangerous data class in the tool surface, which is why the plan
puts the first end-to-end slice here: it exercises transport
selection, config fail-fast, the error contract, the audit path, the
result cap and `_meta` without depending on EEO exclusion or candidate
redaction.

**Epoch milliseconds are carried through as integers, not parsed.**
SS9 hazard 2 records the date asymmetry - requests take `yyyy-MM-dd`
strings and responses return epoch milliseconds - and says it is
normalised at the boundary. `utils/normalise.py` is **U8's file** by
the plan's SS4 ownership table, so this unit does not create it and
does not write a second normaliser beside it. The field's type says
exactly what Jobvite sent, and U8's normaliser is where it changes.

**`eId` keeps Jobvite's casing in the generated fencing path and takes
snake_case on the model.** That is the two key spaces DESIGN.md:202-205
names, working as intended: `eid` is our attribute, `eId` is Jobvite's
key. SS9 hazard 1's casing asymmetry (`eId` on reads, `EId` on the
create response) is pinned by U10's test on the write path; this model
only ever sees the read spelling.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, computed_field

from .fencing import Fenced, FencingDecision

#: The Jobvite envelope key a v2 job search returns its page under
#: (SS9 hazard 3: v2 jobs key on `requisitions`, the v1 feed on
#: `jobs`, and the create response nests under `application` - three
#: names for one concept, which is why this is a named constant and
#: not a literal in the tool body).
JOBS_ENVELOPE_KEY = "requisitions"

#: Jobvite's own key for the page total, read from the envelope rather
#: than counted from the items (DESIGN.md:469-477: `total` is reported
#: and never trusted as a loop condition).
TOTAL_ENVELOPE_KEY = "total"

_NOT_FREE_TEXT = FencingDecision.NOT_FREE_TEXT


class JobLocation(BaseModel):
    """One location on a requisition.

    Every member is a place name from Jobvite's own taxonomy, not text
    a candidate typed, so none of it is the attacker-authored class
    DESIGN.md:738-744 defines.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    city: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "city", "place name from Jobvite, not candidate-typed"),
    ] = None
    state: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "state", "region code from Jobvite's own taxonomy"),
    ] = None
    country: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "country", "country code from Jobvite's own taxonomy"),
    ] = None


class Job(BaseModel):
    """One requisition, allow-listed.

    **Every field takes an explicit "not free text" decision**, which
    is what the plan schedules for this unit: job fields are
    recruiter-authored or Jobvite-generated, so none of them is the
    outside-the-organisation class `ai/prompt-injection.md` addresses.
    Recording the decision is the point - the next model is
    `models/candidate.py`, where the answer is different, and a field
    that was never decided about would be indistinguishable from one
    decided to be safe.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    eid: Annotated[
        str,
        Fenced(_NOT_FREE_TEXT, "eId", "opaque 8-character Jobvite identifier"),
    ]
    title: Annotated[
        str,
        Fenced(
            _NOT_FREE_TEXT, "title", "requisition title, authored in the operator org"
        ),
    ]
    description: Annotated[
        str | None,
        Fenced(
            _NOT_FREE_TEXT,
            "description",
            "recruiter-authored posting body; inside the operator org, so not the "
            "attacker-authored class of DESIGN.md:738-744",
        ),
    ] = None
    apply_link: Annotated[
        str | None,
        Fenced(
            _NOT_FREE_TEXT, "applyLink", "URL minted by Jobvite, not typed by anyone"
        ),
    ] = None
    job_state: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "jobState", "enumerated workflow state from Jobvite"),
    ] = None
    department: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "department", "org unit name, from the operator org"),
    ] = None
    category: Annotated[
        str | None,
        Fenced(
            _NOT_FREE_TEXT, "category", "value from Jobvite's own category taxonomy"
        ),
    ] = None
    locations: Annotated[
        list[JobLocation],
        Fenced(_NOT_FREE_TEXT, "locations", "container; its members decide separately"),
    ] = Field(default_factory=list)
    last_updated_date: Annotated[
        int | None,
        Fenced(_NOT_FREE_TEXT, "lastUpdatedDate", "epoch milliseconds (SS9 hazard 2)"),
    ] = None
    sent_date: Annotated[
        int | None,
        Fenced(_NOT_FREE_TEXT, "sentDate", "epoch milliseconds (SS9 hazard 2)"),
    ] = None


class JobSearchResult(BaseModel):
    """One capped page of jobs, with the cap reported not hidden.

    **`request_id` is deliberately NOT a field here**
    (DESIGN.md:639-650). `additionalProperties: false` is set below and
    `ClientSession.validate_tool_result` validates structured content
    against the cached output schema unconditionally, so an undeclared
    top-level `request_id` is *rejected*. Declaring it would work and
    is rejected for a different reason: it would put transport plumbing
    inside the model-facing payload and make it part of five tools'
    data contracts. `_meta` is the protocol's own channel, and the
    validator never inspects it.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    #: THE FENCING DECISIONS ON THIS MODEL EXIST BECAUSE OF R4-M1.
    #: `fencing_paths` was only ever called with `Job` named by hand,
    #: so the model that is actually serialised to the caller carried
    #: no decisions at all and no test asked it to. It now cannot:
    #: `test_every_output_model_in_the_package_has_a_registry`
    #: discovers the models rather than naming them.
    jobs: Annotated[
        list[Job],
        Fenced(_NOT_FREE_TEXT, "requisitions", "container; each element decides"),
    ]

    #: Jobvite's own reported total for the query, from the envelope.
    #: **Reported, never trusted as a loop condition**
    #: (DESIGN.md:487-489); U6 owns the scan that would.
    total: Annotated[int, Fenced(_NOT_FREE_TEXT, "total", "integer from the envelope")]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def showing(
        self,
    ) -> Annotated[
        int, Fenced(_NOT_FREE_TEXT, "showing", "integer derived from len(jobs)")
    ]:
        """How many jobs this result actually carries.

        Derived rather than stored, so it cannot disagree with `jobs`.

        The decision lives in the RETURN annotation because a computed
        field has no `FieldInfo.metadata` (R4-M1).
        """
        return len(self.jobs)

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

        DESIGN.md:474-476 uses `showing 50 of 1,240` as its own worked
        example, and DESIGN.md:469-477 is explicit that a capped
        result **reports** rather than truncating silently: a capped
        call is a mismatch against `total` by design, and is not an
        anomaly to be logged.

        Derived from `showing` and `total` in one place, so the string
        a caller reads and the numbers beside it cannot drift - which
        is the same defect DESIGN.md:202-205 avoids for the fencing
        paths, applied to a much smaller surface.
        """
        return f"showing {self.showing:,} of {self.total:,}"
