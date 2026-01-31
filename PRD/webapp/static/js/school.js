/**
 * School Catchment Search JavaScript
 * Handles school autocomplete, address filtering, and map visualization
 */

// Global state
let currentSchoolId = null;
let currentSchoolLocation = null;
let allAddresses = [];
let filteredAddresses = [];
let debounceTimer = null;
let catchmentMap = null;
let catchmentLayer = null;
let currentPage = 1;
let totalPages = 1;
let pageSize = 500;
let totalAddresses = 0;

// DOM Elements
const schoolInput = document.getElementById('schoolInput');
const schoolSuggestions = document.getElementById('schoolSuggestions');
const schoolSearchForm = document.getElementById('schoolSearchForm');
const schoolInfoSection = document.getElementById('schoolInfoSection');
const mapSection = document.getElementById('mapSection');
const addressSearchSection = document.getElementById('addressSearchSection');
const resultsSection = document.getElementById('resultsSection');
const loadingIndicator = document.getElementById('loadingIndicator');
const searchResults = document.getElementById('searchResults');

// Search form elements
const searchStreetNumber = document.getElementById('searchStreetNumber');
const searchStreet = document.getElementById('searchStreet');
const searchSuburb = document.getElementById('searchSuburb');
const searchPostcode = document.getElementById('searchPostcode');
const searchState = document.getElementById('searchState');
const searchLimit = document.getElementById('searchLimit');
const searchAddressBtn = document.getElementById('searchAddressBtn');
const searchStreetSuggestions = document.getElementById('search-street-suggestions');
const searchSuburbSuggestions = document.getElementById('search-suburb-suggestions');

// Check for URL parameters to auto-load a school
const urlParams = new URLSearchParams(window.location.search);
const schoolIdParam = urlParams.get('school_id');
if (schoolIdParam) {
    currentSchoolId = parseInt(schoolIdParam);
    // Auto-load the school after a short delay to ensure DOM is ready
    setTimeout(() => {
        loadSchoolData(currentSchoolId);
    }, 100);
}

// ============================================
// Address Search Autocomplete
// ============================================

// Autocomplete for Street Name in address filter
let streetSearchDebounce;
if (searchStreet && searchStreetSuggestions) {
    searchStreet.addEventListener('input', (e) => {
        clearTimeout(streetSearchDebounce);
        const query = e.target.value.trim();

        if (query.length < 2) {
            searchStreetSuggestions.innerHTML = '';
            searchStreetSuggestions.style.display = 'none';
            return;
        }

        streetSearchDebounce = setTimeout(async() => {
            try {
                const response = await fetch(`/api/autocomplete/streets?q=${encodeURIComponent(query)}`);
                const data = await response.json();

                if (data.length > 0) {
                    searchStreetSuggestions.innerHTML = data.map(item => {
                        const streetFull = item.street_type ? `${item.street_name} ${item.street_type}` : item.street_name;
                        return `<div class="suggestion-item" data-value="${item.street_name}">${streetFull}</div>`;
                    }).join('');
                    searchStreetSuggestions.style.display = 'block';

                    // Add click handlers
                    searchStreetSuggestions.querySelectorAll('.suggestion-item').forEach(item => {
                        item.addEventListener('click', () => {
                            searchStreet.value = item.dataset.value;
                            searchStreetSuggestions.style.display = 'none';
                        });
                    });
                } else {
                    searchStreetSuggestions.style.display = 'none';
                }
            } catch (error) {
                console.error('Error fetching street suggestions:', error);
            }
        }, 300);
    });
}

// Autocomplete for Suburb in address filter
let suburbSearchDebounce;
if (searchSuburb && searchSuburbSuggestions) {
    searchSuburb.addEventListener('input', (e) => {
        clearTimeout(suburbSearchDebounce);
        const query = e.target.value.trim();

        if (query.length < 2) {
            searchSuburbSuggestions.innerHTML = '';
            searchSuburbSuggestions.style.display = 'none';
            return;
        }

        suburbSearchDebounce = setTimeout(async() => {
            try {
                const response = await fetch(`/api/autocomplete/suburbs?q=${encodeURIComponent(query)}`);
                const data = await response.json();

                if (data.length > 0) {
                    searchSuburbSuggestions.innerHTML = data.map(item =>
                        `<div class="suggestion-item" data-value="${item.suburb}">
                            ${item.suburb} <span class="suggestion-meta">${item.state} ${item.postcode}</span>
                        </div>`
                    ).join('');
                    searchSuburbSuggestions.style.display = 'block';

                    // Add click handlers
                    searchSuburbSuggestions.querySelectorAll('.suggestion-item').forEach(item => {
                        item.addEventListener('click', () => {
                            searchSuburb.value = item.dataset.value;
                            searchSuburbSuggestions.style.display = 'none';
                        });
                    });
                } else {
                    searchSuburbSuggestions.style.display = 'none';
                }
            } catch (error) {
                console.error('Error fetching suburb suggestions:', error);
            }
        }, 300);
    });
}

