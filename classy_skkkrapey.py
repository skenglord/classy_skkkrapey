#!/usr/bin/env python3
"""
Robust, Multi-Site, Refactored Event Scraper (v2)

This monolithic script combines the successful scraping architecture from mono_ticketmaster.py
with the necessary fixes to handle the dynamic, JavaScript-heavy nature of
ibiza-spotlight.com. It is designed for robustness, maintainability, and extensibility.

Key Features:
- Object-Oriented Design: A base scraper class with site-specific subclasses.
- Scraper Factory: Automatically selects the correct scraper based on the target URL.
- Multi-Layered Extraction: For ticketsibiza.com, it prioritizes structured data
  (JSON-LD, Microdata) before falling back to HTML parsing.
- Dynamic Content Handling: Forces browser rendering via Playwright for the
  JavaScript-dependent ibiza-spotlight.com calendar.
- Corrected Logic: Implements the fixed "crawl-then-scrape" workflow.
- Refined Link Filtering: Improved logic for IbizaSpotlightScraper to differentiate
  between event detail links and calendar navigation links.
- Self-Contained: Includes all necessary schema definitions, helper functions,
  and command-line execution logic in one file.
"""

import argparse
import sys
import json
import time
import random
import re
import logging
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
from typing import Optional, List, Any, Type, TypedDict, Literal
from dataclasses import dataclass

# --- Dependency Imports ---
import requests
from bs4 import BeautifulSoup, Tag # Added Tag for type hinting
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from playwright.sync_api import sync_playwright, Page, Browser # Added Page, Browser for type hinting
except ImportError:
    # This allows the script to run without Playwright if only used for static sites
    sync_playwright = None
    Page = None
    Browser = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ScraperConfig:
    url: str
    action: Literal["scrape", "crawl"]
    headless: bool
    output_dir: Path
    min_delay: float
    max_delay: float
    verbose: bool # Added for more control over logging

# --- Constants ---
OUTPUT_DIR_DEFAULT = "output"
MIN_DELAY_DEFAULT = 0.5
MAX_DELAY_DEFAULT = 1.5
SCRAPE_ACTION = "scrape"
CRAWL_ACTION = "crawl"

# --- Configuration ---
MODERN_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

# --- Data Schema Definitions (from mono_ticketmaster.py) ---

class LocationSchema(TypedDict, total=False):
    venue: str
    address: str
    city: str
    country: str

class DateTimeSchema(TypedDict, total=False):
    startDate: str
    endDate: str
    doorTime: str
    timeZone: str
    displayText: str

class ArtistSchema(TypedDict, total=False):
    name: str
    headliner: bool

class TicketInfoSchema(TypedDict, total=False):
    url: str
    availability: str
    startingPrice: float
    currency: str

class EventSchema(TypedDict, total=False):
    url: str
    scrapedAt: str
    extractionMethod: str
    title: str
    location: LocationSchema
    dateTime: DateTimeSchema
    lineUp: List[ArtistSchema]
    ticketInfo: TicketInfoSchema
    description: str

# --- Base Scraper Class ---

