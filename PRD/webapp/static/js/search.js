// ============================================
// Search Page JavaScript
// ============================================

document.addEventListener('DOMContentLoaded', () => {
            // Tab switching
            const tabButtons = document.querySelectorAll('.tab-button');
            const tabContents = document.querySelectorAll('.tab-content');

            tabButtons.forEach(button => {
                button.addEventListener('click', () => {
                    const tabName = button.dataset.tab;

                    // Remove active class from all tabs
                    tabButtons.forEach(btn => btn.classList.remove('active'));
                    tabContents.forEach(content => content.classList.remove('active'));

                    // Add active class to clicked tab
                    button.classList.add('active');
                    document.getElementById(`${tabName}-tab`).classList.add('active');
                });
            });

            // ============================================
            // Search by Postcode
            // ============================================

            const postcodeInput = document.getElementById('postcode-input');
            const postcodeSearchBtn = document.getElementById('postcode-search-btn');
            const postcodeResults = document.getElementById('postcode-results');

            async function searchByPostcode() {
                const postcode = postcodeInput.value.trim();

                if (!postcode) {
                    postcodeResults.innerHTML = '<div class="error">Please enter a postcode</div>';
                    return;
                }

                if (postcode.length !== 4 || !/^\d{4}$/.test(postcode)) {
                    postcodeResults.innerHTML = '<div class="error">Please enter a valid 4-digit postcode</div>';
                    return;
                }

                showLoading('postcode-results');

                try {
                    const response = await fetch(`/api/search/suburbs?postcode=${postcode}`);
                    const data = await response.json();

                    if (!response.ok) {
                        throw new Error(data.error || 'Failed to fetch data');
                    }

                    if (data.suburbs.length === 0) {
                        postcodeResults.innerHTML = `
                    <div class="no-results">
                        No suburbs found for postcode ${postcode}
                    </div>
                `;
                        return;
                    }

                    postcodeResults.innerHTML = `
                <div class="results-header">
                    <div class="results-title">Suburbs for Postcode ${postcode}</div>
                    <div class="results-count">${data.count} result(s)</div>
                </div>
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>Suburb</th>
                            <th>Postcode</th>
                            <th>State</th>
                            <th>Addresses</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.suburbs.map(suburb => `
                            <tr class="clickable-row" data-suburb="${suburb.suburb}" data-postcode="${suburb.postcode}">
                                <td><strong>${suburb.suburb}</strong></td>
                                <td>${suburb.postcode}</td>
                                <td>${suburb.state}</td>
                                <td>${formatNumber(suburb.address_count)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
                    
                    // Add click handlers to navigate to address lookup
                    const rows = postcodeResults.querySelectorAll('.clickable-row');
                    rows.forEach(row => {
                        row.addEventListener('click', () => {
                            const suburb = row.dataset.suburb;
                            const postcode = row.dataset.postcode;
                            window.location.href = `/address-lookup?suburb=${encodeURIComponent(suburb)}&postcode=${encodeURIComponent(postcode)}&auto=true`;
                        });
                    });
        } catch (error) {
            postcodeResults.innerHTML = handleAPIError(error);
        }
    }
    
    postcodeSearchBtn.addEventListener('click', searchByPostcode);
    postcodeInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchByPostcode();
    });
    
    // ============================================
    // Search by Suburb
    // ============================================
    
    const suburbInput = document.getElementById('suburb-input');
    const suburbSearchBtn = document.getElementById('suburb-search-btn');
    const suburbResults = document.getElementById('suburb-results');
    const autocompleteDiv = document.getElementById('suburb-autocomplete');
    
    async function searchBySuburb() {
        const suburb = suburbInput.value.trim();
        
        if (!suburb) {
            suburbResults.innerHTML = '<div class="error">Please enter a suburb name</div>';
            return;
        }
        
        showLoading('suburb-results');
        autocompleteDiv.innerHTML = ''; // Clear autocomplete
        
        try {
            const response = await fetch(`/api/search/postcodes?suburb=${encodeURIComponent(suburb)}`);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch data');
            }
            
            if (data.results.length === 0) {
                suburbResults.innerHTML = `
                    <div class="no-results">
                        No postcodes found for suburb "${suburb}"
                    </div>
                `;
                return;
            }
            
            suburbResults.innerHTML = `
                <div class="results-header">
                    <div class="results-title">Results for "${suburb}"</div>
                    <div class="results-count">${data.count} result(s)</div>
                </div>
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>Suburb</th>
                            <th>Postcode</th>
                            <th>State</th>
                            <th>Addresses</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.results.map(result => `
                            <tr class="clickable-row" data-suburb="${result.suburb}" data-postcode="${result.postcode}">
                                <td><strong>${result.suburb}</strong></td>
                                <td>${result.postcode}</td>
                                <td>${result.state}</td>
                                <td>${formatNumber(result.address_count)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
                    
                    // Add click handlers to navigate to address lookup
                    const rows = suburbResults.querySelectorAll('.clickable-row');
                    rows.forEach(row => {
                        row.addEventListener('click', () => {
                            const suburb = row.dataset.suburb;
                            const postcode = row.dataset.postcode;
                            window.location.href = `/address-lookup?suburb=${encodeURIComponent(suburb)}&postcode=${encodeURIComponent(postcode)}&auto=true`;
                        });
                    });
        } catch (error) {
            suburbResults.innerHTML = handleAPIError(error);
        }
    }
    
    // Autocomplete for suburb search
    const autocompleteSuburbs = debounce(async (query) => {
        if (query.length < 2) {
            autocompleteDiv.innerHTML = '';
            return;
        }
        
        try {
            const response = await fetch(`/api/autocomplete/suburbs?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.length === 0) {
                autocompleteDiv.innerHTML = '';
                return;
            }
            
            autocompleteDiv.innerHTML = data.map(item => `
                <div class="autocomplete-item" data-suburb="${item.suburb}">
                    <strong>${item.suburb}</strong> - ${item.postcode} (${item.state})
                </div>
            `).join('');
            
            // Add click handlers to autocomplete items
            document.querySelectorAll('.autocomplete-item').forEach(item => {
                item.addEventListener('click', () => {
                    suburbInput.value = item.dataset.suburb;
                    autocompleteDiv.innerHTML = '';
                    searchBySuburb();
                });
            });
        } catch (error) {
            console.error('Autocomplete error:', error);
        }
    }, 300);
    
    suburbInput.addEventListener('input', (e) => {
        autocompleteSuburbs(e.target.value);
    });
    
    suburbSearchBtn.addEventListener('click', searchBySuburb);
    suburbInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchBySuburb();
    });
    
    // Clear autocomplete when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('#suburb-input') && !e.target.closest('#suburb-autocomplete')) {
            autocompleteDiv.innerHTML = '';
        }
    });
});