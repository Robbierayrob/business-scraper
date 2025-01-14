# 🗺️ Australian Business Scraper and Dashboard

A powerful tool to extract and visualize business data from Google Maps. The project consists of:
- **Python Scraper**: Extracts business information using Google Maps API
- **Web Dashboard**: Interactive interface to explore and analyze the collected data

![Dashboard Screenshot](https://github.com/yourusername/business-scraper/raw/main/screenshot_01.PNG)

## 🚀 Features

### Scraper Features
- ✅ Search businesses by location and radius
- ✅ Filter by business types
- ✅ Automatic deduplication
- ✅ Caching to minimize API calls
- ✅ Cost estimation before running
- ✅ Detailed logging

### Dashboard Features
- 🔍 Search and filter businesses
- 📊 Sort by name, type, or date
- 📄 Detailed business information view
- 📝 Activity log
- 🎨 Color-coded business types

## ⚙️ Setup

### Prerequisites
- Python 3.8+
- Google Maps API Key ([Get one here](https://console.cloud.google.com/))

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/business-scraper.git
   cd business-scraper
   ```

2. Set up virtual environment:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file:
   ```env
   GOOGLE_MAPS_API_KEY=your_api_key_here
   ```

## 🛠️ Usage

### Running the Scraper
```bash
python google_maps_scraper.py
```
The scraper will prompt for:
- Location/address
- Search radius (in km)
- Business types to search

Results are saved to `businesses.json` and logs to `scraper.log`

### Using the Dashboard
1. Run the dashboard:
   ```bash
   # Windows
   start index.html
   # macOS
   open index.html
   # Linux
   xdg-open index.html
   ```

2. Explore features:
   - Search by name/type
   - Sort results
   - View detailed business info
   - Monitor activity logs

## 💡 Tips
- Start with a small radius to test
- Use specific business types for better results
- Monitor API costs in the scraper
- Check the logs for detailed activity

## 📦 Dependencies
- `googlemaps` - Google Maps API client
- `python-dotenv` - Environment variable management
- `pandas` - Data processing
- `fastapi` - (Future API integration)

## 🤝 Contributing
Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License
MIT License - See [LICENSE](LICENSE) for details

## 📋 TODO: Additional Data Sources

### Australian Business Data
- [ ] ABN Lookup (https://abr.business.gov.au/)
  - Scrape business details using ABN
  - Verify business registration status
  - Get GST registration information
- [ ] ASIC Connect (https://connectonline.asic.gov.au/)
  - Company registration details
  - Officeholder information
  - Business names registry
- [ ] Australian Business Register
  - Bulk data downloads
  - Business location mapping
- [ ] State-based business directories
  - NSW Fair Trading
  - Victorian Business Licence Finder
  - QLD Business and Industry Portal

### International Business Data
- [ ] LinkedIn Company Pages
- [ ] Crunchbase
- [ ] Yellow Pages Australia
- [ ] TrueLocal
- [ ] Industry-specific directories

### Features to Add
- [ ] Data enrichment from multiple sources
- [ ] Automated data validation
- [ ] Bulk ABN lookup integration
- [ ] Business health scoring
- [ ] Competitor analysis tools

> **Note:** This project uses Google Maps API which may incur costs. Please monitor your API usage.
