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
        
    # Get business type
    business_type = questionary.text(
        "Enter business type (restaurant, cafe, etc) or leave blank:"
    ).ask()
    
    # Perform search
    results = scraper.search_businesses(
        place_id=place_id,
        radius=radius,
        business_type=business_type
    )
    
    # Save results to memory
    scraper.cached_results = results.to_dict('records')
    
    # Show results count
    print(f"\nFound {len(scraper.cached_results)} businesses")
    
    # Save to JSON
    with open('businesses.json', 'w') as f:
        json.dump(scraper.cached_results, f, indent=2)
    print("Results saved to businesses.json")
    
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
