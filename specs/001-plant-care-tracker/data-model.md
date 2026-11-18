# Data Model: Shared Household Plant Care Tracker

## Stored entities

### member

| Field | Type | Rules |
|-------|------|-------|
| id | integer PK | |
| name | text | required, trimmed, 1–40 chars, unique (case-insensitive) |
| created_at | text (UTC ISO) | set on insert |

Delete allowed only when no `care_event` references the member (FR-001).

### plant

| Field | Type | Rules |
|-------|------|-------|
| id | integer PK | |
| name | text | required, trimmed, 1–60 chars; duplicates allowed |
| location | text | required, trimmed, 1–60 chars |
| water_interval_days | integer | ≥ 1 (FR-004) |
| max_outside_hours | real | > 0, ≤ 72; fractions allowed (FR-005) |
| created_at | text (UTC ISO) | set on insert |

Deleting a plant deletes its care events (`ON DELETE CASCADE`), after a confirmation page
(FR-007).

### care_event

| Field | Type | Rules |
|-------|------|-------|
| id | integer PK | |
| plant_id | integer FK → plant.id | `ON DELETE CASCADE` |
| member_id | integer FK → member.id | required; `ON DELETE RESTRICT` |
| kind | text | one of `watered`, `moved_outside`, `brought_inside` |
| occurred_at | text (UTC ISO) | when it happened; default now; not in the future (1-minute grace) |
| recorded_at | text (UTC ISO) | when it was entered |

Index: `(plant_id, kind, occurred_at)`.

Recording rules (validated in `web.py` using `care.py` helpers, inside one transaction):

- `moved_outside`: rejected if the plant is currently outside, or if `occurred_at` is earlier
  than the plant's latest sun event (FR-016).
- `brought_inside`: rejected if the plant is currently inside, or if `occurred_at` is earlier
  than the matching `moved_outside` (spec edge case).
- `watered`: allowed at any past time. If the plant is not yet due and `confirm` is absent, it is
  not saved and the duplicate warning is shown (FR-020).

## Derived state (computed in `care.py`, never stored)

### WateringStatus (per plant, given `today` in local time)

- `last_watered`: latest `watered` event (time, member) or none.
- `next_due`: `local_date(last_watered.occurred_at) + water_interval_days`, or none.
- `state`:
  - `never`: no watering recorded (FR-011)
  - `overdue`: `today > next_due`; `days_overdue = today - next_due` (FR-010)
  - `due_today`: `today == next_due` (FR-010)
  - `ok`: `today < next_due`; `days_until_due = next_due - today`
- Duplicate warning applies when `state == ok` (FR-020).

### SunStatus (per plant, given `now`)

- `latest_sun_event`: latest of `moved_outside` / `brought_inside` by `occurred_at`.
- `last_moved_outside`: latest `moved_outside` event (time, member), shown even when inside
  (FR-018).
- `state`:
  - `inside`: no sun events, or latest is `brought_inside`
  - `outside`: latest is `moved_outside` and `now <= bring_in_by`
  - `overdue_inside`: latest is `moved_outside` and `now > bring_in_by` (FR-014)
- `bring_in_by` (when outside): `latest moved_outside.occurred_at + max_outside_hours`; uses the
  current limit, so editing the limit recalculates it (spec edge case).

### State transitions (sun)

```text
inside --record moved_outside--> outside --(time passes bring_in_by)--> overdue_inside
outside --record brought_inside--> inside
overdue_inside --record brought_inside--> inside
(deleting the latest sun event reverts to the state implied by the remaining events)
```

### DashboardItem

`(group, plant, detail, action)`, where `group` is one of, in priority order:

1. `overdue_inside`, sorted by `bring_in_by` ascending; action: Bring inside
2. `overdue_water`, sorted by `days_overdue` descending; action: Water
3. `never_watered`, sorted by name; action: Water
4. `due_today`, sorted by name; action: Water
5. `outside`, sorted by `bring_in_by` ascending; action: Bring inside

Plants with `ok` watering and `inside` sun state produce no items. When there are no items the
dashboard shows the soonest upcoming `next_due` (FR-026).
