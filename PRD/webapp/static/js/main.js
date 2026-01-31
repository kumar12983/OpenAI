// ============================================
// Main JavaScript for GNAF Web Application
// ============================================

// Utility function to handle API errors
function handleAPIError(error) {
    console.error('API Error:', error);
    return `<div class="error">Error: ${error.message || 'Something went wrong. Please try again.'}</div>`;
}

// Utility function to show loading state
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="loading">⏳ Loading...</div>';
    }
}

// Format number with commas
function formatNumber(num) {
    return num ? num.toLocaleString() : '0';
}

// Debounce function for autocomplete
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}