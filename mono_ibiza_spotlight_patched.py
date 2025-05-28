#!/usr/bin/env python3
"""Lean Ibiza‑Spotlight scraper
================================
Scrapes events from **https://www.ibiza‑spotlight.com/night/events** using the
JSON calendar endpoint first and falls back to HTML parsing rendered through
Playwright when JSON is unavailable or malformed.

Key points
----------
* **Single reject‑only regex** to skip calendar listing URLs and let everything
  else through – no more costly cascade.
* **context.set_default_timeout(15000)** and **wait_until="domcontentloaded"**
  keep the browser snappy (vs. the old `networkidle`).
* **DOM snapshot** is taken automatically on any Playwright failure for easy
  debugging.
* A friendly **ASCII fireworks** animation prints only when at least one event
  is scraped.
* Optional **headed debug mode** (`--headed`) to watch the browser in real time.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import re
import sys
import textwrap
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeout,
    sync_playwright,
)

# ──────────────────────────────────────────────────────────────────────────────
# Constants & Regex
# ──────────────────────────────────────────────────────────────────────────────

RE_LISTING = re.compile(r"^/night/events/\d{4}(?:/\d{1,2}){0,2}$")  # reject‑only
CAL_JSON_FMT = (
    "https://www.ibiza-spotlight.com/services/calendar/json?month={month}&year={year}"
)

ASCII_FIREWORKS = [
    "    *",
    "   /*\\ ",
    "  /***\\",
    " /*****\\",
    "/*******\\",
]

# ──────────────────────────────────────────────────────────────────────────────
# Dataclass
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class Event:
    title: str
    date: str
    url: str

    @classmethod
    def from_calendar_json(cls, obj: dict) -> "Event":
        return cls(
            title=obj.get("title", ""),
            date=obj.get("date", ""),
            url=obj.get("url", ""),
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


# ──────────────────────────────────────────────────────────────────────────────
# Scraper Class
# ──────────────────────────────────────────────────────────────────────────────


class SpotlightScraper:
    """JSON‑first, HTML‑fallback scraper for Ibiza Spotlight."""

    def __init__(self, *, headed: bool = False, verbose: bool = False):
        self.logger = logging.getLogger("SpotlightScraper")
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        ch = logging.StreamHandler()
        ch.setFormatter(
            logging.Formatter("%(levelname)s | %(name)s | %(message)s")
        )
        self.logger.addHandler(ch)

        # HTTP session for JSON endpoint
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:126.0) "
                    "Gecko/20100101 Firefox/126.0"
                )
            }
        )

        # Playwright vars (lazy‑initialised)
        self._pw = None  # type: ignore
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self.headed = headed

    # ───────────────────────── Internal helpers ──────────────────────────

    def _ensure_browser(self):
        if self._page is None:
            self.logger.debug("Launching Playwright…")
            self._pw = sync_playwright().start()
            self._browser = self._pw.firefox.launch(headless=not self.headed)
            self._context = self._browser.new_context()
            self._context.set_default_timeout(15_000)  # 15 s everywhere
            # Block images, fonts, media for speed
            self._context.route(
                re.compile(r".*\.(png|jpe?g|gif|webp|svg|woff2?|ttf|otf)$"),
                lambda route: route.abort(),
            )
            self._page = self._context.new_page()

    # ───────────────────────── Fetching ──────────────────────────

    def fetch_page(self, url: str, *, use_browser_override: bool = False) -> str:
        """Return raw text from JSON endpoint or rendered HTML."""
        if not use_browser_override and "/night/events/" in url:
            # Derive month/year from the URL if possible
            parts = url.rstrip("/").split("/")
            try:
                year = int(parts[-2])
                month = int(parts[-1])
                json_url = CAL_JSON_FMT.format(month=f"{month:02d}", year=year)
                self.logger.debug(f"Attempting calendar JSON → {json_url}")
                return self._fetch_json(json_url)
            except (ValueError, IndexError):
                # Could not parse – fall back
                pass
        # Fallback to browser‑rendered HTML
        return self._fetch_html(url)

    def _fetch_json(self, url: str) -> str:
        try:
            r = self.session.get(url, timeout=10)
            r.raise_for_status()
            self.logger.debug("Calendar JSON fetched OK.")
            return r.text
        except Exception as e:  # noqa: BLE001
            self.logger.warning(f"JSON fetch failed ({e!s}) – falling back to HTML")
            return self._fetch_html(url.replace("services/calendar/json", "night/events"))

    def _fetch_html(self, url: str, *, force_browser: bool = True) -> str:
        self._ensure_browser()
        assert self._page, "Browser page not initialised"

        try:
            self._page.goto(url, wait_until="domcontentloaded")
            self.logger.debug("HTML page rendered via Playwright.")
            return self._page.content()
        except PlaywrightTimeout:
            self.logger.error("Playwright timeout – taking DOM snapshot.")
            self._snapshot_dom(url)
            raise

    def _snapshot_dom(self, url: str):
        if not self._page:
            return
        fname = (
            Path("snapshots")
            / f"dom_{int(time.time())}_{re.sub(r'\W+', '_', url)}.html"
        )
        fname.parent.mkdir(exist_ok=True)
        fname.write_text(self._page.content())
        self.logger.info(f"DOM snapshot saved → {fname}")

    # ───────────────────────── Parsing ──────────────────────────

    def _parse_events(self, source: str) -> List[Event]:
        """Return list of Event objects from JSON or HTML."""
        trimmed = source.lstrip()
        if trimmed.startswith("{") or trimmed.startswith("["):
            try:
                data = json.loads(trimmed)
                # Calendar JSON returns a dict with "events" list sometimes
                if isinstance(data, dict):
                    data = data.get("events", [])
                return [
                    Event.from_calendar_json(obj)
                    for obj in data
                    if obj.get("url") and not RE_LISTING.match(obj["url"])
                ]
            except json.JSONDecodeError:
                self.logger.warning("Bad JSON – using HTML parser")
        # Fall back to HTML parser
        return self._parse_events_html(trimmed)

    def _parse_events_html(self, html: str) -> List[Event]:
        soup = BeautifulSoup(html, "html.parser")
        events: list[Event] = []
        for li in soup.select("li.event-item"):
            try:
                title = li.select_one("h3").get_text(strip=True)
                date = li.get("data-date", "")
                url = li.select_one("a[href]")["href"]
                if RE_LISTING.match(url):
                    continue  # skip listing pages
                events.append(Event(title=title, date=date, url=url))
            except Exception:  # noqa: BLE001
                continue
        return events

    # ───────────────────────── Crawl public API ──────────────────────────

    def crawl(self, month: int, year: int) -> List[Event]:
        listing_url = f"https://www.ibiza-spotlight.com/night/events/{year}/{month:02d}"
        self.logger.info(f"Crawling → {listing_url}")
        raw = self.fetch_page(listing_url)
        events = self._parse_events(raw)
        self.logger.info(f"Scraped {len(events)} event(s).")
        if events:
            self._fireworks()
        return events

    # ───────────────────────── Fun bits ──────────────────────────

    def _fireworks(self):
        """Tiny ASCII fireworks animation (terminal)."""
        fanout = ASCII_FIREWORKS + ASCII_FIREWORKS[::-1]
        for frame in fanout:
            print(f"\033[92m{frame}\033[0m", flush=True)
            time.sleep(0.12)

    # ───────────────────────── Cleanup ──────────────────────────

    def close(self):
        if self._page:
            self._page.close()
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()
        self.session.close()

    # ───────────────────────── Dunder ──────────────────────────

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
        self.close()


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Ibiza Spotlight scraper (JSON-first, Playwright fallback)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            Examples
            --------
            Scrape May 2025 (headed browser, verbose logs):
                python mono_ibiza_spotlight.py 5 2025 --headed --verbose
            """
        ),
    )
    p.add_argument("month", type=int, help="Month (1‑12)")
    p.add_argument("year", type=int, help="4‑digit year")
    p.add_argument("--headed", action="store_true", help="Run browser headed")
    p.add_argument("--verbose", action="store_true", help="Debug logs")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Save events JSON to this file (default: stdout)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    with SpotlightScraper(headed=args.headed, verbose=args.verbose) as sp:
        events = sp.crawl(args.month, args.year)
        output = [asdict(ev) for ev in events]
        out_json = json.dumps(output, ensure_ascii=False, indent=2)
        if args.output:
            args.output.write_text(out_json)
            print(f"Saved → {args.output}")
        else:
            print(out_json)


if __name__ == "__main__":
    sys.exit(main())
