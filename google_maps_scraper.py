import googlemaps
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os
import logging

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
        print("\nPlease select the correct address:")
        for i, result in enumerate(autocomplete, 1):
            print(f"{i}. {result['description']}")
        
        while True:
            try:
                choice = int(input("Enter number: "))
                if 1 <= choice <= len(autocomplete):
                    selected = autocomplete[choice-1]['description']
                    break
                print("Invalid choice, try again")
            except ValueError:
                print("Please enter a number")
        
        if not selected:
            logger.warning("No address selected by user")
            return None
            
        logger.info("User selected address: %s", selected)
            
        # Get the place details for the selected address
        place = next((p for p in autocomplete if p['description'] == selected), None)
        return place['place_id']
        
    def search_businesses(self, place_id, radius=2500, business_type=None):
        """Search for businesses in a specific location"""
        logger.info("Searching businesses near place_id: %s", place_id)
        # Get the location coordinates from place_id
        place_details = self.gmaps.place(place_id, fields=['geometry'])
        location = place_details['result']['geometry']['location']
        logger.debug("Location coordinates: lat=%s, lng=%s", location['lat'], location['lng'])
        
        logger.info("Searching businesses within %d meters radius", radius)
        # Track nearby search request
        self.request_count['nearby_search'] += 1
        places_result = self.gmaps.places_nearby(
            location=f"{location['lat']},{location['lng']}",
            radius=radius,
            type=business_type
        )
        
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
        
    # Search all business types
    business_type = None
    logger.info("Starting business search with radius: %d meters", radius)
    print("\nSearching all business types...")
    
    # Perform search
    results = scraper.search_businesses(
        place_id=place_id,
        radius=radius,
        business_type=business_type
    )
    
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
    print(f"Total businesses in file: {len(combined_data)}")
    print("\nAPI Usage and Cost Estimate:")
    print(f"  Nearby Searches: {cost_estimate['nearby_search']['count']} requests")
    print(f"  Place Details: {cost_estimate['place_details']['count']} requests")
    print(f"  Estimated Cost: ${cost_estimate['total_cost']:.4f}")
    
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
