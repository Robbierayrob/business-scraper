import googlemaps
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class GoogleMapsScraper:
    def __init__(self, api_key):
        self.gmaps = googlemaps.Client(key=api_key)
        self.cached_results = []
        
    def validate_address(self, address):
        """Use Google's autocomplete to validate and confirm address"""
        autocomplete = self.gmaps.places_autocomplete(
            input_text=address,
            types='geocode'
        )
        
        if not autocomplete:
            print("No matching addresses found")
            return None
            
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
            return None
            
        # Get the place details for the selected address
        place = next((p for p in autocomplete if p['description'] == selected), None)
        return place['place_id']
        
    def search_businesses(self, place_id, radius=2500, business_type=None):
        """Search for businesses in a specific location"""
        # Get the location coordinates from place_id
        place_details = self.gmaps.place(place_id, fields=['geometry'])
        location = place_details['result']['geometry']['location']
        
        places_result = self.gmaps.places_nearby(
            location=f"{location['lat']},{location['lng']}",
            radius=radius,
            type=business_type
        )
        
        results = []
        for place in places_result['results']:
            # Get place details
            place_details = self.gmaps.place(
                place['place_id'],
                fields=['name', 'formatted_address', 'formatted_phone_number',
                       'website', 'opening_hours', 'business_status',
                       'wheelchair_accessible_entrance']
            )
            
            # Extract email if available
            website = place_details['result'].get('website', '')
            email = self.extract_email(website) if website else ''
            
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
            
        return pd.DataFrame(results)
    
    def extract_email(self, website):
        """Extract email from website (basic implementation)"""
        # This would need a proper implementation using requests/BeautifulSoup
        # or a dedicated email extraction service
        return ''
    
    def format_opening_hours(self, opening_hours):
        """Format opening hours into readable string"""
        if not opening_hours:
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
    # Get API key from environment variables
    API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    if not API_KEY:
        raise ValueError("GOOGLE_MAPS_API_KEY not found in .env file")
        
    scraper = GoogleMapsScraper(API_KEY)
    
    # Get address from user
    address = input("Enter the town/address to search near: ")
    if not address:
        return
        
    # Validate address
    place_id = scraper.validate_address(address)
    if not place_id:
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
        return
        
    # Search all business types
    business_type = None
    print("\nSearching all business types...")
    
    # Perform search
    results = scraper.search_businesses(
        place_id=place_id,
        radius=radius,
        business_type=business_type
    )
    
    # Save results to memory
    scraper.cached_results = results.to_dict('records')
    
    # Show confirmation list
    print("\nFound these businesses:")
    for i, business in enumerate(scraper.cached_results, 1):
        print(f"{i}. {business['name']} - {business['address']}")
    
    # Confirm before saving
    confirm = input(f"\nSave {len(scraper.cached_results)} businesses to JSON? (y/n): ").lower()
    if confirm != 'y':
        print("Operation cancelled.")
        return
        
    # Add location metadata to each business
    location_name = input("Enter a name for this location search (e.g., 'Sydney CBD'): ")
    
    if not location_name:
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
        with open(output_file, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
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
    
    print(f"\nAdded {len(new_businesses)} new businesses to {output_file}")
    print(f"Total businesses in file: {len(combined_data)}")
    
    # Ask about scraping
    if input("Do you want to scrape these places? (y/n): ").lower() == 'y':
        # Add scraping logic here
        print("Scraping additional details...")
        # You can access the cached results with place IDs
        for business in scraper.cached_results:
            # Add your scraping logic here
            pass
            
if __name__ == "__main__":
    main()
