# Feature Specification: Shared Household Plant Care Tracker

**Feature Branch**: `001-plant-care-tracker`

**Created**: 2026-11-17

**Status**: Draft

**Input**: User description: the manually written specification in `docs/initial-spec.md`
(Plant Care Tracker; goals G2 Track Watering, G3 Track Sunlight Exposure, G4 Coordinate Shared
Plant Care; requirements R1–R19), together with the stakeholder interview and goal model.

## Problem

Two roommates share responsibility for the plants in their apartment and track care on a
handwritten fridge chart. The chart fails in three ways: (1) someone waters a plant but forgets
to update it, so plants are missed for days or watered twice; (2) plants moved outside for sun are
forgotten and left out too long; (3) neither roommate can easily tell what the other has done or
what needs attention right now. Different plants need different watering frequencies and
different amounts of time outside.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep plants watered on their own schedules (Priority: P1)

A household member adds each plant with a name, a location in the apartment, and how often it
needs water (every N days). Whenever they water a plant they record it, choosing their name. For
every plant the app shows when it was last watered, by whom, and when it is next due. A plant
whose due date has passed is shown as overdue until someone records a watering. A plant that has
never been watered in the app is shown as needing water.

**Why this priority**: Watering is the stakeholder's primary pain point (missed and double
waterings) and the first thing they named for version one. Adding plants is the prerequisite.

**Independent Test**: Add two plants with different intervals, record a watering for one, and
confirm the list shows correct last-watered / next-due / overdue / needs-water states as time
passes.

**Acceptance Scenarios**:

1. **Given** no plants, **When** a user adds "Monstera" in "Living room" watered every 7 days,
   **Then** it appears in the plant list marked "Needs water (never watered)".
2. **Given** "Monstera" (every 7 days), **When** Alex records a watering on Nov 10,
   **Then** the plant shows "Last watered Nov 10 by Alex" and "Next due Nov 17".
3. **Given** "Monstera" last watered Nov 10 (every 7 days), **When** it is Nov 17,
   **Then** the plant is shown as "Due today".
4. **Given** "Monstera" last watered Nov 10 (every 7 days), **When** it is Nov 18 and nobody has
   recorded a watering, **Then** the plant is shown as "Overdue by 1 day", and it stays overdue
   until a watering is recorded.
5. **Given** an existing plant, **When** a user changes its watering interval from 7 to 3 days,
   **Then** the next due date is recalculated from the last watering.
6. **Given** Sam watered a plant this morning but forgot to record it, **When** Sam records the
   watering and sets the time to this morning, **Then** the plant shows this morning as the last
   watering.

---

### User Story 2 - See what needs attention at a glance (Priority: P2)

When a household member opens the app they land on a dashboard that lists only the plants that
need attention, grouped and ordered by urgency: plants overdue to come inside, plants overdue
for water, plants that have never been watered, plants due for water today, and plants currently
outside. Each item is visually distinct by urgency and has a one-step action (Water / Bring
inside) so care can be recorded right from the dashboard.

**Why this priority**: The stakeholder explicitly asked for "a dashboard showing what needs
attention" so they no longer need to check the fridge chart daily.

**Independent Test**: With plants in each state, open the dashboard and verify grouping,
ordering, visual distinction, and that recording an action from the dashboard removes or moves
the item.

**Acceptance Scenarios**:

1. **Given** one plant overdue for water, one due today, and one not due for 3 days,
   **When** a user opens the dashboard, **Then** the overdue plant appears above the due-today
   plant, and the not-yet-due plant is not listed as needing attention.
2. **Given** a plant overdue to come inside and a plant overdue for water, **When** the dashboard
   loads, **Then** the plant overdue to come inside appears first.
3. **Given** a plant listed as "Due today", **When** a user taps "Water" on the dashboard and
   selects their name, **Then** the watering is recorded and the plant leaves the attention list.
4. **Given** nothing needs attention, **When** the dashboard loads, **Then** it says all plants
   are taken care of and shows when the next watering is due.

---

### User Story 3 - Don't forget plants that are outside (Priority: P3)

Each plant has a maximum time it should spend outside (in hours), set by the household. When a
member moves a plant outside they record it with their name. The app shows that the plant is
outside, who moved it, and when it should be brought back in. Once that time passes the plant is
marked overdue to come inside until someone records that it was brought inside.

**Why this priority**: Sunlight was the stakeholder's second named problem; it depends on plants
existing (US1) and is surfaced through the dashboard (US2).

**Independent Test**: Set a plant's outside limit to 2 hours, record it moved outside, confirm
the bring-inside time, advance past it, confirm the overdue mark, record it brought inside, and
confirm the outside and overdue marks are gone.

**Acceptance Scenarios**:

1. **Given** "Basil" with a 3-hour outside limit, **When** Sam records moving it outside at
   10:00, **Then** it shows "Outside since 10:00 (Sam) - bring in by 13:00".
