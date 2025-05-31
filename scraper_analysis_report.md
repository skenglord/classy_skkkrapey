# Scraper Component Analysis Report

This report analyzes various scraper components within the `my_scrapers/` directory, focusing on their reusability, robustness, and effectiveness with minimal configuration. The goal is to identify components for modularization and potential candidates for deletion.

## Evaluation Criteria:

*   **Reusability:** How easily can this method/component be extracted and used in other scrapers? (Score: 1-5, 5 being highly reusable)
*   **Robustness:** How well does it handle errors and unexpected situations? (Score: 1-5, 5 being highly robust)
*   **Effectiveness & Configurability:** How well does it perform its intended function, and how little site-specific setup does it require to be useful? (Score: 1-5, 5 being highly effective and easily configurable)
*   **Overall Recommendation:** Brief note on whether to keep, refactor for reusability, or delete.

---

## 1. `classy_skkkrapey.py`

### Scraping Methods
*   `fetch_page` (in `BaseEventScraper`)
    *   Reusability: 4 (Generic fetching logic for both requests and Playwright. Tightly coupled with BaseEventScraper's session/browser management, but core logic is reusable.)
    *   Robustness: 4 (Handles basic request/Playwright errors, includes retries for requests. Playwright part can be fragile if site structure changes drastically or anti-bot measures are strong.)
    *   Effectiveness & Configurability: 4 (Effectively fetches HTML. `use_browser_override` provides good configurability. UA rotation is a basic stealth measure.)
    *   Overall: Strong candidate for refactoring into a generic fetching utility.
*   `scrape_event_data` (in `IbizaSpotlightScraper` - primarily fetching/orchestration, minimal parsing)
    *   Reusability: 1 (Highly specific to Ibiza Spotlight structure and logic.)
    *   Robustness: 2 (Basic error handling. Relies on Playwright fetch succeeding and specific title selectors.)
    *   Effectiveness & Configurability: 2 (Extracts only title and hardcoded values. Not configurable for other fields or sites.)
    *   Overall: Site-specific scraping orchestrator. Parsing logic is not reusable.

### Crawling Methods
*   `crawl_listing_for_events` (for `IbizaSpotlightScraper`)
    *   Reusability: 2 (While the filtering logic has some generic ideas, the initial selector `a[href*='/night/events/']` and the base path `/night/events/` are specific to Ibiza Spotlight.)
    *   Robustness: 3 (Relies on Playwright successfully rendering the page. Filtering logic is fairly robust for the specific URL patterns it targets but could be broken by site changes.)
    *   Effectiveness & Configurability: 3 (Effective for Ibiza Spotlight. The core path `/night/events/` is hardcoded, limiting direct configurability for other sites.)
    *   Overall: Keep for IbizaSpotlightScraper; filtering logic might offer patterns for a more generic crawler but needs significant abstraction.
*   `crawl_listing_for_events` (for `TicketsIbizaScraper`)
    *   Reusability: 2 (Selector `a.tribe-events-calendar-list__event-title-link` is highly specific to TicketsIbiza.)
    *   Robustness: 3 (Basic error handling for request failures. Relies on stable site structure for the selector.)
    *   Effectiveness & Configurability: 3 (Effective for its specific site. Not configurable without code changes.)
    *   Overall: Keep for TicketsIbizaScraper; site-specific.

### Parsing Methods
*   `_parse_json_ld` (`TicketsIbizaScraper`)
    *   Reusability: 4 (Parses standard MusicEvent JSON-LD. The specific fields it extracts into `EventSchema` are common, but mapping to a *different* schema would require changes. Good for general JSON-LD `MusicEvent`.)
    *   Robustness: 4 (Handles missing script tags, non-MusicEvent types, JSON decode errors, and missing attributes within the JSON-LD via `.get()` and default values. Unit tests confirm this.)
    *   Effectiveness & Configurability: 4 (Effective for standard `MusicEvent` JSON-LD. Not directly configurable for different schemas/types without code changes.)
    *   Overall: Highly reusable for `MusicEvent` JSON-LD. Could be part of a generic structured data parsing module.
*   `_parse_microdata` (`TicketsIbizaScraper`)
    *   Reusability: 3 (Parses basic schema.org/MusicEvent microdata. The current implementation is simplified and makes assumptions like event name being venue name, which limits broader reusability.)
    *   Robustness: 2 (Basic check for `event_scope` and `title`. Does not deeply handle missing optional itemprops. Unit tests show it doesn't extract many fields like description, lineup, offers.)
    *   Effectiveness & Configurability: 2 (Effective for very simple MusicEvent microdata. Not very configurable for variations in microdata structure without code changes.)
    *   Overall: Limited current utility due to simplified parsing. Potential for a more robust, reusable microdata parser exists but this version is basic.
*   `_parse_html_fallback` (`TicketsIbizaScraper`)
    *   Reusability: 1 (Selector `h1.entry-title` is highly specific to TicketsIbiza.)
    *   Robustness: 2 (Only checks for the title tag. No other error handling.)
    *   Effectiveness & Configurability: 2 (Only extracts title. Not configurable.)
    *   Overall: Site-specific basic fallback. Minimal value beyond this site.
*   `format_event_to_markdown` (Utility function)
    *   Reusability: 5 (Takes a generic `EventSchema` dictionary and formats it. Highly reusable.)
    *   Robustness: 4 (Handles missing keys and `None` values gracefully. Unit tests confirm its specific N/A and line omission logic.)
    *   Effectiveness & Configurability: 4 (Effectively formats the defined `EventSchema`. The format is fixed but serves its purpose well. Not configurable for different markdown styles without code changes.)
    *   Overall: Excellent utility function. Highly recommended to keep and use as a standard formatter.

### Stealth Methods
*   `rotate_user_agent` & `_create_session` (`BaseEventScraper`)
    *   Reusability: 4 (Logic for session creation with retries and UA rotation is quite generic.)
    *   Robustness: 3 (Basic retry mechanism. UA rotation is basic stealth. No proxy support or advanced fingerprinting evasion.)
    *   Effectiveness & Configurability: 3 (Effective for basic anti-scraping measures. UA list is hardcoded but could be made configurable. Rotation interval is configurable.)
    *   Overall: Good foundational methods for session management and basic stealth. Could be part of a base utilities module.
*   Playwright Usage (via `fetch_page` in `BaseEventScraper` and default in `IbizaSpotlightScraper`)
    *   Reusability: N/A (Technology choice, applied in `fetch_page`.)
    *   Robustness: 3 (Helps with JS-heavy sites but can be slower, more resource-intensive, and subject to anti-Playwright measures.)
    *   Effectiveness & Configurability: 4 (Highly effective for JS rendering. Configurable via `headless` mode and `use_browser_override`.)
    *   Overall: Essential tool for specific sites. The integration pattern in `fetch_page` is good.

---

## 2. `mono_ticketmaster.py`

### Scraping Methods
*   `fetch_page` (in `MultiLayerEventScraper`)
    *   Reusability: 3 (Has both requests and Playwright logic. Playwright part is basic. Less refined than `classy_skkkrapey.BaseEventScraper.fetch_page`.)
    *   Robustness: 3 (Basic error handling for requests and Playwright. Session setup is reasonable.)
    *   Effectiveness & Configurability: 3 (Fetches content. `use_browser_for_this_fetch` offers some control. UA rotation is present but simpler than in `classy_skkkrapey`.)
    *   Overall: Decent, but `classy_skkkrapey.BaseEventScraper.fetch_page` is preferred. Somewhat redundant.
*   `scrape_event_data` (in `MultiLayerEventScraper` - overall orchestration)
    *   Reusability: 2 (Orchestrates extraction layers specific to its own methods and schema mapping.)
    *   Robustness: 3 (Depends on its sub-methods. Handles cases where HTML is not fetched.)
    *   Effectiveness & Configurability: 3 (Effective for its multi-layer approach. Not easily configurable for different layers or schemas without code change.)
    *   Overall: Concept is good; `classy_skkkrapey.TicketsIbizaScraper.scrape_event_data` is a more refined version.
*   `scrape_event_strategically` (in `MultiLayerEventScraper`)
    *   Reusability: 2 (Specific to trying requests then browser, tied to `is_data_sufficient` and its own `scrape_event_data`.)
    *   Robustness: 3 (Depends on sub-methods. The strategy itself is a robustness pattern.)
    *   Effectiveness & Configurability: 3 (Implements a useful strategy. `is_data_sufficient` is a basic control point.)
    *   Overall: Strategy is valuable. `classy_skkkrapey.BaseEventScraper.fetch_page` (with `use_browser_override`) offers a cleaner fetch strategy.

### Crawling Methods
*   `crawl_listing_for_events` (standalone function)
    *   Reusability: 2 (Specific to Playwright and a particular selector pattern `text=INFO`. Path for links is not configurable.)
    *   Robustness: 2 (Basic Playwright error handling. Selector is fragile.)
    *   Effectiveness & Configurability: 2 (Effective for the site it was implicitly designed for. `max_pages` is a config. Not easily adaptable.)
    *   Overall: Functionally specific and less robust than `classy_skkkrapey` crawlers. Redundant.

### Parsing Methods
*   `extract_jsonld_data` (in `MultiLayerEventScraper`)
    *   Reusability: 4 (Fairly generic JSON-LD extraction logic for MusicEvents, handles single events and graphs.)
    *   Robustness: 3 (Basic error handling for JSON parsing. Iterates through scripts and graph nodes.)
    *   Effectiveness & Configurability: 3 (Effective for common JSON-LD `MusicEvent` patterns.)
    *   Overall: Good. Similar, slightly more refined logic in `classy_skkkrapey.TicketsIbizaScraper._parse_json_ld`.
*   `extract_wordpress_data` (in `MultiLayerEventScraper`)
    *   Reusability: 2 (Targets common WordPress/WooCommerce CSS selectors. Might work on some WP sites but not universally.)
    *   Robustness: 2 (Relies on specific selectors being present. No complex error handling.)
    *   Effectiveness & Configurability: 2 (Can be effective if selectors match. Selectors are hardcoded.)
    *   Overall: Heuristic-based. Less reliable than structured data. Limited reusability.
*   `extract_meta_data` (in `MultiLayerEventScraper`)
    *   Reusability: 4 (Generic logic for extracting common Open Graph and meta description/keywords.)
    *   Robustness: 3 (Handles missing meta tags gracefully.)
    *   Effectiveness & Configurability: 4 (Effective for standard meta tags. Mappings are clear.)
    *   Overall: Useful generic function. Could be a standard utility.
*   `extract_text_patterns` (in `MultiLayerEventScraper`)
    *   Reusability: 2 (Regex patterns for dates/prices are somewhat generic but can be locale-specific or insufficient.)
    *   Robustness: 2 (Relies on regex matching; can easily miss or misinterpret data.)
    *   Effectiveness & Configurability: 2 (Can find simple patterns. Patterns are hardcoded.)
    *   Overall: Brittle, last-resort type of extraction.
*   `extract_lineup_from_html` (in `MultiLayerEventScraper`)
    *   Reusability: 1 (Highly specific regex and selector logic tailored to observed patterns on one site.)
    *   Robustness: 1 (Very fragile, likely to break with minor site changes.)
    *   Effectiveness & Configurability: 2 (Might work for the specific case it was built for.)
    *   Overall: Site-specific helper, not for general use.
*   `extract_ticket_url_from_html` (in `MultiLayerEventScraper`)
    *   Reusability: 1 (Highly specific regex and selector logic.)
    *   Robustness: 1 (Fragile.)
    *   Effectiveness & Configurability: 2 (Might work for specific cases.)
    *   Overall: Site-specific helper.
*   `_map_jsonld_to_event_schema` (in `MultiLayerEventScraper`)
    *   Reusability: 2 (Tied to its specific `EventSchemaTypedDict` and data structure from `extract_jsonld_data`.)
    *   Robustness: 3 (Extensive use of `.get()` provides some robustness.)
    *   Effectiveness & Configurability: 3 (Effectively transforms its input to its schema.)
    *   Overall: Internal mapping. `classy_skkkrapey` approach of parsing directly into its schema is cleaner.
*   `_map_fallback_to_event_schema` (in `MultiLayerEventScraper`)
    *   Reusability: 2 (Tied to its specific `EventSchemaTypedDict` and combined fallback data.)
    *   Robustness: 3 (Many `.get()` calls.)
    *   Effectiveness & Configurability: 3 (Transforms its input to its schema.)
    *   Overall: Internal mapping for fallback data.
*   `_populate_derived_fields` (in `MultiLayerEventScraper`)
    *   Reusability: 3 (Logic for deriving boolean/count fields could be somewhat generic if schema is standardized.)
    *   Robustness: 3 (Handles missing `ticketInfo` or `lineUp`.)
    *   Effectiveness & Configurability: 3 (Effectively populates these fields for its schema.)
    *   Overall: Useful helper logic.
*   `format_event_to_markdown` (standalone function in this file)
    *   Reusability: 4 (More complex and tied to `EventSchemaTypedDict` than `classy_skkkrapey` version.)
    *   Robustness: 3 (Many `.get()` calls.)
    *   Effectiveness & Configurability: 3 (Formats many fields. Format is fixed.)
    *   Overall: Redundant. The `format_event_to_markdown` in `classy_skkkrapey.py` is cleaner and preferred.

### Stealth Methods
*   `rotate_user_agent` & `_setup_session` (in `MultiLayerEventScraper`)
    *   Reusability: 3 (Similar to `classy_skkkrapey` but less refined. Session headers are more extensive.)
    *   Robustness: 3 (Basic retries, UA rotation.)
    *   Effectiveness & Configurability: 3 (UA list hardcoded. Rotation logic simpler.)
    *   Overall: Foundational; `classy_skkkrapey` versions are generally improvements or equivalent.
*   Playwright usage (in `fetch_page` and `crawl_listing_for_events`)
    *   Reusability: N/A (Technology choice.)
    *   Robustness: 2 (Playwright part in `fetch_page` is very basic, no page re-use. `crawl_listing_for_events` is also basic.)
    *   Effectiveness & Configurability: 3 (Effective for JS rendering if used. `headless` is configurable.)
    *   Overall: Basic Playwright integration. `classy_skkkrapey` offers more robust Playwright usage.

---

## 3. `mono_ticketmaster_with_db.py`
*(Focus on differences from `mono_ticketmaster.py`)*

The `MongoIntegratedEventScraper` class in this file inherits directly from `MultiLayerEventScraper` (defined in `mono_ticketmaster.py`).
The core scraping, parsing, and stealth methods (`fetch_page`, `scrape_event_data` orchestration, `extract_jsonld_data`, `extract_wordpress_data`, `extract_meta_data`, `extract_text_patterns`, `rotate_user_agent`, `_setup_session`, etc.) are **identical in their logic and implementation** to those analyzed in `mono_ticketmaster.py`. This file primarily wraps the existing scraping functionality with database interactions (MongoDB) and a quality scoring mechanism.

**Key new methods related to workflow (but not changing core scraping components):**
*   `scrape_and_save_event`: Calls the inherited `scrape_event_data` and adds DB saving.
*   `scrape_multiple_events`: Orchestrates scraping for multiple URLs.
*   `get_events_needing_update`: Queries DB, not a scraping component.

**Notable observations regarding scraper components:**
*   The schema mapping functions (`_map_jsonld_to_event_schema`, `_map_fallback_to_event_schema`) and `_populate_derived_fields` inherited from `MultiLayerEventScraper` are used as-is. The `EventSchemaTypedDict` is consistent.
*   The DB integration does not fundamentally alter how the individual scraping or parsing steps are performed by the parent class methods.

Therefore, the evaluation of the core scraper components is the same as for `mono_ticketmaster.py`. The additions here are application-level logic for data persistence and workflow management.

### Scraping Methods
*   (No new or significantly different core scraping methods compared to `MultiLayerEventScraper`)

### Crawling Methods
*   (No new or significantly different core crawling methods; `crawl_listing_for_events` would be used via an instance of `MongoIntegratedEventScraper` calling the standalone function from `mono_ticketmaster.py` if that pattern were followed, but this class focuses on scraping specific URLs.)

### Parsing Methods
*   (No new or significantly different core parsing methods compared to `MultiLayerEventScraper`)

### Stealth Methods
*   (No new or significantly different core stealth methods compared to `MultiLayerEventScraper`)

---

## 4. `ibiza_events_spider.py` (Scrapy Spider)

### Scraping Methods
*   `start_requests`
    *   Reusability: 2 (Specific to Scrapy's `scrapy.Request` and `scrapy-playwright` meta arguments. The URL is hardcoded for `ticketsibiza.com`.)
    *   Robustness: 3 (Playwright integration itself is for robustness on JS-heavy sites. `wait_for_selector` and `wait_for_function` add to this for the specific target. Error handling is Scrapy/Playwright's default.)
    *   Effectiveness & Configurability: 3 (Effective for the target page. Playwright methods are hardcoded; timeout is configurable but also hardcoded. Viewport size is set.)
    *   Overall: Standard Scrapy entry point. Playwright integration logic is specific but demonstrates a pattern.
*   Use of `response.follow` (in `parse` method)
    *   Reusability: 4 (Standard Scrapy method for following links. Very reusable within Scrapy projects.)
    *   Robustness: N/A (Method itself is robust; overall robustness depends on link extraction and server responses.)
    *   Effectiveness & Configurability: 4 (Effective for crawling. Callback and meta passing are standard Scrapy configurations.)
    *   Overall: Core Scrapy mechanism for crawling, used appropriately.

### Crawling Methods
*   Logic within `parse` (extracting INFO links)
    *   Reusability: 1 (CSS selector `a.wcs-btn` and text filter `'INFO'` are highly specific to `ticketsibiza.com`'s calendar view as rendered by its specific JS framework.)
    *   Robustness: 2 (Relies on specific CSS classes, text content, and JS rendering via Playwright. Will break if site changes these significantly.)
    *   Effectiveness & Configurability: 3 (Effective for its target. Not configurable without code changes.)
    *   Overall: Site-specific link extraction logic within a standard Scrapy parse method.

### Parsing Methods
*   `parse` (callback for the calendar/listing page)
    *   Reusability: 1 (As a whole method, specific to the task of finding 'INFO' links on `ticketsibiza.com` and triggering `parse_event`.)
    *   Robustness: 2 (Basic logging if no links found. Depends on `response.css`, Playwright rendering, and specific link structure.)
    *   Effectiveness & Configurability: 3 (Effective for its specific purpose on the target site.)
    *   Overall: Site-specific listing page processor.
*   `parse_event` (callback for individual event detail pages)
    *   Reusability: 1 (CSS selectors like `h1.tribe-events-single-event-title`, `.tribe-events-venue-details`, etc., are entirely specific to `ticketsibiza.com`'s event page structure and its "The Events Calendar" WordPress plugin.)
    *   Robustness: 2 (Uses `.get(default='')` which prevents errors if selectors don't find anything, but leads to empty/default data. Some regex parsing for date/price can be brittle. No deep error handling for missing sections. Relies on Playwright rendering.)
    *   Effectiveness & Configurability: 3 (Extracts a good range of data for the target site. Not configurable for other site structures without code changes.)
    *   Overall: Typical site-specific Scrapy item parsing logic. Tightly coupled to one site's specific HTML structure.

### Stealth Methods
*   User-Agent in `start_requests` headers
    *   Reusability: 5 (Setting a User-Agent is a universal concept.)
    *   Robustness: N/A (It's just a string; robustness depends on whether the UA is blocked.)
    *   Effectiveness & Configurability: 2 (A single hardcoded modern UA is used. Not rotated. Better than default Scrapy UA, but very basic.)
    *   Overall: Basic stealth. Less sophisticated than UA rotation in `BaseEventScraper` or `MultiLayerEventScraper`.
*   Playwright usage via `scrapy-playwright`
    *   Reusability: N/A (It's a middleware/technology choice integrated into Scrapy requests via `meta` tags.)
    *   Robustness: 3 (Handles JS rendering, which is robust against sites requiring JS. Adds complexity and potential points of failure compared to static requests. Subject to anti-Playwright measures.)
    *   Effectiveness & Configurability: 4 (Very effective for JS-heavy sites. Configurable through `meta` dict passed to `Request`, including specific Playwright `PageMethod` calls for fine-grained interaction.)
    *   Overall: Powerful tool for specific sites. The way it's configured in `start_requests` with `PageMethod` calls shows good control over browser actions.

---

## 5. `playwright_mistune_scraper.py`

This script uses `asyncio` and `playwright.async_api` for scraping. It appears to target `ticketsibiza.com`. The "Mistune" reference in the filename seems unrelated to its actual functionality of HTML scraping and basic Markdown generation.

### Scraping Methods
*   `scrape_event_data` (async function)
    *   Reusability: 2 (Playwright async logic for fetching a page and extracting a title is somewhat generic, but the locator `h1.post-title` is site-specific. Only extracts title, URL, and full HTML.)
    *   Robustness: 2 (Basic `try-except` for Playwright errors. Uses fixed timeouts. Relies on a specific selector for the title.)
    *   Effectiveness & Configurability: 2 (Effective only for extracting a title from a site matching the selector. URL is an argument. Not easily configurable for other data points or site structures without code changes.)
    *   Overall: Basic site-specific Playwright scraping function.

### Crawling Methods
*   Logic within `main` function (extracting INFO links from `ticketsibiza.com/ibiza-calendar/2025-events/`)
    *   Reusability: 1 (Targets a specific URL and uses Playwright locators `a:has-text("Info")` which are specific to that site's rendered HTML structure.)
    *   Robustness: 2 (Includes basic Playwright waits (`wait_for_selector`, `wait_for_timeout`). Relies on specific text and link structure; will break if these change.)
    *   Effectiveness & Configurability: 2 (Effective for the target page. Not configurable for other listing page structures or link patterns without code changes.)
    *   Overall: Site-specific crawling logic embedded directly in the main execution flow. Not designed as a reusable component.

### Parsing Methods
*   Embedded within `scrape_event_data` (title extraction: `await page.locator('h1.post-title', ...).inner_text()`)
    *   Reusability: 1 (The CSS selector `h1.post-title` is site-specific.)
    *   Robustness: 2 (Relies on the selector being present; timeout is handled by Playwright. No fallback if selector fails.)
    *   Effectiveness & Configurability: 2 (Extracts only the title text. Not configurable for other elements.)
    *   Overall: Very basic, site-specific parsing for a single field. The script also formats a simple Markdown output in `main`, but this is not a generalized parsing component for `EventSchema`.
*   (No other distinct parsing methods or helpers for structured data extraction like JSON-LD, Microdata, etc.)

### Stealth Methods
*   Playwright Usage (general)
    *   Reusability: N/A (This refers to the use of the Playwright library itself.)
    *   Robustness: 3 (Standard Playwright async usage provides robustness against basic anti-scraping that blocks simple HTTP requests, good for JS-heavy sites. However, it's still detectable.)
    *   Effectiveness & Configurability: 3 (Effective for rendering JavaScript. `headless=False` is used in `main` (atypical for production). Timeouts are used. No advanced stealth like UA rotation, proxy usage, or anti-fingerprinting measures are evident beyond default Playwright capabilities.)
    *   Overall: Standard Playwright usage. The other scrapers (`classy_skkkrapey`, `mono_ticketmaster`) demonstrate more explicit (though still basic) stealth features like UA rotation.

---

## 6. `mono_basic_html.py`

This scraper provides basic HTML fetching and data extraction capabilities using CSS selectors and XPath expressions. It does not use Playwright.

### Scraping Methods
*   `fetch_page` (in `BasicHTMLScraper`)
    *   Reusability: 4 (Generic `requests`-based HTML fetching. Simpler than `classy_skkkrapey.BaseEventScraper.fetch_page` as it lacks Playwright, but highly reusable for static sites.)
    *   Robustness: 3 (Includes session setup with retries. Basic error handling for request exceptions, returns `None` on failure.)
    *   Effectiveness & Configurability: 4 (Effectively fetches static HTML. Timeout is fixed at 10s. User-Agent is hardcoded but modern.)
    *   Overall: A good, simple, reusable requests-based fetcher for static content.

### Crawling Methods
*   (N/A - This scraper is designed for single-page extraction via its `scrape` method, not for crawling/discovering new links.)

### Parsing Methods
*   `extract_css` (in `BasicHTMLScraper`)
    *   Reusability: 5 (Highly reusable. Takes an HTML string and a list of CSS selectors as input, returns a dictionary of extracted text lists. No site-specific logic.)
    *   Robustness: 4 (Relies on BeautifulSoup's HTML parsing. Handles cases where selectors don't match by returning empty lists for those selectors. Assumes valid HTML input for BeautifulSoup.)
    *   Effectiveness & Configurability: 5 (Very effective for CSS-based text extraction. Highly configurable as selectors are passed as arguments. Unit tests confirm its behavior.)
    *   Overall: Excellent, highly reusable component for CSS extraction. A core, valuable function.
*   `extract_xpath` (in `BasicHTMLScraper`)
    *   Reusability: 5 (Highly reusable. Takes an HTML string and a list of XPath expressions, returns a dictionary of extracted text/attribute lists. No site-specific logic other than the XPaths themselves.)
    *   Robustness: 4 (Relies on `lxml`'s HTML parsing. Handles XPaths not finding nodes by returning empty lists. Raises `RuntimeError` if `lxml` is not available, and `lxml.etree.ParserError` for empty HTML, both of which are tested.)
    *   Effectiveness & Configurability: 5 (Very effective for XPath-based extraction. Highly configurable as XPaths are passed as arguments. Unit tests confirm its behavior.)
    *   Overall: Excellent, highly reusable component for XPath extraction, contingent on the availability of `lxml`.

### Stealth Methods
*   `_setup_session` (in `BasicHTMLScraper`)
    *   Reusability: 4 (Generic `requests.Session` setup with retries and a User-Agent can be reused.)
    *   Robustness: 3 (Standard retry mechanism from `urllib3`. Uses a single, hardcoded User-Agent, which is a very basic form of stealth and not rotated.)
    *   Effectiveness & Configurability: 3 (Effective as a basic session setup for simple sites. User-Agent is not configurable from outside nor rotated.)
    *   Overall: Solid basic session setup. `classy_skkkrapey.BaseEventScraper` provides more advanced User-Agent rotation.

---

## 7. `mono_ibiza_spotlight_patched.py`

This script is designed to scrape events from `www.ibiza-spotlight.com/night/events`. It has a `SpotlightScraper` class with a JSON-first approach (fetching calendar data) and falling back to HTML parsing with Playwright. It uses a simple `Event` dataclass.

### Scraping Methods
*   `fetch_page` (in `SpotlightScraper`):
    *   Reusability: 2 (Logic to derive JSON URL from HTML URL is specific to Ibiza Spotlight. Fallback to `_fetch_html` is a good pattern, but overall method is site-specific.)
    *   Robustness: 3 (Handles JSON fetch failure by falling back to HTML. Relies on Playwright for HTML.)
    *   Effectiveness & Configurability: 3 (Effective for its dual strategy on Spotlight. Not easily configurable for other sites.)
    *   Overall: Site-specific fetching strategy. The idea of trying JSON then HTML is good.
*   `_fetch_json` (in `SpotlightScraper`):
    *   Reusability: 3 (Generic JSON fetching with requests session. URL construction is external.)
    *   Robustness: 3 (Basic error handling, falls back to HTML fetch.)
    *   Effectiveness & Configurability: 3 (Effective for fetching JSON if URL is correct.)
    *   Overall: Standard JSON fetching.
*   `_fetch_html` (in `SpotlightScraper`):
    *   Reusability: 3 (Generic Playwright HTML fetching logic. Uses `domcontentloaded`, default timeout, resource blocking. More refined than `mono_ticketmaster.py` Playwright fetch.)
    *   Robustness: 4 (Includes timeout handling and DOM snapshot on error, which is good for debugging.)
    *   Effectiveness & Configurability: 3 (Effective for rendering JS-heavy pages. Headless mode is configurable. Resource blocking improves speed.)
    *   Overall: A decent, more robust Playwright fetcher compared to earlier scripts. Similar to `classy_skkkrapey.BaseEventScraper.fetch_page`'s Playwright path but simpler context management.

### Crawling Methods
*   `crawl` (in `SpotlightScraper`):
    *   Reusability: 2 (Hardcoded URL format for Ibiza Spotlight month/year. Orchestrates fetching and parsing for that site.)
    *   Robustness: 3 (Depends on `fetch_page` and `_parse_events`.)
    *   Effectiveness & Configurability: 3 (Effective for crawling the specific Spotlight calendar structure by month/year.)
    *   Overall: Site-specific crawling orchestration.

### Parsing Methods
*   `_parse_events` (in `SpotlightScraper`):
    *   Reusability: 2 (Handles two types of input: JSON from Spotlight's calendar endpoint, or HTML. The JSON parsing part is specific to that endpoint's structure. HTML parsing part is specific to Spotlight's event item HTML.)
    *   Robustness: 3 (Tries JSON, then HTML. JSON parsing checks for type and URL. HTML parsing has basic try-except for item processing.)
    *   Effectiveness & Configurability: 3 (Effective for Spotlight. The dual parsing strategy is good. Uses `RE_LISTING` to filter.)
    *   Overall: Site-specific parser with a smart dual-source strategy.
*   `_parse_events_html` (in `SpotlightScraper`):
    *   Reusability: 1 (CSS selectors `li.event-item`, `h3`, `a[href]` and `data-date` attribute are specific to Ibiza Spotlight's HTML structure for event listings.)
    *   Robustness: 2 (Basic try-except in loop. Relies on specific HTML structure.)
    *   Effectiveness & Configurability: 2 (Effective for its target HTML. Not configurable.)
    *   Overall: Site-specific HTML parsing logic.
*   `Event.from_calendar_json` (classmethod):
    *   Reusability: 2 (Specific to the structure of Ibiza Spotlight's calendar JSON.)
    *   Robustness: 2 (Uses `.get()` for resilience against missing keys.)
    *   Effectiveness & Configurability: 3 (Effectively maps known JSON fields to its simple `Event` dataclass.)
    *   Overall: Simple data mapping for a specific JSON structure.

### Stealth Methods
*   Session User-Agent (in `SpotlightScraper.__init__`):
    *   Reusability: 5 (Setting a UA is universal.)
    *   Robustness: N/A.
    *   Effectiveness & Configurability: 2 (Single hardcoded Firefox UA. No rotation.)
    *   Overall: Very basic.
*   Playwright Configuration (in `_ensure_browser`):
    *   Reusability: 3 (Pattern for lazy-initializing Playwright and setting default timeout / resource blocking is reusable.)
    *   Robustness: N/A (Configuration aspects.)
    *   Effectiveness & Configurability: 4 (Default timeout, resource blocking, and headed mode are good configurations for effectiveness and debugging.)
    *   Overall: Good Playwright setup pattern. More advanced than basic Playwright usage in `mono_ticketmaster.py`.

---

## 8. `unified_scraper.py`

This script, "Unified Ibiza Spotlight Event Scraper", is specifically tailored for `ibiza-spotlight.com` and uses Playwright for all interactions. It features modes for scraping single event pages and crawling monthly calendars with weekly pagination handling. It introduces more refined Playwright interactions like simulated human clicks and overlay handling, and a unique Markdown generation fallback using `mistune` on cleaned HTML text. It uses its own `Event` dataclass.

### Scraping Methods
*   `fetch_page_html` (in `IbizaSpotlightUnifiedScraper`)
    *   Reusability: 2 (Playwright logic for fetching, handling overlays, and waiting for selectors is somewhat generic but tailored by its internal calls like `_handle_overlays` and `_human_click`. Tied to this class structure and site-specific configurations like `BASE_URL`.)
    *   Robustness: 4 (Includes timeout handling, overlay handling, and waits for specific content selectors. More robust than basic Playwright fetches in other scripts.)
    *   Effectiveness & Configurability: 3 (Effective for JS-heavy pages for Ibiza Spotlight. User-Agent is randomized from a list. `wait_for_content_selector` offers some config. Timeout is configurable globally in constructor.)
    *   Overall: A robust Playwright page fetching method for its target site. The overlay and human click helpers contribute to this.
*   `scrape_single_event` (in `IbizaSpotlightUnifiedScraper`)
    *   Reusability: 1 (Orchestrates `fetch_page_html` and parsing specifically for Ibiza Spotlight event pages. Relies on internal parsing methods with hardcoded selectors.)
    *   Robustness: 3 (Depends on `fetch_page_html` and parsing. The fallback to generating Markdown from cleaned HTML text via `mistune` is a unique robustness strategy, though `mistune` is for rendering Markdown, not parsing HTML to structured data.)
    *   Effectiveness & Configurability: 2 (Highly specific to Ibiza Spotlight's structure. Selectors are hardcoded within `_parse_event_detail_page_content`.)
    *   Overall: Site-specific orchestration for scraping one event, with an interesting, if slightly misused, fallback.

### Crawling Methods
*   `crawl_calendar` (in `IbizaSpotlightUnifiedScraper`)
    *   Reusability: 1 (Hardcoded URL structure for Ibiza Spotlight calendar, specific pagination logic via `_handle_calendar_pagination` and link extraction via `_extract_event_links_from_calendar`.)
    *   Robustness: 3 (Depends on the success of its sub-methods for fetching, link extraction, and pagination, each of which has specific error handling or fragility.)
    *   Effectiveness & Configurability: 2 (Effective for its target calendar structure. Year/month are parameters, but core logic is site-specific.)
    *   Overall: Site-specific crawling orchestration for Ibiza Spotlight.
*   `_extract_event_links_from_calendar` (in `IbizaSpotlightUnifiedScraper`)
    *   Reusability: 1 (Selectors and link filtering logic are specific to Ibiza Spotlight calendar's HTML structure and URL patterns.)
    *   Robustness: 2 (Relies on specific HTML structure and CSS selectors. Includes fallback selectors. Saves snapshot on no links, which aids debugging.)
    *   Effectiveness & Configurability: 2 (Effective for its target. Not configurable without code changes.)
    *   Overall: Site-specific link extraction tailored to Ibiza Spotlight.
*   `_handle_calendar_pagination` (in `IbizaSpotlightUnifiedScraper`)
    *   Reusability: 1 (Highly specific to Ibiza Spotlight's desktop and mobile pagination UI elements and logic for determining active/next week.)
    *   Robustness: 2 (Attempts to handle both mobile and desktop, uses timeouts. Can be fragile to minor UI changes on the target site.)
    *   Effectiveness & Configurability: 2 (Effective for the target site's pagination. Not configurable.)
    *   Overall: Very site-specific pagination logic, demonstrating deep interaction with a specific calendar UI.

### Parsing Methods
*   `_parse_event_detail_page_content` (in `IbizaSpotlightUnifiedScraper`)
    *   Reusability: 1 (The dictionary of CSS selectors is hardcoded and specific to Ibiza Spotlight event detail pages. Date/time/price parsing logic is also tailored.)
    *   Robustness: 2 (Uses `soup.select_one` which returns `None` if not found, preventing some errors. Basic regex for date/time/price can be brittle. Returns `None` only if very little data is found, otherwise returns partial data.)
    *   Effectiveness & Configurability: 2 (Designed for Ibiza Spotlight. Selectors are internal and not easily changed without code modification.)
    *   Overall: Site-specific HTML parsing logic for event details.
*   `_parse_html_to_markdown_fallback` (in `IbizaSpotlightUnifiedScraper`)
    *   Reusability: 2 (The use of `cleanup_html` and then `mistune` (a Markdown parser) on `soup.get_text()` is an unusual approach. `cleanup_html` might be reusable if generic enough. The idea of a text-dump fallback is somewhat generic, but `mistune` here is likely misused – it's for parsing Markdown text, not generating it from arbitrary plain text derived from HTML.)
    *   Robustness: 2 (Depends heavily on the quality of `cleanup_html` and how well `mistune` handles arbitrary text. Likely to produce poor quality "Markdown" that is mostly just plain text.)
    *   Effectiveness & Configurability: 1 (Unlikely to be effective at producing structured or useful Markdown from general HTML text. `mistune` is not designed for this.)
    *   Overall: An experimental fallback. The `cleanup_html` utility is the more interesting part. Using `mistune` on plain text is not standard.

### Stealth Methods
*   `_ensure_browser` & Playwright setup (in `IbizaSpotlightUnifiedScraper`)
    *   Reusability: 3 (General pattern for initializing Playwright, context, and page, including UA randomization and resource blocking, is reusable.)
    *   Robustness: 3 (Standard Playwright setup. Includes re-initialization if browser is disconnected.)
    *   Effectiveness & Configurability: 4 (Sets UA from a list, blocks common resource types, configurable headless mode. Default timeouts are set on context.)
    *   Overall: Good Playwright setup pattern, more robust than in `mono_ibiza_spotlight_patched.py` due to browser check.
*   `_human_click` (in `IbizaSpotlightUnifiedScraper`)
    *   Reusability: 4 (Attempts to simulate more human-like clicks with random offsets and mouse movements. Logic is generic for Playwright `Locator` objects.)
    *   Robustness: 3 (Includes fallbacks to direct Playwright click if bounding box detection fails or other errors occur. Uses timeouts.)
    *   Effectiveness & Configurability: 3 (Potentially more effective at avoiding some bot detection than direct `.click()`. Delays are somewhat hardcoded but based on class min/max delay.)
    *   Overall: Interesting and potentially reusable component for more robust Playwright interactions.
*   `_handle_overlays` (in `IbizaSpotlightUnifiedScraper`)
    *   Reusability: 3 (The list of common overlay CSS selectors provides a decent starting point for generic overlay handling. Logic to iterate and click is reusable. Basic iframe check included.)
    *   Robustness: 2 (Relies on common selectors. May not handle all types of overlays, especially those with dynamic/obfuscated class names or complex interactions. Quick visibility check might miss some.)
    *   Effectiveness & Configurability: 3 (Can handle many common cookie banners/overlays. Selectors are hardcoded but could be parameterized.)
    *   Overall: Good attempt at a generic overlay handler; a useful pattern for Playwright scripts.
*   Random delays (`_get_random_delay`)
    *   Reusability: 5 (Standard utility for adding random delays.)
    *   Robustness: 5 (Simple and effective; no error modes.)
    *   Effectiveness & Configurability: 4 (Min/max delays are class attributes, allowing some configuration. Multiplier provides call-site control.)
    *   Overall: Standard and good practice for mimicking human browsing speed.

---

## 9. `fixed_scraper.py`

This script, "Enhanced Ibiza Spotlight Event Scraper (v4.0) - Professional Grade", is another iteration specifically for `www.ibiza-spotlight.com`. It emphasizes a "rewritten parsing logic to match the site's row-based structure" and uses `playwright-stealth` along with "human-like interactions". It defines its own `Event` dataclass.

### Scraping Methods
*   `fetch_page_html` (in `IbizaSpotlightScraper`)
    *   Reusability: 2 (Playwright logic is somewhat generic, but tailored with specific waits like for `#PartyCalBody` and use of `playwright-stealth`. Site-specific focus.)
    *   Robustness: 4 (Integrates `playwright-stealth`, overlay handling, specific waits for content, and saves DOM snapshot on timeout. This is quite robust for its target.)
    *   Effectiveness & Configurability: 3 (Effective for Ibiza Spotlight. Headless mode configurable. UA randomized. Delays configurable.)
    *   Overall: A robust, site-specific Playwright fetcher with enhanced stealth and debugging.

### Crawling Methods
*   `crawl_month` (in `IbizaSpotlightScraper`)
    *   Reusability: 1 (Hardcoded URL structure for Ibiza Spotlight calendar. Orchestrates `fetch_page_html` and the specialized `parse_html_events`.)
    *   Robustness: 3 (Depends on the success of `fetch_page_html` and `parse_html_events`.)
    *   Effectiveness & Configurability: 2 (Effective for the target site's specific calendar structure. Year/month are parameters, but core logic is site-specific.)
    *   Overall: Site-specific crawling orchestration, notable for its unique row-based parsing strategy.

### Parsing Methods
*   `parse_html_events` (in `IbizaSpotlightScraper`)
    *   Reusability: 1 (The logic of iterating venue rows (`.partyCal-row`), then day cells (`li.partyCal-day`), using date headers (`.partyCal-head li a`), and then calling `Event.from_html` is extremely specific to the Ibiza Spotlight calendar's unique HTML table/row layout.)
    *   Robustness: 2 (Highly dependent on the stability of complex and specific CSS selectors and HTML structure. Errors in date parsing or card parsing are handled per item, which is good, but the overall structure must match.)
    *   Effectiveness & Configurability: 3 (Likely effective for the very specific row-based layout it targets. Not configurable for other layouts.)
    *   Overall: This is the core "fixed" or specialized parsing strategy for Ibiza Spotlight's unique calendar. Highly site-specific.
*   `Event.from_html` (classmethod)
    *   Reusability: 1 (CSS selectors like `h3.h3 a.trackEventSpotlight`, `time`, `.price`, `.partyDj a` are specific to the event cards within the Ibiza Spotlight calendar rows/cells.)
    *   Robustness: 2 (Basic try-except `Exception` for parsing an individual card. Relies on the specific card structure holding up.)
    *   Effectiveness & Configurability: 3 (Effective for its target card structure. Not configurable.)
    *   Overall: Site-specific parser for individual event items within the row-based calendar.
*   `Event._parse_time`, `Event._parse_price` (staticmethods)
    *   Reusability: 3 (Regex for time `(\d{1,2}):(\d{2})` and price `\d+\.?\d*` are somewhat generic but might need adjustment for different formats or more complex price strings with ranges/text.)
    *   Robustness: 2 (Basic regex matching. Price parsing handles common currency symbols but might be fragile with varied formats. Time parsing is simple for HH:MM.)
    *   Effectiveness & Configurability: 3 (Effective for simple HH:MM times and common price formats. Not highly configurable without changing regex.)
    *   Overall: Simple helper methods for common data type parsing; could be part of a utility library if made more robust.

### Stealth Methods
*   `_ensure_browser` & Playwright setup (using `playwright-stealth`)
    *   Reusability: 3 (General pattern for initializing Playwright with `playwright-stealth` is reusable.)
    *   Robustness: 4 (Using `playwright-stealth` significantly improves robustness against bot detection compared to vanilla Playwright.)
    *   Effectiveness & Configurability: 4 (Applies `playwright-stealth`. Configurable headless mode. Random UA from a list.)
    *   Overall: Strong Playwright setup incorporating a dedicated stealth library. This is a good pattern.
*   `human_click` (in `IbizaSpotlightScraper`)
    *   Reusability: 4 (Attempts to simulate more human-like clicks with random offsets and mouse movements. Logic is generic for Playwright `Locator` objects.)
    *   Robustness: 3 (Includes fallbacks to direct Playwright click if bounding box detection fails or other errors occur. Uses timeouts.)
    *   Effectiveness & Configurability: 3 (Potentially more effective at avoiding some bot detection than direct `.click()`. Delays are somewhat hardcoded but based on class min/max delay.)
    *   Overall: A good reusable component for more robust Playwright interactions, similar to the one in `unified_scraper.py`.
*   `handle_overlays` (in `IbizaSpotlightScraper`)
    *   Reusability: 3 (The list of common overlay CSS selectors provides a decent starting point for generic overlay handling. Logic to iterate and click is reusable.)
    *   Robustness: 2 (Relies on common selectors. May not handle all types of overlays, especially those with dynamic/obfuscated class names or complex interactions. Uses `is_visible` with timeout.)
    *   Effectiveness & Configurability: 3 (Can handle many common cookie banners/overlays. Selectors are hardcoded but could be parameterized.)
    *   Overall: Good attempt at a generic overlay handler, similar to the one in `unified_scraper.py`.
*   Random delays (`_get_random_delay`)
    *   Reusability: 5 (Standard utility for adding random delays.)
    *   Robustness: 5 (Simple and effective; no error modes.)
    *   Effectiveness & Configurability: 4 (Min/max delays are class attributes, allowing some configuration. Multiplier provides call-site control.)
    *   Overall: Standard and good practice for mimicking human browsing speed.

---

## 10. `improved_scraping_execution.py`
*(Determine if it contains scraper components or is an execution script)*

This script is an **orchestration and execution script**, not a provider of new, fundamental scraper components (like page fetching or parsing logic). It imports `BaseEventScraper`, `EventSchema`, and `ScraperConfig` from `classy_skkkrapey.py` and is designed to work with instances of scrapers derived from `BaseEventScraper`.

**Core Purpose:**
The script defines a `ScrapingExecutor` class that takes a scraper instance and a configuration, then manages the execution of scraping or crawling tasks. It enhances the execution with features like:
*   Detailed progress tracking (`ScrapingProgress` dataclass).
*   Retry logic for scraping individual URLs (`_scrape_with_retry`).
*   Centralized error handling and reporting (`_handle_scraping_error`, `_save_error_report`).
*   URL validation (normalization, deduplication) before scraping (`_validate_urls`).
*   Optional concurrent scraping using `ThreadPoolExecutor` for multiple URLs (`_scrape_concurrent`).
*   Enhanced logging throughout the process.

**Evaluation as Scraper Components:**
Since this script primarily orchestrates and enhances the execution of other scraper components (defined in `classy_skkkrapey.py`), it doesn't offer new low-level scraping, parsing, or stealth methods for evaluation in the same way as the other scraper modules.

*   **Reusability:** The `ScrapingExecutor` class itself is highly reusable if one wants to add robust execution features around any scraper that conforms to the `BaseEventScraper` interface (i.e., has `scrape_event_data` and `crawl_listing_for_events` methods). Score: 4.
*   **Robustness:** It significantly enhances the robustness of a scraping *process* through retries, error logging, and potentially concurrent execution. Score: 4.
*   **Effectiveness & Configurability:** It's effective in managing complex scraping tasks. Configuration is via `ScraperConfig`. Score: 4.
*   **Overall Recommendation:** Keep. This provides valuable execution management logic that should ideally be integrated or used by the main application/CLI runner. It's not a scraper *component* per se, but an excellent *component manager/executor*.

### Scraping Methods
*   (N/A - Uses methods from the passed `scraper_instance`)

### Crawling Methods
*   (N/A - Uses methods from the passed `scraper_instance`)

### Parsing Methods
*   (N/A - Uses methods from the passed `scraper_instance`)

### Stealth Methods
*   (N/A - Relies on stealth features of the passed `scraper_instance`)

---

## Overall Synthesis & Recommendations

The scrapers in `my_scrapers/` show an evolution of techniques and approaches. Early scripts often mix orchestration, site-specific logic, and potentially reusable components. Later scripts like `classy_skkkrapey.py` and `mono_basic_html.py` demonstrate a move towards more modular and reusable base components, while `improved_scraping_execution.py` provides a good model for an orchestration layer. Several scripts tackle similar sites (Ibiza Spotlight, TicketsIbiza) with different strategies, leading to some redundancy.

*   **Highly Reusable Components:**
    *   **Fetching Logic:**
        *   `BaseEventScraper.fetch_page` (from `classy_skkkrapey.py`): Best all-around fetcher with dual requests/Playwright modes, UA rotation, and error handling. (Overall Score based on its analysis: 4)
        *   `BasicHTMLScraper.fetch_page` (from `mono_basic_html.py`): Good, simple `requests`-only fetcher for static sites. (Score: 4)
        *   Advanced Playwright Setup: Patterns from `mono_ibiza_spotlight_patched.py` (`_ensure_browser` with resource blocking), `unified_scraper.py` (`_ensure_browser` with UA randomization, `_handle_overlays`), and `fixed_scraper.py` (adding `playwright-stealth`, `human_click`) should be combined for a top-tier Playwright fetching utility.
    *   **Parsing Utilities:**
        *   `TicketsIbizaScraper._parse_json_ld` (from `classy_skkkrapey.py`): Robust and effective for standard `MusicEvent` JSON-LD. (Score: 4)
        *   `MultiLayerEventScraper.extract_meta_data` (from `mono_ticketmaster.py`): Good for generic OpenGraph/meta tag extraction. (Score: 4)
        *   `BasicHTMLScraper.extract_css` & `extract_xpath` (from `mono_basic_html.py`): Excellent, configurable general-purpose content extractors. (Score: 5)
        *   `format_event_to_markdown` (from `classy_skkkrapey.py`): Clean, robust, uses the preferred `EventSchema`. (Score: 5)
    *   **Stealth & Interaction Utilities:**
        *   Session Management: `BaseEventScraper._create_session` and `rotate_user_agent` (from `classy_skkkrapey.py`) provide a good base for `requests`.
        *   Playwright Interactions: `_human_click`, `_handle_overlays` (from `unified_scraper.py`, `fixed_scraper.py`) are valuable for robust Playwright scripting. `playwright-stealth` integration (from `fixed_scraper.py`) is crucial for Playwright's effectiveness.
        *   Delay Mechanism: `_get_random_delay` (from `unified_scraper.py`, `fixed_scraper.py`) is standard good practice.
    *   **Execution Orchestration:**
        *   `ScrapingExecutor` class (from `improved_scraping_execution.py`): Excellent framework for managing scraping tasks, retries, concurrency, and error reporting. Should be the standard way to run scrapers. (Score: 4 for reusability with compatible scraper interfaces)

*   **Redundant/Obsolete Methods & Scrapers:**
    *   **Fetching:** `mono_ticketmaster.py`'s `fetch_page` is largely superseded by `classy_skkkrapey.py`'s more robust and configurable version. `playwright_mistune_scraper.py`'s fetching is too basic.
    *   **Crawling:** The standalone `crawl_listing_for_events` in `mono_ticketmaster.py` is less robust and more site-specific than the class-based crawlers in `classy_skkkrapey.py`. The crawling logic embedded in `playwright_mistune_scraper.py`'s `main` is not reusable.
    *   **Parsing:**
        *   Many site-specific HTML parsing methods/selectors found in `mono_ticketmaster.py` (e.g., `extract_wordpress_data`, `extract_lineup_from_html`, `extract_ticket_url_from_html`), `ibiza_events_spider.py` (`parse_event` selectors), `playwright_mistune_scraper.py` (title selector), and `mono_ibiza_spotlight_patched.py` (`_parse_events_html`) are too brittle. These should be replaced by strategies prioritizing structured data (JSON-LD, Microdata) first, then falling back to highly configurable generic extractors (CSS/XPath from `mono_basic_html.py`) if necessary for specific sites.
        *   `mono_ticketmaster.py`'s `extract_jsonld_data` is good but `classy_skkkrapey.py`'s `_parse_json_ld` is slightly preferred.
        *   Schema mapping functions in `mono_ticketmaster.py` are tied to its specific, more complex `EventSchemaTypedDict`. The direct parsing into `EventSchema` in `classy_skkkrapey.py` is preferred.
        *   The `format_event_to_markdown` in `mono_ticketmaster.py` is redundant due to the superior and tested version in `classy_skkkrapey.py`.
    *   **Stealth:** Basic User-Agent settings in older/simpler scripts (e.g., `mono_ibiza_spotlight_patched.py`, `mono_basic_html.py`) are less advanced than rotation strategies or `playwright-stealth` integration.

*   **Priorities for Modularization:**
    *   **Core Scraper Library/Framework:**
        *   A generic `Fetcher` utility/class: Abstracting the best of `BaseEventScraper.fetch_page` (dual mode, UA rotation) and advanced Playwright techniques from `fixed_scraper.py`/`unified_scraper.py` (stealth, overlay handling, human-like clicks, robust page state waits, resource blocking).
        *   A `Parser` utility module:
            *   Standardized `parse_jsonld` (from `classy_skkkrapey.py`).
            *   An improved, more robust `parse_microdata` (current one in `classy_skkkrapey.py` is too basic).
            *   `extract_meta_tags` (from `mono_ticketmaster.py`).
            *   The `extract_css` and `extract_xpath` methods from `mono_basic_html.py` as core tools.
        *   A single, standardized `EventSchema` (likely based on `classy_skkkrapey.py`'s simpler version, extended as needed).
        *   Common Utilities: `format_event_to_markdown` (from `classy_skkkrapey.py`), `cleanup_html` (if proven robust, from `unified_scraper.py` context), delay mechanisms.
    *   **Site-Specific Scrapers:** These should become lightweight classes inheriting from a new common base (or using the core library components). Their main role would be to define site-specific configurations:
        *   Target URLs and URL patterns.
        *   Selectors/XPaths for any necessary HTML fallback parsing (using the generic CSS/XPath extractors).
        *   Logic to choose which parsing strategies to apply (e.g., JSON-LD first, then Microdata, then HTML).
    *   **Execution Framework:** `ScrapingExecutor` from `improved_scraping_execution.py` should be adopted/adapted as the standard way to run scraping tasks, providing concurrency, retries, progress tracking, and error reporting.

*   **Candidates for Deletion (or heavy refactoring to extract only unique, valuable logic):**
    *   **`mono_ticketmaster.py`**: Largely superseded by `classy_skkkrapey.py` and `mono_basic_html.py` for its reusable parts. Its `extract_meta_data` is worth salvaging.
    *   **`mono_ticketmaster_with_db.py`**: Logic for DB interaction is separate from scraping components. If `mono_ticketmaster.py` is deprecated, this follows. Quality scoring could be a separate module.
    *   **`playwright_mistune_scraper.py`**: Basic, site-specific, little reusable value. "Mistune" aspect seems a misnomer.
    *   **`ibiza_events_spider.py`**: Its Scrapy-specific implementation for `ticketsibiza.com` is likely redundant if `classy_skkkrapey.TicketsIbizaScraper` (which also handles this site with Playwright for dynamic content) is sufficiently robust. The Scrapy/Playwright integration patterns are noted but may not be needed if a unified non-Scrapy framework is pursued.
    *   **`mono_ibiza_spotlight_patched.py`**: An evolutionary step for scraping Ibiza Spotlight. Its JSON-first strategy and Playwright setup are good, but `classy_skkkrapey.IbizaSpotlightScraper` along with advanced techniques from `unified_scraper.py` and `fixed_scraper.py` should form the basis of the final Spotlight scraper.
    *   **`unified_scraper.py` & `fixed_scraper.py`**: These are advanced, site-specific implementations for Ibiza Spotlight. Their value is in the techniques they demonstrate (human clicks, overlay handling, specific parsing logic for Spotlight's row/card structure, `playwright-stealth`). These techniques should be evaluated and potentially merged into a refined, single Ibiza Spotlight scraper (likely an evolution of `classy_skkkrapey.IbizaSpotlightScraper`) or into the core Playwright utility class, rather than existing as standalone monolithic scripts. If their specific parsing logic for Spotlight's unique calendar structure is still the most effective, that part is valuable but it's highly site-specific.