// Hide suggestions when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.autocomplete-wrapper')) {
        if (searchStreetSuggestions) searchStreetSuggestions.style.display = 'none';
        if (searchSuburbSuggestions) searchSuburbSuggestions.style.display = 'none';
    }
});

// ============================================
// School Autocomplete
// ============================================

schoolInput.addEventListener('input', function() {
    const query = this.value.trim();

    // Clear previous timer
    clearTimeout(debounceTimer);

    if (query.length < 3) {
        schoolSuggestions.innerHTML = '';
        schoolSuggestions.style.display = 'none';
        return;
    }

    // Debounce API call
    debounceTimer = setTimeout(() => {
        fetchSchoolSuggestions(query);
    }, 300);
});

async function fetchSchoolSuggestions(query) {
    try {
        const url = `/api/autocomplete/schools?q=${encodeURIComponent(query)}`;
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displaySchoolSuggestions(data);
    } catch (error) {
        console.error('Error fetching school suggestions:', error);
        schoolSuggestions.innerHTML = '<div class="autocomplete-item error">Error loading suggestions</div>';
        schoolSuggestions.style.display = 'block';
    }
}

function displaySchoolSuggestions(schools) {
    if (!schools || schools.length === 0) {
        schoolSuggestions.innerHTML = '<div class="autocomplete-item no-results">No schools found</div>';
        schoolSuggestions.style.display = 'block';
        return;
    }

    schoolSuggestions.innerHTML = schools.map(school => `
        <div class="autocomplete-item" data-school-id="${school.school_id}" data-school-name="${school.school_name}">
            <div class="school-suggestion">
                <span class="school-name">${school.school_name}</span>
                <span class="school-meta">
                    <span class="badge badge-${school.school_type.toLowerCase()}">${school.school_type}</span>
                </span>
            </div>
        </div>
    `).join('');

    schoolSuggestions.style.display = 'block';

    // Add click handlers
    document.querySelectorAll('#schoolSuggestions .autocomplete-item').forEach(item => {
        item.addEventListener('click', function() {
            const schoolId = this.dataset.schoolId;
            const schoolName = this.dataset.schoolName;

            schoolInput.value = schoolName;
            currentSchoolId = schoolId;
            schoolSuggestions.style.display = 'none';

            // Auto-submit form
            loadSchoolData(schoolId);
        });
    });
}

// Close suggestions when clicking outside
document.addEventListener('click', function(e) {
    if (!schoolInput.contains(e.target) && !schoolSuggestions.contains(e.target)) {
        schoolSuggestions.style.display = 'none';
    }
});

// ============================================
// Form Submission
// ============================================

schoolSearchForm.addEventListener('submit', function(e) {
    e.preventDefault();

    if (currentSchoolId) {
        console.log('Selected school ID:', currentSchoolId);
        loadSchoolData(currentSchoolId);
    } else {
        // If user typed something but didn't select from dropdown,
        // try to find the best match by name
        const searchText = schoolInput.value.trim();
        if (searchText && searchText.length >= 3) {
            console.log('No school selected, searching for:', searchText);
            alert('Please select a school from the suggestions dropdown');
            schoolInput.focus();
        } else {
            alert('Please type at least 3 characters and select a school from the suggestions');
        }
    }
});

// ============================================
// Load School Data
// ============================================

async function loadSchoolData(schoolId) {
    console.log('loadSchoolData called with schoolId:', schoolId, 'type:', typeof schoolId);
    showLoading(true);
    hideAllSections();

    try {
        // Load school info and boundary
        console.log('Fetching /api/school/' + schoolId + '/info');
        const [infoResponse, boundaryResponse] = await Promise.all([
            fetch(`/api/school/${schoolId}/info`),
            fetch(`/api/school/${schoolId}/boundary`)
        ]);

        if (!infoResponse.ok) {
            throw new Error(`Info API error: ${infoResponse.status} ${infoResponse.statusText}`);
        }
        if (!boundaryResponse.ok) {
            throw new Error(`Boundary API error: ${boundaryResponse.status} ${boundaryResponse.statusText}`);
        }

        const info = await infoResponse.json();
        console.log('API response:', info);
        const boundaryData = await boundaryResponse.json();

        // Display school info and map
        displaySchoolInfo(info);
        displayCatchmentMap(boundaryData, info.school_location);

        // Show sections
        schoolInfoSection.style.display = 'block';
        mapSection.style.display = 'block';
        addressSearchSection.style.display = 'block';

        // Scroll to results
        schoolInfoSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    } catch (error) {
        console.error('Error loading school data:', error);
        alert('Error loading school data. Please try again.');
    } finally {
        showLoading(false);
    }
}