2. **Given** "Basil" outside since 10:00 with a 3-hour limit, **When** it is 13:01 and nobody has
   brought it in, **Then** it is marked "Overdue to bring inside".
3. **Given** "Basil" overdue to bring inside, **When** Alex records bringing it inside,
   **Then** the outside and overdue marks are removed and the event is recorded with Alex's name.
4. **Given** a plant that is already outside, **When** a user views it, **Then** the only sun
   action offered is "Bring inside" (it cannot be moved outside twice).

---

### User Story 4 - Coordinate care between roommates (Priority: P4)

Both roommates see the same plants, schedules, and history from their own devices, and a change
by one is visible to the other. Each plant shows who last watered it and who last moved it
outside, and has a full care history. If someone tries to water a plant that has already been
watered and is not yet due, the app warns them (showing who watered it and when) and lets them
proceed anyway or cancel.

**Why this priority**: Coordination is what the fridge chart lacked; it builds on the events
recorded in US1 and US3.

**Independent Test**: Record actions from two different browsers as two different members and
confirm both see identical state and history; attempt a second watering and confirm the warning
and the bypass.

**Acceptance Scenarios**:

1. **Given** Alex records a watering on their phone, **When** Sam opens or refreshes the app on
   their laptop, **Then** Sam sees the watering with Alex's name and time.
2. **Given** a plant watered yesterday by Alex with a 7-day interval, **When** Sam tries to water
   it, **Then** the app warns "Already watered by Alex yesterday - next due in 6 days" and offers
   "Water anyway" and "Cancel".
3. **Given** the duplicate-watering warning, **When** Sam chooses "Water anyway", **Then** the
   watering is recorded normally; **When** Sam chooses "Cancel", **Then** nothing is recorded.
4. **Given** a plant with several waterings and sun events, **When** a user opens its history,
   **Then** all events are listed newest first with the action, the person, and the time.
5. **Given** a care event was recorded by mistake, **When** a user deletes it from the history,
   **Then** the plant's status is recalculated as if that event had never been recorded.

---

### Edge Cases

- **Never watered**: a newly added plant has no last watering and is shown as needing water
  (not as overdue by an arbitrary amount).
- **Simultaneous watering**: if both roommates press "Water" on the same plant at nearly the
  same time, the second submission still triggers the duplicate-watering warning, because the
  check uses the latest saved state, not what was on that person's screen.
- **Back-dated entries**: a care time may be set in the past but never in the future; a
  bring-inside time cannot be earlier than the matching move-outside time.
- **Schedule edits while outside**: changing a plant's outside limit while it is outside
  recalculates its bring-inside time from the original move-outside time.
- **Removing a plant**: a removed plant disappears from the dashboard and plant list; removal
  requires confirmation.
- **Invalid input**: empty names, a watering interval below 1 day, or an outside limit of zero or
  less are rejected with a clear message and nothing is saved.
- **Duplicate plant names**: allowed (e.g. two "Pothos" in different rooms); the location tells
  them apart.
- **Day boundaries**: "due today" and "overdue" are based on the household's local calendar
  date, so a plant on a 1-day schedule watered at 21:00 is due the next day, not 24 hours later.

## Requirements *(mandatory)*

### Functional Requirements

**Household members**

- **FR-001**: The system MUST let the household maintain a list of member names (initially the
  two roommates) and MUST require choosing a member whenever a care event is recorded.
- **FR-002**: The system MUST NOT require passwords or accounts.

**Plants (G1)**

- **FR-003**: Users MUST be able to add a plant with a name and a location. *(R1)*
- **FR-004**: Users MUST be able to set each plant's watering interval as a whole number of days
  (minimum 1). *(R2)*
- **FR-005**: Users MUST be able to set each plant's maximum time outside in hours (greater than
  zero; fractions such as 1.5 allowed). *(R3)*
- **FR-006**: Users MUST be able to edit a plant's name, location, watering interval, and outside
  limit; status MUST be recalculated immediately. *(R4)*
- **FR-007**: Users MUST be able to remove a plant after confirming.

**Watering (G2)**

- **FR-008**: Users MUST be able to record that a plant was watered, by whom, and when (default:
  now; may be set to an earlier time). *(R5)*
- **FR-009**: For each plant the system MUST show the last watering (time and person) and the
  next due date, calculated as the date of the last watering plus the interval. *(R6, R14)*
- **FR-010**: The system MUST show a plant as "due today" on its due date and as "overdue"
  (with the number of days) after its due date, and MUST keep it overdue until a watering is
  recorded. *(R7)*
- **FR-011**: A plant with no recorded watering MUST be shown as needing water. *(R8)*

**Sunlight (G3)**

- **FR-012**: Users MUST be able to record that a plant was moved outside, by whom, and when.
  *(R9)*
