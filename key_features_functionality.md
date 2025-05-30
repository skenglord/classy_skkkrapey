## Key Features & Functionality

The project exhibits a comprehensive set of features and functionalities geared towards effective web scraping, data management, and accessibility:

1.  **Multi-Site Scraping Capabilities:**
    *   Supports scraping from both static content websites (`ticketsibiza.com`) and dynamic, JavaScript-rendered websites (`ibiza-spotlight.com`).
    *   Employs `requests` and `BeautifulSoup` for static sites, and `Playwright` for dynamic sites, demonstrating adaptability to different web technologies.
    *   Site-specific logic is encapsulated in dedicated scraper classes (`TicketsIbizaScraper`, `IbizaSpotlightScraper`).

2.  **Robust Scraping Engine:**
    *   **Configurable Actions:** Allows for both `scrape` (single page) and `crawl` (listing page to find multiple event URLs) actions.
    *   **User-Agent Rotation:** Automatically rotates User-Agent strings to reduce the likelihood of being blocked.
    *   **Request Delays:** Implements configurable random delays between requests to avoid overloading target servers.
    *   **Multi-Layered Data Extraction:** For `ticketsibiza.com`, it attempts to parse structured data (JSON-LD, Microdata) before falling back to generic HTML parsing, increasing data accuracy.
    *   **Refined Link Filtering:** The `IbizaSpotlightScraper` includes logic to differentiate event detail links from calendar navigation links.

3.  **Data Storage and Management:**
    *   **MongoDB Integration:** Utilizes MongoDB for storing scraped event data, suitable for handling structured and semi-structured information.
    *   **Defined Schema:** Employs Pydantic-like `TypedDict` schemas (`EventSchema`, `LocationSchema`, etc.) for structuring event data within the scraper, which is then translated to the MongoDB documents.
    *   **Data Migration Scripts:** Includes scripts for migrating existing JSON data into the MongoDB structure (`database/data_migration.py`).

4.  **Data Quality Assurance:**
    *   **Quality Scoring System:** A significant feature is the built-in system for calculating quality scores for various aspects of the event data (e.g., title, location, date/time).
    *   **Quality-Based Filtering:** The API allows consumers to filter events based on a minimum overall quality score.
    *   **Validation Metadata:** The database schema is designed to store validation flags and confidence scores for different data fields.

5.  **FastAPI-Based API Server:**
    *   **RESTful API:** Provides a RESTful API for accessing the event data.
    *   **Rich Querying Capabilities:**
        *   Filter events by minimum quality score.
        *   Filter events by venue.
        *   Filter for future events only.
        *   Full-text search for events.
        *   List all venues and events for a specific venue.
        *   Retrieve upcoming events within a specified number of days.
    *   **Data Validation:** Leverages FastAPI's Pydantic integration for automatic request and response data validation.
    *   **API Documentation:** Automatically generates interactive API documentation (Swagger UI/OpenAPI) via FastAPI.
    *   **Event Refresh Endpoint:** Includes an endpoint to mark an event for re-scraping.

6.  **Output and Reporting:**
    *   The scraper can save output as JSON and Markdown files.
    *   The API provides statistical endpoints for data quality and venue summaries.

7.  **Development and Maintenance Support:**
    *   **Command-Line Interface:** The scraper is configurable and runnable via a CLI (`argparse`).
    *   **Logging:** Comprehensive logging is implemented throughout the scraper and API server.
    *   **Modularity:** Code is organized into distinct modules and classes.
    *   **Dependency Management:** `requirements.txt` for runtime and `requirements-dev.txt` for development/testing tools (like `pytest` and `Sphinx`).
    *   **Google Sheets Export:** Includes functionality to export event data to Google Sheets.
