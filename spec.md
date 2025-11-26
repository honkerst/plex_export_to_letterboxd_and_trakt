# Plex Export to Letterboxd & Trakt Converter

This script converts a CSV export from Webtools-NG (Plex library export) into formats compatible with Letterboxd and Trakt imports.

## Overview

The script processes your Plex movie library export and creates filtered, formatted CSV files ready for import into both Letterboxd and Trakt. It:
- Filters movies to only include those with ratings
- Filters movies by how recently they were watched (configurable)
- Fixes a known Webtools-NG date offset bug (dates are one month early)
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

## Running the Script

### Option 1: One Command
```bash
cd /Users/timh/plex_export_to_letterboxd && python3 plex_export_to_letterboxd_and_trakt.py
```

### Option 2: Step by Step
```bash
# Navigate to the directory
cd /Users/timh/plex_export_to_letterboxd

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

## Output Summary

After processing, the script displays:
- Total number of rows processed
- Number of rows skipped (no rating)
- Number of rows skipped (too old)
- Location of output file

Example output:
```
Process complete!
  500 rows skipped (no rating)
  200 rows skipped (last watched more than 365 days ago)
Check processed_movies_letterboxd.csv and processed_movies_trakt.csv for results.
```

## Importing to Letterboxd and Trakt

After running the script, you'll have two CSV files ready to import:

### Importing to Letterboxd

1. Sign in to your Letterboxd account
2. Go to [https://letterboxd.com/import/](https://letterboxd.com/import/)
3. Upload the `processed_movies_letterboxd.csv` file
4. Follow the on-screen instructions to complete the import

### Importing to Trakt

1. Sign in to your Trakt account
2. Go to [https://trakt.tv/settings/data#import](https://trakt.tv/settings/data#import)
3. Upload the `processed_movies_trakt.csv` file
5. Follow the on-screen instructions to complete the import

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

## Future Enhancements

Potential improvements you might want to add:
- Command-line arguments for configuration
- Support for different date formats
- Option to include movies without ratings
- Custom output file naming
- Progress bar for large libraries