class BaseEventScraper:
    """A base class for web scrapers with common, site-agnostic functionality."""

    def __init__(self, use_browser: bool = False, headless: bool = True):
        self.use_browser_default = use_browser # Renamed to avoid conflict with method param
        self.headless = headless
        self.browser: Any = None  # Changed from Optional[Browser] to Any to avoid type expression error
        self.playwright_context = None # Renamed from playwright to avoid conflict with module
        self.current_user_agent = random.choice(MODERN_USER_AGENTS)
        self.session = self._create_session()
        self.pages_scraped_since_ua_rotation = 0
        self.rotate_ua_after_pages = 10 # Configurable: rotate UA every N pages

        if self.use_browser_default:
            if sync_playwright is None:
                raise ImportError("Playwright is not installed. Please run 'pip install playwright' and 'playwright install'.")
            print("[INFO] Starting Playwright...")
            self.playwright_context = sync_playwright().start()
            self.browser = self.playwright_context.chromium.launch(headless=self.headless)

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({"User-Agent": self.current_user_agent})
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def rotate_user_agent(self):
        self.current_user_agent = random.choice(MODERN_USER_AGENTS)
        self.session.headers.update({"User-Agent": self.current_user_agent})
        self.pages_scraped_since_ua_rotation = 0
        print(f"[INFO] Rotated User-Agent to: {self.current_user_agent}")

    def fetch_page(self, url: str, use_browser_override: bool = False) -> str:
        """Fetches page content using the appropriate method (requests or Playwright)."""
        # Rotate UA if needed, applies to both requests and browser new pages
        self.pages_scraped_since_ua_rotation += 1
        if self.pages_scraped_since_ua_rotation >= self.rotate_ua_after_pages:
            self.rotate_user_agent()

        if self.use_browser_default or use_browser_override:
            if not self.browser: # Ensure browser is initialized if default is False but override is True
                if sync_playwright is None:
                    raise ImportError("Playwright is not installed for on-demand browser use.")
                if not self.playwright_context: # Initialize Playwright if not already done
                    print("[INFO] Starting Playwright for on-demand browser use...")
                    self.playwright_context = sync_playwright().start()
                self.browser = self.playwright_context.chromium.launch(headless=self.headless)

            page: Optional["Page"] = None # Ensure page is defined for finally block
            try:
                page = self.browser.new_page(user_agent=self.current_user_agent)
                print(f"[INFO] Fetching with Playwright: {url}")
                page.goto(url, wait_until="networkidle", timeout=45000) # Increased timeout
                content = page.content()
            except Exception as e:
                print(f"[ERROR] Playwright fetch failed for {url}: {e}")
                raise # Re-raise the exception to be handled by the caller
            finally:
                if page:
                    page.close()
            return content
        else:
            print(f"[INFO] Fetching with Requests: {url}")
            time.sleep(random.uniform(1, 3))  # Respectful rate limiting
            response = self.session.get(url, timeout=20) # Increased timeout
            response.raise_for_status()
            return response.text

    def close(self):
        """Closes the browser and playwright instances gracefully."""
        if self.browser:
            self.browser.close()
        if self.playwright_context:
            self.playwright_context.stop()
        print("[INFO] Scraper resources closed.")

    def scrape_event_data(self, url: str) -> Optional[EventSchema]:
        """Abstract method for site-specific event data scraping."""
        raise NotImplementedError("Each scraper subclass must implement 'scrape_event_data'.")

    def crawl_listing_for_events(self, url: str) -> List[str]:
        """Abstract method for site-specific event link crawling."""
        raise NotImplementedError("Each scraper subclass must implement 'crawl_listing_for_events'.")

# --- Site-Specific Scraper Implementations ---

