# Data Flattening Strategy for Analysis

This document outlines a strategy for flattening the nested MongoDB event data into a more relational format, suitable for traditional data analysis tools, BI dashboards, or SQL-based querying.

## 1. Summary of Data Quality

The current event data collection process has several strengths:
*   **Robust Extraction:** Captures a wide range of event details including title, location, date/time, lineup, and ticket information.
*   **Quality Scoring:** A comprehensive quality scoring system (`_quality`) is in place, providing scores for overall data quality and individual fields.
*   **Validation Metadata:** Detailed validation flags and confidence scores (`_validation`) offer insights into the reliability of each piece of information.

The primary weakness identified, particularly relevant for time-series analysis, is the **inconsistent parsing and storage of `dateTime` information**. This often results in `None` values or varied string formats, making direct temporal analysis challenging without significant preprocessing.

## 2. Recap of Data Structure

The event data in MongoDB is stored in a nested document structure. Each event document contains:
*   Top-level fields (e.g., `url`, `title`, `description`, `scrapedAt`, `extractionMethod`).
*   Nested objects for structured information:
    *   `location` (venue name, address, geo-coordinates)
    *   `dateTime` (original string, potential start/end datetime objects - often `None`)
    *   `ticketInfo` (availability, price range)
    *   `_quality` (overall score, scores for individual fields)
    *   `_validation` (overall confidence, validation details for individual fields including item-level validation for lineups)
*   A list of dictionaries for `lineUp` (artist names, potentially roles).

This rich, nested structure is excellent for application use but requires flattening for many analytical purposes.

## 3. Detailed Flattening Strategy

The proposed strategy involves creating two primary flat tables (which can be represented as CSV files or database tables):

### A. `events_flat` Table/CSV

This table will represent the main event details, with one row per event. Nested one-to-one fields will be flattened by prefixing their original field names.

**Key Fields and Handling:**

*   **Event Identifiers:**
    *   `event_id`: The MongoDB `_id` of the event.
    *   `url`: Original URL of the event.
*   **Basic Event Details:**
    *   `title`
    *   `description`
    *   `scrapedAt`
    *   `extractionMethod`
*   **Location (prefixed with `location_`):**
    *   `location_name` (from `location.name`)
    *   `location_address_streetAddress` (from `location.address.streetAddress`)
    *   `location_address_addressLocality` (from `location.address.addressLocality`)
    *   `location_address_postalCode` (from `location.address.postalCode`)
    *   `location_address_addressCountry` (from `location.address.addressCountry`)
    *   `location_geo_latitude` (from `location.geo.latitude`)
    *   `location_geo_longitude` (from `location.geo.longitude`)
*   **DateTime (prefixed with `dateTime_`):**
    *   `dateTime_originalString` (from `dateTime.originalString`)
    *   `dateTime_startDateTime_utc` (standardized to ISO 8601 UTC, from `dateTime.startDateTime` if available and valid)
    *   `dateTime_endDateTime_utc` (standardized to ISO 8601 UTC, from `dateTime.endDateTime` if available and valid)
    *   `dateTime_date_is_estimate` (boolean, derived from validation or parsing confidence)
*   **TicketInfo (prefixed with `ticket_`):**
    *   `ticket_availability` (from `ticketInfo.availability`)
    *   `ticket_priceRange_minPrice` (from `ticketInfo.priceRange.minPrice`)
    *   `ticket_priceRange_maxPrice` (from `ticketInfo.priceRange.maxPrice`)
    *   `ticket_priceRange_currency` (from `ticketInfo.priceRange.currency`)
*   **Quality Scores (prefixed with `quality_`):**
    *   `quality_overall_score` (from `_quality.overall.score`)
    *   `quality_title_score` (from `_quality.title.score`)
    *   `quality_location_score` (from `_quality.location.score`)
    *   `quality_dateTime_score` (from `_quality.dateTime.score`)
    *   `quality_lineUp_score` (from `_quality.lineUp.score`)
    *   `quality_ticketInfo_score` (from `_quality.ticketInfo.score`)
*   **Validation Methods & Confidence (prefixed with `validation_`):**
    *   `validation_overall_confidence` (from `_validation.overall.confidence`)
    *   `validation_title_method` (from `_validation.title.method`)
    *   `validation_location_method` (from `_validation.location.method`)
    *   `validation_dateTime_method` (from `_validation.dateTime.method`)
    *   `validation_lineUp_method` (from `_validation.lineUp.method`)
    *   `validation_ticketInfo_method` (from `_validation.ticketInfo.method`)
