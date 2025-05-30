# Ibiza Event Scraper & API

## Description

This project is designed to scrape event information from key Ibiza event websites: "ticketsibiza.com" (a primarily static site) and "ibiza-spotlight.com" (a JavaScript-heavy, dynamic site). It processes this information, scores it for quality and completeness, stores the curated data in a MongoDB database, and provides a FastAPI-based API for easy access to the event data.

## Key Features

*   **Multi-Site Scraping:** Capable of scraping data from multiple websites with different structures.
*   **Dynamic Content Handling:** Utilizes Playwright to effectively scrape JavaScript-rendered content.
*   **Static Content Handling:** Uses Requests and BeautifulSoup for efficient scraping of static sites.
*   **Data Quality Scoring:** Implements a system to score the quality of scraped data, ensuring reliability.
*   **MongoDB Storage:** Stores structured event data in a MongoDB database.
*   **FastAPI Powered API:** Provides a robust and well-documented API for accessing event data, with filtering capabilities (including by quality score).
*   **Configurable Scraper:** Offers CLI options for targeted scraping and crawling.
*   **User-Agent Rotation & Delays:** Implements polite scraping practices.

## Technologies Used

*   **Programming Language:** Python 3.9+
*   **Web Scraping:**
    *   Playwright (for dynamic sites)
    *   Requests (for static sites)
    *   BeautifulSoup4 (for HTML parsing)
*   **API Development:**
    *   FastAPI
    *   Pydantic (for data validation and settings)
*   **Database:**
    *   MongoDB
    *   Pymongo (driver)
*   **CLI:** Argparse
*   **Logging:** Python `logging` module

## Prerequisites

Before you begin, ensure you have the following installed:

*   Python 3.9 or higher
*   MongoDB
*   Access to a terminal or command prompt

## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create and Activate a Python Virtual Environment:**
    ```bash
    python -m venv venv
    # On macOS/Linux
    source venv/bin/activate
    # On Windows
    # venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    Install all required packages from `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Playwright Browser Drivers:**
    Playwright requires browser binaries to operate. Install them with:
    ```bash
    playwright install
    ```
    This will download the default browsers (Chromium, Firefox, WebKit).

5.  **MongoDB Setup:**
    *   Ensure your MongoDB instance is running.
    *   The project includes scripts and guidelines for setting up the necessary collections and potentially indexes. Refer to `database/README.md` and `database/mongodb_setup.py` for detailed instructions on configuring the database schema. You might need to adjust the MongoDB connection URI in `database/api_server.py` or relevant configuration files if not using default settings.

## Usage

### Scraper (`my_scrapers/classy_skkkrapey.py`)

The main scraper script is used to fetch and process event data from the target websites.

**Basic Command Structure:**
```bash
python my_scrapers/classy_skkkrapey.py <URL> <action> [options]
```

**Actions:**
*   `scrape`: Scrapes a single event detail page.
*   `crawl`: Crawls a listing page to find multiple event URLs and then scrapes each one.

**Common Options:**
*   `-v`, `--verbose`: Enable verbose logging.
*   `-H`, `--headless`: Control whether Playwright runs in headless mode (default is True).
*   `--delay`: Set a delay between requests.
*   `--user_agent`: Specify a custom User-Agent.

**Example Commands:**

*   **Crawl Ibiza Spotlight for events:**
    ```bash
    python my_scrapers/classy_skkkrapey.py https://www.ibiza-spotlight.com/nightlife/club_dates_i.htm crawl -v
    ```
*   **Scrape a specific event from Tickets Ibiza:**
    ```bash
    python my_scrapers/classy_skkkrapey.py https://ticketsibiza.com/event/amnesia-ibiza-closing-festival-2024 scrape -v
    ```

**Output:**
The scraper saves output as:
*   JSON files (containing the structured event data) in the `output/json/` directory.
*   Markdown files (human-readable summaries) in the `output/markdown/` directory.

### API Server (`database/api_server.py`)

The API server provides access to the scraped event data stored in MongoDB.

1.  **Run the API Server:**
    Navigate to the `database` directory and run:
    ```bash
    python api_server.py
    ```
    By default, the server will run on `http://localhost:8000`.

2.  **Access API Documentation:**
    Once the server is running, you can access the interactive API documentation (Swagger UI) by navigating to:
    `http://localhost:8000/docs`
    This interface allows you to explore all available endpoints, view their request/response models, and even test them directly from your browser.

## Directory Structure Overview

*   `my_scrapers/`: Contains the core web scraping logic, including the base scraper and site-specific scraper classes.
*   `database/`: Includes scripts for API server, database setup, data migration, quality scoring, and example queries.
*   `utils/`: Contains various utility modules used across the project.
*   `models/`: Contains data models or machine learning model integration (e.g., `deepseek.py`).
*   `output/`: Default directory for scraped data (JSON, Markdown).
*   `tests/`: Contains test scripts for the project.
*   `test_cases/`: May contain sample HTML files or data for testing purposes.

## Data Quality

A key aspect of this project is its data quality scoring system. After scraping, event data is evaluated based on completeness, format correctness, and other heuristics. This score is stored alongside the event information and can be used via the API to filter for high-quality, reliable event listings.

## Contributing

Contributions are welcome! If you'd like to contribute, please consider the following:
*   Check for open issues or propose new features.
*   Follow the existing code style and add tests for new functionality.
*   A `CONTRIBUTING.md` file exists with more detailed guidelines.

---

This README provides a basic guide to getting the project set up and running. For more detailed information on specific components, please refer to the documentation within the respective directories and code files.