class TicketsIbizaScraper(BaseEventScraper):
    """Scraper for ticketsibiza.com, using a multi-layered extraction strategy."""

    def _parse_json_ld(self, soup: BeautifulSoup) -> Optional[EventSchema]:
        scripts = soup.find_all("script", type="application/ld+json")
        for script_tag in scripts: # Renamed variable
            try:
                # Ensure script_tag.string is not None before attempting to load
                if script_tag.string:
                    data = json.loads(script_tag.string)
                    if data.get("@type") == "MusicEvent":
                        loc = data.get("location", {})
                        offer_list = data.get("offers", [{}]) # offers can be a list
                        offer = offer_list[0] if isinstance(offer_list, list) and offer_list else {}

                        return EventSchema(
                            title=data.get("name"),
                            location=LocationSchema(venue=loc.get("name"), address=loc.get("address", {}).get("streetAddress")),
                            dateTime=DateTimeSchema(startDate=data.get("startDate"), endDate=data.get("endDate")),
                            lineUp=[ArtistSchema(name=p.get("name"), headliner=True) for p in data.get("performer", []) if p.get("name")],
                            ticketInfo=TicketInfoSchema(url=offer.get("url"), startingPrice=float(offer.get("price", 0)) if offer.get("price") else None, currency=offer.get("priceCurrency")),
                            description=data.get("description"),
                            extractionMethod="json-ld"
                        )
            except (json.JSONDecodeError, AttributeError, TypeError, IndexError) as e:
                print(f"[DEBUG] Error parsing JSON-LD: {e}")
                continue
        return None

    def _parse_microdata(self, soup: BeautifulSoup) -> Optional[EventSchema]:
        event_scope = soup.find(itemtype=re.compile(r"schema.org/MusicEvent"))
        if not event_scope: return None
        
        def get_prop(tag: Tag, prop: str) -> Optional[str]:
            elem = tag.find(itemprop=prop)
            return elem.get("content") or elem.text.strip() if elem else None

        title = get_prop(event_scope, "name")
        if not title: return None

        # Microdata parsing can be more detailed, this is a simplified example
        return EventSchema(
            title=title,
            location=LocationSchema(venue=get_prop(event_scope, "name")), # Venue name often same as event name in microdata
            dateTime=DateTimeSchema(startDate=get_prop(event_scope, "startDate")),
            extractionMethod="microdata"
        )

    def _parse_html_fallback(self, soup: BeautifulSoup) -> Optional[EventSchema]:
        title_tag = soup.select_one("h1.entry-title") # Specific to TicketsIbiza
        if not title_tag: return None
        return EventSchema(
            title=title_tag.text.strip(),
            extractionMethod="html-fallback"
        )

    def scrape_event_data(self, url: str) -> Optional[EventSchema]:
        print(f"[INFO] Scraping (TicketsIbiza): {url}")
        try:
            html = self.fetch_page(url) # Defaults to requests for this scraper
            soup = BeautifulSoup(html, "html.parser")
            
            event_data = self._parse_json_ld(soup)
            if not event_data:
                event_data = self._parse_microdata(soup)
            if not event_data:
                event_data = self._parse_html_fallback(soup)
            
            if event_data:
                event_data["url"] = url
                event_data["scrapedAt"] = datetime.utcnow().isoformat() + "Z"
                return event_data
            
            print(f"[WARNING] No data could be extracted for {url}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Request failed for {url}: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error scraping {url}: {e}")
        return None

    def crawl_listing_for_events(self, url: str) -> List[str]:
        print(f"[INFO] Crawling (TicketsIbiza): {url}")
        try:
            html = self.fetch_page(url) # Uses requests by default
            soup = BeautifulSoup(html, "html.parser")
            links = set()
            # Selector specific to ticketsibiza.com event calendar links
            link_tags = soup.select("a.tribe-events-calendar-list__event-title-link")
            for tag in link_tags:
                href = tag.get('href')
                if href:
                    links.add(urljoin(url, href))
            return list(links)
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Request failed for crawling {url}: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error crawling {url}: {e}")
        return []


