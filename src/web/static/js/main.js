// Investment Dashboard Main JavaScript

// Global variables
let currentTheme = 'light';
let autoRefreshInterval = null;
let isLoading = false;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    loadInitialData();
    setupEventListeners();
    setupThemeToggle();
    setupAutoRefresh();
});

// Dashboard initialization
function initializeDashboard() {
    console.log('Initializing Investment Dashboard...');
    
    // Set last update time
    updateLastUpdateTime();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Load user preferences
    loadUserPreferences();
}

// Load initial data
async function loadInitialData() {
    try {
        showLoadingState();
        
        // Load portfolio data
        await loadPortfolioData();
        
        // Load market overview
        await loadMarketOverview();
        
        // Load recent alerts
        await loadRecentAlerts();
        
        hideLoadingState();
    } catch (error) {
        console.error('Error loading initial data:', error);
        showError('Failed to load dashboard data');
        hideLoadingState();
    }
}

// Setup event listeners
function setupEventListeners() {
    // Navigation
    setupNavigation();
    
    // Search functionality
    setupSearch();
    
    // Filter buttons
    setupFilters();
    
    // Settings forms
    setupSettingsForms();
    
    // Refresh buttons
    setupRefreshButtons();
}

// Navigation setup
function setupNavigation() {
    // Mobile menu toggle
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        navbarToggler.addEventListener('click', function() {
            navbarCollapse.classList.toggle('show');
        });
    }
}

// Search functionality
function setupSearch() {
    const searchInputs = document.querySelectorAll('#stock-search, #portfolio-search');
    
    searchInputs.forEach(input => {
        input.addEventListener('input', debounce(function(e) {
            const searchTerm = e.target.value.toLowerCase();
            performSearch(searchTerm);
        }, 300));
    });
}

// Filter setup
function setupFilters() {
    const filterButtons = document.querySelectorAll('[data-filter]');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filter = this.getAttribute('data-filter');
            applyFilter(filter);
            
            // Update active state
            const group = this.parentElement;
            group.querySelectorAll('[data-filter]').forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

// Settings forms
function setupSettingsForms() {
    const forms = document.querySelectorAll('#general-settings, #portfolio-settings, #alert-settings, #api-settings');
    
    forms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            await saveSettings(this);
        });
    });
}

// Refresh buttons
function setupRefreshButtons() {
    const refreshButtons = document.querySelectorAll('#refresh-stocks, #refresh-portfolio, #refresh-alerts');
    
    refreshButtons.forEach(button => {
        button.addEventListener('click', function() {
            const type = this.id.replace('refresh-', '');
            refreshData(type);
        });
    });
}

// Theme toggle
function setupThemeToggle() {
    const themeToggle = document.querySelector('#theme-toggle');
    
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        setTheme('dark');
    }
}

// Auto refresh setup
function setupAutoRefresh() {
    const refreshInterval = localStorage.getItem('autoRefreshInterval') || 300; // 5 minutes default
    
    if (refreshInterval > 0) {
        startAutoRefresh(refreshInterval);
    }
}

// Data loading functions
async function loadPortfolioData() {
    try {
        const response = await fetch('/api/portfolio');
        const data = await response.json();
        
        updatePortfolioDisplay(data);
        updateCharts(data);
    } catch (error) {
        console.error('Error loading portfolio:', error);
    }
}

async function loadMarketOverview() {
    try {
        const response = await fetch('/api/market-overview');
        const data = await response.json();
        
        updateMarketDisplay(data);
    } catch (error) {
        console.error('Error loading market data:', error);
    }
}

