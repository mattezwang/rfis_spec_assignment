# Contract: HTTP Routes and Screens

Server-rendered HTML. Every state-changing request is a `POST` from a form and ends in a
redirect (Post/Redirect/Get), except when it returns a validation error (HTTP 400, form shown
again with a message) or the duplicate-watering warning (HTTP 200, confirmation page).
Unknown plant, member, or event ids return 404.

If no members exist, every route except `/setup` and `/static/*` redirects to `/setup`.

## Members

| Method & path | Purpose | Spec |
|---------------|---------|------|
| `GET /setup` | First-use form: enter one or two member names | FR-001 |
| `POST /setup` | Create members; set acting member to the first; redirect `/` | FR-001 |
| `GET /members` | List members; add / rename / delete forms | FR-001 |
| `POST /members` | Add member (`name`) | FR-001 |
| `POST /members/<id>/rename` | Rename (`name`) | FR-001 |
| `POST /members/<id>/delete` | Delete; 400 with message if member has care events | FR-001 |
| `GET /choose-member` | "Who's recording?" page shown when an action has no member; buttons post to `/acting-member` (`next` preserved) | FR-001, R-5 |
| `POST /acting-member` | Set the acting-member cookie (`member_id`, `next`) | FR-001, R-5 |

## Plants

| Method & path | Purpose | Spec |
|---------------|---------|------|
| `GET /` | Dashboard (auto-refresh 60 s) | FR-023–FR-026, FR-017 |
| `GET /plants` | All plants with watering and sun status, last watered / last outside by whom | FR-009, FR-013, FR-018 |
| `GET /plants/new` | Add form | FR-003–FR-005 |
| `POST /plants` | Create (`name`, `location`, `water_interval_days`, `max_outside_hours`) → `/plants/<id>` | FR-003–FR-005 |
| `GET /plants/<id>` | Detail: status, actions with member + time fields, full history newest first | FR-009, FR-013, FR-018, FR-019 |
| `GET /plants/<id>/edit` | Edit form | FR-006 |
| `POST /plants/<id>/edit` | Update → `/plants/<id>` | FR-006 |
| `GET /plants/<id>/delete` | Confirm removal | FR-007 |
| `POST /plants/<id>/delete` | Remove plant and its history → `/plants` | FR-007 |

## Care events

Common form fields: `member_id` (optional; defaults to the acting-member cookie; if neither is
present, redirect to `/choose-member` and save nothing), `occurred_at` (optional
`datetime-local` in local time; default now; future rejected), `next` (where to redirect;
must be a local path).

| Method & path | Purpose | Spec |
|---------------|---------|------|
| `POST /plants/<id>/water` | Record watering. If not yet due and no `confirm=1`: 200 warning page naming last waterer and time, with "Water anyway" and "Cancel" | FR-008, FR-020 |
| `POST /plants/<id>/outside` | Record moved outside; 400 if already outside or time earlier than the latest sun event | FR-012, FR-016 |
| `POST /plants/<id>/inside` | Record brought inside; 400 if already inside or time earlier than moved-outside time | FR-015, FR-016 |
| `POST /events/<id>/delete` | Delete a mistaken event → `next` or the plant page | FR-021 |

## Screen contract (what each screen MUST show)

- **Header (all pages)**: app name, links Dashboard / Plants / Members, "Recording as: <name>"
  with a switcher.
- **Dashboard**: groups in order Overdue to bring inside → Overdue for water → Never watered →
  Due today → Outside. Each item: plant name, location, a text badge (e.g. "Overdue 2 days",
  "Bring in by 13:00"), a group color, and one action button. Empty state: "All plants are taken
  care of" + next upcoming watering.
- **Plant detail**: last watered (when, by whom), next due / state, outside state (since, by
  whom, bring in by), last moved outside (when, by whom), action forms with member and time,
  history table (action, member, time, delete button).
- **Warning page**: "<Plant> was already watered by <member> <relative time>. Next watering due
  <date>." Buttons: "Water anyway", "Cancel".
