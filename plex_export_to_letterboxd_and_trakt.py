import csv
import json
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from calendar import monthrange

# Configuration: Maximum age in days for "Last Viewed at" date
MAX_DAYS_OLD = 365  # Change this value to adjust the cutoff

# Webtools-NG date fix: Set to True to add one month to all dates (fixes known bug)
FIX_WEBTOOLS_DATE_OFFSET = True  # Set to False to disable the fix

# Plex Configuration
# Get your Plex server URL (e.g., http://192.168.1.100:32400 or https://your-plex-server.com)
# You can specify multiple URLs separated by commas - the script will try each one
# Get your Plex token from: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
PLEX_SERVER_URLS = [
    "http://192.168.0.103:32400",  # Private IP of your Plex server
    "https://86.31.161.42:32400",  # Public IP (from your network settings)
]  # The script will try each URL until one works
PLEX_TOKEN = "tav2wvdVwrUXx6gJyt_P"  # Your Plex server API token (X-Plex-Token)

# Plex Community API Configuration
# Option 1: Try using your Plex token (X-Plex-Token) - this often works!
# If that doesn't work, get your Bearer token by:
# 1. Open Plex Web in your browser
# 2. Open DevTools (F12) → Network tab
# 3. Navigate to a movie page
# 4. Find a request to https://community.plex.tv/api
# 5. Click on it, go to "Headers" tab, find "Request Headers" section
# 6. Look for "Authorization: Bearer <token>" and copy the token part
# 7. If not found, check the "Cookies" tab or try using your PLEX_TOKEN below
PLEX_COMMUNITY_TOKEN = ""  # Your Plex Community API Bearer token (leave empty to try using PLEX_TOKEN)

# Set to False to disable review fetching (useful if you don't have tokens configured)
FETCH_REVIEWS = True  # Set to False to skip review fetching


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

def get_plex_metadata_id(title, year, tmdb_id=None):
    """
    Get Plex metadataID (global ID) for a movie using Plex server API.
    Returns the metadataID string or None if not found.
    
    The global metadata ID is extracted from the 'guid' attribute in the format:
    plex://movie/{global_metadata_id}
    """
    if not PLEX_TOKEN:
        return None
    
    # Try each server URL until one works
    server_urls = PLEX_SERVER_URLS if isinstance(PLEX_SERVER_URLS, list) else [PLEX_SERVER_URLS]
    
    for server_url in server_urls:
        if not server_url:
            continue
            
        try:
            # Search for the movie by title
            search_url = f"{server_url}/search?type=1&query={urllib.parse.quote(title)}&X-Plex-Token={PLEX_TOKEN}"
            
            req = urllib.request.Request(search_url)
            req.add_header('Accept', 'application/xml')
            
            # Try to connect - if this succeeds, we know which URL works
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                
                # Look for matching movie by title and year
                for video in root.findall('.//Video'):
                    video_title = video.get('title', '')
                    video_year = video.get('year', '')
                    
                    # Match by title and year
                    if video_title.lower() == title.lower() and video_year == str(year):
                        # Get the ratingKey
                        rating_key = video.get('ratingKey')
                        if not rating_key:
                            continue
                        
                        # Fetch full metadata to get the global metadata ID from guid attribute
                        metadata_url = f"{server_url}/library/metadata/{rating_key}?X-Plex-Token={PLEX_TOKEN}"
                        metadata_req = urllib.request.Request(metadata_url)
                        metadata_req.add_header('Accept', 'application/xml')
                        
                        with urllib.request.urlopen(metadata_req, timeout=10) as metadata_response:
                            metadata_xml = metadata_response.read()
                            metadata_root = ET.fromstring(metadata_xml)
                            
                            # Extract global metadata ID from guid attribute
                            # Format: plex://movie/{global_metadata_id}
                            video_elem = metadata_root.find('.//Video')
                            if video_elem is not None:
                                guid_attr = video_elem.get('guid', '')
                                if guid_attr and 'plex://' in guid_attr:
                                    # Extract the ID part after the last '/'
                                    parts = guid_attr.split('/')
                                    if len(parts) >= 3:
                                        global_id = parts[-1]
                                        # Verify it looks like a valid metadata ID (hex string, typically 24 chars)
                                        if global_id and len(global_id) >= 16:
                                            return global_id
                                
                return None
            
        except urllib.error.URLError as e:
            # Try next server URL
            continue
        except Exception as e:
            # Try next server URL
            continue
    
    # If we get here, none of the server URLs worked
    return None

