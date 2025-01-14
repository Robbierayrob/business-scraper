import googlemaps
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os
import logging
import time  # Added for sleep()

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
        logger.debug("Google Maps client initialized")
        
    def validate_address(self, address):
        """Use Google's autocomplete to validate and confirm address"""
        autocomplete = self.gmaps.places_autocomplete(
            input_text=address,
            types='geocode'
        )
        
        if not autocomplete:
            logger.warning("No matching addresses found for: %s", address)
            return None
            
        logger.info("Found %d address suggestions for: %s", len(autocomplete), address)
        
        # Return all suggestions - client will handle selection
        return [{
            'description': r['description'],
            'place_id': r['place_id']
        } for r in autocomplete]
        
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

    def search_businesses(self, place_id, radius=2500, business_types=None):
        """Search for businesses in a specific location by type(s)"""
        logger.info("Searching businesses near place_id: %s", place_id)
        if business_types is None:
            business_types = self.BUSINESS_TYPES
        # Get the location coordinates from place_id
        place_details = self.gmaps.place(place_id, fields=['geometry'])
        location = place_details['result']['geometry']['location']
        logger.debug("Location coordinates: lat=%s, lng=%s", location['lat'], location['lng'])
        
        logger.info("Searching businesses within %d meters radius", radius)
        all_results = []
        
        # Search each business type individually
        for business_type in business_types:
            logger.info("Searching for %s businesses...", business_type)
            
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
            all_results.extend(type_results)
            
            # Avoid hitting API rate limits
            time.sleep(1)
        
        logger.info("Found %d businesses in initial search", len(places_result['results']))
        results = []
        for i, place in enumerate(places_result['results'], 1):
            logger.debug("Processing business %d/%d: %s", i, len(places_result['results']), place.get('name'))
            logger.debug("Fetching details for place_id: %s", place['place_id'])
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
                'accessibility': place_details['result'].get(
                    'wheelchair_accessible_entrance', False
                )
            }
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

def main():
    logger.info("Starting Google Maps scraper")
    # Get API key from environment variables
    API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    if not API_KEY:
        logger.error("GOOGLE_MAPS_API_KEY not found in .env file")
        raise ValueError("GOOGLE_MAPS_API_KEY not found in .env file")
        
    scraper = GoogleMapsScraper(API_KEY)
    
    # Get address from user
    address = input("Enter the town/address to search near: ")
    if not address:
        logger.warning("No address provided by user")
        return
        
    # Validate address
    place_id = scraper.validate_address(address)
    if not place_id:
        logger.warning("No valid place_id obtained")
        return
        
    print("\nSelect search radius:")
    print("1. 2.5 km")
    print("2. 5 km")
    print("3. 10 km")
    
    while True:
        try:
            choice = int(input("Enter number (1-3): "))
            if choice == 1:
                radius = 2500
                break
            elif choice == 2:
                radius = 5000
                break
            elif choice == 3:
                radius = 10000
                break
            print("Invalid choice, try again")
        except ValueError:
            print("Please enter a number")
    
    if not radius:
        logger.warning("No radius selected by user")
        return
        
    # Search all business types sequentially
    logger.info("Starting business search with radius: %d meters", radius)
    print("\nSearching all business types sequentially...")
    
    # Perform search in chunks to avoid timeout
    results = pd.DataFrame()
    chunk_size = 10
    for i in range(0, len(scraper.BUSINESS_TYPES), chunk_size):
        types_chunk = scraper.BUSINESS_TYPES[i:i + chunk_size]
        print(f"\nSearching types: {', '.join(types_chunk)}")
        
        chunk_results = scraper.search_businesses(
            place_id=place_id,
            radius=radius,
            business_types=types_chunk
        )
        
        # Combine results while avoiding duplicates
        if not results.empty:
            existing_ids = set(results['place_id'])
            chunk_results = chunk_results[~chunk_results['place_id'].isin(existing_ids)]
        
        results = pd.concat([results, chunk_results])
        
        print(f"Total businesses found so far: {len(results)}")
    
    # Save results to memory
    scraper.cached_results = results.to_dict('records')
    logger.info("Cached %d business results", len(scraper.cached_results))
    
    # Show confirmation list
    print("\nFound these businesses:")
    for i, business in enumerate(scraper.cached_results, 1):
        print(f"{i}. {business['name']} - {business['address']}")
    
    # Confirm before saving
    confirm = input(f"\nSave {len(scraper.cached_results)} businesses to JSON? (y/n): ").lower()
    if confirm != 'y':
        logger.info("User cancelled operation")
        print("Operation cancelled.")
        return
        
    # Add location metadata to each business
    location_name = input("Enter a name for this location search (e.g., 'Sydney CBD'): ")
    
    if not location_name:
        logger.warning("No location name provided by user")
        print("Location name is required")
        return
        
    # Add metadata to each business
    for business in scraper.cached_results:
        business['search_location'] = location_name
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
    
    # Ask about scraping
    if input("Do you want to scrape these places? (y/n): ").lower() == 'y':
        logger.info("Starting detailed scraping of %d businesses", len(scraper.cached_results))
        print("Scraping additional details...")
        # You can access the cached results with place IDs
        for i, business in enumerate(scraper.cached_results, 1):
            logger.debug("Scraping business %d/%d: %s", i, len(scraper.cached_results), business['name'])
            # Add your scraping logic here
            pass
            
if __name__ == "__main__":
    main()
