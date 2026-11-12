import html
from pathlib import Path

from browser_support import configure_browser
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
configure_browser()
with sync_playwright() as p:
    browser=p.chromium.launch()
    page=browser.new_page(viewport={"width":1440,"height":460})
    page.set_content('<meta charset="utf-8"><style>body{margin:30px;background:#f6f5f0;color:#213e30}h1{font:25px Arial}pre{font:16px/1.45 monospace;white-space:pre-wrap;background:white;padding:24px;border:1px solid #dce4d7;border-radius:10px}</style><h1>Просмотр собственного документа · docs/TZ.md</h1><pre>'+html.escape((ROOT/"docs/TZ.md").read_text())+'</pre>')
    page.screenshot(path=str(ROOT/"docs/evidence/TZ_preview.png"))
    browser.close()