class IbizaSpotlightScraper(BaseEventScraper):
    """Scraper for ibiza-spotlight.com, with forced browser rendering and refined link filtering."""

    def scrape_event_data(self, url: str) -> Optional[EventSchema]:
        print(f"[INFO] Scraping (IbizaSpotlight): {url}")
        try:
            # Individual event pages on Spotlight might also need JS, so force browser
            html = self.fetch_page(url, use_browser_override=True)
            soup = BeautifulSoup(html, "html.parser")
            
            # Try a more specific title selector first, then fallback
            title_tag = soup.select_one("h1.eventTitle") # Common pattern for event detail pages
            if not title_tag:
                title_tag = soup.select_one("h1") # General fallback
                
            if not title_tag:
                print(f"[WARNING] No title found for {url}. This might be a calendar page or unexpected structure.")
                # Attempt to see if it's a calendar page title to avoid mislabeling
                # Calendar page titles are usually like "Ibiza Spotlight Party Calendar Month Year"
                # If we correctly filter links, we shouldn't land here often for calendar pages.
                # However, if a link was misidentified, this helps.
                # For now, if no specific event title, return None.
                return None 
            
            event_data: EventSchema = {
                "title": title_tag.text.strip(),
                "url": url,
                "scrapedAt": datetime.utcnow().isoformat() + "Z",
                "extractionMethod": "html-dynamic"
                # TODO: Add more detailed field extraction for Spotlight event pages
                # (e.g., date, venue, lineup) using selectors from reverse-scrape log.
            }
            return event_data
        except Exception as e: # Catch Playwright errors or others
            print(f"[ERROR] Error scraping Ibiza Spotlight event page {url}: {e}")
        return None

    def crawl_listing_for_events(self, url: str) -> List[str]:
        print(f"[INFO] Crawling (IbizaSpotlight): {url}")
        try:
            print("[INFO] Forcing browser usage to render JavaScript calendar...")
            html = self.fetch_page(url, use_browser_override=True)
            soup = BeautifulSoup(html, "html.parser")
            
            links = set()
            
            # Broad selector, filtering is key.
            # Inspect the live page in non-headless mode to find a better selector
            # for containers of actual event links if this still picks up too much.
            # e.g., soup.select("div.event-card a[href*='/night/events/']")
            link_tags = soup.select("a[href*='/night/events/']")

            if not link_tags:
                print("[WARNING] No anchor tags matching basic pattern 'a[href*=/night/events/]' found.")

            for tag in link_tags:
                href = tag.get('href')
                if not href:
                    continue

                full_url = urljoin(url, href)
                parsed_url_obj = urlparse(full_url)
                parsed_link_path = parsed_url_obj.path

                # --- Start of refined filtering logic ---
                # 1. Basic path check
                if not parsed_link_path.startswith('/night/events/'):
                    continue
                
                # 2. Skip link to self or identical path
                if full_url == url or parsed_link_path == urlparse(url).path:
                    continue
                
                # 3. Skip links with query parameters or fragments (often filters or anchors, not distinct events)
                if parsed_url_obj.query or parsed_url_obj.fragment:
                    # print(f"[DEBUG] Skipping link with query/fragment: {full_url}")
                    continue

                # 4. Analyze path segments after '/night/events/'
                # path_after_base will be like 'YYYY/MM' or 'event-slug' or 'YYYY/MM/DD'
                path_after_base = parsed_link_path.replace('/night/events/', '', 1).strip('/')
                if not path_after_base: # If href was just '/night/events/'
                    continue
                
                parts = [p for p in path_after_base.split('/') if p]

                if not parts: # Should be redundant due to previous check
                    continue

                # 5. Identify and skip calendar navigation links (YYYY, YYYY/MM, YYYY/MM/DD patterns)
                is_calendar_nav_link = False
                if len(parts) == 1 and parts[0].isdigit() and len(parts[0]) == 4: # e.g., /2024
                    is_calendar_nav_link = True
                elif len(parts) == 2 and parts[0].isdigit() and len(parts[0]) == 4 and \
                     parts[1].isdigit() and 1 <= len(parts[1]) <= 2: # e.g., /2024/05 or /2024/5
                    is_calendar_nav_link = True
                elif len(parts) == 3 and parts[0].isdigit() and len(parts[0]) == 4 and \
                     parts[1].isdigit() and 1 <= len(parts[1]) <= 2 and \
                     parts[2].isdigit() and 1 <= len(parts[2]) <= 2: # e.g., /2024/05/01 or /2024/5/1
                    is_calendar_nav_link = True
                
                if is_calendar_nav_link:
                    # print(f"[DEBUG] Filtered out calendar navigation link: {full_url}")
                    continue
                
                # 6. If it's not a recognized calendar navigation pattern, it's likely an event.
                # A good heuristic: event slugs usually contain alphabetic characters.
                # This helps ensure we're not picking up unexpected numeric-only paths.
                if any(any(char.isalpha() for char in part) for part in parts):
                    links.add(full_url)
                # else:
                    # print(f"[DEBUG] Filtered out link with no alphabetic characters in slug parts: {full_url}")
                # --- End of refined filtering logic ---

            return list(links)
        except Exception as e: # Catch Playwright errors or others
            print(f"[ERROR] Error crawling Ibiza Spotlight listing {url}: {e}")
            import traceback
            traceback.print_exc() # Print full traceback for debugging
        return []