async function loadPage(page) {
    if (page < 1 || page > totalPages) return;

    showLoading(true);
    currentPage = page;
    const offset = (page - 1) * pageSize;

    try {
        const response = await fetch(`/api/school/${currentSchoolId}/addresses?limit=${pageSize}&offset=${offset}`);
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const addressData = await response.json();

        // Update total based on search results
        totalAddresses = addressData.total_count;
        totalPages = Math.ceil(totalAddresses / pageSize);

        // Replace addresses with new page
        allAddresses = addressData.addresses || [];
        filteredAddresses = [...allAddresses];

        // Re-display addresses
        displayAddresses(filteredAddresses);

        // Update filter count
        document.getElementById('filterResultCount').textContent = totalAddresses.toLocaleString();

        // Update pagination UI
        updatePagination();

        // Scroll to filter section
        if (page > 1) {
            filterSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    } catch (error) {
        console.error('Error loading page:', error);
        alert('Error loading addresses. Please try again.');
    } finally {
        showLoading(false);
    }
}

function updatePagination() {
    const paginationDiv = document.getElementById('paginationControls');
    if (!paginationDiv) return;

    if (totalPages <= 1) {
        paginationDiv.style.display = 'none';
        return;
    }

    paginationDiv.style.display = 'flex';

    // Update page info
    document.getElementById('pageInfo').textContent = `Page ${currentPage} of ${totalPages} (${totalAddresses.toLocaleString()} total addresses)`;

    // Generate page buttons
    const pageButtonsDiv = document.getElementById('pageButtons');
    pageButtonsDiv.innerHTML = '';

    // First button
    const firstBtn = document.createElement('button');
    firstBtn.textContent = 'First';
    firstBtn.className = 'btn-page';
    firstBtn.disabled = currentPage === 1;
    firstBtn.onclick = () => loadPage(1);
    pageButtonsDiv.appendChild(firstBtn);

    // Previous button
    const prevBtn = document.createElement('button');
    prevBtn.textContent = 'Previous';
    prevBtn.className = 'btn-page';
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = () => loadPage(currentPage - 1);
    pageButtonsDiv.appendChild(prevBtn);

    // Page number buttons (show max 7 pages)
    const maxButtons = 7;
    let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
    let endPage = Math.min(totalPages, startPage + maxButtons - 1);

    if (endPage - startPage < maxButtons - 1) {
        startPage = Math.max(1, endPage - maxButtons + 1);
    }

    if (startPage > 1) {
        const ellipsis = document.createElement('span');
        ellipsis.textContent = '...';
        ellipsis.className = 'page-ellipsis';
        pageButtonsDiv.appendChild(ellipsis);
    }

    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.textContent = i;
        pageBtn.className = i === currentPage ? 'btn-page active' : 'btn-page';
        pageBtn.onclick = () => loadPage(i);
        pageButtonsDiv.appendChild(pageBtn);
    }

    if (endPage < totalPages) {
        const ellipsis = document.createElement('span');
        ellipsis.textContent = '...';
        ellipsis.className = 'page-ellipsis';
        pageButtonsDiv.appendChild(ellipsis);
    }

    // Next button
    const nextBtn = document.createElement('button');
    nextBtn.textContent = 'Next';
    nextBtn.className = 'btn-page';
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.onclick = () => loadPage(currentPage + 1);
    pageButtonsDiv.appendChild(nextBtn);

    // Last button
    const lastBtn = document.createElement('button');
    lastBtn.textContent = 'Last';
    lastBtn.className = 'btn-page';
    lastBtn.disabled = currentPage === totalPages;
    lastBtn.onclick = () => loadPage(totalPages);
    pageButtonsDiv.appendChild(lastBtn);

    // Jump to page
    const jumpInput = document.getElementById('jumpToPage');
    if (jumpInput) {
        jumpInput.max = totalPages;
        jumpInput.value = currentPage;
    }
}

// ============================================
// Display Functions
// ============================================

