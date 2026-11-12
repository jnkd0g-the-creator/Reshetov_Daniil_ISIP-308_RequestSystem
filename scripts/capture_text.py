"""Screenshot of genuine command output rendered readably in a local browser."""

import argparse
import html
from pathlib import Path

from browser_support import configure_browser
from playwright.sync_api import sync_playwright


def capture(source, target, title):
    configure_browser()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page.set_content('<html lang="ru"><meta charset="utf-8"><style>body{background:#12251f;color:#f0f4ea;font:18px monospace;padding:32px}h1{font:26px sans-serif;color:#d4ba8b}pre{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.4}</style><h1>' + html.escape(title) + '</h1><pre>' + html.escape(Path(source).read_text()) + '</pre></html>')
        page.screenshot(path=str(target), full_page=True)
        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("target")
    parser.add_argument("--title", default="CoffeeDesk · фактический вывод команды")
    args = parser.parse_args()
    capture(args.source, args.target, args.title)