# --- Utility Functions ---

def format_event_to_markdown(event: EventSchema) -> str:
    """Converts a single event dictionary to a Markdown string."""
    lines = [f"### {event.get('title', 'N/A')}"]
    lines.append(f"**URL**: {event.get('url', 'N/A')}")
    if loc := event.get("location"): # Python 3.8+ walrus operator
        lines.append(f"**Venue**: {loc.get('venue', 'N/A')}")
    if dt := event.get("dateTime"):
        lines.append(f"**Date**: {dt.get('startDate', 'N/A')}")
    if lineup := event.get("lineUp"):
        lines.append("**Lineup**: " + ", ".join(a.get("name") for a in lineup if a.get("name")))
    lines.append(f"**Extraction Method**: {event.get('extractionMethod', 'N/A')}")
    return "\n".join(lines)

def datetime_serializer(obj: Any) -> str:
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

# --- Main Execution Block & Scraper Factory ---

def get_scraper_class(url: str) -> Type[BaseEventScraper]:
    """Factory function to select the correct scraper class based on URL."""
    hostname = urlparse(url).hostname
    if not hostname: # Handle cases where URL might be malformed or relative (though argparse should enforce full URL)
        raise ValueError("Invalid URL: Could not determine hostname.")
    if "ticketsibiza" in hostname:
        return TicketsIbizaScraper
    elif "ibiza-spotlight" in hostname:
        return IbizaSpotlightScraper
    else:
        raise ValueError(f"No scraper configured for hostname: {hostname}")

def _parse_arguments() -> ScraperConfig:
    """Parses command-line arguments and returns a ScraperConfig object."""
    parser = argparse.ArgumentParser(description="Robust, Multi-Site Event Scraper (v2)")
    parser.add_argument("url", help="The target URL to scrape or crawl.")
    parser.add_argument("action", choices=[SCRAPE_ACTION, CRAWL_ACTION], help=f"Action to perform: '{SCRAPE_ACTION}' a single page or '{CRAWL_ACTION}' a listing page.")
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=True, help="Run browser in headless mode. Use --no-headless to show browser.")
    parser.add_argument("--output_dir", default=OUTPUT_DIR_DEFAULT, help="Directory to save output files.")
    parser.add_argument("--min_delay", type=float, default=MIN_DELAY_DEFAULT, help="Minimum delay (seconds) between individual event scrapes during crawling.")
    parser.add_argument("--max_delay", type=float, default=MAX_DELAY_DEFAULT, help="Maximum delay (seconds) between individual event scrapes during crawling.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled.")

    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    return ScraperConfig(
        url=args.url,
        action=args.action,
        headless=args.headless,
        output_dir=output_path,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        verbose=args.verbose
    )

def _initialize_scraper(config: ScraperConfig) -> BaseEventScraper:
    """Initializes and returns the appropriate scraper instance."""
    try:
        ScraperClass = get_scraper_class(config.url)
        # Default to use_browser=True for instantiation, as Spotlight needs it for crawling.
        # Individual fetch_page calls within classes can decide if they need browser.
        scraper_instance = ScraperClass(use_browser=True, headless=config.headless)
        return scraper_instance
    except ValueError as e:
        logger.fatal(f"Configuration error: {e}")
        sys.exit(1)
    except ImportError as e:
        logger.fatal(f"Dependency error: {e}. Please ensure Playwright is installed ('pip install playwright' and 'playwright install').")
        sys.exit(1)