function displaySchoolInfo(info) {
    // Debug: Log full API response
    console.log('displaySchoolInfo received:', info);
    
    document.getElementById('schoolName').textContent = info.school_name;
    document.getElementById('schoolTypeBadge').textContent = info.school_type;
    document.getElementById('schoolTypeBadge').className = `badge badge-${info.school_type.toLowerCase()}`;
    document.getElementById('yearLevels').textContent = info.year_levels;

    // Display school type description
    const typeDescriptions = {
        'PRIMARY': 'Government Primary School',
        'SECONDARY': 'Government Secondary School',
        'FUTURE': 'Planned Future School',
        'HIGH_GIRLS': 'Selective Girls High School',
        'HIGH_BOYS': 'Selective Boys High School',
        'HIGH_CO_ED': 'Selective Co-Ed High School',
        'HIGH': 'Selective High School'
    };
    document.getElementById('schoolType').textContent = typeDescriptions[info.school_type] || (info.school_type ? `Government ${info.school_type} School` : 'Government School');

    // Display school sector
    document.getElementById('schoolSector').textContent = info.school_sector || 'N/A';

    // Display school URL if available
    if (info.school_url && info.school_url.trim()) {
        let urlString = info.school_url.trim();
        // Add https:// if no protocol is specified
        if (!urlString.startsWith('http://') && !urlString.startsWith('https://')) {
            urlString = 'https://' + urlString;
        }
        document.getElementById('schoolUrl').href = urlString;
        document.getElementById('schoolUrlText').textContent = info.school_name;
        document.getElementById('schoolUrl-container').style.display = 'block';
    } else {
        document.getElementById('schoolUrl-container').style.display = 'none';
    }

    // Display catchment priority
    const priorityDescriptions = {
        '1': 'Local Intake Area',
        '2': 'Buffer Zone',
        '3': 'Non-Local'
    };
    document.getElementById('catchmentPriority').textContent = priorityDescriptions[info.priority] || (info.priority ? `Priority ${info.priority}` : 'N/A');

    // Display ICSEA if available
    console.log('ICSEA value:', info.icsea, 'Type:', typeof info.icsea);
    if (info.icsea !== null && info.icsea !== undefined && info.icsea !== '') {
        document.getElementById('icsea').textContent = Math.round(info.icsea);
        document.getElementById('icsea-container').style.display = 'block';
        console.log('✓ ICSEA displayed:', Math.round(info.icsea));
    } else {
        document.getElementById('icsea-container').style.display = 'none';
        console.log('✗ ICSEA hidden (value is:', info.icsea, ')');
    }

    // Display ICSEA percentile if available
    console.log('ICSEA percentile value:', info.icsea_percentile, 'Type:', typeof info.icsea_percentile);
    if (info.icsea_percentile !== null && info.icsea_percentile !== undefined && info.icsea_percentile !== '') {
        document.getElementById('icsea-percentile').textContent = Math.round(info.icsea_percentile) + '%';
        document.getElementById('icsea-percentile-container').style.display = 'block';
        console.log('✓ ICSEA percentile displayed:', Math.round(info.icsea_percentile) + '%');
    } else {
        document.getElementById('icsea-percentile-container').style.display = 'none';
        console.log('✗ ICSEA percentile hidden (value is:', info.icsea_percentile, ')');
    }
}

function displayCatchmentMap(boundaryData, schoolLocation) {
    // Initialize map if not exists
    if (!catchmentMap) {
        catchmentMap = L.map('catchmentMap').setView([-33.8688, 151.2093], 13); // Default to Sydney

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(catchmentMap);
    }

    // Remove existing layer
    if (catchmentLayer) {
        catchmentMap.removeLayer(catchmentLayer);
    }

    // Add catchment boundary
    catchmentLayer = L.geoJSON(boundaryData.geojson, {
        style: {
            color: '#c41230',
            weight: 2,
            opacity: 0.8,
            fillColor: '#c41230',
            fillOpacity: 0.1
        }
    }).addTo(catchmentMap);

    // Fix map size and fit to boundary
    setTimeout(() => {
        catchmentMap.invalidateSize();
        catchmentMap.fitBounds(catchmentLayer.getBounds());
    }, 100);

    // Add school marker at centroid
    if (schoolLocation) {
        L.marker([schoolLocation.latitude, schoolLocation.longitude], {
            icon: L.divIcon({
                className: 'school-marker',
                html: '<div style="background: #c41230; color: white; padding: 5px 10px; border-radius: 4px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">🏫 School</div>',
                iconSize: [60, 30]
            })
        }).addTo(catchmentMap);
    }
}

// ============================================
// Address Search Functionality
// ============================================

