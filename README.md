# Export Plex Ratings and Watched Status for Letterboxd & Trakt, plus Plex User Review (for Letterboxd only)

This script converts a CSV export from Webtools-NG (Plex library export) into formats compatible with Letterboxd and Trakt imports, and then (for Letterboxd only) adds your user review from Plex. 

## Overview

The script processes your Plex movie library export and creates filtered, formatted CSV files ready for import into both Letterboxd and Trakt. It:
- Filters movies to only include those with ratings
- Filters movies by how recently they were watched (configurable)
- Fixes a known Webtools-NG date offset bug (dates are one month early)
- Fetches user reviews from Plex (if available) and adds them to Letterboxd output (Trakt does not support importing reviews).
- Formats data into Letterboxd-compatible format
- Formats data into Trakt-compatible format

## Prerequisites

- Python 3.x (tested with Python 3.13.5)
- macOS (or any system with Python 3)
- A CSV export from Webtools-NG with the following columns:
  - `Title`
  - `Year`
  - `TMDB ID`
  - `User Rating`
  - `Last Viewed at`

**Note:** This script only uses Python's standard library, so no additional packages or virtual environments are required.

## Setup

### Prepare Your Input File

- Export your Plex library from Webtools-NG
- Save the CSV file as `movies.csv` in the script directory
- Ensure the CSV has the required columns listed above

## Configuration

Edit the configuration variables at the top of `plex_export_to_letterboxd_and_trakt.py`:

### `MAX_DAYS_OLD` (Line 9)
- **Default:** `365`
- **Purpose:** Maximum age (in days) for "Last Viewed at" date
- **Usage:** Only movies watched within this timeframe will be included
- **Examples:**
  - `365` = Last year only
  - `30` = Last month only
  - `0` = Disable date filtering (include all dates)

### `FIX_WEBTOOLS_DATE_OFFSET` (Line 12)
- **Default:** `True`
- **Purpose:** Fixes known bug in some versions of Webtools-NG caused by Plex returning Unix timestamps in milliseconds but Webtools-NG reading them as seconds 
- **Usage:** 
  - `True` = Automatically add one month to all dates (recommended)
  - `False` = Use dates as exported (if bug is fixed in future Webtools-NG versions)

### Plex Review Fetching Configuration

To enable review fetching, you need to configure your Plex server connection:

#### `PLEX_SERVER_URLS` (Line 20)
- **Default:** `[]` (empty list)
- **Purpose:** List of Plex server URLs to try when fetching reviews
- **Usage:** 
  - Add your Plex server URL(s) - the script will try each one until one works
  - For local network: `"http://192.168.0.103:32400"` (use your server's local IP)
  - For remote access: `"https://your-public-ip:32400"` (use your server's public IP)
  - You can specify multiple URLs - the script tries them in order
  - Example:
    ```python
    PLEX_SERVER_URLS = [
        "http://192.168.0.103:32400",  # Private IP (tried first)
        "https://86.31.103.18:32400",  # Public IP (fallback)
    ]
    ```

#### `PLEX_TOKEN` (Line 24)
- **Default:** `""` (empty string)
- **Purpose:** Your Plex server API token (X-Plex-Token)
- **How to get it:**
  1. Open Plex Web in your browser
  2. The token appears in the URL: `https://app.plex.tv/desktop?X-Plex-Token=xxxxxxxxxxxxx`
  3. Or follow: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
- **Usage:** Paste your token as a string, e.g., `"tav2wvdVwrUXx6gJyt_P"`

#### `PLEX_COMMUNITY_TOKEN` (Line 36)
- **Default:** `""` (empty string)
- **Purpose:** Optional - Plex Community API Bearer token (usually not needed)
- **Usage:** 
  - Leave empty to use your `PLEX_TOKEN` for Community API (this usually works)
  - Only set this if you get authentication errors and need a separate Bearer token
  - To get it: Open Plex Web → DevTools → Network → Find request to `community.plex.tv/api` → Check Request Headers for `Authorization: Bearer <token>`

#### `FETCH_REVIEWS` (Line 38)
- **Default:** `True`
- **Purpose:** Enable/disable review fetching
- **Usage:**
  - `True` = Fetch reviews from Plex and add to Letterboxd CSV
  - `False` = Skip review fetching (faster, but no reviews in output)

## Running the Script

### Option 1: One Command
```bash
cd /path/to/plex_export_to_letterboxd_and_trakt && python3 plex_export_to_letterboxd_and_trakt.py
```

### Option 2: Step by Step
```bash
# Navigate to the directory
cd /path/to/plex_export_to_letterboxd_and_trakt

# Run the script
python3 plex_export_to_letterboxd_and_trakt.py
```

## Input Format

The script expects `movies.csv` with these columns:
- `Title` - Movie title
- `Year` - Release year
- `TMDB ID` - The Movie Database ID
- `User Rating` - Your rating (1-10 scale, or empty)
- `Last Viewed at` - Date/time in format: `YYYY-MM-DD HH:MM:SS`

## Output Format

The script creates two CSV files:

### Letterboxd Format (`processed_movies_letterboxd.csv`)
- `Title` - Movie title
- `Year` - Release year
- `tmdbID` - The Movie Database ID
- `Rating10` - Your rating (1-10 scale, rounded)
- `WatchedDate` - Date in format: `YYYY-MM-DD` (corrected for Webtools-NG bug)
- `Review` - Your user review from Plex (if available and review fetching is enabled)
  - Empty string if no review exists
  - Only added to Letterboxd CSV, not Trakt CSV

### Trakt Format (`processed_movies_trakt.csv`)
- `tmdb_id` - The Movie Database ID
- `watched_at` - Watch date in format: `YYYY-MM-DD` (corrected for Webtools-NG bug)
- `rating` - Your rating (1-10 scale, rounded)
- `rated_at` - Rating date (same as watched_at)
- `type` - Always set to `'movie'`

## Filtering Rules

The script applies two filters:

1. **Rating Filter:** Only includes movies that have a `User Rating` value
   - Movies without ratings are skipped
   - Ratings are rounded to nearest integer

2. **Date Filter:** Only includes movies watched within `MAX_DAYS_OLD` days
   - Uses the corrected date (after fixing Webtools-NG offset)
   - Movies without a "Last Viewed at" date are excluded
   - Movies older than the cutoff are skipped

## Webtools-NG Date Bug Fix

Webtools-NG has a known bug where exported dates are one month early. For example:
- Movie watched on **November 26, 2024** → Exported as **October 26, 2024**
- Movie watched on **January 15, 2024** → Exported as **December 15, 2023**

The script automatically fixes this by adding one month to all dates. The fix handles:
- Year boundaries (December → January of next year)
- Month-end edge cases (e.g., Jan 31 → Feb 28/29)

## Review Fetching

The script can automatically fetch your user reviews from Plex and add them to the Letterboxd CSV output. This feature:

- **Connects to your Plex server** to find movies and get their global metadata IDs
- **Queries the Plex Community API** to retrieve your user reviews
- **Adds reviews to the Letterboxd CSV only** (Trakt CSV does not include reviews)
- **Handles missing reviews gracefully** - if a movie has no review, the Review column will be empty
- **Tries multiple server URLs** - if your private IP doesn't work, it tries your public IP automatically

### How It Works

1. For each movie that passes the filters, the script:
   - Searches your Plex server for the movie by title and year
   - Extracts the global metadata ID from the Plex server response
   - Uses that metadata ID to query the Plex Community API for your review
   - Adds the review text to the `Review` column in the Letterboxd CSV

2. If review fetching fails (server unreachable, no review exists, etc.), the script continues normally - the Review column will just be empty for that movie.

3. The script prints progress messages showing when reviews are found:
   - `Found review (58 chars)` - Review successfully fetched
   - `No review found` - Movie found in Plex but no review exists
   - `Could not find Plex metadataID` - Movie not found in Plex server

### Performance

- Review fetching adds API calls for each movie, so processing will be slower
- The script makes one request to your Plex server and one to the Plex Community API per movie
- If you have many movies, this can take several minutes
- You can disable review fetching by setting `FETCH_REVIEWS = False` for faster processing

## Output Summary

After processing, the script displays:
- Total number of rows processed
- Number of rows skipped (no rating)
- Number of rows skipped (too old)
- Number of reviews found and added (if review fetching is enabled)
- Location of output files

Example output:
```
Starting lookup for 1000 items...
Review fetching enabled - will try 2 server URL(s).
  Will use Plex server token for Community API.

Processing item 1 of 1000
    Found review (58 chars)

...

Process complete!
  500 rows skipped (no rating)
  200 rows skipped (last watched more than 365 days ago)
  300 reviews found and added to Letterboxd CSV
Check processed_movies_letterboxd.csv and processed_movies_trakt.csv for results.
```

## Importing to Letterboxd and Trakt

After running the script, you'll have two CSV files ready to import:

### Importing to Trakt

1. Sign in to your Trakt account
2. Go to [https://trakt.tv/settings/data#import](https://trakt.tv/settings/data#import)
3. Upload the `processed_movies_trakt.csv` file
5. Follow the on-screen instructions to complete the import
6. NB: Trakt can undo imports.

### Importing to Letterboxd

1. Sign in to your Letterboxd account
2. Go to [https://letterboxd.com/import/](https://letterboxd.com/import/)
3. Upload the `processed_movies_letterboxd.csv` file
4. Follow the on-screen instructions to complete the import
5. NB Letterboxd has no 'undo' for imports. Double check your CSV!

**Note:** Both platforms will match your movies using the TMDB ID, so make sure your original export includes valid TMDB IDs for accurate matching.

## Troubleshooting

### "FileNotFoundError: movies.csv"
- Ensure `movies.csv` is in the same directory as the script
- Check the filename is exactly `movies.csv` (case-sensitive)

### Dates still seem wrong
- Verify `FIX_WEBTOOLS_DATE_OFFSET` is set to `True`
- Check that your Webtools-NG export actually has the date bug (compare a known date)

### No output file created
- Check that at least some movies passed both filters (have ratings AND are within date range)
- Review the skip counts in the output to see why movies were excluded

### Review fetching issues

#### "Warning: Cannot connect to Plex server"
- Check that `PLEX_SERVER_URLS` contains at least one valid URL
- Verify your Plex server is running and accessible
- Try accessing the server URL in your browser
- If using private IP, make sure you're on the same network
- The script will try multiple URLs automatically - check which one works

#### "Could not find Plex metadataID" for all movies
- The movie might not be in your Plex library (check the title/year match)
- The Plex server might not be accessible from your network
- Try adding your public IP to `PLEX_SERVER_URLS` if private IP doesn't work

#### Reviews are empty in output CSV
- The movie might not have a review in Plex (check in Plex Web)
- Review fetching might be disabled (`FETCH_REVIEWS = False`)
- Check the console output for error messages
- Verify your `PLEX_TOKEN` is correct and valid

#### "HTTP Error 401: Unauthorized" when fetching reviews
- Your `PLEX_TOKEN` might be invalid or expired
- Try getting a new token from Plex Web
- If using `PLEX_COMMUNITY_TOKEN`, make sure it's a valid Bearer token