async function loadRecentAlerts() {
    try {
        const response = await fetch('/api/alerts/recent');
        const data = await response.json();
        
        updateAlertsDisplay(data);
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

// Portfolio display updates
function updatePortfolioDisplay(data) {
    const totalValue = document.querySelector('#total-portfolio-value');
    const dailyChange = document.querySelector('#daily-change');
    const dailyChangePercent = document.querySelector('#daily-change-percent');
    
    if (totalValue) totalValue.textContent = formatCurrency(data.totalValue);
    if (dailyChange) {
        dailyChange.textContent = formatCurrency(data.dailyChange);
        dailyChange.className = data.dailyChange >= 0 ? 'positive' : 'negative';
    }
    if (dailyChangePercent) {
        dailyChangePercent.textContent = formatPercentage(data.dailyChangePercent);
        dailyChangePercent.className = data.dailyChangePercent >= 0 ? 'positive' : 'negative';
    }
}

// Chart updates
function updateCharts(data) {
    // Update portfolio allocation chart
    updateAllocationChart(data.allocation);
    
    // Update performance chart
    updatePerformanceChart(data.performance);
    
    // Update sector chart
    updateSectorChart(data.sectors);
}

// Utility functions
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

function formatPercentage(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value / 100);
}

function formatNumber(value) {
    return new Intl.NumberFormat('en-US').format(value);
}

function formatLargeNumber(value) {
    if (value >= 1e12) {
        return (value / 1e12).toFixed(1) + 'T';
    } else if (value >= 1e9) {
        return (value / 1e9).toFixed(1) + 'B';
    } else if (value >= 1e6) {
        return (value / 1e6).toFixed(1) + 'M';
    } else if (value >= 1e3) {
        return (value / 1e3).toFixed(1) + 'K';
    }
    return value.toString();
}

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

// Loading states
function showLoadingState() {
    isLoading = true;
    document.body.classList.add('loading');
    
    const loadingElements = document.querySelectorAll('.loading-placeholder');
    loadingElements.forEach(el => el.classList.add('loading'));
}

function hideLoadingState() {
    isLoading = false;
    document.body.classList.remove('loading');
    
    const loadingElements = document.querySelectorAll('.loading-placeholder');
    loadingElements.forEach(el => el.classList.remove('loading'));
}

// Error handling
function showError(message) {
    const toast = createToast(message, 'error');
    showToast(toast);
}

function showSuccess(message) {
    const toast = createToast(message, 'success');
    showToast(toast);
}

// Toast notifications
function createToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : 'success'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    return toast;
}

function showToast(toast) {
    const container = getToastContainer();
    container.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function getToastContainer() {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    return container;
}

// Settings management
async function saveSettings(form) {
    try {
        const formData = new FormData(form);
        const settings = Object.fromEntries(formData.entries());
        
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings)
        });
        
        if (response.ok) {
            showSuccess('Settings saved successfully');
            localStorage.setItem('settings', JSON.stringify(settings));
        } else {
            throw new Error('Failed to save settings');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        showError('Failed to save settings');
    }
}

// Theme management
function setTheme(theme) {
    currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    // Update theme toggle button
    const themeToggle = document.querySelector('#theme-toggle');
    if (themeToggle) {
        themeToggle.innerHTML = theme === 'dark' ? 
            '<i class="fas fa-sun"></i>' : 
            '<i class="fas fa-moon"></i>';
    }
}

function toggleTheme() {
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
}

// Auto refresh
function startAutoRefresh(intervalSeconds) {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    if (intervalSeconds > 0) {
        autoRefreshInterval = setInterval(() => {
            refreshData('all');
        }, intervalSeconds * 1000);
    }
}

// Data refresh
async function refreshData(type) {
    if (isLoading) return;
    
    try {
        showLoadingState();
        
        switch (type) {
            case 'portfolio':
                await loadPortfolioData();
                break;
            case 'stocks':
                await loadMarketOverview();
                break;
            case 'alerts':
                await loadRecentAlerts();
                break;
            case 'all':
                await Promise.all([
                    loadPortfolioData(),
                    loadMarketOverview(),
                    loadRecentAlerts()
                ]);
                break;
        }
        
        updateLastUpdateTime();
        showSuccess('Data refreshed successfully');
    } catch (error) {
        console.error('Error refreshing data:', error);
        showError('Failed to refresh data');
    } finally {
        hideLoadingState();
    }
}

// Search functionality
function performSearch(searchTerm) {
    const searchables = document.querySelectorAll('[data-searchable]');
    
    searchables.forEach(element => {
        const text = element.textContent.toLowerCase();
        const shouldShow = !searchTerm || text.includes(searchTerm);
        element.style.display = shouldShow ? '' : 'none';
    });
}

// Filter functionality
function applyFilter(filter) {
    const filterables = document.querySelectorAll('[data-filterable]');
    
    filterables.forEach(element => {
        const tags = element.getAttribute('data-tags');
        const shouldShow = filter === 'all' || (tags && tags.includes(filter));
        element.style.display = shouldShow ? '' : 'none';
    });
}

// User preferences
function loadUserPreferences() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        setTheme(savedTheme);
    }
    
    const savedSettings = localStorage.getItem('settings');
    if (savedSettings) {
        const settings = JSON.parse(savedSettings);
        applySettings(settings);
    }
}

function applySettings(settings) {
    // Apply theme
    if (settings.theme) {
        setTheme(settings.theme);
    }
    
    // Apply auto refresh
    if (settings.autoRefresh) {
        startAutoRefresh(parseInt(settings.autoRefresh));
    }
}

// Tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Time updates
function updateLastUpdateTime() {
    const lastUpdate = document.querySelector('#last-update');
    if (lastUpdate) {
        lastUpdate.textContent = new Date().toLocaleString();
    }
}

// Export functions for use in other modules
window.InvestmentDashboard = {
    formatCurrency,
    formatPercentage,
    formatNumber,
    formatLargeNumber,
    showSuccess,
    showError,
    refreshData,
    setTheme,
    saveSettings
};