- **FR-013**: For each plant that is outside the system MUST show when it went out, who moved it,
  and the bring-inside time (move-outside time plus the plant's outside limit). *(R10, R14)*
- **FR-014**: Once the bring-inside time passes, the system MUST mark the plant "overdue to bring
  inside" until someone records it was brought inside. *(R11)*
- **FR-015**: Users MUST be able to record that a plant was brought inside, by whom, and when;
  this MUST clear the outside and overdue marks. *(R12)*
- **FR-016**: The system MUST NOT allow moving a plant outside that is already outside, or
  bringing inside a plant that is already inside.

**Shared care (G4)**

- **FR-017**: All members MUST see the same plants, schedules, and history from any device on the
  household network; a change by one member MUST appear for the other on their next page load,
  and the dashboard MUST refresh itself at least once a minute. *(R13)*
- **FR-018**: Each plant MUST show who last watered it and when, and who last moved it outside
  and when. *(R14)*
- **FR-019**: Users MUST be able to view a plant's full care history (waterings, moved outside,
  brought inside) newest first, each with the person and time. *(R15)*
- **FR-020**: When a user tries to record a watering for a plant whose next watering is not yet
  due, the system MUST warn them, showing who last watered it and when, and MUST let them either
  record it anyway or cancel. The check MUST use the latest saved data. *(R16; see Clarifications)*
- **FR-021**: Users MUST be able to delete a care event recorded by mistake; plant status MUST be
  recalculated.
- **FR-022**: The system MUST NOT change any care state automatically; only recorded events change
  state.

**Dashboard**

- **FR-023**: The default screen MUST be a dashboard listing plants that need attention: overdue to
  bring inside, overdue for water, never watered, due for water today, and currently outside.
  *(R17)*
- **FR-024**: Dashboard items MUST be ordered by urgency in the order listed in FR-023 (within a
  group, the most overdue first) and each group MUST be visually distinct (color plus a text
  label, so it does not rely on color alone). *(R18)*
- **FR-025**: Users MUST be able to record a watering, a move outside, or a bring-inside directly
  from the dashboard. *(R19)*
- **FR-026**: When no plant needs attention, the dashboard MUST say so and show the next upcoming
  watering.

### Key Entities

- **Household member**: a person who cares for plants. Attribute: display name.
- **Plant**: a plant in the household. Attributes: name, location, watering interval (days),
  maximum time outside (hours), date added.
- **Care event**: something a member did to a plant. Attributes: plant, type (watered / moved
  outside / brought inside), member, time it happened. A plant's current state (last watered,
  next due, outside or inside, bring-inside time) is derived from its care events and schedule.

### Traceability

| Goal | Initial spec | This spec |
|------|--------------|-----------|
| G1.1 Record plants | R1 | FR-003, FR-007 |
| G1.2 Maintain individual schedules | R2, R3, R4 | FR-004, FR-005, FR-006 |
| G2.1 Record watering events | R5 | FR-001, FR-008 |
| G2.2 Identify upcoming and overdue watering | R6, R7, R8 | FR-009, FR-010, FR-011 |
| G3.1 Track when plants are moved outside | R9, R12 | FR-012, FR-015, FR-016 |
| G3.2 Identify when plants should be brought inside | R10, R11 | FR-013, FR-014 |
| G4.1 Maintain shared care records | R13, R14, R15 | FR-017, FR-018, FR-019, FR-021 |
| G4.2 Avoid duplicate or missed care | R16, R17–R19 | FR-020, FR-022, FR-023–FR-026 |

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A member can record a watering or a sun movement from the dashboard in at most two
  taps after opening the app.
- **SC-002**: A new member can add a plant with its watering and outside schedule in under one
  minute without instructions.
- **SC-003**: With up to 20 plants, a member can tell which plants need attention, and why,
  within 5 seconds of opening the app.
- **SC-004**: 100% of plants that are overdue for water or overdue to come inside appear on the
  dashboard, and none leaves that state without a recorded event.
- **SC-005**: A care event recorded by one member is visible to the other member within one
  minute without them doing anything, or immediately on refresh.
- **SC-006**: Every attempt to water a plant that is not yet due produces the duplicate warning
  naming who last watered it.
- **SC-007**: The app is usable on a phone screen without horizontal scrolling.

## Assumptions

- The household has two members to start; adding more names is allowed but there are no roles
  or permissions.
- Both members are on the same home network; the app runs on one machine in the home and is
  opened in a browser.
- No login is needed (from the initial spec); anyone who can reach the app can record care.
- Members enter all schedules and events themselves; no automatic calculation of water or sun
  needs (from the initial spec and interview).
- Times are shown in the household's local time zone.
- "Recently watered" for the duplicate warning means the plant is not yet due again
  (see Clarifications).

## Out of Scope

- Notifications or reminders (email, push, text) - stakeholder said "not immediately".
- Calculating how much water or sunlight a plant needs.
- Other care such as fertilizing, repotting, or pruning.
- Plant photos.
- Multiple households, user accounts, or passwords.
