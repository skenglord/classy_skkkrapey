## Project Overview

The project is a sophisticated web scraping solution designed to gather event information from two primary sources: "ticketsibiza.com" (a primarily static website) and "ibiza-spotlight.com" (a JavaScript-heavy, dynamic website).

The core objectives of the project are:

1.  **Automated Data Collection:** To reliably and automatically scrape event details (such as title, location, date/time, lineup, and ticket information) from the specified websites.
2.  **Data Storage:** To store the extracted event data in a structured MongoDB database.
3.  **Data Quality Assurance:** To implement a system for scoring the quality and completeness of the scraped data, ensuring that users are presented with reliable information.
4.  **Data Accessibility:** To provide a robust API (Application Programming Interface) that allows client applications to easily access and consume the curated event data, with options for filtering based on data quality and other criteria.

The system is comprised of several key components: a configurable web scraping engine capable of handling different website structures, a MongoDB database acting as the central data repository, a data quality scoring mechanism integrated into the data processing pipeline, and a FastAPI-based API server for external data access.
