import googlemaps
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class GoogleMapsScraper:
    def __init__(self, api_key):
        self.gmaps = googlemaps.Client(key=api_key)
        
    def search_businesses(self, location, radius=5000, business_type=None):
        """Search for businesses in a specific location"""
        places_result = self.gmaps.places_nearby(
            location=location,
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

# Example usage:
if __name__ == "__main__":
    # Get API key from environment variables
    API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    if not API_KEY:
        raise ValueError("GOOGLE_MAPS_API_KEY not found in .env file")
        
    scraper = GoogleMapsScraper(API_KEY)
    
    # Search for restaurants in Sydney
    location = "-33.8670522,151.1957362"  # Sydney coordinates
    results = scraper.search_businesses(location, business_type='restaurant')
    
    # Save to CSV
    results.to_csv('businesses.csv', index=False)
