# Plant Care Tracker Constitution

## Core Principles

### I. Stakeholder-Driven Scope

Every feature MUST trace back to a requirement in the feature spec, and every requirement MUST
trace back to a goal in the goal model (G1–G4) or a statement in the stakeholder interview.
Features that do not trace (notifications, automatic water/sunlight calculation, fertilizing,
photos, multiple households) MUST NOT be built in this version.

Rationale: the stakeholder asked for a small first version: "add our plants, keep track of
watering and sunlight, and see what needs attention."

### II. People Record Care, the App Never Assumes It

The application MUST only change care state (watered, moved outside, brought inside) in response
to an explicit action by a household member. It MUST NOT automatically mark anything as done.
Overdue states MUST persist until a person records the corresponding action. Every care event
MUST record who performed it and when.

Rationale: the stakeholder said "I wouldn't want it to automatically mark anything as done" and
that knowing "who last took care of a plant" is useful.

### III. One Shared Source of Truth

Both household members MUST see the same plants, schedules, and history. All state MUST live in a
single server-side store; no care data may live only in one person's browser. A change made by one
person MUST be visible to the other on their next page load.

Rationale: the core failure of the fridge chart was the two roommates working from different
information.

### IV. Simplicity First

The prototype MUST use the smallest workable stack: one process, one local database file, and
server-rendered pages. No authentication, no build step for the front end, no external services.
Any added dependency or layer MUST be justified in the plan's Complexity Tracking table.

Rationale: this is a prototype for a two-person household; complexity costs more than it returns.

### V. Tested Care Logic

The rules that decide status (last/next watering, overdue, due today, bring-inside time, overdue
to bring inside, duplicate-watering warning, dashboard ordering) MUST live in plain functions that
take the current time as a parameter, and MUST have automated tests. Each user story MUST also
have at least one end-to-end test through the web layer.

Rationale: these rules are where the stakeholder's problems (missed and double watering,
forgotten outdoor plants) are actually solved, so they must be verifiable.

## Technology & Constraints

- Language: Python 3.11+, dependencies managed with `uv`.
- Persistence: a single SQLite file; schema created by the application on startup.
- Interface: a web app reachable from any browser on the household network, usable on a phone.
- Identity: no passwords. The acting household member is chosen by name when recording care.
- Times are stored in UTC and displayed in local time.

## Development Workflow

- Work follows the Spec Kit chain in order: constitution → specify → (clarify) → plan → tasks →
  implement. Skipping a step is not allowed.
- `docs/initial-spec.md` is the manually written baseline and MUST NOT be edited by tooling.
- Each Spec Kit step and each implementation phase is committed to git separately so the
  progression is reviewable.
- A phase is complete only when its tests pass.
- When a decision changes during implementation, the spec is updated first, then the code.

## Governance

This constitution overrides other practices for this project. Plans MUST include a Constitution
Check that evaluates each principle; violations MUST be recorded and justified in Complexity
Tracking or the plan MUST change. Amendments are made by editing this file, bumping the version
(MAJOR for removed or redefined principles, MINOR for added principles or sections, PATCH for
wording), and updating the Last Amended date.

**Version**: 1.0.0 | **Ratified**: 2026-11-17 | **Last Amended**: 2026-11-17
