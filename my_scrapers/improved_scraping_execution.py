#!/usr/bin/env python3
"""
Improved scraping execution module with enhanced error handling, performance optimization,
and better code organization.
"""

import asyncio
import time
import random
import logging
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json

# Import the necessary types from the original file
from classy_skkkrapey import (
    BaseEventScraper, EventSchema, ScraperConfig,
    SCRAPE_ACTION, CRAWL_ACTION
)

logger = logging.getLogger(__name__)


@dataclass
class ScrapingProgress:
    """Tracks the progress of a scraping operation."""
    total_urls: int = 0
    processed_urls: int = 0
    successful_scrapes: int = 0
    failed_scrapes: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate of scraping."""
        if self.processed_urls == 0:
            return 0.0
        return (self.successful_scrapes / self.processed_urls) * 100
    
    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds."""
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def avg_time_per_url(self) -> float:
        """Calculate average time per URL."""
        if self.processed_urls == 0:
            return 0.0
        return self.elapsed_time / self.processed_urls
    
    def log_progress(self):
        """Log current progress statistics."""
        logger.info(
            f"Progress: {self.processed_urls}/{self.total_urls} URLs processed | "
            f"Success rate: {self.success_rate:.1f}% | "
            f"Avg time/URL: {self.avg_time_per_url:.2f}s"
        )


