# Traceability

How each part of the prototype traces back through the requirements to the stakeholder
interview. R# are the requirements in the manual spec (`docs/initial-spec.md`), FR-### are the
functional requirements in `specs/001-plant-care-tracker/spec.md`, and T### are the tasks in
`tasks.md`.

## Interview → goal → requirements

| Interview statement | Goal | Initial spec | Refined spec |
|---------------------|------|--------------|--------------|
| "I'd like to see all our plants in one place" | G1.1 Record plants | R1 | FR-003, FR-007 |
| "set a watering schedule for each plant"; "specify how long we want to leave it outside" | G1.2 Maintain individual schedules | R2, R3, R4 | FR-004, FR-005, FR-006 |
| "either of us should be able to update it whenever we water something" | G2.1 Record watering events | R5 | FR-001, FR-008 |
| "when each was last watered, and when it needs to be watered next"; "show that it's overdue until someone waters it" | G2.2 Identify upcoming and overdue watering | R6, R7, R8 | FR-009, FR-010, FR-011 |
| "track when we moved a plant outside" | G3.1 Track when plants are moved outside | R9, R12 | FR-012, FR-015, FR-016 |
| "forget to bring them back inside… when we should bring it back" | G3.2 Identify when plants should be brought inside | R10, R11 | FR-013, FR-014 |
| "We should both be able to see the same information"; "know who last took care of a plant" | G4.1 Maintain shared care records | R13, R14, R15 | FR-017, FR-018, FR-019, FR-021 |
| "We've also accidentally watered the same plant twice"; "I wouldn't want it to automatically mark anything as done" | G4.2 Avoid duplicate or missed care | R16 | FR-020, FR-022 |
| "A dashboard showing what needs attention" | G2.2, G3.2, G4.2 | R17, R18, R19 | FR-023, FR-024, FR-025, FR-026 |
| "Notifications would be nice too, but I don't think we need those immediately" | (none) | Out of scope | Out of scope |

## Requirement → task → code → test

| FR | What | Tasks | Code | Tests |
|----|------|-------|------|-------|
| FR-001, FR-002 | Household members, no passwords, acting member | T007, T009 | `db.py` members; `web.py` `setup`, `members`, `set_acting_member`, `choose_member`, `resolve_member` | `test_members.py`; `test_us1_watering.py::test_no_member_redirects_to_choose_and_saves_nothing` |
| FR-003–FR-007 | Add, edit, remove plants with interval and outside limit | T014, T015, T016 | `db.py` `clean_plant`, `create_plant`, `update_plant`, `delete_plant`; `web.py` plant routes; `plant_form.html`, `confirm_delete.html` | `test_us1_watering.py` (invalid input, edit, delete, fractional hours) |
| FR-008 | Record watering, who and when, back-dating | T014, T015 | `web.py` `water`, `parse_occurred_at` | `test_us1_watering.py::test_backdated_watering`, `test_future_watering_rejected` |
| FR-009–FR-011 | Last watered, next due, due today, overdue, never | T013 | `care.py` `watering_status` | `test_care.py::TestWateringStatus`; `test_us1_watering.py::test_due_today_then_overdue_until_watered` |
| FR-012, FR-015 | Record moved outside / brought inside | T025 | `web.py` `move_outside`, `bring_inside`, `record_sun_event` | `test_us3_sunlight.py` |
| FR-013, FR-014 | Bring-in-by time, overdue to bring inside | T024 | `care.py` `sun_status` | `test_care.py::TestSunStatus`; `test_us3_sunlight.py::test_overdue_then_bring_inside_clears` |
| FR-016 | No double move-outside; time order | T024, T025 | `care.py` `sun_event_error` | `test_care.py::TestSunEventRules`; `test_us3_sunlight.py` |
| FR-017 | Shared state, 60 s refresh | T020, T021 | single SQLite file (`db.py`); `dashboard.html` meta refresh | `test_us4_coordination.py::test_both_roommates_see_the_same_state`; `test_us2_dashboard.py::test_dashboard_auto_refreshes` |
| FR-018 | Who last watered / last moved outside | T016, T026 | `plant_detail.html`, `plants.html` | `test_us1_watering.py::test_record_watering_shows_who_and_next_due`; `test_us3_sunlight.py` |
| FR-019 | Care history newest first | T031 | `db.py` `events_by_plant`; `plant_detail.html` history | `test_us4_coordination.py::test_history_newest_first_with_who_and_action` |
| FR-020 | Duplicate-watering warning with bypass | T029, T030 | `care.py` `needs_duplicate_warning`; `web.py` `water` (inside `db.write_lock`); `confirm_water.html` | `test_care.py::TestDuplicateWarning`; `test_us4_coordination.py` (warning, anyway, cancel, stale page) |
| FR-021 | Delete mistaken event, recalculate | T031 | `db.py` `delete_event`; `web.py` `delete_event` | `test_us4_coordination.py::test_delete_mistaken_event_recalculates` |
| FR-022 | Nothing changes automatically | design (research R-3) | status derived in `care.py`; no scheduler | overdue persistence tests in `test_care.py` |
| FR-023, FR-024 | Dashboard groups and urgency order, color plus text | T019, T021, T024 | `care.py` `dashboard_items`, `group_items`; `dashboard.html`; `style.css` | `test_care.py::TestDashboard`, `TestSunDashboard`; `test_us2_dashboard.py`; `test_us3_sunlight.py::test_dashboard_sun_groups_and_bring_inside_button` |
| FR-025 | Actions from the dashboard | T021, T026 | `dashboard.html` Water / Bring inside / Move outside forms | `test_us2_dashboard.py::test_water_from_dashboard_is_one_tap`; `test_us3_sunlight.py::test_move_outside_from_dashboard` |
| FR-026 | Empty state with next watering | T019, T021 | `care.py` `next_upcoming`; `dashboard.html` | `test_us2_dashboard.py::test_empty_states` |

## Where the refined spec differs from the manual spec

- **R16** said "warn if the plant was recently brought outside". The interview problem is
  watering the same plant twice, so `/speckit-clarify` recorded the intent as "warn if it was
  already watered and isn't due yet" (FR-020).
- The refined spec added items the manual spec didn't cover: first-use member setup, removing
  plants, deleting mistaken entries, back-dating, calendar-day due logic, the case where both
  roommates tap Water at once, and measurable success criteria.
- G1 (plant information) was not listed as a goal in the manual spec, but R1–R4 cover it.
  The refined spec traces them to G1.1 and G1.2 explicitly.