def get_plex_user_review(metadata_id):
    """
    Fetch user review from Plex Community API using metadataID.
    Returns the review text (message) or None if no review exists.
    """
    if not metadata_id:
        return None
    
    # Use PLEX_COMMUNITY_TOKEN if provided, otherwise try PLEX_TOKEN
    auth_token = PLEX_COMMUNITY_TOKEN if PLEX_COMMUNITY_TOKEN else PLEX_TOKEN
    if not auth_token:
        return None
    
    try:
        # Minimal GraphQL query to get just the user review
        # Note: Must use inline fragments because userReview can return different activity types
        query = """
        query getRatingsAndReviewsHubData($metadataID: ID!) {
          userReview: metadataReviewV2(
            metadata: { id: $metadataID }
            ignoreFutureMetadata: true
          ) {
            __typename
            ... on ActivityReview {
              message
              reviewRating: rating
              hasSpoilers
              status
            }
            ... on ActivityWatchReview {
              message
              reviewRating: rating
              hasSpoilers
              status
            }
            ... on ActivityRating {
              rating
            }
            ... on ActivityWatchRating {
              rating
            }
          }
        }
        """
        
        payload = {
            "query": query,
            "variables": {"metadataID": metadata_id},
            "operationName": "getRatingsAndReviewsHubData"
        }
        
        url = "https://community.plex.tv/api"
        data = json.dumps(payload).encode('utf-8')
        
        req = urllib.request.Request(url, data=data)
        req.add_header('Content-Type', 'application/json')
        
        # Use X-Plex-Token header (this is what works with Plex Community API)
        req.add_header('X-Plex-Token', auth_token)
        req.add_header('X-Plex-Client-Identifier', 'plex-export-script')
        req.add_header('X-Plex-Product', 'Plex Web')
        req.add_header('X-Plex-Version', '4.156.0')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if 'errors' in result:
                return None
            
            user_review = result.get('data', {}).get('userReview')
            if user_review and user_review.get('message'):
                return user_review.get('message')
            
            return None
            
    except Exception as e:
        # Silently fail - reviews are optional
        return None

# Allow override of input file for testing
INPUT_FILE = 'movies.csv'
import sys
if len(sys.argv) > 1:
    INPUT_FILE = sys.argv[1]

with open(INPUT_FILE, 'r') as infile, \
     open('processed_movies_letterboxd.csv', 'w', newline='') as letterboxd_file, \
     open('processed_movies_trakt.csv', 'w', newline='') as trakt_file:
    
    reader = csv.DictReader(infile)
    
    # Letterboxd format
    letterboxd_fieldnames = ['Title', 'Year', 'tmdbID', 'Rating10', 'WatchedDate', 'Review']
    letterboxd_writer = csv.DictWriter(letterboxd_file, fieldnames=letterboxd_fieldnames)
    letterboxd_writer.writeheader()
    
    # Trakt format
    trakt_fieldnames = ['tmdb_id', 'watched_at', 'rating', 'rated_at', 'type']
    trakt_writer = csv.DictWriter(trakt_file, fieldnames=trakt_fieldnames)
    trakt_writer.writeheader()
    
    total_rows = sum(1 for row in csv.DictReader(open(INPUT_FILE)))
    print(f"Starting lookup for {total_rows} items...")
    
    # Check review fetching configuration
    if FETCH_REVIEWS:
        server_urls = PLEX_SERVER_URLS if isinstance(PLEX_SERVER_URLS, list) else [PLEX_SERVER_URLS] if PLEX_SERVER_URLS else []
        if not server_urls or not PLEX_TOKEN:
            print("Warning: Plex server URL or token not configured. Review fetching disabled.")
            print("  Set PLEX_SERVER_URLS and PLEX_TOKEN to enable review fetching.")
        else:
            print(f"Review fetching enabled - will try {len(server_urls)} server URL(s).")
            if PLEX_COMMUNITY_TOKEN:
                print("  Using Plex Community API token.")
            else:
                print("  Will use Plex server token for Community API.")
    else:
        print("Review fetching disabled (FETCH_REVIEWS = False).")
    
    processed = 0
    skipped_no_rating = 0
    skipped_too_old = 0
    reviews_found = 0
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
        
        # Fetch user review from Plex if enabled
        review = None
        server_urls = PLEX_SERVER_URLS if isinstance(PLEX_SERVER_URLS, list) else [PLEX_SERVER_URLS] if PLEX_SERVER_URLS else []
        if FETCH_REVIEWS and server_urls and PLEX_TOKEN:
            try:
                year_int = int(row['Year']) if row['Year'] else None
                tmdb_id = row['TMDB ID'] if row['TMDB ID'] else None
                metadata_id = get_plex_metadata_id(row['Title'], year_int, tmdb_id)
                if metadata_id:
                    review = get_plex_user_review(metadata_id)
                    if review:
                        reviews_found += 1
                        print(f"    Found review ({len(review)} chars)")
                    else:
                        print(f"    No review found")
                else:
                    print(f"    Could not find Plex metadataID")
            except Exception as e:
                print(f"    Warning: Error fetching review: {e}")
        
        # Letterboxd format row
        letterboxd_row = {
            'Title': row['Title'],
            'Year': row['Year'],
            'tmdbID': row['TMDB ID'],
            'Rating10': rating,
            'WatchedDate': watched_date,
            'Review': review if review else ''
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
if FETCH_REVIEWS:
    print(f"  {reviews_found} reviews found and added to Letterboxd CSV")
print(f"Check processed_movies_letterboxd.csv and processed_movies_trakt.csv for results.")