class ScrapingExecutor:
    """Enhanced scraping executor with improved error handling and performance features."""
    
    def __init__(self, scraper_instance: BaseEventScraper, config: ScraperConfig):
        self.scraper = scraper_instance
        self.config = config
        self.progress = ScrapingProgress()
        
    def execute(self) -> List[EventSchema]:
        """Execute the scraping process with enhanced error handling and progress tracking."""
        if self.config.action == SCRAPE_ACTION:
            return self._execute_single_scrape()
        elif self.config.action == CRAWL_ACTION:
            return self._execute_crawl_and_scrape()
        else:
            raise ValueError(f"Unknown action: {self.config.action}")
    
    def _execute_single_scrape(self) -> List[EventSchema]:
        """Execute a single page scrape with error handling."""
        all_events: List[EventSchema] = []
        self.progress.total_urls = 1
        
        try:
            logger.info(f"Starting single page scrape for: {self.config.url}")
            event = self._scrape_with_retry(self.config.url)
            
            if event:
                all_events.append(event)
                self.progress.successful_scrapes += 1
                logger.info(f"Successfully scraped event: {event.get('title', 'Unknown')}")
            else:
                self.progress.failed_scrapes += 1
                logger.warning(f"No data extracted from: {self.config.url}")
                
        except Exception as e:
            self._handle_scraping_error(self.config.url, e)
        finally:
            self.progress.processed_urls += 1
            self.progress.log_progress()
            
        return all_events
    
    def _execute_crawl_and_scrape(self) -> List[EventSchema]:
        """Execute crawling followed by scraping with enhanced features."""
        all_events: List[EventSchema] = []
        
        try:
            # Phase 1: Crawl for event URLs
            event_urls = self._crawl_with_validation()
            
            if not event_urls:
                logger.warning(
                    "No event URLs found after filtering. "
                    "Possible causes:\n"
                    "1. The page structure may have changed\n"
                    "2. The selectors need updating\n"
                    "3. The page requires different wait conditions\n"
                    "4. There are genuinely no events on this page"
                )
                return all_events
            
            # Phase 2: Scrape individual events
            all_events = self._scrape_event_urls(event_urls)
            
        except Exception as e:
            logger.error(f"Critical error during crawl operation: {e}", exc_info=True)
            raise
        
        return all_events
    
    def _crawl_with_validation(self) -> List[str]:
        """Crawl for event URLs with validation and logging."""
        logger.info(f"Starting crawl operation for: {self.config.url}")
        
        try:
            event_urls = self.scraper.crawl_listing_for_events(self.config.url)
            
            # Validate and deduplicate URLs
            validated_urls = self._validate_urls(event_urls)
            
            logger.info(
                f"Crawl complete: Found {len(event_urls)} URLs, "
                f"{len(validated_urls)} after validation"
            )
            
            # Log sample of URLs for debugging
            if validated_urls:
                logger.debug(f"Sample URLs (first 5): {validated_urls[:5]}")
            
            return validated_urls
            
        except Exception as e:
            logger.error(f"Error during crawl phase: {e}", exc_info=True)
            raise
    
    def _validate_urls(self, urls: List[str]) -> List[str]:
        """Validate and deduplicate URLs."""
        seen = set()
        validated = []
        
        for url in urls:
            # Remove fragments and normalize
            normalized_url = url.split('#')[0].rstrip('/')
            
            if normalized_url and normalized_url not in seen:
                seen.add(normalized_url)
                validated.append(normalized_url)
        
        return validated
    
    def _scrape_event_urls(self, event_urls: List[str]) -> List[EventSchema]:
        """Scrape a list of event URLs with progress tracking and error recovery."""
        all_events: List[EventSchema] = []
        self.progress.total_urls = len(event_urls)
        
        logger.info(f"Starting to scrape {len(event_urls)} event URLs")
        
        # Determine scraping strategy based on URL count
        if len(event_urls) > 20 and hasattr(self.config, 'use_concurrent') and self.config.use_concurrent:
            # Use concurrent scraping for large batches
            all_events = self._scrape_concurrent(event_urls)
        else:
            # Use sequential scraping for small batches or when concurrent is disabled
            all_events = self._scrape_sequential(event_urls)
        
        # Final summary
        logger.info(
            f"\nScraping completed:\n"
            f"- Total URLs: {self.progress.total_urls}\n"
            f"- Successful: {self.progress.successful_scrapes}\n"
            f"- Failed: {self.progress.failed_scrapes}\n"
            f"- Success rate: {self.progress.success_rate:.1f}%\n"
            f"- Total time: {self.progress.elapsed_time:.1f}s"
        )
        
        if self.progress.errors:
            logger.warning(f"Encountered {len(self.progress.errors)} errors during scraping")
            self._save_error_report()
        
        return all_events
    
    def _scrape_sequential(self, event_urls: List[str]) -> List[EventSchema]:
        """Scrape URLs sequentially with delays."""
        all_events: List[EventSchema] = []
        
        for i, url in enumerate(event_urls, 1):
            try:
                # Progress update
                logger.info(
                    f"[{i}/{len(event_urls)}] Scraping: {url} "
                    f"(Success rate: {self.progress.success_rate:.1f}%)"
                )
                
                # Scrape with retry logic
                event = self._scrape_with_retry(url)
                
                if event:
                    all_events.append(event)
                    self.progress.successful_scrapes += 1
                    logger.debug(f"Successfully extracted: {event.get('title', 'Unknown')}")
                else:
                    self.progress.failed_scrapes += 1
                    logger.warning(f"No data extracted from: {url}")
                
            except Exception as e:
                self._handle_scraping_error(url, e)
            
            finally:
                self.progress.processed_urls += 1
                
                # Add delay between requests (except for the last one)
                if i < len(event_urls):
                    delay = random.uniform(self.config.min_delay, self.config.max_delay)
                    logger.debug(f"Waiting {delay:.2f}s before next request...")
                    time.sleep(delay)
                
                # Log progress every 10 URLs or at specific percentages
                if i % 10 == 0 or i in [len(event_urls) // 4, len(event_urls) // 2, 3 * len(event_urls) // 4]:
                    self.progress.log_progress()
        
        return all_events
    
    def _scrape_concurrent(self, event_urls: List[str]) -> List[EventSchema]:
        """Scrape URLs concurrently for better performance (when appropriate)."""
        all_events: List[EventSchema] = []
        max_workers = min(5, len(event_urls))  # Limit concurrent requests
        
        logger.info(f"Using concurrent scraping with {max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(self._scrape_with_retry, url): url
                for url in event_urls
            }
            
            # Process completed tasks
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    event = future.result()
                    if event:
                        all_events.append(event)
                        self.progress.successful_scrapes += 1
                    else:
                        self.progress.failed_scrapes += 1
                        
                except Exception as e:
                    self._handle_scraping_error(url, e)
                
                finally:
                    self.progress.processed_urls += 1
                    if self.progress.processed_urls % 10 == 0:
                        self.progress.log_progress()
        
        return all_events
    
    def _scrape_with_retry(self, url: str, max_retries: int = 2) -> Optional[EventSchema]:
        """Scrape a URL with retry logic for transient failures."""
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{max_retries} for: {url}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                
                return self.scraper.scrape_event_data(url)
                
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                else:
                    raise
        
        raise last_error
    
    def _handle_scraping_error(self, url: str, error: Exception):
        """Handle and log scraping errors."""
        error_info = {
            'url': url,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat()
        }
        
        self.progress.errors.append(error_info)
        self.progress.failed_scrapes += 1
        
        logger.error(
            f"Failed to scrape {url}: {type(error).__name__}: {str(error)}",
            exc_info=logger.isEnabledFor(logging.DEBUG)
        )
    
    def _save_error_report(self):
        """Save detailed error report for debugging."""
        if not self.progress.errors:
            return
        
        error_file = self.config.output_dir / f"scraping_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(error_file, 'w') as f:
                json.dump({
                    'summary': {
                        'total_errors': len(self.progress.errors),
                        'error_rate': f"{(len(self.progress.errors) / self.progress.processed_urls * 100):.1f}%",
                        'unique_error_types': list(set(e['error_type'] for e in self.progress.errors))
                    },
                    'errors': self.progress.errors
                }, f, indent=2)
            
            logger.info(f"Error report saved to: {error_file}")
            
        except Exception as e:
            logger.error(f"Failed to save error report: {e}")


def execute_scraping_improved(scraper_instance: BaseEventScraper, config: ScraperConfig) -> List[EventSchema]:
    """
    Improved version of _execute_scraping with enhanced error handling and progress tracking.
    
    This is a drop-in replacement for the original _execute_scraping function.
    """
    executor = ScrapingExecutor(scraper_instance, config)
    return executor.execute()


# Example of how to integrate this into the existing code:
def _execute_scraping_enhanced(scraper_instance: BaseEventScraper, config: ScraperConfig) -> List[EventSchema]:
    """
    Enhanced version of _execute_scraping with all improvements.
    
    Key improvements:
    1. Better progress tracking and logging
    2. Retry logic for transient failures
    3. Error collection and reporting
    4. Optional concurrent scraping for large batches
    5. URL validation and deduplication
    6. More informative error messages
    """
    # Use the improved executor
    return execute_scraping_improved(scraper_instance, config)


# Minimal change version - direct replacement for lines 518-519 with enhanced logging
def enhanced_crawl_logging(event_urls: List[str], logger: logging.Logger) -> None:
    """
    Enhanced logging for crawl results with more actionable information.
    
    This can replace lines 518-519 in the original code.
    """
    url_count = len(event_urls)
    
    if url_count > 0:
        logger.info(
            f"✓ Found {url_count} potential event link{'s' if url_count != 1 else ''} to scrape"
        )
        
        # Log URL distribution for debugging
        if url_count > 5:
            logger.debug(f"First 3 URLs: {event_urls[:3]}")
            logger.debug(f"Last 2 URLs: {event_urls[-2:]}")
        else:
            logger.debug(f"URLs found: {event_urls}")
    else:
        logger.warning(
            "✗ No event URLs found after filtering.\n"
            "Troubleshooting steps:\n"
            "1. Run with --no-headless to see what the page looks like\n"
            "2. Check if the page structure has changed\n"
            "3. Verify the CSS selectors in the scraper class\n"
            "4. Ensure JavaScript is fully loaded (may need longer wait)\n"
            "5. Check if there are genuinely no events on this page"
        )
        
        # Additional debug info
        logger.debug(
            "Consider checking:\n"
            "- Network requests in browser DevTools\n"
            "- Console errors on the page\n"
            "- Whether events are loaded dynamically via API calls"
        )