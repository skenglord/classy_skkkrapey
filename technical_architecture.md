## Technical Architecture

The project is built using a modern Python stack and is composed of several key components that work together to achieve its objectives.

1.  **Core Technologies:**
    *   **Programming Language:** Python (version 3.9+ indicated by type hints and syntax).
    *   **Web Scraping & Parsing:**
        *   `requests`: For making HTTP requests to fetch HTML content from static websites.
        *   `BeautifulSoup4`: For parsing HTML and XML content.
        *   `Playwright`: For browser automation, used to scrape dynamic, JavaScript-heavy websites by rendering them in a headless browser (Chromium by default).
    *   **Database:**
        *   `MongoDB`: A NoSQL document database used to store the scraped event data.
        *   `pymongo`: The synchronous Python driver for interacting with MongoDB.
        *   `motor`: An asynchronous Python driver for MongoDB (listed in requirements, but `api_server.py` primarily uses synchronous `pymongo`).
    *   **API Development:**
        *   `FastAPI`: A modern, high-performance web framework for building RESTful APIs.
        *   `uvicorn`: An ASGI (Asynchronous Server Gateway Interface) server used to run the FastAPI application.
    *   **Data Validation & Serialization:**
        *   `Pydantic`: Used extensively by FastAPI for data validation, serialization, and settings management. `TypedDict` is also used in the scraper for schema definition.
    *   **Development & Testing:**
        *   `pytest`: A testing framework (listed in dev requirements).
        *   `Sphinx`: For documentation generation (listed in dev requirements).

2.  **System Components:**

    *   **A. Scraper Engine (`my_scrapers/classy_skkkrapey.py`):**
        *   **Design:** A monolithic script architected with an object-oriented approach. It features a `BaseEventScraper` class providing common functionalities and site-specific derived classes (`TicketsIbizaScraper`, `IbizaSpotlightScraper`).
        *   **Execution Flow:** Can be run via CLI. It takes a URL and an action (`crawl` or `scrape`).
            *   `crawl`: Fetches a listing page, identifies event URLs using site-specific logic (and Playwright for dynamic pages), and then scrapes each identified event URL.
            *   `scrape`: Fetches and extracts data from a single event page.
        *   **Data Extraction:** Uses a combination of JSON-LD parsing, Microdata parsing, and direct HTML element selection via CSS selectors.
        *   **Output:** Can save scraped data to JSON and Markdown files.

    *   **B. MongoDB Database:**
        *   **Role:** Acts as the central repository for all scraped event data.
        *   **Schema:** While NoSQL databases are schema-flexible, the project defines an implicit schema through its Python data structures (TypedDicts, Pydantic models) and the `mongodb_setup.py` script, which creates collections and potentially indexes.
        *   **Collections:** Key collections include `events`, `quality_scores`, `validation_history`, and `extraction_methods` as indicated in `database/README.md`.
        *   **Data Quality Integration:** The `events` collection is augmented with `_quality` and `_validation` sub-documents to store quality scores and validation metadata per event.

    *   **C. API Server (`database/api_server.py`):**
        *   **Framework:** Built using FastAPI.
        *   **Functionality:** Exposes endpoints for clients to query event data. It handles incoming HTTP requests, fetches data from MongoDB (synchronously using `pymongo`), validates and serializes data using Pydantic models, and returns HTTP responses.
        *   **Key Endpoints:** Provides data retrieval based on quality, venue, date, text search, and also offers statistical data.
        *   **Documentation:** Benefits from FastAPI's automatic generation of OpenAPI (Swagger UI) documentation.

    *   **D. Data Quality Module (Conceptual - integrated within database scripts):**
        *   **`database/quality_scorer.py`:** Contains the logic for calculating quality scores for different event fields based on predefined rules (e.g., presence, format, known values).
        *   **`database/data_migration.py`:** Applies quality scoring during the migration of existing data.
        *   Scrapers are intended to integrate this scoring after fetching data, before saving to the database.

3.  **Workflow:**
    1.  **Scraping:** The `classy_skkkrapey.py` script is executed to crawl and scrape event data from target websites.
    2.  **Data Processing & Storage:** Scraped data is processed, (ideally) scored for quality, and then stored in the MongoDB `events` collection.
    3.  **API Access:** Client applications interact with the `api_server.py` to request event data. The API server queries MongoDB, applying filters (like quality score) as requested.
    4.  **Data Presentation:** The client application receives data in JSON format and can present it to end-users.

This architecture emphasizes modularity in scraping logic and leverages modern Python frameworks for API development and data handling. The integration of a data quality layer is a key architectural consideration.
