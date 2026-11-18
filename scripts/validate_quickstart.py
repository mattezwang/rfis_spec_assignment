"""Browser walkthrough of quickstart.md scenarios against a running server.

Usage (server must be running on an empty database):
    uv run --no-project --with playwright python scripts/validate_quickstart.py http://127.0.0.1:8000 docs/screenshots
"""

import glob
import os
import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[1]
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)
results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + (f" - {detail}" if detail and not cond else ""))


def no_hscroll(page):
    return page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")


exe = None
cands = sorted(glob.glob(os.path.expanduser("~/Library/Caches/ms-playwright/chromium-*/chrome-mac*/*.app/Contents/MacOS/*")))
if cands:
    exe = cands[-1]

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
    alex = browser.new_context(viewport={"width": 1100, "height": 900})
    a = alex.new_page()

    # 1. First use
    a.goto(BASE + "/")
    check("first use asks for names", "/setup" in a.url and a.is_visible("text=Welcome to Plant Care"))
    a.screenshot(path=f"{OUT}/01-setup.png", full_page=True)
    a.fill("#name1", "Alex")
    a.fill("#name2", "Sam")
    a.click("text=Get started")
    check("setup lands on dashboard with no plants", a.is_visible("text=No plants yet"))

    # 2. US1 add plant -> never watered on dashboard
    a.click("a:has-text('Add your first plant')")
    a.fill("#name", "Monstera")
    a.fill("#location", "Living room")
    a.fill("#water_interval_days", "7")
    a.fill("#max_outside_hours", "2")
    a.click("button:has-text('Add plant')")
    check("plant page shows never watered", a.is_visible("text=Never watered"))
    for name, loc, days, hrs in [("Basil", "Kitchen", "2", "0.05"), ("Fern", "Bathroom", "3", "4"), ("Cactus", "Desk", "14", "6")]:
        a.goto(BASE + "/plants/new")
        a.fill("#name", name)
        a.fill("#location", loc)
        a.fill("#water_interval_days", days)
        a.fill("#max_outside_hours", hrs)
        a.click("button:has-text('Add plant')")

    a.goto(BASE + "/")
    check("dashboard lists never-watered plants", a.is_visible("h2:has-text('Never watered')"))

    # Water Monstera from the dashboard (one tap)
    a.locator("li.item", has_text="Monstera").locator("button:has-text('Water')").first.click()
    check("one-tap watering from dashboard", a.is_visible("text=Alex watered Monstera"))
    check("watered plant leaves attention list",
          a.locator("section.group li.item", has_text="Monstera").count() == 0)

    # 3. Back-dated watering -> overdue
    fern = a.locator("li.item", has_text="Fern").locator("a").first
    fern.click()
    fern_url = a.url
    a.evaluate("""() => {
        const d = new Date(Date.now() - 5*24*3600*1000);
        const pad = n => String(n).padStart(2, '0');
        document.querySelector('#occurred_at').value =
          `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
    }""")
    a.click("button:has-text('Record watering')")
    check("back-dated watering makes Fern overdue", a.is_visible("text=Overdue by 2 days"))
    a.goto(BASE + "/plants")
    a.locator("li.item", has_text="Cactus").locator("a").first.click()
    a.click("button:has-text('Record watering')")

    # 5. US3 sunlight: Basil outside for 3 minutes; move from dashboard
    a.goto(BASE + "/")
    a.click("summary:has-text('Move a plant outside')")
    a.locator("details li.item", has_text="Basil").locator("button:has-text('Move outside')").click()
    check("move outside from dashboard", a.is_visible("text=Alex moved Basil outside"))
    check("Basil in Outside now group", a.locator("section.group-outside li.item", has_text="Basil").count() == 1)
    a.screenshot(path=f"{OUT}/02-dashboard-desktop.png", full_page=True)

    # 6. US4: Sam on a phone-sized second browser
    sam_ctx = browser.new_context(viewport={"width": 360, "height": 780}, is_mobile=True, has_touch=True)
    s = sam_ctx.new_page()
    s.goto(BASE + "/")
    check("Sam sees Alex's outside move", s.locator("section.group-outside li.item", has_text="Basil").count() == 1)
    check("Sam sees Fern overdue", s.locator("section.group-overdue_water li.item", has_text="Fern").count() == 1)
    check("no horizontal scroll at 360px (dashboard)", no_hscroll(s))
    s.select_option("#acting-select", label="Sam")
    s.click("button:has-text('Switch')")
    check("Sam switches acting member", s.is_visible("text=Recording as Sam on this device"))
    s.screenshot(path=f"{OUT}/03-dashboard-phone.png", full_page=True)

    # 7. Duplicate warning: Sam tries Monstera
    s.goto(BASE + "/plants")
    s.locator("li.item", has_text="Monstera").locator("a").first.click()
    monstera_url = s.url
    check("no horizontal scroll at 360px (plant page)", no_hscroll(s))
    s.click("button:has-text('Record watering')")
    check("duplicate warning names Alex", s.is_visible("text=Already watered") and s.is_visible("strong:has-text('Alex')"))
    s.screenshot(path=f"{OUT}/04-duplicate-warning-phone.png", full_page=True)
    s.click("text=Cancel")
    check("cancel records nothing", s.locator("table tbody tr").count() == 1)
    s.click("button:has-text('Record watering')")
    s.click("button:has-text('Water anyway')")
    check("water anyway records as Sam", s.locator("table tbody tr").count() == 2 and s.locator("table tbody tr").first.inner_text().find("Sam") >= 0)

    # 8. History + delete mistaken event (accept confirm dialog)
    s.on("dialog", lambda d: d.accept())
    s.locator("table tbody tr").first.locator("button").click()
    s.wait_for_selector("text=Deleted the")
    check("deleting entry returns to previous status", s.locator("table tbody tr").count() == 1
          and "Alex" in s.locator("table tbody tr").first.inner_text()
          and "by Alex" in s.locator("section[aria-labelledby=water-h]").inner_text())
    s.screenshot(path=f"{OUT}/05-plant-detail-phone.png", full_page=True)

    # 5b. Wait for Basil (0.05 h = 3 min) to become overdue to bring inside
    a.goto(BASE + "/")
    a.wait_for_timeout(185_000)
    a.reload()
    check("Basil overdue to bring inside after limit", a.locator("section.group-overdue_inside li.item", has_text="Basil").count() == 1)
    first_group = a.locator("section.group").first.get_attribute("class")
    check("overdue-inside group is first", "group-overdue_inside" in first_group, first_group)
    a.screenshot(path=f"{OUT}/06-overdue-inside-desktop.png", full_page=True)
    a.locator("section.group-overdue_inside li.item", has_text="Basil").locator("button").click()
    check("bring inside clears", a.locator("section.group li.item", has_text="Basil").count() == 0
          or a.locator("section.group-overdue_inside").count() == 0)

    # Sam's dashboard auto-refresh picks up change (meta refresh 60s)
    s.goto(BASE + "/")
    check("meta refresh present", s.locator("meta[http-equiv='refresh']").count() == 1)

    browser.close()

failed = [r for r in results if not r[1]]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
