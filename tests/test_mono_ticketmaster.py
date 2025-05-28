import os
import sys
import pytest

pytest.importorskip("mistune", reason="mistune not installed")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mono_ticketmaster import MultiLayerEventScraper


def test_scrape_event_data_jsonld(mocker):
    html = '''<html><head><script type="application/ld+json">{
        "@context": "https://schema.org",
        "@type": "MusicEvent",
        "name": "Sample Event",
        "location": {"name": "My Venue", "address": {"streetAddress": "123 St", "addressRegion": "CA", "addressCountry": "USA"}},
        "startDate": "2025-01-01T20:00:00",
        "endDate": "2025-01-01T23:00:00",
        "offers": {"name": "General", "price": "30", "priceCurrency": "USD", "availability": "InStock", "url": "http://ticket.example.com"}
    }</script></head><body></body></html>'''
    scraper = MultiLayerEventScraper(use_browser=False)
    mocker.patch.object(scraper, "fetch_page", return_value=html)
    data = scraper.scrape_event_data("http://example.com")
    assert data["title"] == "Sample Event"
    assert data["ticketInfo"]["currency"] == "USD"
    assert data["extractionMethod"] == "jsonld"
