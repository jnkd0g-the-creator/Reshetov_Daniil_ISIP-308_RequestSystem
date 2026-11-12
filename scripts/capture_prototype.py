from pathlib import Path

from browser_support import configure_browser
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
configure_browser()
out = ROOT / "docs/prototype/screens"
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    for screen in ["login", "list", "new", "detail", "edit", "error", "empty"]:
        page.goto((ROOT / "docs/prototype/index.html").as_uri() + "#" + screen)
        page.screenshot(path=str(out / f"{screen}.png"), full_page=True)
    page.get_by_role("link", name="Все заявки").click()
    page.set_viewport_size({"width": 390, "height": 844})
    page.screenshot(path=str(out / "mobile.png"), full_page=True)
    browser.close()
print("Prototype: 7 desktop screens + mobile captured from local HTML")