def _execute_scraping(scraper_instance: BaseEventScraper, config: ScraperConfig) -> List[EventSchema]:
    """Executes the scraping or crawling process based on the configuration."""
    all_events: List[EventSchema] = []
    try:
        if config.action == SCRAPE_ACTION:
            event = scraper_instance.scrape_event_data(config.url)
            if event:
                all_events.append(event)
        
        elif config.action == CRAWL_ACTION:
            event_urls = scraper_instance.crawl_listing_for_events(config.url)
            
            # Enhanced logging with actionable information
            url_count = len(event_urls)
            
            if url_count > 0:
                # Calculate time estimate based on delay settings
                min_time = url_count * config.min_delay
                max_time = url_count * config.max_delay
                
                logger.info(
                    f"✓ Found {url_count} potential event link{'s' if url_count != 1 else ''} to scrape "
                    f"(estimated time: {min_time:.0f}-{max_time:.0f} seconds)"
                )
                
                # Log sample URLs in debug mode
                if logger.isEnabledFor(logging.DEBUG):
                    sample = min(3, url_count)
                    logger.debug(f"First {sample} URLs: {event_urls[:sample]}")
            else:
                logger.warning(
                    "⚠️  No event URLs found after filtering.\n"
                    "   Troubleshooting:\n"
                    "   • Run with --no-headless to see the page\n"
                    "   • Check if CSS selectors need updating\n"
                    "   • Verify JavaScript loads completely\n"
                    "   • Test a different page with known events"
                )

            for i, url_to_scrape in enumerate(event_urls, 1):
                logger.info(f"--- Scraping event {i}/{len(event_urls)}: {url_to_scrape} ---")
                event = scraper_instance.scrape_event_data(url_to_scrape)
                if event:
                    all_events.append(event)
                # Add a small delay between scraping individual event pages
                time.sleep(random.uniform(config.min_delay, config.max_delay))
    except Exception as e:
        logger.fatal(f"An unexpected error occurred during {config.action}: {e}", exc_info=True)
    return all_events

def _save_results(all_events: List[EventSchema], config: ScraperConfig):
    """Saves the scraped events to JSON and Markdown files."""
    if not all_events:
        logger.info("No events were ultimately scraped. Skipping file output.")
        return

    logger.info(f"Successfully scraped {len(all_events)} events.")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hostname = urlparse(config.url).hostname

    # Save to JSON
    json_filename = f"events_{hostname}_{timestamp}.json"
    json_path = config.output_dir / json_filename
    try:
        with json_path.open("w", encoding="utf-8") as f:
            json.dump({"events": all_events, "source_url": config.url, "action": config.action}, f, indent=2, default=datetime_serializer)
        logger.info(f"Saved JSON to: {json_path}")
    except IOError as e:
        logger.error(f"Failed to save JSON to {json_path}: {e}")

    # Save to Markdown
    md_filename = f"events_{hostname}_{timestamp}.md"
    md_path = config.output_dir / md_filename
    try:
        with md_path.open("w", encoding="utf-8") as f:
            f.write(f"# Scrape Report - {timestamp}\n")
            f.write(f"**Source URL**: {config.url}\n")
            f.write(f"**Action**: {config.action}\n")
            f.write(f"**Total Events Scraped**: {len(all_events)}\n\n---\n\n")
            for event_item in all_events:
                f.write(format_event_to_markdown(event_item))
                f.write("\n\n---\n\n")
        logger.info(f"Saved Markdown to: {md_path}")
    except IOError as e:
        logger.error(f"Failed to save Markdown to {md_path}: {e}")

def main():
    """Main function to orchestrate the scraping process."""
    config = _parse_arguments()
    scraper_instance: Optional[BaseEventScraper] = None
    try:
        scraper_instance = _initialize_scraper(config)
        all_events = _execute_scraping(scraper_instance, config)
        _save_results(all_events, config)
    finally:
        if scraper_instance:
            scraper_instance.close()

if __name__ == "__main__":
    main()