searchAddressBtn.addEventListener('click', async function() {
    const streetNumber = searchStreetNumber.value.trim();
    const street = searchStreet.value.trim();
    const suburb = searchSuburb.value.trim();
    const postcode = searchPostcode.value.trim();
    const state = searchState.value.trim();
    const limit = searchLimit.value;

    if (!street && !suburb && !postcode && !state) {
        searchResults.innerHTML = '<div class="error">Please enter at least one search criteria</div>';
        resultsSection.style.display = 'block';
        return;
    }

    showLoading(true);

    try {
        const params = new URLSearchParams();
        if (streetNumber) params.append('street_number', streetNumber);
        if (street) params.append('street', street);
        if (suburb) params.append('suburb', suburb);
        if (postcode) params.append('postcode', postcode);
        if (state) params.append('state', state);
        params.append('limit', limit);

        const response = await fetch(`/api/address/search?${params}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch data');
        }

        if (data.addresses.length === 0) {
            searchResults.innerHTML = `
                <div class="no-results">
                    No addresses found matching your search criteria
                </div>
            `;
            resultsSection.style.display = 'block';
            return;
        }

        // Display results in the same format as address lookup
        displaySearchResults(data);
        resultsSection.style.display = 'block';

    } catch (error) {
        console.error('Error searching addresses:', error);
        searchResults.innerHTML = `<div class="error">Error: ${error.message}</div>`;
        resultsSection.style.display = 'block';
    } finally {
        showLoading(false);
    }
});

// Allow Enter key on search inputs
[searchStreetNumber, searchStreet, searchSuburb, searchPostcode].forEach(input => {
    if (input) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchAddressBtn.click();
            }
        });
    }
});

// ============================================
// Helper Functions
// ============================================

function calculateDistance(lat1, lon1, lat2, lon2) {
    // Haversine formula
    const R = 6371; // Earth's radius in km
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);

    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distance = R * c;

    if (distance < 1) {
        return `${Math.round(distance * 1000)} m`;
    } else {
        return `${distance.toFixed(2)} km`;
    }
}

function toRad(degrees) {
    return degrees * Math.PI / 180;
}

function generatePropertyLinks(address) {
    if (!address.street_name || !address.suburb || !address.street_number) {
        return '-';
    }

    // Helper function to format text for URLs
    const formatForUrl = (text) => {
        if (!text) return '';
        return text.toLowerCase()
            .replace(/\s+/g, '-')
            .replace(/[^a-z0-9-]/g, '');
    };

    // Build street number
    const urlStreetNumber = address.street_number.replace('N/A', '').trim();

    // Get unit number (just the number, not the type)
    const urlUnitNumber = address.unit_number ? address.unit_number.toString().trim() : '';

    const expandedTypeRE = expandStreetTypeRealEstate(address.street_type);
    const expandedTypeDomain = expandStreetTypeDomain(address.street_type);

    const urlStreetNameRealEstate = formatForUrl([address.street_name, expandedTypeRE].filter(Boolean).join(' '));
    const urlStreetNameDomain = formatForUrl([address.street_name, expandedTypeDomain].filter(Boolean).join(' '));
    const urlSuburb = formatForUrl(address.suburb);
    const urlState = (address.state || 'nsw').toLowerCase();
    const urlPostcode = address.postcode || '';

    // Build RealEstate URL with unit prefix if unit exists
    let realEstateUrl = '';
    if (urlStreetNumber && urlStreetNameRealEstate && urlSuburb && urlState && urlPostcode) {
        if (urlUnitNumber) {
            // Format: unit-4-53-57-burdett-cres-hornsby-nsw-2077
            realEstateUrl = `https://www.realestate.com.au/property/unit-${urlUnitNumber}-${urlStreetNumber}-${urlStreetNameRealEstate}-${urlSuburb}-${urlState}-${urlPostcode}/`;
        } else {
            realEstateUrl = `https://www.realestate.com.au/property/${urlStreetNumber}-${urlStreetNameRealEstate}-${urlSuburb}-${urlState}-${urlPostcode}/`;
        }
    }

    // Build Domain URL with unit number (no prefix) if unit exists
    let domainUrl = '';
    if (urlStreetNumber && urlStreetNameDomain && urlSuburb && urlState && urlPostcode) {
        if (urlUnitNumber) {
            // Format: 4-53-57-burdett-crescent-hornsby-nsw-2077
            domainUrl = `https://www.domain.com.au/property-profile/${urlUnitNumber}-${urlStreetNumber}-${urlStreetNameDomain}-${urlSuburb}-${urlState}-${urlPostcode}`;
        } else {
            domainUrl = `https://www.domain.com.au/property-profile/${urlStreetNumber}-${urlStreetNameDomain}-${urlSuburb}-${urlState}-${urlPostcode}`;
        }
    }

    if (!realEstateUrl && !domainUrl) {
        return '-';
    }

    return `
        <div style="display: flex; flex-direction: column; gap: 6px;">
            ${realEstateUrl ? `<a href="${realEstateUrl}" target="_blank" class="property-link" style="display: block; text-align: center; padding: 4px 8px; background: #c41230; color: white; text-decoration: none; border-radius: 3px; font-size: 0.85rem; font-weight: 500; white-space: nowrap;" title="View on RealEstate.com.au">RealEstate</a>` : ''}
            ${domainUrl ? `<a href="${domainUrl}" target="_blank" class="property-link" style="display: block; text-align: center; padding: 4px 8px; background: #16a34a; color: white; text-decoration: none; border-radius: 3px; font-size: 0.85rem; font-weight: 500; white-space: nowrap;" title="View on Domain.com.au">Domain</a>` : ''}
        </div>
    `;
}

function expandStreetTypeRealEstate(streetType) {
    if (!streetType) return '';
    const abbreviations = {
        'avenue': 'ave', 'av': 'ave', 'ave': 'ave',
        'street': 'st', 'st': 'st',
        'road': 'rd', 'rd': 'rd',
        'drive': 'dr', 'dr': 'dr',
        'court': 'ct', 'ct': 'ct',
        'place': 'pl', 'pl': 'pl',
        'crescent': 'cres', 'cres': 'cres', 'cr': 'cres',
        'lane': 'ln', 'ln': 'ln',
        'terrace': 'tce', 'tce': 'tce',
        'parade': 'pde', 'pde': 'pde',
        'way': 'way',
        'highway': 'hwy', 'hwy': 'hwy',
        'esplanade': 'esp', 'espl': 'esp', 'esp': 'esp'
    };
    const lowerType = streetType.toLowerCase();
    return abbreviations[lowerType] || lowerType;
}

function expandStreetTypeDomain(streetType) {
    if (!streetType) return '';
    const expansions = {
        'av': 'avenue', 'ave': 'avenue', 'avenue': 'avenue',
        'st': 'street', 'street': 'street',
        'rd': 'road', 'road': 'road',
        'dr': 'drive', 'drive': 'drive',
        'ct': 'court', 'court': 'court',
        'pl': 'place', 'place': 'place',
        'cr': 'crescent', 'cres': 'crescent', 'crescent': 'crescent',
        'ln': 'lane', 'lane': 'lane',
        'tce': 'terrace', 'terrace': 'terrace',
        'pde': 'parade', 'parade': 'parade',
        'way': 'way',
        'hwy': 'highway', 'highway': 'highway',
        'espl': 'esplanade', 'esp': 'esplanade', 'esplanade': 'esplanade'
    };
    const lowerType = streetType.toLowerCase();
    return expansions[lowerType] || lowerType;
}

function getGeocodeTypeDescription(code) {
    const descriptions = {
        'BAP': 'Building Access Point - Point of access to the building',
        'BC': 'Building Centroid - Centre of building footprint',
        'BCP': 'Building Centroid Point - Centre of building',
        'CDF': 'Cadastral Frontage - Property boundary on street',
        'EC': 'Emergency Access - Emergency service access point',
        'ECP': 'Emergency Centroid Point - Emergency centroid',
        'FC': 'Frontage Centre - Centre of property frontage',
        'FCP': 'Frontage Centre Point - Centre point of frontage',
        'GAP': 'Gazetted Address Point - Official gazetted location',
        'LCP': 'Locality Centre Point - Centre of locality',
        'PAP': 'Property Access Point - Main property access',
        'PC': 'Property Centroid - Centre of property',
        'UC': 'Unit Centroid - Centre of unit'
    };
    return descriptions[code] || 'Unknown geocode type';
}

function getConfidenceDescription(confidence) {
    const descriptions = {
        'HIGH': 'High confidence in coordinate accuracy',
        'MEDIUM': 'Medium confidence in coordinate accuracy',
        'LOW': 'Low confidence in coordinate accuracy',
        'VERY LOW': 'Very low confidence in coordinate accuracy',
        'UNKNOWN': 'Confidence level unknown'
    };
    return descriptions[confidence] || 'Unknown confidence level';
}

function openGoogleMaps(lat, lng) {
    window.open(`https://www.google.com/maps?q=${lat},${lng}`, '_blank');
}

function showLoading(show) {
    loadingIndicator.style.display = show ? 'flex' : 'none';
}

function displaySearchResults(data) {
    // Use the same format as address lookup page
    searchResults.innerHTML = `
        <div class="results-header">
            <div class="results-title">Search Results in this School Catchment</div>
            <div class="results-count">${data.count} result(s)</div>
        </div>
        <table class="results-table">
            <thead>
                <tr>
                    <th>Unit/Flat</th>
                    <th>Street Number</th>
                    <th>Street Name</th>
                    <th>Suburb</th>
                    <th>State</th>
                    <th>Postcode</th>
                    <th>Coordinates</th>
                    <th>Geocode Type</th>
                    <th>Confidence</th>
                    <th>School Catchments</th>
                    <th>Useful Links</th>
                </tr>
            </thead>
            <tbody id="schoolAddressResultsTableBody">
                ${data.addresses.map((addr, index) => {
                    const streetName = [addr.street_name, addr.street_type].filter(Boolean).join(' ').trim();
                    const streetNumber = addr.number_last 
                        ? `${addr.number_first}${addr.number_first_suffix || ''}-${addr.number_last}${addr.number_last_suffix || ''}` 
                        : `${addr.number_first || 'N/A'}${addr.number_first_suffix || ''}`;
                    
                    const unit = addr.flat_number 
                        ? (addr.flat_type ? `${addr.flat_type} ${addr.flat_number}` : addr.flat_number)
                        : '-';
                    
                    const coords = addr.latitude && addr.longitude 
                        ? `${parseFloat(addr.latitude).toFixed(6)}, ${parseFloat(addr.longitude).toFixed(6)}`
                        : 'N/A';
                    
                    // Calculate distance from state CBD using Haversine formula
                    let distanceFromCBD = '';
                    if (addr.latitude && addr.longitude) {
                        // Define CBD coordinates for each state
                        const stateCBDs = {
                            'NSW': { lat: -33.8688, lng: 151.2093, city: 'Sydney' },
                            'VIC': { lat: -37.8136, lng: 144.9631, city: 'Melbourne' },
                            'QLD': { lat: -27.4698, lng: 153.0251, city: 'Brisbane' },
                            'SA': { lat: -34.9285, lng: 138.6007, city: 'Adelaide' },
                            'WA': { lat: -31.9505, lng: 115.8605, city: 'Perth' },
                            'TAS': { lat: -42.8821, lng: 147.3272, city: 'Hobart' },
                            'NT': { lat: -12.4634, lng: 130.8456, city: 'Darwin' },
                            'ACT': { lat: -35.2809, lng: 149.1300, city: 'Canberra' }
                        };
                        
                        const stateCBD = stateCBDs[addr.state];
                        if (stateCBD) {
                            const lat1 = parseFloat(addr.latitude);
                            const lng1 = parseFloat(addr.longitude);
                            const lat2 = stateCBD.lat;
                            const lng2 = stateCBD.lng;
                            
                            // Haversine formula
                            const R = 6371; // Earth's radius in km
                            const dLat = (lat2 - lat1) * Math.PI / 180;
                            const dLng = (lng2 - lng1) * Math.PI / 180;
                            const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                                     Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                                     Math.sin(dLng/2) * Math.sin(dLng/2);
                            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
                            const distance = R * c;
                            
                            distanceFromCBD = `Distance from ${stateCBD.city} CBD: ${distance.toFixed(2)} km&#10;(Haversine formula used to calculate as-the-crow-flies distance, driving distance can be calculated from Google Maps)`;
                        }
                    }
                    
                    const googleMapsUrl = addr.latitude && addr.longitude
                        ? `https://www.google.com/maps?q=${parseFloat(addr.latitude).toFixed(6)},${parseFloat(addr.longitude).toFixed(6)}`
                        : '';
                    
                    const geocodeType = addr.geocode_type_code || 'N/A';
                    
                    let confidenceText = 'Unknown';
                    let confidenceColor = '#999';
                    
                    if (addr.confidence !== null && addr.confidence !== undefined) {
                        const confValue = parseInt(addr.confidence);
                        if (confValue === 3) {
                            confidenceText = 'Very High';
                            confidenceColor = '#28a745';
                        } else if (confValue === 2) {
                            confidenceText = 'High';
                            confidenceColor = '#5cb85c';
                        } else if (confValue === 1) {
                            confidenceText = 'Medium';
                            confidenceColor = '#ffc107';
                        } else if (confValue === 0) {
                            confidenceText = 'Low';
                            confidenceColor = '#ff9800';
                        } else if (confValue === -1) {
                            confidenceText = 'None';
                            confidenceColor = '#dc3545';
                        }
                    }
                    
                    // Helper function for URL formatting
                    const formatForUrl = (str) => {
                        if (!str) return '';
                        return str.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
                    };
                    
                    // Expand street type for RealEstate
                    const expandStreetTypeRealEstate = (type) => {
                        if (!type) return '';
                        const abbreviations = {
                            'avenue': 'ave', 'av': 'ave', 'ave': 'ave',
                            'street': 'st', 'st': 'st',
                            'road': 'rd', 'rd': 'rd',
                            'drive': 'dr', 'dr': 'dr',
                            'court': 'ct', 'ct': 'ct',
                            'place': 'pl', 'pl': 'pl',
                            'crescent': 'cres', 'cres': 'cres', 'cr': 'cres',
                            'lane': 'ln', 'ln': 'ln',
                            'terrace': 'tce', 'tce': 'tce',
                            'parade': 'pde', 'pde': 'pde',
                            'way': 'way',
                            'highway': 'hwy', 'hwy': 'hwy',
                            'esplanade': 'esp', 'espl': 'esp', 'esp': 'esp'
                        };
                        return abbreviations[type.toLowerCase()] || type.toLowerCase();
                    };
                    
                    // Expand street type for Domain
                    const expandStreetTypeDomain = (type) => {
                        if (!type) return '';
                        const abbreviations = {
                            'av': 'avenue', 'ave': 'avenue', 'avenue': 'avenue',
                            'st': 'street', 'street': 'street',
                            'rd': 'road', 'road': 'road',
                            'dr': 'drive', 'drive': 'drive',
                            'ct': 'court', 'court': 'court',
                            'pl': 'place', 'place': 'place',
                            'cr': 'crescent', 'cres': 'crescent', 'crescent': 'crescent',
                            'ln': 'lane', 'lane': 'lane',
                            'tce': 'terrace', 'terrace': 'terrace',
                            'pde': 'parade', 'parade': 'parade',
                            'way': 'way',
                            'hwy': 'highway', 'highway': 'highway',
                            'espl': 'esplanade', 'esp': 'esplanade', 'esplanade': 'esplanade'
                        };
                        return abbreviations[type.toLowerCase()] || type.toLowerCase();
                    };
                    
                    // Build property URLs
                    const urlStreetNumber = streetNumber.replace('N/A', '').trim();
                    const urlUnitNumber = addr.flat_number ? addr.flat_number.toString() : '';
                    const urlStreetNameRealEstate = formatForUrl([addr.street_name, expandStreetTypeRealEstate(addr.street_type)].filter(Boolean).join(' '));
                    const urlStreetNameDomain = formatForUrl([addr.street_name, expandStreetTypeDomain(addr.street_type)].filter(Boolean).join(' '));
                    const urlSuburb = formatForUrl(addr.suburb);
                    const urlState = (addr.state || '').toLowerCase();
                    const urlPostcode = addr.postcode || '';
                    
                    // Build RealEstate URL
                    let realEstateUrl = '';
                    if (urlStreetNumber && urlStreetNameRealEstate && urlSuburb && urlState && urlPostcode) {
                        if (urlUnitNumber) {
                            realEstateUrl = `https://www.realestate.com.au/property/unit-${urlUnitNumber}-${urlStreetNumber}-${urlStreetNameRealEstate}-${urlSuburb}-${urlState}-${urlPostcode}/`;
                        } else {
                            realEstateUrl = `https://www.realestate.com.au/property/${urlStreetNumber}-${urlStreetNameRealEstate}-${urlSuburb}-${urlState}-${urlPostcode}/`;
                        }
                    }
                    
                    // Build Domain URL
                    let domainUrl = '';
                    if (urlStreetNumber && urlStreetNameDomain && urlSuburb && urlState && urlPostcode) {
                        if (urlUnitNumber) {
                            domainUrl = `https://www.domain.com.au/property-profile/${urlUnitNumber}-${urlStreetNumber}-${urlStreetNameDomain}-${urlSuburb}-${urlState}-${urlPostcode}`;
                        } else {
                            domainUrl = `https://www.domain.com.au/property-profile/${urlStreetNumber}-${urlStreetNameDomain}-${urlSuburb}-${urlState}-${urlPostcode}`;
                        }
                    }
                    
                    return `
                        <tr data-row-index="${index}" data-lat="${addr.latitude || ''}" data-lng="${addr.longitude || ''}">
                            <td>${unit}</td>
                            <td><strong>${streetNumber}</strong></td>
                            <td>${streetName || 'N/A'}</td>
                            <td>${addr.suburb || 'N/A'}</td>
                            <td>${addr.state || 'N/A'}</td>
                            <td>${addr.postcode || 'N/A'}</td>
                            <td style="font-size: 0.85rem;">
                                ${googleMapsUrl 
                                    ? `<a href="${googleMapsUrl}" target="_blank" class="coords-button" title="View on Google Maps${distanceFromCBD ? '&#10;' + distanceFromCBD : ''}">📍 ${coords}</a>` 
                                    : '<span style="color: var(--text-muted);">N/A</span>'}
                            </td>
                            <td style="font-size: 0.85rem;">${geocodeType}</td>
                            <td style="font-size: 0.85rem;">
                                <span style="color: ${confidenceColor}; font-weight: 500;">
                                    ${confidenceText}
                                </span>
                            </td>
                            <td class="school-catchment-cell" style="font-size: 0.85rem;">
                                <span style="color: #999;">Loading...</span>
                            </td>
                            <td style="font-size: 0.85rem;">
                                ${realEstateUrl ? `<a href="${realEstateUrl}" target="_blank" style="display: inline-block; padding: 4px 8px; background: #dc3545; color: white; text-decoration: none; border-radius: 3px; margin-right: 4px; font-size: 0.75rem;">RealEstate</a>` : ''}
                                ${domainUrl ? `<a href="${domainUrl}" target="_blank" style="display: inline-block; padding: 4px 8px; background: #28a745; color: white; text-decoration: none; border-radius: 3px; font-size: 0.75rem;">Domain</a>` : ''}
                                ${!realEstateUrl && !domainUrl ? '<span style="color: #999;">-</span>' : ''}
                            </td>
                        </tr>
                    `;
                }).join('')}
            </tbody>
        </table>
    `;
    
    // Fetch school catchments for each address
    fetchSchoolCatchmentsForResults();
}

// Function to fetch school catchments for all addresses in search results
async function fetchSchoolCatchmentsForResults() {
    const rows = document.querySelectorAll('#schoolAddressResultsTableBody tr');
    
    for (const row of rows) {
        const lat = row.dataset.lat;
        const lng = row.dataset.lng;
        const schoolCell = row.querySelector('.school-catchment-cell');
        
        if (!lat || !lng) {
            schoolCell.innerHTML = '<span style="color: #999;">No coordinates</span>';
            continue;
        }
        
        try {
            const response = await fetch(`/api/address/schools?lat=${lat}&lng=${lng}`);
            const data = await response.json();
            
            if (data.schools && data.schools.length > 0) {
                const schoolsHtml = data.schools.map(school => {
                    const typeColors = {
                        'PRIMARY': '#2196F3',
                        'SECONDARY': '#4CAF50',
                        'HIGH_COED': '#4CAF50',
                        'FUTURE': '#FF9800'
                    };
                    const color = typeColors[school.school_type] || '#999';
                    
                    return `
                        <div style="margin-bottom: 4px;">
                            <a href="/school-search?school_id=${school.school_id}" 
                               style="color: var(--primary-color); text-decoration: none; font-weight: 500;"
                               title="Click to view all addresses in ${school.school_name} catchment">
                                ${school.school_name}
                            </a>
                            <span style="font-size: 0.75rem; color: ${color}; font-weight: 500; margin-left: 4px;">
                                (${school.school_type})
                            </span>
                        </div>
                    `;
                }).join('');
                
                schoolCell.innerHTML = schoolsHtml;
            } else {
                schoolCell.innerHTML = '<span style="color: #999;">No catchment</span>';
            }
        } catch (error) {
            console.error('Error fetching schools:', error);
            schoolCell.innerHTML = '<span style="color: #dc3545;">Error loading</span>';
        }
    }
}

function hideAllSections() {
    schoolInfoSection.style.display = 'none';
    mapSection.style.display = 'none';
    addressSearchSection.style.display = 'none';
    resultsSection.style.display = 'none';
}