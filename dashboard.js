class Dashboard {
    constructor() {
        this.businesses = [];
        this.consoleElement = document.getElementById('console-log');
        this.businessContainer = document.getElementById('businesses-container');
        this.searchBtn = document.getElementById('search-btn');
        this.sortSelect = document.getElementById('sort-by');
        this.filterInput = document.getElementById('filter');
        this.sidebar = document.getElementById('sidebar-content');
        this.selectedBusiness = null;
        
        // Add console toggle
        this.consoleToggle = document.createElement('div');
        this.consoleToggle.className = 'console-toggle';
        this.consoleToggle.textContent = 'Show Log';
        document.body.appendChild(this.consoleToggle);
        
        this.initialize();
    }

    async initialize() {
        this.log('Initializing dashboard...');
        await this.loadBusinesses();
        this.setupEventListeners();
        this.renderBusinesses();
    }

    async loadBusinesses() {
        try {
            this.log("Loading businesses from local JSON file...");
            const response = await fetch('businesses.json');
            
            if (!response.ok) {
                throw new Error(`Failed to load businesses.json: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Handle both array and object with data property
            const businessesArray = Array.isArray(data) ? data : (data.data || []);
            
            this.log(`Successfully loaded ${businessesArray.length} businesses`);
                
            // Debug: Log first business structure
            if (businessesArray.length > 0) {
                this.log(`First business data structure: ${JSON.stringify(businessesArray[0], null, 2)}`);
            }
            
            this.businesses = businessesArray;
                
                // Add unique IDs if missing
                this.businesses = this.businesses.map((b, i) => {
                    if (!b.id) {
                        b.id = `biz-${i + 1}`;
                    }
                    return b;
                });
                
                this.log(`Loaded ${this.businesses.length} businesses`);
                this.log(`First business after processing: ${JSON.stringify(this.businesses[0], null, 2)}`);
            if (this.businesses.length === 0) {
                this.log("No businesses found in businesses.json", 'warning');
            }
            
            // Debug: Check if businesses have required fields
            if (this.businesses.length > 0) {
                const requiredFields = ['name', 'address', 'business_type', 'opening_hours'];
                const missingFields = requiredFields.filter(field => !(field in this.businesses[0]));
                
                if (missingFields.length > 0) {
                    this.log(`Warning: Missing required fields in business data: ${missingFields.join(', ')}`, 'warning');
                }
            }
        } catch (error) {
            this.log(`Error loading businesses: ${error.message}`, 'error');
            console.error('Error loading businesses:', error);
        }
    }

    setupEventListeners() {
        if (this.searchBtn) {
            this.searchBtn.addEventListener('click', () => this.handleSearch());
        }
        if (this.sortSelect) {
            this.sortSelect.addEventListener('change', () => this.renderBusinesses());
        }
        if (this.filterInput) {
            this.filterInput.addEventListener('input', () => this.renderBusinesses());
        }
        
        // Console toggle
        this.consoleToggle.addEventListener('click', () => {
            const consoleEl = document.querySelector('.console');
            consoleEl.classList.toggle('open');
            this.consoleToggle.textContent = consoleEl.classList.contains('open') ? 'Hide Log' : 'Show Log';
        });
        
        // Close console when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.console') && !e.target.closest('.console-toggle')) {
                document.querySelector('.console').classList.remove('open');
                this.consoleToggle.textContent = 'Show Log';
            }
        });
    }

    handleSearch() {
        const query = document.getElementById('search-input').value;
        this.log(`Searching for: ${query}`);
        // Implement search functionality
    }

    renderBusinesses() {
        this.log(`Rendering businesses (total: ${this.businesses.length})`);
        
        const sortBy = this.sortSelect.value;
        const filter = this.filterInput.value.toLowerCase();
        
        let filtered = this.businesses.filter(b => {
            if (!b.name || !b.business_type) {
                this.log(`Warning: Business missing required fields - name: ${b.name}, type: ${b.business_type}`, 'warning');
                return false;
            }
            return b.name.toLowerCase().includes(filter) ||
                   b.business_type.toLowerCase().includes(filter);
        });

        this.log(`Filtered to ${filtered.length} businesses matching "${filter}"`);

        filtered.sort((a, b) => {
            if (sortBy === 'name') return a.name.localeCompare(b.name);
            if (sortBy === 'type') return a.business_type.localeCompare(b.business_type);
            if (sortBy === 'date') return new Date(b.search_date) - new Date(a.search_date);
            return 0;
        });

        // Safely render opening hours with error handling
        const renderOpeningHours = (hours) => {
            if (!hours) return '';
            try {
                return hours.split('\n').map(hour => `<div>${hour}</div>`).join('');
            } catch (error) {
                this.log(`Error rendering opening hours: ${error.message}`, 'error');
                return '<div>Hours information unavailable</div>';
            }
        };

        this.businessContainer.innerHTML = filtered.map(b => {
            try {
                // Safely access properties with fallbacks
                const name = b.name || 'No Name';
                const businessType = (b.business_type || 'unknown').replace(/_/g, ' ');
                const address = b.address || 'No Address';
                const hours = b.opening_hours ? renderOpeningHours(b.opening_hours) : '';
                const id = b.id || `biz-${Math.random().toString(36).substr(2, 9)}`;

                return `
                    <div class="business-card" data-id="${id}" onclick="dashboard.showBusinessDetails('${id}')">
                        <div class="business-header">
                            <h3 class="text-xl font-semibold text-gray-800 mb-2">${name}</h3>
                            <div class="business-tag bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-sm">${businessType}</div>
                        </div>
                        <div class="space-y-4">
                                <div class="info-section">
                                    <div class="info-label text-sm font-medium text-gray-500 mb-1">Address</div>
                                    <div class="info-value text-gray-700">${address}</div>
                                </div>

                                ${b.latitude && b.longitude ? `
                                <div class="info-section">
                                    <div class="info-label text-sm font-medium text-gray-500 mb-1">Location</div>
                                    <a href="https://www.google.com/maps/search/?api=1&query=${b.latitude},${b.longitude}" 
                                       target="_blank" 
                                       class="text-blue-600 hover:text-blue-700">
                                        View on Map
                                    </a>
                                </div>` : ''}

                                ${b.phone ? `
                                <div class="info-section">
                                    <div class="info-label text-sm font-medium text-gray-500 mb-1">Phone</div>
                                    <a href="tel:${b.phone}" class="info-value text-gray-700 hover:text-blue-600">${b.phone}</a>
                                </div>` : ''}

                                ${b.website ? `
                                <div class="info-section">
                                    <div class="info-label text-sm font-medium text-gray-500 mb-1">Website</div>
                                    <a href="${b.website}" target="_blank" class="info-value text-blue-600 hover:text-blue-700 break-all">${b.website}</a>
                                </div>` : ''}

                                ${hours ? `
                                <div class="info-section">
                                    <div class="info-label text-sm font-medium text-gray-500 mb-1">Opening Hours</div>
                                    <div class="info-value text-gray-700 space-y-1">
                                        ${hours.split('\n').map(hour => `
                                            <div>${hour}</div>
                                        `).join('')}
                                    </div>
                                </div>` : ''}
                            </div>
                        </div>
                    </div>
                `;
            } catch (error) {
                this.log(`Error rendering business card: ${error.message}`, 'error');
                return `
                    <div class="business-card error">
                        <div class="business-header">
                            <h3>Error Rendering Business</h3>
                        </div>
                        <div class="business-info">
                            <div class="info-row">Error loading business information</div>
                        </div>
                    </div>
                `;
            }
        }).join('');
        
        // Add click handler for business cards
        this.businessContainer.querySelectorAll('.business-card').forEach(card => {
            card.addEventListener('click', function(e) {
                // Prevent double triggering from both onclick and event listener
                if (e.target.tagName !== 'A') {
                    const id = card.dataset.id;
                    dashboard.showBusinessDetails(id);
                }
            });
        });
    }

    showBusinessDetails(id) {
        if (!id) {
            this.log('No business ID provided', 'error');
            return;
        }
        
        const business = this.businesses.find(b => b.id === id);
        if (!business) {
            this.log(`Business with ID ${id} not found`, 'error');
            return;
        }
        
        this.selectedBusiness = business;
        this.sidebar.innerHTML = `
            <div class="sidebar-content">
                <h2 class="text-xl font-semibold mb-4">${business.name}</h2>
                <div class="space-y-4">
                    <div class="info-section">
                        <h3 class="section-title">Location</h3>
                        <div class="info-content">
                            <p>${business.address}</p>
                            ${business.latitude && business.longitude ? `
                            <div class="map-link">
                                <a href="https://www.google.com/maps/search/?api=1&query=${business.latitude},${business.longitude}" 
                                   target="_blank" 
                                   class="link">
                                    View on Google Maps
                                </a>
                            </div>` : ''}
                        </div>
                    </div>
                    
                    <div class="info-section">
                        <h3 class="section-title">Contact</h3>
                        <div class="info-content">
                            ${business.phone ? `<p>Phone: ${business.phone}</p>` : ''}
                            ${business.email ? `<p>Email: ${business.email}</p>` : ''}
                            ${business.website ? `
                                <p>Website: 
                                    <a href="${business.website}" target="_blank" class="link">
                                        ${business.website}
                                    </a>
                                </p>` : ''}
                        </div>
                    </div>
                    
                    ${business.opening_hours ? `
                    <div class="info-section">
                        <h3 class="section-title">Opening Hours</h3>
                        <div class="info-content">
                            ${business.opening_hours.split('\n').map(hour => `
                                <div class="hour-row">${hour}</div>
                            `).join('')}
                        </div>
                    </div>` : ''}
                </div>
            </div>
        `;
    }

    log(message, type = 'info') {
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        this.consoleElement.appendChild(entry);
        this.consoleElement.scrollTop = this.consoleElement.scrollHeight;
    }
}

// Initialize dashboard when page loads
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new Dashboard();
});
