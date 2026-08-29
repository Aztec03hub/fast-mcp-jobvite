# ADR-0008: EEO and other special-category fields excluded from output models

**Status:** Accepted
**Type:** Deviation

## Context

Our fixtures show `gender`, `race` and `veteranStatus` in candidate responses. These are
special-category personal data and, left alone, would flow straight to a model.

**An earlier draft justified excluding them by saying the GDPR standard is `priority: optional`.
That was false and checkable:** `architecture/gdpr-data-rights.md:9` reads `priority: required`, and
corpus-wide the only `optional` files are twelve README indexes.

## Decision

These fields are not in any output model and therefore never leave the server.

## Consequences

**The correct argument is scope, not priority.** That standard's obligations attach to systems that
**store** personal data - DSAR policies per table, erasure dispositions, a `gdpr_erasures` table.
This server stores nothing and Jobvite is the controller's system of record, so the DSAR and
right-to-be-forgotten machinery does not reach us.

**What is not waived:** `:119-129`, records of processing under Article 30, is field-level and names
downstream processors. Routing candidate PII to a model is exactly that, so `docs/data-inventory.md`
records categories, purpose and recipients.

The mechanism is the allow-listed output models, which generalise: nothing reaches the model that
was not deliberately admitted.

