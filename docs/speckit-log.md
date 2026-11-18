# Spec Kit Workflow Log

The input given to each Spec Kit command, in order, with the artifacts it produced. Each step
was committed separately; see `git log` for the progression.

## 0. Manual specification (no AI)

- Artifact: `docs/initial-spec.md`
- Goals selected: G2 (watering), G3 (sunlight), G4 (shared care); G1 (plant information)
  is covered as supporting requirements R1–R4.

## 1. `specify init --here --integration claude`

- Spec Kit version: specify-cli 1.4.2
- Artifacts: `.specify/` (templates, scripts, workflow), `.claude/skills/speckit-*`

## 2. `/speckit-constitution`

Input:

> Shared Household Plant Care Tracker prototype for two roommates. Keep the constitution short.
> Principles: (1) scope comes from the stakeholder interview and goal model only; (2) people
> record care, the app never marks anything done automatically, and every event records who
> and when; (3) one shared source of truth for both roommates; (4) simplest possible stack,
> no auth; (5) status logic is plain, tested functions. Python + uv, SQLite, server-rendered web
> app usable from a phone.

- Artifact: `.specify/memory/constitution.md` (v1.0.0)

## 3. `/speckit-specify`

Input:

> Build the Shared Household Plant Care Tracker described in `docs/initial-spec.md` (goals G2,
> G3, G4 with supporting G1 requirements R1–R19), using the stakeholder interview and goal model
> as context. Focus on what and why, not how.

- Artifacts: `specs/001-plant-care-tracker/spec.md`, `specs/001-plant-care-tracker/checklists/requirements.md`
- Changes from the manual spec: user stories with Given/When/Then scenarios, edge cases
  (simultaneous watering, back-dating, day boundaries), household members as an entity, removing
  plants and deleting mistaken events, measurable success criteria, and a Goal → R# → FR
  traceability table.

## 4. `/speckit-clarify`

Input: none (ran on the generated spec).

Four questions, answered with the recommended option (see `## Clarifications` in spec.md):

1. Duplicate-watering warning (R16) → warn when the plant is not yet due again; R16's
   "recently brought outside" wording treated as a slip.
2. Due/overdue → calendar days in local time.
3. Household members → editable list, entered on first use.
4. Outside-but-not-overdue plants → shown on the dashboard as the least urgent group.

- Spec Quality Checklist: 16/16 → 16/16 passing.

## 5. `/speckit-plan`

Input:

> Python 3.11+ with uv. Flask with server-rendered Jinja templates, standard-library sqlite3 in a
> single file, no ORM, no JS framework, no auth. Keep status rules in pure functions that take
> the current time. pytest for tests. Must work from both roommates' phones on the home network.

- Artifacts: `plan.md`, `research.md`, `data-model.md`, `contracts/routes.md`, `quickstart.md`
- Key design decisions: status derived from events (never stored), acting-member cookie for
  one-tap actions, server-side duplicate-watering check at submit time, 60 s dashboard refresh.
- Constitution Check: all five principles pass, before and after design.

## 6. `/speckit-tasks`

Input: none (generated from plan.md, spec.md, data-model.md, contracts/, research.md).

- Artifact: `specs/001-plant-care-tracker/tasks.md`: 35 tasks in 7 phases (Setup, Foundational,
  US1–US4, Polish). Test tasks included because Constitution Principle V requires them.
- Coverage check: every FR-001–FR-026 maps to at least one task.

## 7. `/speckit-implement`

Input: none (executed tasks.md phase by phase, tests first in each user story).

| Phase | Tasks | Commit |
|-------|-------|--------|
| 1 Setup | T001–T003 | `impl: phase 1 setup` |
| 2 Foundational | T004–T010 | `impl: phase 2 foundational` |
| 3 US1 Watering (MVP) | T011–T016 | `impl: phase 3 user story 1` |
| 4 US2 Dashboard | T017–T021 | `impl: phase 4 user story 2` |
| 5 US3 Sunlight | T022–T026 | `impl: phase 5 user story 3` |
| 6 US4 Coordination | T027–T031 | `impl: phase 6 user story 4` |
| 7 Polish | T032–T035 | `impl: phase 7 polish` |

Decisions made during implementation, each written back to the design docs:

- Added `GET /choose-member` (contracts/routes.md) for actions taken before a device has picked
  a member.
- Added "Move a plant outside" to the dashboard so FR-025 (record plant movement from the
  dashboard) holds even for plants that need no attention.
- The check and the insert for care events run under a SQLite write lock, so the duplicate
  warning and the FR-016 sequence rules hold when both roommates submit at once.

Result: 35/35 tasks complete, 82 automated tests passing, 22/22 browser checks passing (see
`docs/validation.md`).
