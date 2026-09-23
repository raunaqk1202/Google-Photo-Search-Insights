"""Scraper configuration — per-source settings for all data acquisition targets."""

SCRAPER_CONFIG = {
    "playstore": {
        "app_id": "com.google.android.apps.photos",
        "lang": "en",
        "country": "us",
        "count": 5000,
        "sort": "relevance",
        "filter_keywords": [
            "find", "search", "old photo", "can't find", "retrieve",
            "looking for", "where is", "lost photo", "missing photo",
            "how to find", "scroll", "search bar", "filter",
        ],
    },
    "appstore": {
        "app_name": "google-photos",
        "app_id": 962194608,  # Google Photos iOS app ID
        "country": "us",
        "count": 5000,
    },
    "reddit": {
        "subreddits": ["googlephotos"],
        "search_queries": [
            "find old photo",
            "search photos",
            "can't find picture",
            "photo search not working",
            "looking for old picture",
        ],
        "time_filter": "year",
        "limit": 1000,
        # Apify-specific settings
        "apify_actor_id": "trudax/reddit-scraper-lite",
        "max_items_per_query": 200,
    },
    "youtube": {
        "search_queries": [
            "Google Photos search tips",
            "find old photos Google Photos",
            "Google Photos search not working",
            "Google Photos can't find photo",
            "Google Photos how to search",
        ],
        "max_results_per_query": 50,
        "max_comments_per_video": 200,
    },
    "community": {
        "base_url": "https://support.google.com/photos/community",
        "max_pages": 100,
        "categories": ["search", "find photos", "missing photos"],
        # Search URLs for Google Photos Help Community
        "search_urls": [
            "https://support.google.com/photos/threads?hl=en&thread_filter=(category:search)",
            "https://support.google.com/photos/threads?hl=en&thread_filter=(category:find_photos)",
        ],
    },
}

# Rate limiting defaults (seconds between requests)
RATE_LIMITS = {
    "playstore": 1.0,
    "appstore": 1.0,
    "reddit": 2.0,      # Apify handles its own rate limits, this is for our batch calls
    "youtube": 0.5,      # YouTube API has generous limits
    "community": 2.0,    # Be polite to Google Support
}

# Maximum retries per source on failure
MAX_RETRIES = {
    "playstore": 3,
    "appstore": 3,
    "reddit": 2,
    "youtube": 3,
    "community": 3,
}
