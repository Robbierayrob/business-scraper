class Dashboard {
    constructor() {
        this.businesses = [];
        this.consoleElement = document.getElementById('console-log');
        this.businessContainer = document.getElementById('businesses-container');
        this.searchBtn = document.getElementById('search-btn');
        this.sortSelect = document.getElementById('sort-by');
        this.filterInput = document.getElementById('filter');
        
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
            const response = await fetch('businesses.json');
            this.businesses = await response.json();
            
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
            <div class="business-card" data-id="${b.id}">
                <h3>${b.name}</h3>
                <p><strong>Type:</strong> ${b.business_type}</p>
                <p><strong>Address:</strong> ${b.address}</p>
                <p><strong>Added:</strong> ${new Date(b.search_date).toLocaleDateString()}</p>
            </div>
        `).join('');
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
