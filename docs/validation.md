# Validation Results (T034, T035)

Run on 2026-11-17 against commit `653ffc8` plus Phase 7 polish.

## Automated tests

`uv run pytest`: **82 passed**.

| Suite | Tests | Covers |
|-------|-------|--------|
| `tests/unit/test_care.py` | 37 | Watering, sunlight, sequence rules, duplicate warning, dashboard ordering |
| `tests/unit/test_timeutil.py` | 7 | Local dates, parsing, formatting |
| `tests/integration/test_members.py` | 8 | First use, members, acting member (FR-001, FR-002) |
| `tests/integration/test_us1_watering.py` | 13 | US1 scenarios 1–6 and edge cases |
| `tests/integration/test_us2_dashboard.py` | 5 | US2 scenarios 1, 3, 4 |
| `tests/integration/test_us3_sunlight.py` | 9 | US3 scenarios 1–4, US2 scenario 2, FR-025 |
| `tests/integration/test_us4_coordination.py` | 8 | US4 scenarios 1–5, simultaneous watering |

## Browser walkthrough of quickstart.md

`scripts/validate_quickstart.py` drives headless Chromium against the running app with an empty
database: one desktop browser as Alex (1100 px) and one phone-sized browser as Sam (360 px,
touch). Result: **22/22 checks passed**.

| # | Quickstart scenario | Check | Result |
|---|---------------------|-------|--------|
| 1 | First use | Asks for names; lands on empty dashboard | ✅ |
| 2 | US1 watering | New plant shows "Never watered"; one-tap Water from dashboard; plant leaves the list | ✅ |
| 3 | US1 back-dating | Watering set 5 days ago on a 3-day plant → "Overdue by 2 days" | ✅ |
| 4 | US2 order | Overdue to bring inside → Overdue for water → Never watered; distinct color and text badge | ✅ |
| 5 | US3 sunlight | Move outside from dashboard → "Outside now"; after the 3-minute limit → "Overdue to bring inside" (first group); Bring inside clears it | ✅ |
| 6 | US4 sharing | Sam's separate browser sees Alex's changes; Sam switches "Recording as" | ✅ |
| 7 | US4 duplicate warning | Warning names Alex and time; Cancel records nothing; Water anyway records as Sam | ✅ |
| 8 | US4 history | Deleting the mistaken entry restores the previous status | ✅ |
| SC-007 | Phone layout | No horizontal scroll at 360 px on dashboard and plant page | ✅ |
| FR-017 | Auto refresh | Dashboard has a 60 s refresh | ✅ |

### Issues found and fixed during validation

- On phones the "Recording as" dropdown stretched full width and pushed content down. It now
  sizes to its content.
- Card headings had extra top spacing. Removed.
- Two checks failed because of bugs in the script, not the app: one selector matched the
  welcome message, and one matched a hidden dropdown option. The selectors were fixed and the
  full run repeated on a fresh database.

### Screenshots

| Screen | File |
|--------|------|
| First-use setup | [01-setup.png](screenshots/01-setup.png) |
| Dashboard (desktop) | [02-dashboard-desktop.png](screenshots/02-dashboard-desktop.png) |
| Dashboard (phone, Sam) | [03-dashboard-phone.png](screenshots/03-dashboard-phone.png) |
| Duplicate-watering warning (phone) | [04-duplicate-warning-phone.png](screenshots/04-duplicate-warning-phone.png) |
| Plant detail with history (phone) | [05-plant-detail-phone.png](screenshots/05-plant-detail-phone.png) |
| Overdue to bring inside ranked first (desktop) | [06-overdue-inside-desktop.png](screenshots/06-overdue-inside-desktop.png) |

## Success criteria check

| SC | Result |
|----|--------|
| SC-001 Record from dashboard in ≤ 2 taps | 1 tap when "Recording as" is set; 2 the first time on a device (pick name, then tap) |
| SC-002 Add a plant in < 1 minute | 4 fields on one form |
| SC-003 See what needs attention in 5 s | Dashboard is the home page, grouped and ordered by urgency |
| SC-004 All overdue plants listed; none cleared without an event | Unit and integration tests; status is derived only from events |
| SC-005 Roommate's change visible within 1 minute | 60 s auto-refresh; immediately on reload |
| SC-006 Duplicate warning always names the last waterer | `test_us4_coordination.py` |
| SC-007 Phone usable without horizontal scroll | Verified at 360 px |
