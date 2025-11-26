import csv
from datetime import datetime, timedelta
from calendar import monthrange

# Configuration: Maximum age in days for "Last Viewed at" date
MAX_DAYS_OLD = 365  # Change this value to adjust the cutoff

# Webtools-NG date fix: Set to True to add one month to all dates (fixes known bug)
FIX_WEBTOOLS_DATE_OFFSET = True  # Set to False to disable the fix


def add_one_month(date_obj):
    """Add one month to a datetime object, handling month-end edge cases."""
    if date_obj.month == 12:
        # December -> January of next year
        new_month = 1
        new_year = date_obj.year + 1
    else:
        new_month = date_obj.month + 1
        new_year = date_obj.year
    
    # Handle month-end dates (e.g., Jan 31 -> Feb 28/29)
    max_day = monthrange(new_year, new_month)[1]
    new_day = min(date_obj.day, max_day)
    
    return date_obj.replace(year=new_year, month=new_month, day=new_day)

def fix_date(date_string):
    """Parse and format date, optionally fixing Webtools-NG one-month offset bug."""
    if not date_string:
        return None
    try:
        date_obj = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        
        # Fix Webtools-NG date offset bug (dates are one month early)
        if FIX_WEBTOOLS_DATE_OFFSET:
            date_obj = add_one_month(date_obj)
        
        return date_obj.strftime('%Y-%m-%d')
    except:
        return None

def is_within_days(date_string, max_days):
    """Check if a date string is within max_days from today."""
    if not date_string:
        return False
    try:
        date_obj = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        
        # Fix Webtools-NG date offset bug (dates are one month early)
        if FIX_WEBTOOLS_DATE_OFFSET:
            date_obj = add_one_month(date_obj)
        
        cutoff_date = datetime.now() - timedelta(days=max_days)
        return date_obj >= cutoff_date
    except:
        return False

with open('movies.csv', 'r') as infile, \
     open('processed_movies_letterboxd.csv', 'w', newline='') as letterboxd_file, \
     open('processed_movies_trakt.csv', 'w', newline='') as trakt_file:
    
    reader = csv.DictReader(infile)
    
    # Letterboxd format
    letterboxd_fieldnames = ['Title', 'Year', 'tmdbID', 'Rating10', 'WatchedDate']
    letterboxd_writer = csv.DictWriter(letterboxd_file, fieldnames=letterboxd_fieldnames)
    letterboxd_writer.writeheader()
    
    # Trakt format
    trakt_fieldnames = ['tmdb_id', 'watched_at', 'rating', 'rated_at', 'type']
    trakt_writer = csv.DictWriter(trakt_file, fieldnames=trakt_fieldnames)
    trakt_writer.writeheader()
    
    total_rows = sum(1 for row in csv.DictReader(open('movies.csv')))
    print(f"Starting lookup for {total_rows} items...")
    
    processed = 0
    skipped_no_rating = 0
    skipped_too_old = 0
    for row in reader:
        processed += 1
        print(f"\nProcessing item {processed} of {total_rows}")
        
        # Skip rows without a rating
        if not row['User Rating'] or row['User Rating'].strip() == '':
            skipped_no_rating += 1
            print(f"  Skipping (no rating)")
            continue
        
        # Skip rows where last watched date is too old
        if not is_within_days(row['Last Viewed at'], MAX_DAYS_OLD):
            skipped_too_old += 1
            print(f"  Skipping (last watched more than {MAX_DAYS_OLD} days ago)")
            continue
        
        rating = round(float(row['User Rating']))
        watched_date = fix_date(row['Last Viewed at'])
        
        # Letterboxd format row
        letterboxd_row = {
            'Title': row['Title'],
            'Year': row['Year'],
            'tmdbID': row['TMDB ID'],
            'Rating10': rating,
            'WatchedDate': watched_date
        }
        letterboxd_writer.writerow(letterboxd_row)
        
        # Trakt format row
        trakt_row = {
            'tmdb_id': row['TMDB ID'],
            'watched_at': watched_date,
            'rating': rating,
            'rated_at': watched_date,
            'type': 'movie'
        }
        trakt_writer.writerow(trakt_row)

print(f"\nProcess complete!")
print(f"  {skipped_no_rating} rows skipped (no rating)")
print(f"  {skipped_too_old} rows skipped (last watched more than {MAX_DAYS_OLD} days ago)")
print(f"Check processed_movies_letterboxd.csv and processed_movies_trakt.csv for results.")

