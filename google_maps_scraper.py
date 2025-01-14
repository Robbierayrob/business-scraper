import googlemaps
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os
import questionary

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
            
        choices = [f"{result['description']}" for result in autocomplete]
        selected = questionary.select(
            "Please confirm the correct address:",
            choices=choices
        ).ask()
        
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
            open_time = datetime.strptime(
                period['open']['time'], '%H%M'
            ).strftime('%I:%M %p')
            close_time = datetime.strptime(
                period['close']['time'], '%H%M'
            ).strftime('%I:%M %p')
            formatted_hours.append(f"{open_time} - {close_time}")
            
        return '\n'.join(formatted_hours)

def main():
    # Get API key from environment variables
    API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    if not API_KEY:
        raise ValueError("GOOGLE_MAPS_API_KEY not found in .env file")
        
    scraper = GoogleMapsScraper(API_KEY)
    
    # Get address from user
    address = questionary.text("Enter the town/address to search near:").ask()
    if not address:
        return
        
    # Validate address
    place_id = scraper.validate_address(address)
    if not place_id:
        return
        
    # Get search radius
    radius = questionary.select(
        "Select search radius:",
        choices=[
            ("2.5 km", 2500),
            ("5 km", 5000),
            ("10 km", 10000)
        ]
    ).ask()
    
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
    if not questionary.confirm(f"\nSave {len(scraper.cached_results)} businesses to JSON?").ask():
        print("Operation cancelled.")
        return
        
    # Add location metadata to each business
    location_name = questionary.text(
        "Enter a name for this location search (e.g., 'Sydney CBD'):"
    ).ask()
    
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
    if questionary.confirm("Do you want to scrape these places?").ask():
        # Add scraping logic here
        print("Scraping additional details...")
        # You can access the cached results with place IDs
        for business in scraper.cached_results:
            # Add your scraping logic here
            pass
            
if __name__ == "__main__":
    main()
