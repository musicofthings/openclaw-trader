#!/usr/bin/env python3
"""Automate TradingView script installation without manual copy/paste.

Usage:
  python installer/install_tradingview_script.py \
      --pine plugin/ma_rsi_atr_plugin.pine \
      --email your@email.com

If --email is omitted, the browser opens and you can log in interactively.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Install OpenClaw Pine script into TradingView via browser automation")
    p.add_argument("--pine", required=True, help="Path to .pine file")
    p.add_argument("--email", default=None, help="TradingView email (optional)")
    p.add_argument("--password", default=None, help="TradingView password (optional)")
    p.add_argument("--headless", action="store_true", help="Run browser headless")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    pine_path = Path(args.pine).expanduser().resolve()
    pine_code = pine_path.read_text(encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        context = browser.new_context(viewport={"width": 1440, "height": 1024})
        page = context.new_page()

        page.goto("https://www.tradingview.com/chart/", wait_until="domcontentloaded")

        if args.email and args.password:
            page.goto("https://www.tradingview.com/accounts/signin/", wait_until="domcontentloaded")
            page.get_by_label("Email").fill(args.email)
            page.get_by_label("Password").fill(args.password)
            page.get_by_role("button", name="Sign in").click()
            page.wait_for_timeout(4000)
        else:
            print("Log in to TradingView in the opened browser window, then press Enter here to continue...")
            input()

        page.goto("https://www.tradingview.com/chart/", wait_until="networkidle")
        page.wait_for_timeout(3000)

        page.keyboard.press("Alt+p")
        page.wait_for_timeout(1500)

        editor = page.locator("textarea.inputarea")
        if editor.count() == 0:
            editor = page.locator("div.view-lines")

        page.keyboard.press("Control+a")
        page.keyboard.type(pine_code)
        page.wait_for_timeout(1000)

        page.get_by_role("button", name="Add to chart").click(timeout=8000)
        page.wait_for_timeout(2000)

        print("Script installed and added to chart. Save it from TradingView if desired.")

        context.close()
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
