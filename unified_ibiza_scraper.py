#!/usr/bin/env python3
"""
Unified Ibiza Spotlight Event Scraper (v1.0)

This script provides two modes for scraping ibiza-spotlight.com:
1. 'scrape': Scrapes a single event detail page for comprehensive data.
2. 'crawl': Crawls a monthly calendar, handling weekly pagination, 
             and scrapes details for all events found.

It uses Playwright with stealth for dynamic content and robust parsing.
"""
import argparse
import csv
import json
import random
import re
import time
import traceback
from dataclasses import dataclass, asdict, fields
from datetime import datetime, date, time as dt_time, UTC
from pathlib import Path
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

try:
    from playwright.sync_api import sync_playwright, Browser, Locator, TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api._generated import Page
    from playwright_stealth import stealth_sync  # type: ignore
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    sync_playwright, Page, Browser, Locator, stealth_sync, PlaywrightTimeoutError = (None,) * 6
    PLAYWRIGHT_AVAILABLE = False
# --- Configuration ---
SNAPSHOT_DIR = Path("debug_snapshots")
OUTPUT_DIR = Path("output")
BASE_URL = "https://www.ibiza-spotlight.com"

MODERN_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

# Ensure directories exist
SNAPSHOT_DIR.mkdir(exist_ok=True, parents=True)
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# --- Data Model ---
@dataclass
class Event:
    """Dataclass for a single event, designed for comprehensive detail page scraping."""
    url: str
    title: Optional[str] = None
    venue: Optional[str] = None
    date_text: Optional[str] = None # Raw date string from page
    start_date: Optional[date] = None # Parsed start date
    end_date: Optional[date] = None   # Parsed end date (if range)
    start_time: Optional[dt_time] = None
    end_time: Optional[dt_time] = None
    price_text: Optional[str] = None # Raw price string
    price_value: Optional[float] = None
    currency: Optional[str] = "EUR"
    lineup: Optional[List[str]] = None
    description: Optional[str] = None
    promoter: Optional[str] = None
    categories: Optional[List[str]] = None
    scraped_at: Optional[datetime] = None
    extraction_method: Optional[str] = "detail_page_html"

    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now(UTC)
        if self.lineup is None:
            self.lineup = []
        if self.categories is None:
            self.categories = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to a dictionary for serialization."""
        data = {}
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, (date, dt_time, datetime)):
                data[field.name] = value.isoformat()
            else:
                data[field.name] = value
        return data

# --- Scraper Class ---
class IbizaSpotlightUnifiedScraper:
    """A stealthy, robust scraper for ibiza-spotlight.com with scrape and crawl modes."""
    
    def __init__(self, headless: bool = True, min_delay: float = 2.0, max_delay: float = 5.0):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is not installed. Run: pip install playwright playwright-stealth && playwright install")
        
        self.headless = headless
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.browser: Optional[Browser] = None # type: ignore
        self.playwright_context = None
        self._ensure_browser()  # Now correctly indented within __init__
    def _get_random_delay(self, multiplier: float = 1.0) -> None:
        """Sleep for a random duration."""
        time.sleep(random.uniform(self.min_delay * multiplier, self.max_delay * multiplier))

    def _ensure_browser(self):
        """Initializes Playwright browser if not already running."""
        if not self.browser or not self.browser.is_connected():
            print("[INFO] Starting Playwright browser...")
            if self.playwright_context: # Close existing context if any
                try:
                    self.playwright_context.stop()
                except Exception:
                    pass
            self.playwright_context = sync_playwright().start()
            self.browser = self.playwright_context.chromium.launch(headless=self.headless)

    def _human_click(self, page: Page, locator: Locator, timeout: int = 10000): # type: ignore
        """Moves mouse over an element then clicks it like a human."""
        try:
            locator.wait_for(state="visible", timeout=timeout)
            bounding_box = locator.bounding_box()
            if not bounding_box:
                print(f"[WARNING] Could not get bounding box for locator: {locator}. Using direct click.")
                locator.click(timeout=timeout)
                return

            target_x = bounding_box['x'] + bounding_box['width'] * random.uniform(0.3, 0.7)
            target_y = bounding_box['y'] + bounding_box['height'] * random.uniform(0.3, 0.7)

            page.mouse.move(target_x, target_y, steps=random.randint(10, 20))
            self._get_random_delay(0.2) # Short pause before click
            page.mouse.click(target_x, target_y)
            print(f"[INFO] Human-like click successful on locator.")
            self._get_random_delay(0.5) # Pause after click
        except Exception as e:
            print(f"[WARNING] Human-like click failed: {e}. Falling back to direct click.")
            try:
                locator.click(timeout=timeout) # Fallback click
            except Exception as click_err:
                print(f"[ERROR] Direct click also failed: {click_err}")


    def _handle_overlays(self, page: Page): # type: ignore # type: ignore
        """Robustly finds and closes any cookie banners or pop-up overlays."""
        overlay_selectors = [
            'a.cb-seen-accept',                           # Specific cookie banner button
            'button#onetrust-accept-btn-handler',         # OneTrust accept button
            'button[data-testid="accept-all-cookies"]',
            'button:has-text("Accept all")',
            'button:has-text("Accept Cookies")',
            'button:has-text("I agree")',
            'button:has-text("No problem")',
            '[aria-label="close"]', '[aria-label="Close"]',
            '.modal-close', 'button.close'
        ]
        print("[INFO] Checking for overlays and cookie banners...")
        self._get_random_delay(0.5)

        for selector in overlay_selectors:
            try:
                button_locator = page.locator(selector).first # Important: .first to avoid ambiguity
                if button_locator.is_visible(timeout=3000): # Quick check for visibility
                    print(f"[INFO] Found overlay button with selector: '{selector}'. Attempting click...")
                    self._human_click(page, button_locator, timeout=5000)
                    print(f"[INFO] Clicked overlay with selector: {selector}.")
                    # It's often good to return after one successful click if it's a modal
                    return 
            except PlaywrightTimeoutError:
                # Element not visible or not found within timeout, try next selector
                continue
            except Exception as e:
                print(f"[DEBUG] Error while trying selector '{selector}': {e}")
                continue
        
        # Check for iframes (less common for main cookie banners but possible)
        # This is a simplified iframe check; complex nested iframes might need more
        for frame in page.frames[1:]: # Skip main frame (index 0)
            for selector in overlay_selectors:
                try:
                    button_locator = frame.locator(selector).first
                    if button_locator.is_visible(timeout=2000):
                        print(f"[INFO] Found overlay button in iframe with selector: '{selector}'. Clicking...")
                        self._human_click(page, button_locator, timeout=5000) # page context for click is fine
                        return
                except Exception:
                    continue
        print("[INFO] No active overlays found or handled.")

    def fetch_page_html(self, url: str, wait_for_content_selector: Optional[str] = None) -> str:
        """Fetch page HTML using Playwright with stealth and robust waits."""
        self._ensure_browser()
        page: Optional[Page] = None
        try:
            page = self.browser.new_page(user_agent=random.choice(MODERN_USER_AGENTS))
            
            print("[INFO] Applying stealth modifications...")
            stealth_sync(page)
            
            print(f"[INFO] Navigating to: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=60000) # domcontentloaded is often faster
            
            self._handle_overlays(page) # Handle overlays after initial load
            
            # Wait for specific content if a selector is provided, or a general body load
            content_ready_selector = wait_for_content_selector if wait_for_content_selector else "body"
            print(f"[INFO] Waiting for main content ('{content_ready_selector}')...")
            try:
                page.wait_for_selector(content_ready_selector, timeout=30000, state="visible")
                print(f"[INFO] Main content '{content_ready_selector}' is visible.")
            except PlaywrightTimeoutError:
                print(f"[WARNING] Timed out waiting for '{content_ready_selector}'. Page might be incomplete or structured differently.")
                # Save snapshot for debugging
                snap_path = SNAPSHOT_DIR / f"timeout_content_{urlparse(url).path.replace('/', '_')}_{int(time.time())}.html"
                snap_path.write_text(page.content(), encoding="utf-8", errors="replace")
                print(f"[DEBUG] Saved content timeout snapshot to: {snap_path}")
            
            self._get_random_delay() # Small delay for any final JS rendering
            return page.content()
            
        except Exception as e:
            print(f"[ERROR] Playwright fetch failed for {url}: {e}")
            if page:
                snap_path = SNAPSHOT_DIR / f"error_fetch_{urlparse(url).path.replace('/', '_')}_{int(time.time())}.html"
                try:
                    snap_path.write_text(page.content(), encoding="utf-8", errors="replace")
                    print(f"[DEBUG] Saved error snapshot to: {snap_path}")
                except Exception as snap_err:
                    print(f"[ERROR] Could not save snapshot: {snap_err}")
            raise
        finally:
            if page:
                page.close()

    def _parse_event_detail_page_content(self, html_content: str, url: str) -> Optional[Event]:
        """Parses HTML of an event detail page."""
        print(f"[INFO] Parsing event detail page: {url}")
        soup = BeautifulSoup(html_content, "lxml")
        event_data = Event(url=url)

        # Refined selectors based on the actual page structure
        selectors = {
            "title": "head title",
            "venue": ".section--header .container h2, .section--header .container h1 + p",
            "date_text": ".section--promoter-listings .card-ticket .ticket-date a",
            "time_text": ".section--promoter-listings .card-ticket .ticket-time",
            "price_text": ".section--promoter-listings .card-ticket .ticket-price, .section--body-text .ticket-price",
            "description": ".section--body-text .content, .section--body-text p",
            "promoter": ".section--header .container h1",
        }

        # Title (prefer the more concise title)
        title_elem = soup.select_one(selectors["title"])
        if title_elem:
            # Split the title and take the first part
            full_title = title_elem.get_text(strip=True)
            event_data.title = full_title.split('|')[0].strip()

        # Venue
        venue_elem = soup.select_one(selectors["venue"])
        if venue_elem:
            event_data.venue = venue_elem.get_text(strip=True)

        # Promoter
        promoter_elem = soup.select_one(selectors["promoter"])
        if promoter_elem:
            event_data.promoter = promoter_elem.get_text(strip=True)

        # Description
        desc_elem = soup.select_one(selectors["description"])
        if desc_elem:
            event_data.description = desc_elem.get_text(strip=True)

        # Price parsing
        price_elem = soup.select_one(selectors["price_text"])
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            # Extract numeric value, handling potential currency symbol
            price_match = re.search(r'(\d+(?:\.\d+)?)', price_text.replace(',', ''))
            if price_match:
                event_data.price_text = price_text
                # Correctly handle thousand separators
                price_value_str = price_match.group(1).replace(',', '')
                try:
                    event_data.price_value = float(price_value_str)
                except ValueError:
                    print(f"[WARNING] Could not parse price value from: {price_value_str}")
                event_data.currency = 'EUR'  # Default for Ibiza events

        # Date parsing from event listings
        date_elems = soup.select(selectors["date_text"])
        if date_elems:
            # Collect all dates from the event listings
            dates = [elem.get_text(strip=True) for elem in date_elems]
            # You might want to parse these dates more precisely
            event_data.date_text = ', '.join(dates)

            # Try to parse start date from the first date
            if dates:
                try:
                    # Assuming the date format is like 'Sat03May'
                    # Explicitly add the current year to avoid deprecation warning
                    current_year = datetime.now().year
                    full_date_str = f"{dates[0]} {current_year}"
                    parsed_date = datetime.strptime(full_date_str, '%a%d%b %Y')
                    event_data.start_date = parsed_date.date()
                except ValueError:
                    print(f"[WARNING] Could not parse date: {dates[0]}")

        # Ensure a title is present
        if not event_data.title:
            print(f"[WARNING] No title found for {url}")
            return None

        # Venue
        venue_elem = soup.select_one(selectors["venue"])
        if venue_elem: event_data.venue = venue_elem.get_text(strip=True)
        
        # Date Text (raw)
        date_text_elem = soup.select_one(selectors["date_text"])
        if date_text_elem:
            event_data.date_text = date_text_elem.get_text(strip=True)
            if date_text_elem.name == 'time' and date_text_elem.get('datetime'):
                event_data.date_text = date_text_elem['datetime'] # Prefer datetime attribute
            # TODO: Add robust date parsing from event_data.date_text to fill
            # event_data.start_date and event_data.end_date

        # Time Text & Parsing (Example - needs refinement)
        time_text_elem = soup.select_one(selectors["time_text"])
        if time_text_elem:
            time_full_text = time_text_elem.get_text(strip=True)
            # Example: "23:00 - 06:00" or "from 15:00"
            time_matches = re.findall(r'(\d{1,2}:\d{2})', time_full_text)
            if time_matches:
                try:
                    event_data.start_time = dt_time.fromisoformat(time_matches[0])
                    if len(time_matches) > 1:
                        event_data.end_time = dt_time.fromisoformat(time_matches[1])
                except ValueError:
                    print(f"[WARNING] Could not parse time(s) from: {time_full_text}")

        # Price
        price_elem = soup.select_one(selectors["price_text"])
        if price_elem: 
            event_data.price_text = price_elem.get_text(strip=True)
            price_match = re.search(r'(\d[\d,.]*\d)', event_data.price_text.replace(',', ''))
            if price_match:
                try:
                    event_data.price_value = float(price_match.group(1))
                except ValueError:
                    print(f"[WARNING] Could not parse price value from: {event_data.price_text}")
            # TODO: Extract currency if present

        # Lineup extraction removed
        event_data.lineup = []
        
        # Description
        desc_elem = soup.select_one(selectors["description"])
        if desc_elem: event_data.description = desc_elem.get_text(strip=True, separator="\n")

        # Promoter
        promoter_elem = soup.select_one(selectors["promoter"])
        if promoter_elem: event_data.promoter = promoter_elem.get_text(strip=True)

        # Categories extraction removed
        event_data.categories = []

        if not event_data.title: # If no title, it's probably not a valid event page
            print(f"[WARNING] No title found for {url}, skipping event data.")
            # Save HTML for debugging
            debug_path = SNAPSHOT_DIR / f"no_title_debug_{int(time.time())}.html"
            Path(debug_path).write_text(html_content, encoding="utf-8")
            print(f"[DEBUG] Saved HTML content to {debug_path}")
            return None
            
        return event_data

    def _extract_event_links_from_calendar(self, html_content: str, base_url: str) -> List[str]:
        """Extracts event detail page URLs from a calendar page HTML."""
        soup = BeautifulSoup(html_content, "lxml")
        links = set()
        # Selector for event cards/links on the calendar page
        # This is based on the structure observed in error_1748399555.html
        event_card_links = soup.select("div.card-ticket.partyCal-ticket div.ticket-header h3.h3 a.trackEventSpotlight")
        
        for link_tag in event_card_links:
            href = link_tag.get('href')
            if href:
                full_url = urljoin(base_url, href)
                # Basic validation: ensure it's an event detail page, not another calendar view
                if "/night/events/" in full_url and not re.search(r'/night/events/\d{4}(/\d{1,2})?/?$', full_url):
                    links.add(full_url)
        print(f"[INFO] Extracted {len(links)} potential event detail links from calendar page.")
        return list(links)

    def _handle_calendar_pagination(self, page: Page) -> bool:
        """
        Looks for and clicks the 'Next Week' link on the calendar.
        Returns True if pagination was successful, False otherwise.
        """
        print("[INFO] Checking for calendar pagination (next week)...")
        try:
            # The week navigation is complex. We need to find the 'active' week first.
            # Then find the next sibling that is not active and click its link.
            # This is a simplified approach: click any link that looks like "Next week" or a subsequent week.
            
            # Selector for the "Next week" link in the mobile view (often simpler)
            next_week_mobile_selector = "li.nav-next a"
            next_week_desktop_selector = ".weeknav-container:not(.active) a.calendarNav" # General next week

            # Try mobile selector first
            next_link_locator_mobile = page.locator(next_week_mobile_selector).first
            if next_link_locator_mobile.is_visible(timeout=2000):
                print("[INFO] Found 'Next week' (mobile) link. Clicking...")
                self._human_click(page, next_link_locator_mobile)
                page.wait_for_load_state("networkidle", timeout=20000)
                return True

            # Try desktop selectors
            # This is tricky because there can be multiple "next week" links.
            # We need to find the one immediately following the "active" one if possible.
            # For simplicity, we'll try to find any non-active week link and click the first one.
            # This might not always go to the *immediately* next week if multiple future weeks are shown.
            
            active_week_nav = page.locator(".weeknav-container.active").first
            if active_week_nav.is_visible(timeout=2000):
                # Try to find the next sibling .weeknav-container that is not .active
                # This requires more complex Playwright DOM traversal or JS execution.
                # Simplified: find all week links, find current, click next.
                all_week_links = page.locator(".weeknav-container a.calendarNav").all()
                current_url = page.url
                current_index = -1
                for i, link_loc in enumerate(all_week_links):
                    href = link_loc.get_attribute("href")
                    if href and urljoin(BASE_URL, href) == current_url:
                        current_index = i
                        break
                
                if current_index != -1 and current_index + 1 < len(all_week_links):
                    next_week_locator = all_week_links[current_index + 1]
                    print(f"[INFO] Found next week link via desktop nav. Clicking: {next_week_locator.get_attribute('href')}")
                    self._human_click(page, next_week_locator)
                    page.wait_for_load_state("networkidle", timeout=20000)
                    return True
            
            print("[INFO] No clear 'Next week' pagination link found or active week not identified.")
            return False

        except PlaywrightTimeoutError:
            print("[INFO] No 'Next week' pagination link found (timeout).")
            return False
        except Exception as e:
            print(f"[ERROR] Error during calendar pagination: {e}")
            return False

    # --- Public API Methods ---
    def scrape_single_event(self, event_url: str) -> Optional[Event]:
        """Public method for 'scrape' mode."""
        print(f"[MODE: SCRAPE] Scraping single event: {event_url}")
        try:
            # For event detail pages, a general content selector is often sufficient.
            # '.event-details-container' or 'article.event-item' could be examples.
            # Using a broad selector like 'main' or 'article' initially.
            html_content = self.fetch_page_html(event_url, wait_for_content_selector="main article, main div.content")
            return self._parse_event_detail_page_content(html_content, event_url)
        except Exception as e:
            print(f"[ERROR] Failed to scrape event {event_url}: {e}")
            traceback.print_exc()
            return None

    def crawl_calendar(self, year: int, month: int) -> List[Event]:
        """Public method for 'crawl' mode."""
        start_url = f"{BASE_URL}/night/events/{year}/{month:02d}"
        print(f"[MODE: CRAWL] Starting crawl for {month:02d}/{year} from URL: {start_url}")
        
        all_events: Dict[str, Event] = {} # Use dict to store unique events by URL
        processed_calendar_pages = set() # To avoid re-processing same calendar page if pagination loops

        self._ensure_browser()
        page: Optional[Page] = None
        try:
            page = self.browser.new_page(user_agent=random.choice(MODERN_USER_AGENTS))
            print("[INFO] Applying stealth modifications for crawl session...")
            stealth_sync(page)
            
            current_calendar_url = start_url
            
            for _ in range(10): # Max 10 pages of pagination (e.g., 5 weeks + buffer)
                if current_calendar_url in processed_calendar_pages:
                    print(f"[INFO] Already processed calendar page: {current_calendar_url}. Stopping pagination for this branch.")
                    break
                
                print(f"[INFO] Fetching calendar page: {current_calendar_url}")
                page.goto(current_calendar_url, wait_until="domcontentloaded", timeout=60000)
                self._handle_overlays(page)
                
                # Wait for the main calendar grid to be visible
                try:
                    page.wait_for_selector("#PartyCalBody", timeout=30000, state="visible")
                    print("[INFO] Calendar body is visible.")
                except PlaywrightTimeoutError:
                    print("[ERROR] Main calendar body #PartyCalBody not found. Cannot extract links.")
                    break # Stop if calendar structure is missing

                calendar_html = page.content()
                processed_calendar_pages.add(current_calendar_url)

                event_detail_links = self._extract_event_links_from_calendar(calendar_html, BASE_URL)
                
                for link in event_detail_links:
                    if link not in all_events: # Scrape only if not already processed
                        event_data = self.scrape_single_event(link) # This uses its own page fetching
                        if event_data:
                            all_events[link] = event_data
                        self._get_random_delay() # Delay between scraping individual event pages
                
                if not self._handle_calendar_pagination(page): # page object is passed here
                    print("[INFO] No more calendar pages to paginate or pagination failed.")
                    break 
                
                current_calendar_url = page.url # Update to the new paginated URL
                print(f"[INFO] Paginated to new calendar URL: {current_calendar_url}")
                self._get_random_delay()

        except Exception as e:
            print(f"[ERROR] Crawl failed: {e}")
            traceback.print_exc()
        finally:
            if page:
                page.close()
                
        return list(all_events.values())

    def close(self):
        """Cleans up scraper resources."""
        if self.browser:
            try:
                self.browser.close()
            except Exception as e:
                print(f"[DEBUG] Error closing browser: {e}")
        if self.playwright_context:
            try:
                self.playwright_context.stop()
            except Exception as e:
                print(f"[DEBUG] Error stopping Playwright context: {e}")
        print("[INFO] Scraper resources closed.")

# --- Export and Utility Functions ---
def save_events_to_file(events: List[Event], filepath_base: Path, formats: List[str]):
    """Saves events to specified formats."""
    if not events:
        print("[INFO] No events to save.")
        return

    if "json" in formats:
        json_path = filepath_base.with_suffix(".json")
        with json_path.open("w", encoding="utf-8") as f:
            json.dump([e.to_dict() for e in events], f, indent=2, ensure_ascii=False)
        print(f"[INFO] Saved {len(events)} events to {json_path}")

    if "csv" in formats:
        csv_path = filepath_base.with_suffix(".csv")
        if events:
            # Dynamically get fieldnames from the first event, ensuring all keys are present
            fieldnames = list(events[0].to_dict().keys())
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for event in events:
                    writer.writerow(event.to_dict())
            print(f"[INFO] Saved {len(events)} events to {csv_path}")

# --- Main CLI ---
def main():
    """Main Command Line Interface function."""
    parser = argparse.ArgumentParser(description="Unified Ibiza Spotlight Scraper v1.0")
    
    # Mode selection
    parser.add_argument("action", choices=["scrape", "crawl"], help="Action to perform: 'scrape' a single event URL, or 'crawl' a monthly calendar.")
    
    # Arguments for 'scrape' mode
    parser.add_argument("--url", type=str, help="URL of the single event detail page to scrape (for 'scrape' mode).")
    
    # Arguments for 'crawl' mode
    parser.add_argument("--month", type=int, help="Month to crawl (1-12) (for 'crawl' mode).")
    parser.add_argument("--year", type=int, help="Year to crawl (e.g., 2025) (for 'crawl' mode).")
    
    # Common arguments
    parser.add_argument("--no-headless", action="store_false", dest="headless", default=True, help="Show browser window for debugging.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="Directory to save output files.")
    parser.add_argument("--format", nargs='+', choices=["json", "csv"], default=["json", "csv"], help="Output format(s).")
    parser.add_argument("--min-delay", type=float, default=2.0, help="Minimum random delay (seconds) between requests.")
    parser.add_argument("--max-delay", type=float, default=5.0, help="Maximum random delay (seconds) between requests.")

    args = parser.parse_args()

    # Validate arguments based on mode
    if args.action == "scrape":
        if not args.url:
            parser.error("--url is required for 'scrape' mode.")
        if not urlparse(args.url).scheme or not urlparse(args.url).netloc:
            parser.error("--url must be a full, valid URL (e.g., http://example.com/event).")
    elif args.action == "crawl":
        if args.month is None or args.year is None:
            parser.error("--month and --year are required for 'crawl' mode.")
        if not (1 <= args.month <= 12):
            parser.error("Month must be between 1 and 12.")
        if args.year < 2000 or args.year > datetime.now().year + 5: # Basic year sanity check
             parser.error(f"Year seems invalid. Please provide a realistic year (e.g., {datetime.now().year}).")

    args.output_dir.mkdir(exist_ok=True, parents=True)
    
    scraper = None
    all_events_data: List[Event] = []

    try:
        scraper = IbizaSpotlightUnifiedScraper(
            headless=args.headless,
            min_delay=args.min_delay,
            max_delay=args.max_delay
        )
        
        if args.action == "scrape":
            event = scraper.scrape_single_event(args.url)
            if event:
                all_events_data.append(event)
        elif args.action == "crawl":
            all_events_data = scraper.crawl_calendar(args.year, args.month)
            
        if not all_events_data:
            print("[INFO] No events were successfully scraped.")
        else:
            print(f"[SUCCESS] Completed. Total events scraped: {len(all_events_data)}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if args.action == "scrape":
                site_name_part = urlparse(args.url).hostname.replace('.', '_') if args.url else "single_event"
                base_name = f"scraped_event_{site_name_part}_{timestamp}"
            else: # crawl
                base_name = f"crawled_events_ibiza_spotlight_{args.year}_{args.month:02d}_{timestamp}"
            
            filepath_base = args.output_dir / base_name
            save_events_to_file(all_events_data, filepath_base, args.format)
            
    except KeyboardInterrupt:
        print("\n[INFO] Scraping interrupted by user.")
    except ImportError as e:
        print(f"[FATAL ERROR] A required library is missing: {e}. Please install dependencies.")
        print("Try: pip install playwright playwright-stealth beautifulsoup4 requests")
        print("And then: playwright install")
    except Exception as e:
        print(f"[FATAL ERROR] An unhandled error occurred: {e}")
        traceback.print_exc()
    finally:
        if scraper:
            scraper.close()
        print("[INFO] Script finished.")

if __name__ == "__main__":
    main()
