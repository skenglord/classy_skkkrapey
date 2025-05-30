import pytest
import os
import sys
from urllib.parse import urlparse # Needed for one of the tested functions if used directly

# Add project root to sys.path to allow direct imports if the project is not installed.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from my_scrapers.classy_skkkrapey import get_scraper_class, TicketsIbizaScraper, IbizaSpotlightScraper
from bs4 import BeautifulSoup # For later tests

# --- Tests for get_scraper_class (factory function) ---

def test_get_scraper_class_ticketsibiza():
    scraper_class = get_scraper_class("https://www.ticketsibiza.com/event/some-event")
    assert scraper_class == TicketsIbizaScraper

def test_get_scraper_class_ibiza_spotlight():
    scraper_class = get_scraper_class("https://www.ibiza-spotlight.com/night/events/some-event")
    assert scraper_class == IbizaSpotlightScraper

def test_get_scraper_class_unknown_hostname():
    with pytest.raises(ValueError, match="No scraper configured for hostname: www.unknownsite.com"):
        get_scraper_class("https://www.unknownsite.com/event")

def test_get_scraper_class_malformed_url_no_hostname():
    # urlparse("htp://no_hostname_here").hostname is "no_hostname_here"
    # So it falls into the "No scraper configured" case.
    with pytest.raises(ValueError, match="No scraper configured for hostname: no_hostname_here"):
        get_scraper_class("htp://no_hostname_here") # Intentionally malformed protocol too

def test_get_scraper_class_url_with_path_only_no_hostname():
    # urlparse on "/just/a/path" results in hostname=None
    with pytest.raises(ValueError, match="Invalid URL: Could not determine hostname."):
        get_scraper_class("/just/a/path")

# TODO: Add tests for TicketsIbizaScraper._parse_json_ld
# TODO: Add tests for TicketsIbizaScraper._parse_microdata
# TODO: Add tests for IbizaSpotlightScraper.crawl_listing_for_events (link filtering)
# TODO: Add tests for format_event_to_markdown
