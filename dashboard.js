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
            const response = await fetch('http://localhost:8000/businesses');
            const data = await response.json();
            this.businesses = data.data;
            
            // Add unique IDs if missing
            this.businesses = this.businesses.map((b, i) => {
                if (!b.id) {
                    b.id = `biz-${i + 1}`;
                }
                return b;
            });
            
            this.log(`Loaded ${this.businesses.length} businesses`);
        } catch (error) {
            this.log(`Error loading businesses: ${error.message}`, 'error');
        }
    }

    setupEventListeners() {
        this.searchBtn.addEventListener('click', () => this.handleSearch());
        this.sortSelect.addEventListener('change', () => this.renderBusinesses());
        this.filterInput.addEventListener('input', () => this.renderBusinesses());
        
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
        const sortBy = this.sortSelect.value;
        const filter = this.filterInput.value.toLowerCase();
        
        let filtered = this.businesses.filter(b => 
            b.name.toLowerCase().includes(filter) ||
            b.business_type.toLowerCase().includes(filter)
        );

        filtered.sort((a, b) => {
            if (sortBy === 'name') return a.name.localeCompare(b.name);
            if (sortBy === 'type') return a.business_type.localeCompare(b.business_type);
            if (sortBy === 'date') return new Date(b.search_date) - new Date(a.search_date);
            return 0;
        });

        this.businessContainer.innerHTML = filtered.map(b => `
            <div class="business-card" data-id="${b.id}" onclick="dashboard.showBusinessDetails('${b.id}')">
                <div class="business-header">
                    <h3>${b.name}</h3>
                    <div class="business-tag">${b.business_type.replace(/_/g, ' ')}</div>
                </div>
                <div class="business-info">
                    <div class="info-row">
                        <span class="info-label">Address:</span>
                        <span class="info-value">${b.address}</span>
                    </div>
                    ${b.phone ? `<div class="info-row">
                        <span class="info-label">Phone:</span>
                        <span class="info-value">${b.phone}</span>
                    </div>` : ''}
                    ${b.website ? `<div class="info-row">
                        <span class="info-label">Website:</span>
                        <a href="${b.website}" target="_blank" class="info-value link">Visit Website</a>
                    </div>` : ''}
                    <div class="info-row">
                        <span class="info-label">Hours:</span>
                        <div class="info-value">
                            ${b.opening_hours.split('\n').map(hour => `<div>${hour}</div>`).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
        
        // Add click handler for business cards
        this.businessContainer.querySelectorAll('.business-card').forEach(card => {
            card.addEventListener('click', () => {
                const id = card.dataset.id;
                this.showBusinessDetails(id);
            });
        });
    }

    showBusinessDetails(id) {
        const business = this.businesses.find(b => b.id === id);
        if (!business) return;
        
        this.selectedBusiness = business;
        this.sidebar.innerHTML = `
            <div class="sidebar-content">
                <h2 class="text-xl font-semibold mb-4">${business.name}</h2>
                <div class="space-y-4">
                    <div class="info-section">
                        <h3 class="section-title">Location</h3>
                        <div class="info-content">
                            <p>${business.address}</p>
                            <div class="map-link">
                                <a href="https://www.google.com/maps/search/?api=1&query=${business.latitude},${business.longitude}" 
                                   target="_blank" 
                                   class="link">
                                    View on Google Maps
                                </a>
                            </div>
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
                    
                    <div class="info-section">
                        <h3 class="section-title">Opening Hours</h3>
                        <div class="info-content">
                            ${business.opening_hours.split('\n').map(hour => `
                                <div class="hour-row">${hour}</div>
                            `).join('')}
                        </div>
                    </div>
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
document.addEventListener('DOMContentLoaded', () => new Dashboard());
