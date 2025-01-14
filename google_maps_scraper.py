import googlemaps
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os
import logging
import time
import uuid
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class GoogleMapsScraper:
    # Pricing information from Google Places API docs
    PRICING = {
        'nearby_search': {
            'basic': 32 / 1000,  # $32 per 1000 requests
            'advanced': 35 / 1000,
            'preferred': 40 / 1000
        },
        'place_details': {
            'basic': 17 / 1000,  # $17 per 1000 requests
            'advanced': 20 / 1000,
            'preferred': 40 / 1000
        }
    }
    
    def __init__(self, api_key):
        logger.info("Initializing GoogleMapsScraper")
        self.gmaps = googlemaps.Client(key=api_key)
        self.cached_results = []
        self.request_count = {
            'nearby_search': 0,
            'place_details': 0
        }
        self.cache_dir = 'business_cache'
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        logger.debug("Google Maps client initialized")
        
    def validate_address(self, address):
        """Use Google's autocomplete to validate and confirm address"""
        try:
            autocomplete = self.gmaps.places_autocomplete(
                input_text=address,
                types='geocode'
            )
            
            if not autocomplete:
                logger.warning("No matching addresses found for: %s", address)
                return []
                
            logger.info("Found %d address suggestions for: %s", len(autocomplete), address)
            
            # Return all suggestions - client will handle selection
            return [{
                'description': r['description'],
                'place_id': r['place_id']
            } for r in autocomplete]
        except Exception as e:
            logger.error("Error validating address: %s", str(e))
            return []
        
    # Common business types from Google Places API
    BUSINESS_TYPES = [
        'accounting', 'airport', 'amusement_park', 'aquarium', 'art_gallery',
        'atm', 'bakery', 'bank', 'bar', 'beauty_salon', 'bicycle_store',
        'book_store', 'bowling_alley', 'bus_station', 'cafe', 'campground',
        'car_dealer', 'car_rental', 'car_repair', 'car_wash', 'casino',
        'cemetery', 'church', 'city_hall', 'clothing_store', 'convenience_store',
        'courthouse', 'dentist', 'department_store', 'doctor', 'drugstore',
        'electrician', 'electronics_store', 'embassy', 'fire_station',
        'florist', 'funeral_home', 'furniture_store', 'gas_station', 'gym',
        'hair_care', 'hardware_store', 'hindu_temple', 'home_goods_store',
        'hospital', 'insurance_agency', 'jewelry_store', 'laundry', 'lawyer',
        'library', 'light_rail_station', 'liquor_store', 'local_government_office',
        'locksmith', 'lodging', 'meal_delivery', 'meal_takeaway', 'mosque',
        'movie_rental', 'movie_theater', 'moving_company', 'museum', 'night_club',
        'painter', 'park', 'parking', 'pet_store', 'pharmacy', 'physiotherapist',
        'plumber', 'police', 'post_office', 'primary_school', 'real_estate_agency',
        'restaurant', 'roofing_contractor', 'rv_park', 'school', 'secondary_school',
        'shoe_store', 'shopping_mall', 'spa', 'stadium', 'storage', 'store',
        'subway_station', 'supermarket', 'synagogue', 'taxi_stand', 'tourist_attraction',
        'train_station', 'transit_station', 'travel_agency', 'university',
        'veterinary_care', 'zoo'
    ]

    def get_cache_file_path(self, place_id, business_type):
        """Generate a cache file path based on place_id and business_type"""
        safe_place_id = place_id.replace('/', '_')
        safe_type = business_type.replace('/', '_')
        return os.path.join(self.cache_dir, f"{safe_place_id}_{safe_type}.json")

    def load_cached_businesses(self, place_id, business_type):
        """Load cached businesses from file if they exist"""
        cache_file = self.get_cache_file_path(place_id, business_type)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading cache file {cache_file}: {str(e)}")
        return None

    def save_businesses_to_cache(self, place_id, business_type, businesses):
        """Save businesses to cache file"""
        cache_file = self.get_cache_file_path(place_id, business_type)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(businesses, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(businesses)} businesses to cache: {cache_file}")
        except Exception as e:
            logger.error(f"Error saving to cache file {cache_file}: {str(e)}")

    def search_businesses(self, place_id, radius=2500, business_types=None, use_cache=True):
        """Search for businesses in a specific location by type(s)
        
        Args:
            place_id: Google Maps place ID
            radius: Search radius in meters
            business_types: List of business types to search for (from BUSINESS_TYPES)
            use_cache: Whether to use cached results if available
                      Set to False to force fresh API search
        """
        logger.info("Searching businesses near place_id: %s", place_id)
        if business_types is None:
            business_types = ['restaurant']  # Default to just restaurants
            
        # Validate business types
        invalid_types = [t for t in business_types if t not in self.BUSINESS_TYPES]
        if invalid_types:
            logger.warning("Invalid business types provided: %s", invalid_types)
            business_types = [t for t in business_types if t in self.BUSINESS_TYPES]
            if not business_types:
                logger.error("No valid business types provided")
                return pd.DataFrame()
            
        # Check if we have fresh cached results (less than 1 day old)
        if use_cache:
            for business_type in business_types:
                cache_file = self.get_cache_file_path(place_id, business_type)
                if os.path.exists(cache_file):
                    file_age = time.time() - os.path.getmtime(cache_file)
                    if file_age < 86400:  # 1 day in seconds
                        logger.info("Using cached results from today for %s", business_type)
                        cached = self.load_cached_businesses(place_id, business_type)
                        if cached:
                            return pd.DataFrame(cached)
                    else:
                        logger.info("Cached results are older than 1 day - refreshing")
        # Get the location coordinates from place_id
        place_details = self.gmaps.place(place_id, fields=['geometry'])
        location = place_details['result']['geometry']['location']
        logger.debug("Location coordinates: lat=%s, lng=%s", location['lat'], location['lng'])
        
        logger.info("Searching businesses within %d meters radius", radius)
        all_results = []
        
        # Handle "all" search by searching each type individually
        if 'all' in business_types:
            logger.info("Searching all business types individually...")
            # Search each business type one by one
            for business_type in self.BUSINESS_TYPES:
                logger.info("Searching for %s businesses...", business_type)
                
                # Check cache first
                if use_cache:
                    cached = self.load_cached_businesses(place_id, business_type)
                    if cached is not None:
                        logger.info(f"Loaded {len(cached)} {business_type} businesses from cache")
                        all_results.extend(cached)
                        continue
                
                # Track nearby search request
                self.request_count['nearby_search'] += 1
                places_result = self.gmaps.places_nearby(
                    location=f"{location['lat']},{location['lng']}",
                    radius=radius,
                    type=business_type
                )
                type_results = places_result['results']
                
                # Get additional pages if available
                while 'next_page_token' in places_result and len(type_results) < 60:
                    time.sleep(2)  # Required delay for next_page_token
                    places_result = self.gmaps.places_nearby(
                        page_token=places_result['next_page_token']
                    )
                    type_results.extend(places_result['results'])
                
                logger.info("Found %d %s businesses", len(type_results), business_type)
                
                # Process and cache the results
                if type_results:
                    processed_results = []
                    for place in type_results:
                        try:
                            # Add the search type to the place data before processing
                            place['search_type'] = business_type
                            business_data = self.process_business(place)
                            if business_data:
                                processed_results.append(business_data)
                        except Exception as e:
                            logger.error(f"Error processing business {place.get('name')}: {str(e)}")
                    
                    if processed_results:
                        # Save to cache
                        self.save_businesses_to_cache(place_id, business_type, processed_results)
                        all_results.extend(processed_results)
                
                # Avoid hitting API rate limits
                time.sleep(1)
        else:
            # Search each business type individually
            for business_type in business_types:
                logger.info("Searching for %s businesses...", business_type)
            
                # Check cache first
                if use_cache:
                    cached = self.load_cached_businesses(place_id, business_type)
                    if cached is not None:
                        logger.info(f"Loaded {len(cached)} {business_type} businesses from cache")
                        all_results.extend(cached)
                        continue
            
            # Track nearby search request
            self.request_count['nearby_search'] += 1
            places_result = self.gmaps.places_nearby(
                location=f"{location['lat']},{location['lng']}",
                radius=radius,
                type=business_type
            )
            type_results = places_result['results']
            
            # Get additional pages if available
            while 'next_page_token' in places_result and len(type_results) < 60:
                time.sleep(2)  # Required delay for next_page_token
                places_result = self.gmaps.places_nearby(
                    page_token=places_result['next_page_token']
                )
                type_results.extend(places_result['results'])
            
            logger.info("Found %d %s businesses", len(type_results), business_type)
            
            # Process and cache the results
            if type_results:
                processed_results = []
                for place in type_results:
                    try:
                        # Add the search type to the place data before processing
                        place['search_type'] = business_type
                        business_data = self.process_business(place)
                        if business_data:
                            processed_results.append(business_data)
                    except Exception as e:
                        logger.error(f"Error processing business {place.get('name')}: {str(e)}")
                
                if processed_results:
                    # Save to cache
                    self.save_businesses_to_cache(place_id, business_type, processed_results)
                    all_results.extend(processed_results)
            
            # Avoid hitting API rate limits
            time.sleep(1)
        
        logger.info("Found %d businesses in total search", len(all_results))
        results = []
        for i, place in enumerate(all_results, 1):
            logger.debug("Processing business %d/%d: %s", i, len(all_results), place.get('name'))
            logger.debug("Fetching details for place_id: %s", place['place_id'])
            try:
                # Get place details
                # Track place details request
                self.request_count['place_details'] += 1
                place_details = self.gmaps.place(
                    place['place_id'],
                    fields=['name', 'formatted_address', 'formatted_phone_number',
                           'website', 'opening_hours', 'business_status',
                           'wheelchair_accessible_entrance']
                )
                
                # Extract email if available
                website = place_details['result'].get('website', '')
                email = self.extract_email(website) if website else ''
                
                logger.debug("Preparing business data for: %s", place_details['result'].get('name'))
                
                # Safely get geometry data
                lat = place.get('geometry', {}).get('location', {}).get('lat', 0)
                lng = place.get('geometry', {}).get('location', {}).get('lng', 0)
                
                # Prepare business data
                business_data = {
                    'name': place_details['result'].get('name'),
                    'address': place_details['result'].get('formatted_address'),
                    'phone': place_details['result'].get('formatted_phone_number'),
                    'website': website,
                    'email': email,
                    'opening_hours': self.format_opening_hours(
                        place_details['result'].get('opening_hours', {})
                    ),
                    'business_type': business_type,
                    'business_types': business_types,  # Include all types
                    'accessibility': place_details['result'].get(
                        'wheelchair_accessible_entrance', False
                    ),
                    'place_id': place['place_id'],
                    'latitude': lat,
                    'longitude': lng
                }
            except Exception as e:
                logger.error(f"Error processing business {place.get('name')}: {str(e)}")
                continue
            results.append(business_data)
            
        logger.info("Processed %d businesses successfully", len(results))
        return pd.DataFrame(results)
    
    def extract_email(self, website):
        """Extract email from website (basic implementation)"""
        logger.debug("Attempting to extract email from website: %s", website)
        # This would need a proper implementation using requests/BeautifulSoup
        # or a dedicated email extraction service
        return ''
    
    def calculate_cost(self):
        """Calculate estimated API costs based on request counts"""
        # Nearby search is considered "Basic" SKU
        nearby_cost = self.request_count['nearby_search'] * self.PRICING['nearby_search']['basic']
        
        # Place details is considered "Advanced" SKU since we're requesting multiple fields
        details_cost = self.request_count['place_details'] * self.PRICING['place_details']['advanced']
        
        total_cost = nearby_cost + details_cost
        return {
            'nearby_search': {
                'count': self.request_count['nearby_search'],
                'cost': nearby_cost
            },
            'place_details': {
                'count': self.request_count['place_details'],
                'cost': details_cost
            },
            'total_cost': total_cost
        }

    def process_business(self, place):
        """Process raw business data from Google Maps API"""
        try:
            # Get place details only if we don't already have them
            if 'formatted_address' not in place:
                place_details = self.gmaps.place(
                    place['place_id'],
                    fields=['name', 'formatted_address', 'formatted_phone_number',
                           'website', 'opening_hours', 'business_status',
                           'wheelchair_accessible_entrance']
                )
                place.update(place_details['result'])
            
            # Extract email if available
            website = place.get('website', '')
            email = self.extract_email(website) if website else ''
            
            # Safely get geometry data
            lat = place.get('geometry', {}).get('location', {}).get('lat', 0)
            lng = place.get('geometry', {}).get('location', {}).get('lng', 0)
            
            # Get business types - combine search types with place types
            search_types = place.get('search_type', ['restaurant'])
            if isinstance(search_types, str):
                search_types = [search_types]
                
            # Get all types from the place
            place_types = place.get('types', [])
            
            # Combine and deduplicate types
            all_types = list(set(search_types + place_types))
            
            # If searching all types, keep all valid types
            if 'all' in search_types:
                business_types = [t for t in all_types if t in self.BUSINESS_TYPES]
            else:
                # Filter to only search types that match our selected types
                business_types = [t for t in all_types if t in search_types]
            
            # Use the most specific type as primary
            business_type = self.get_primary_business_type(business_types)
            
            # If no types found, use first search type
            if not business_types:
                business_types = search_types
                business_type = search_types[0]
            
            # Prepare business data
            business_data = {
                'name': place.get('name'),
                'address': place.get('formatted_address'),
                'phone': place.get('formatted_phone_number'),
                'website': website,
                'email': email,
                'opening_hours': self.format_opening_hours(
                    place.get('opening_hours', {})
                ),
                'business_type': business_type,
                'accessibility': place.get(
                    'wheelchair_accessible_entrance', False
                ),
                'place_id': place['place_id'],
                'latitude': lat,
                'longitude': lng
            }
            return business_data
        except Exception as e:
            logger.error(f"Error processing business {place.get('name')}: {str(e)}")
            return None

    def get_primary_business_type(self, types):
        """Get the most relevant business type from the types list"""
        if not types:
            return 'unknown'
            
        # Prefer restaurant-related types first
        restaurant_types = ['restaurant', 'food', 'cafe', 'meal_takeaway', 'meal_delivery']
        for t in types:
            if t in restaurant_types:
                return t
                
        # Return the first non-generic type
        generic_types = ['point_of_interest', 'establishment']
        for t in types:
            if t not in generic_types:
                return t
                
        return types[0]  # fallback to first type if all are generic

    def format_opening_hours(self, opening_hours):
        """Format opening hours into readable string"""
        if not opening_hours:
            logger.debug("No opening hours data available")
            return 'Not Available'
        
        periods = opening_hours.get('periods', [])
        formatted_hours = []
        
        for period in periods:
            try:
                # Handle open time
                open_time = datetime.strptime(
                    period['open']['time'], '%H%M'
                ).strftime('%I:%M %p')
                
                # Handle close time if available
                if 'close' in period:
                    close_time = datetime.strptime(
                        period['close']['time'], '%H%M'
                    ).strftime('%I:%M %p')
                    formatted_hours.append(f"{open_time} - {close_time}")
                else:
                    formatted_hours.append(f"Opens at {open_time}")
                    
            except (KeyError, ValueError):
                # Skip malformed periods
                continue
                
        if not formatted_hours:
            return 'Not Available'
            
        return '\n'.join(formatted_hours)

