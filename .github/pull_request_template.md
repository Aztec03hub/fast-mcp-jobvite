<!--
F-7. Body copied VERBATIM from devops/development-workflow.md:201-241, which
mandates it. quality-gates.md:50 (B100 - and this does NOT close B101, the reviewer checklist) gates PR creation on "Completed PR template",
so the artifact itself is the obligation. COMPLIANCE-SPEC.md:320 marks the
CONTENT [STD] REQUIRED and the PATH [REC] - .github/pull_request_template.md is
the GitHub convention, not a standards requirement.

Two sections below are inapplicable to this repository and are KEPT rather than
deleted: "E2E tests" (no frontend - COMPLIANCE-SPEC.md:113) and "Screenshots"
(no UI). The standard mandates the body; dropping rows silently is a deviation,
and both already carry "if applicable". Tick them N/A.

Only the "Related Issues" section is extended, for the `Refs:` trailer that
ruling C3 requires on every commit.
-->

## Summary
Brief description of changes (2-3 sentences)

## Type of Change
- [ ] Feature (new functionality)
- [ ] Bug fix (non-breaking fix)
- [ ] Breaking change (fix or feature that would break existing functionality)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] E2E tests added/updated (if applicable)
- [ ] Manual testing completed

### Test Commands Run
```bash
# Commands used to test
```

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] All tests pass locally
- [ ] CHANGELOG updated (if user-facing)

## Related Issues
Closes #XXX

<!--
Ruling C3: every commit carries a `Refs:` trailer, and the PR title is
semantic - `type(scope): description`. The title is checked automatically by
.github/workflows/pr-title.yml; the trailer is checked in review.
-->
Refs:
