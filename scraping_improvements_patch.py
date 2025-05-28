#!/usr/bin/env python3
"""
Direct improvements for lines 518-519 in classy_skkkrapey.py
This shows both minimal and comprehensive improvements.
"""

import logging
from typing import List

# OPTION 1: Minimal improvement - Enhanced logging for lines 518-519
# Replace lines 518-519 with this:
def minimal_improvement(event_urls: List[str], logger: logging.Logger):
    """Minimal improvement focusing on better logging."""
    url_count = len(event_urls)
    
    # Line 518 replacement - more informative success message
    if url_count > 0:
        logger.info(
            f"✓ Found {url_count} potential event link{'s' if url_count != 1 else ''} to scrape. "
            f"Estimated time: {url_count * 2.5:.0f}-{url_count * 5:.0f} seconds"
        )
    else:
        logger.info("Found 0 potential event links to scrape.")
    
    # Line 519-520 replacement - more actionable failure message
    if not event_urls:
        logger.warning(
            "⚠️  No event URLs found after filtering. Possible causes:\n"
            "   • Page structure changed - check CSS selectors\n"
            "   • JavaScript not fully loaded - try increasing timeout\n"
            "   • No events on this page - verify manually with --no-headless\n"
            "   • Rate limiting - check for captchas or blocks"
        )


# OPTION 2: Moderate improvement - Add validation and debugging info
def moderate_improvement(event_urls: List[str], logger: logging.Logger, config):
    """Moderate improvement with URL validation and debugging."""
    # Validate and deduplicate URLs
    validated_urls = []
    seen = set()
    
    for url in event_urls:
        # Normalize URL (remove fragments and trailing slashes)
        normalized = url.split('#')[0].rstrip('/')
        if normalized and normalized not in seen:
            seen.add(normalized)
            validated_urls.append(normalized)
    
    url_count = len(validated_urls)
    original_count = len(event_urls)
    
    # Enhanced logging with validation info
    if url_count > 0:
        logger.info(
            f"✓ Found {original_count} URLs, {url_count} after validation/deduplication"
        )
        
        # Show sample URLs in debug mode
        if logger.isEnabledFor(logging.DEBUG):
            sample_size = min(3, url_count)
            logger.debug(f"Sample URLs: {validated_urls[:sample_size]}")
    else:
        logger.warning(
            f"⚠️  No valid event URLs found (0/{original_count} passed validation)\n"
            f"   Debug info: Run with --verbose flag for detailed logging"
        )
        
        # Log the current URL being crawled for context
        if hasattr(config, 'url'):
            logger.info(f"   Crawled URL: {config.url}")
    
    return validated_urls


# OPTION 3: Comprehensive improvement - Full replacement of lines 517-520
def comprehensive_improvement(scraper_instance, config, logger):
    """
    Comprehensive improvement that replaces lines 517-520 with better
    error handling, validation, and progress tracking.
    """
    try:
        # Crawl with timing
        import time
        start_time = time.time()
        
        logger.info(f"🔍 Starting crawl for event URLs at: {config.url}")
        event_urls = scraper_instance.crawl_listing_for_events(config.url)
        
        crawl_time = time.time() - start_time
        logger.debug(f"Crawl completed in {crawl_time:.2f} seconds")
        
        # Validate URLs
        validated_urls = []
        seen = set()
        invalid_count = 0
        
        for url in event_urls:
            # More sophisticated validation
            if not url or url.startswith('#'):
                invalid_count += 1
                continue
                
            # Normalize
            normalized = url.split('#')[0].rstrip('/')
            
            # Check for common invalid patterns
            if any(pattern in normalized.lower() for pattern in ['javascript:', 'mailto:', 'tel:']):
                invalid_count += 1
                continue
                
            if normalized not in seen:
                seen.add(normalized)
                validated_urls.append(normalized)
        
        # Detailed logging based on results
        total_found = len(event_urls)
        valid_count = len(validated_urls)
        
        if valid_count > 0:
            # Success case with rich information
            logger.info(
                f"✅ Crawl Results:\n"
                f"   • Total URLs found: {total_found}\n"
                f"   • Valid URLs: {valid_count}\n"
                f"   • Duplicates removed: {total_found - valid_count - invalid_count}\n"
                f"   • Invalid URLs filtered: {invalid_count}\n"
                f"   • Estimated scraping time: {valid_count * 3:.0f}-{valid_count * 6:.0f} seconds"
            )
            
            # Log samples for debugging
            if logger.isEnabledFor(logging.DEBUG) and valid_count > 0:
                logger.debug("Sample valid URLs:")
                for i, url in enumerate(validated_urls[:3]):
                    logger.debug(f"   {i+1}. {url}")
                if valid_count > 3:
                    logger.debug(f"   ... and {valid_count - 3} more")
                    
        else:
            # Failure case with actionable guidance
            logger.warning(
                f"⚠️  No valid event URLs found!\n"
                f"   • URLs checked: {total_found}\n"
                f"   • Invalid/filtered: {invalid_count}\n"
                f"   • Duplicates: {total_found - invalid_count}\n"
                f"\n"
                f"   🔧 Troubleshooting steps:\n"
                f"   1. Run with --no-headless to inspect the page visually\n"
                f"   2. Check browser console for JavaScript errors\n"
                f"   3. Verify CSS selectors match current page structure\n"
                f"   4. Test with a different date/page that should have events\n"
                f"   5. Check if site requires authentication or has anti-bot measures"
            )
            
            # Additional context
            if crawl_time < 2:
                logger.warning(
                    f"   ⚡ Page loaded very quickly ({crawl_time:.2f}s) - "
                    f"might indicate blocked/rate-limited request"
                )
        
        return validated_urls
        
    except Exception as e:
        logger.error(f"❌ Error during crawl phase: {type(e).__name__}: {str(e)}")
        raise


# DIRECT PATCH: This is what you would actually change in classy_skkkrapey.py
# Replace lines 518-520 with:
"""
# Enhanced logging with actionable information
url_count = len(event_urls)

if url_count > 0:
    # Calculate time estimate based on delay settings
    min_time = url_count * config.min_delay
    max_time = url_count * config.max_delay
    
    logger.info(
        f"✓ Found {url_count} potential event link{'s' if url_count != 1 else ''} to scrape "
        f"(estimated time: {min_time:.0f}-{max_time:.0f} seconds)"
    )
    
    # Log sample URLs in debug mode
    if logger.isEnabledFor(logging.DEBUG):
        sample = min(3, url_count)
        logger.debug(f"First {sample} URLs: {event_urls[:sample]}")
else:
    logger.warning(
        "⚠️  No event URLs found after filtering.\n"
        "   Troubleshooting:\n"
        "   • Run with --no-headless to see the page\n"
        "   • Check if CSS selectors need updating\n"
        "   • Verify JavaScript loads completely\n"
        "   • Test a different page with known events"
    )
"""


# Example of how to use these improvements in the main code:
if __name__ == "__main__":
    # This demonstrates the improved code structure
    logger = logging.getLogger(__name__)
    
    # Example event URLs
    test_urls = [
        "https://example.com/event1",
        "https://example.com/event1#section",  # Duplicate with fragment
        "https://example.com/event2",
        "javascript:void(0)",  # Invalid
        "https://example.com/event3/",
        "https://example.com/event3",  # Duplicate
    ]
    
    print("MINIMAL IMPROVEMENT:")
    minimal_improvement(test_urls, logger)
    
    print("\nMODERATE IMPROVEMENT:")
    class MockConfig:
        url = "https://example.com/events"
    validated = moderate_improvement(test_urls, logger, MockConfig())
    
    print(f"\nValidated URLs: {validated}")