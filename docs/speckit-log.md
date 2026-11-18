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
