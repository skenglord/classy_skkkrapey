import asyncio
import os
import sys

import pytest

pytest.importorskip("playwright", reason="playwright not installed")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from playwright_mistune_scraper import scrape_event_data


class DummyLocator:
    async def inner_text(self):
        return "Event Title"


class DummyPage:
    def __init__(self):
        self.url = None

    async def goto(self, url, timeout=30000):
        self.url = url

    async def wait_for_selector(self, selector, timeout=30000):
        pass

    async def content(self):
        return "<html><h1 class='post-title'>Event Title</h1></html>"

    def locator(self, *args, **kwargs):
        return DummyLocator()


@pytest.mark.asyncio
async def test_scrape_event_data():
    page = DummyPage()
    data = await scrape_event_data(page, "http://example.com")
    assert data["title"] == "Event Title"
    assert data["url"] == "http://example.com"