def safe_print(text):
    """Handle Unicode printing safely"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode('ascii'))

def main():
    logger.info("Starting Google Maps scraper")
    # Get API key from environment variables
    API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    if not API_KEY:
        logger.error("GOOGLE_MAPS_API_KEY not found in .env file")
        raise ValueError("GOOGLE_MAPS_API_KEY not found in .env file")
    
    # Set up UTF-8 encoding for Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        
    scraper = GoogleMapsScraper(API_KEY)
    
    # Get address from user
    address = input("Enter the town/address to search near: ")
    if not address:
        logger.warning("No address provided by user")
        return
        
    # Validate address and let user select
    suggestions = scraper.validate_address(address)
    if not suggestions:
        logger.warning("No valid place_id obtained")
        return
        
    print("\nSelect address:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion['description']}")
    
    while True:
        try:
            choice = int(input("Enter number: ")) - 1
            if 0 <= choice < len(suggestions):
                selected = suggestions[choice]
                place_id = selected['place_id']
                break
            print("Invalid choice, try again")
        except ValueError:
            print("Please enter a number")

    # Get custom radius
    while True:
        try:
            radius_km = float(input("Enter search radius in kilometers (e.g. 2.5): "))
            if radius_km > 0:
                radius = int(radius_km * 1000)  # Convert km to meters
                break
            print("Radius must be greater than 0")
        except ValueError:
            print("Please enter a number")
    
    if not radius:
        logger.warning("No radius selected by user")
        return
        
    # Let user select business types
    print("\nAvailable business types:")
    print("0. All business types")
    for i, biz_type in enumerate(scraper.BUSINESS_TYPES, 1):
        print(f"{i}. {biz_type}")
    
    print("\nEnter numbers of business types to search (comma separated):")
    print("Example: 1,2,3 for restaurant, cafe, bar")
    print("Or enter 0 to search all business types")
    while True:
        try:
            choices = input("Your choices: ").strip()
            if not choices:
                business_types = ['restaurant']  # Default
                break
                
            selected_indices = [int(c.strip()) - 1 for c in choices.split(',')]
            
            # Handle "All" selection
            if -1 in selected_indices:  # 0 becomes -1 after subtracting 1
                business_types = scraper.BUSINESS_TYPES
                break
                
            business_types = [scraper.BUSINESS_TYPES[i] for i in selected_indices 
                            if 0 <= i < len(scraper.BUSINESS_TYPES)]
            if business_types:
                break
            print("Please select at least one valid business type")
        except (ValueError, IndexError):
            print("Please enter valid numbers separated by commas")

    logger.info("Starting business search with radius: %d meters", radius)
    print(f"\nSearching {', '.join(business_types)}...")
    
    results = pd.DataFrame()
    try:
        results = scraper.search_businesses(
            place_id=place_id,
            radius=radius,
            business_types=business_types,
            use_cache=False  # Force fresh search
        )
    except Exception as e:
        logger.error(f"Error searching restaurants: {str(e)}")
    
    print(f"Total restaurants found: {len(results)}")
    
    # Save results to memory
    scraper.cached_results = results.to_dict('records')
    logger.info("Cached %d business results", len(scraper.cached_results))
    
    # Show confirmation list
    print("\nFound these businesses:")
    for i, business in enumerate(scraper.cached_results, 1):
        safe_print(f"{i}. {business['name']} - {business['address']}")
    
    # Confirm before saving
    confirm = input(f"\nSave {len(scraper.cached_results)} businesses to JSON? (y/n): ").lower()
    if confirm != 'y':
        logger.info("User cancelled operation")
        print("Operation cancelled.")
        return
        
    # Add metadata to each business
    for business in scraper.cached_results:
        business['search_location'] = address  # Use the original search address
        business['search_radius'] = f"{radius/1000}km"
        business['search_date'] = datetime.now().isoformat()
    
    output_file = 'businesses.json'
    existing_data = []
    
    # Load existing data if file exists
    if os.path.exists(output_file):
        logger.info("Found existing output file: %s", output_file)
        with open(output_file, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
                logger.debug("Loaded %d existing records", len(existing_data))
            except json.JSONDecodeError as e:
                logger.error("Error reading JSON file: %s", str(e))
                existing_data = []
    
    # Create set of existing business IDs (name + address)
    existing_businesses = {
        (b['name'], b['address']) for b in existing_data
    }
    
    # Filter out duplicates
    new_businesses = [
        b for b in scraper.cached_results
        if (b['name'], b['address']) not in existing_businesses
    ]
    
    if not new_businesses:
        logger.info("No new businesses to add - all found businesses already exist")
        print("\nNo new businesses found to add.")
        return
        
    # Combine old and new data
    combined_data = existing_data + new_businesses
    
    # Save combined data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, 
                 indent=2, 
                 ensure_ascii=False,
                 sort_keys=True)
    
    logger.info("Added %d new businesses to %s", len(new_businesses), output_file)
    logger.info("Total businesses in file: %d", len(combined_data))
    # Calculate and display API costs
    cost_estimate = scraper.calculate_cost()
    print(f"\nAdded {len(new_businesses)} new businesses to {output_file}")
    print(f"Previously had {len(existing_data)} businesses")
    print(f"Total businesses in file: {len(combined_data)}")
    print("\nAPI Usage and Cost Estimate:")
    print(f"  Nearby Searches: {cost_estimate['nearby_search']['count']} requests")
    print(f"  Place Details: {cost_estimate['place_details']['count']} requests")
    print(f"  Estimated Cost: ${cost_estimate['total_cost']:.4f}")
    
    # Calculate scraping costs
    scrape_cost = len(scraper.cached_results) * scraper.PRICING['place_details']['advanced']
    print(f"\nScraping {len(scraper.cached_results)} businesses would cost ~${scrape_cost:.4f}")
    
    # Scrape additional details automatically since we already have the data
    logger.info("Starting detailed scraping of %d businesses", len(scraper.cached_results))
    print("Scraping additional details...")
    for i, business in enumerate(scraper.cached_results, 1):
        logger.debug("Scraping business %d/%d: %s", i, len(scraper.cached_results), business['name'])
            
if __name__ == "__main__":
    main()