*   **Validation Flags (concatenated strings):**
    *   For each field that has validation flags (e.g., `_validation.title.flags`), these will be concatenated into a single string, separated by a delimiter (e.g., semicolon).
    *   Example: `validation_title_flags`: "MISSING_INFO;LOW_CONFIDENCE_FORMAT"

### B. `event_artists` Table/CSV

This table will handle the one-to-many relationship between events and artists in the `lineUp`.

**Key Fields:**

*   `event_artist_id`: A unique identifier for this specific event-artist link (e.g., generated by hashing event_id and artist name, or a sequence).
*   `event_id`: Foreign key linking back to `events_flat.event_id`.
*   `artist_name`: The name of the artist (from `lineUp.name`).
*   `artist_role`: (If available) The role of the artist (e.g., "DJ Set", "Live").
*   **Lineup Item Validation Details (prefixed with `validation_artist_`):**
    *   `validation_artist_name_method`: Method used to validate this specific artist's name (from `_validation.lineUp.itemValidation[i].name.method`).
    *   `validation_artist_name_confidence`: Confidence for this artist's name (from `_validation.lineUp.itemValidation[i].name.confidence`).
    *   `validation_artist_name_flags`: Concatenated validation flags for this artist's name.

## 4. Outline of Flattening Script

A Python script leveraging `pymongo` for database connection and `pandas` for data manipulation and CSV export is proposed.

**Key Components:**

1.  **`connect_to_db(uri, db_name, collection_name)`:**
    *   Connects to the MongoDB instance and returns the specified collection object.

2.  **`flatten_event(event_doc)`:**
    *   Takes a single event document (dictionary) as input.
    *   Extracts top-level fields.
    *   Handles nested one-to-one fields by creating prefixed column names (e.g., `location_name`, `quality_title_score`).
    *   Processes `dateTime` fields, attempting to standardize valid dates to ISO 8601 UTC format and flagging estimates. This will be the most complex part due to current data inconsistencies.
    *   Concatenates validation flags into delimited strings.
    *   Returns a flat dictionary representing one row in `events_flat`.

3.  **`extract_event_artists(event_doc)`:**
    *   Takes a single event document as input.
    *   Iterates through the `lineUp` array.
    *   For each artist, creates a dictionary containing `event_id`, `artist_name`, `artist_role`.
    *   If `_validation.lineUp.itemValidation` exists and matches the lineup structure, it incorporates the specific validation method, confidence, and flags for that artist entry, prefixing them (e.g., `validation_artist_name_method`).
    *   Returns a list of dictionaries, each representing one row in `event_artists`.

**Script Workflow:**

1.  Connect to MongoDB.
2.  Fetch all event documents from the collection.
3.  Initialize two empty lists: `flat_events_list` and `event_artists_list`.
4.  Iterate through each event document:
    *   Call `flatten_event()` and append its result to `flat_events_list`.
    *   Call `extract_event_artists()` and extend `event_artists_list` with its results.
5.  Create pandas DataFrames from `flat_events_list` and `event_artists_list`.
6.  Export DataFrames to `events_flat.csv` and `event_artists.csv`.

**Key Considerations for Implementation:**

*   **Error Handling:** Robust error handling for missing fields, unexpected data types, or failed date conversions.
*   **Date Consistency:** A significant effort will be required to parse and standardize the `dateTime` fields. This might involve:
    *   Attempting parsing with multiple known formats.
    *   Using heuristics based on `dateTime_originalString`.
    *   Clearly flagging dates that could not be reliably parsed or are estimates.
*   **Scalability:** For very large datasets, fetching all documents at once might be memory-intensive. Consider processing documents in batches.
*   **Data Type Conversion:** Ensure appropriate data types in the resulting DataFrames/CSVs (e.g., numeric types for scores, boolean for flags where applicable before string concatenation).
*   **Configuration:** Make MongoDB URI, database name, and collection name configurable.

This strategy provides a structured approach to transform the rich, nested event data into a flat format more amenable to various analytical tasks, while preserving as much detail as possible, including valuable quality and validation metadata.Okay, I will now create the `data_flattening_strategy_presentation.md` file with the compiled information.
