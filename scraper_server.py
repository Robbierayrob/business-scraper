from datetime import datetime
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google_maps_scraper import GoogleMapsScraper
from dotenv import load_dotenv
import os
import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize scraper
API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
if not API_KEY:
    raise ValueError("GOOGLE_MAPS_API_KEY not found in .env file")
scraper = GoogleMapsScraper(API_KEY)

@app.post("/validate-address")
async def validate_address(address: str):
    try:
        suggestions = scraper.validate_address(address)
        if not suggestions:
            raise HTTPException(status_code=400, detail="No matching addresses found")
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_businesses(place_id: str, radius: int = 2500, business_types: list = None):
    try:
        # Search businesses using provided place_id
        results = scraper.search_businesses(place_id, radius, business_types)
        
        # Add metadata
        businesses = results.to_dict('records')
        for business in businesses:
            business['search_date'] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "count": len(businesses),
            "data": businesses
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/businesses")
async def get_businesses():
    try:
        with open('businesses.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Ensure data is in the correct format
        if not isinstance(data, list):
            data = [data]
            
        return {
            "status": "success",
            "count": len(data),
            "data": data
        }
    except FileNotFoundError:
        return {
            "status": "success",
            "count": 0,
            "data": []
        }
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid JSON format: {str(e)}",
            "count": 0,
            "data": []
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
