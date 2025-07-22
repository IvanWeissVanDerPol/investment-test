// Advanced Browser Debugging Tools for Investment Dashboard

class InvestmentDashboardDebugger {
    constructor() {
        this.isEnabled = localStorage.getItem('debugMode') === 'true';
        this.logs = [];
        this.apiCalls = [];
        this.errors = [];
        this.performanceMetrics = {};
        this.init();
    }

    init() {
        if (this.isEnabled) {
            this.setupDebugPanel();
            this.setupConsoleCommands();
            this.startPerformanceMonitoring();
            this.setupNetworkMonitoring();
            this.setupErrorHandling();
            this.showWelcomeMessage();
        }
    }

    setupDebugPanel() {
        // Create floating debug panel
        const panel = document.createElement('div');
        panel.id = 'debug-panel';
        panel.innerHTML = `
            <div class="debug-header">
                <h4>🛠️ Debug Panel</h4>
                <div class="debug-controls">
                    <button onclick="debugger.clearLogs()">Clear</button>
                    <button onclick="debugger.exportLogs()">Export</button>
                    <button onclick="debugger.togglePanel()">Hide</button>
                </div>
            </div>
            <div class="debug-tabs">
                <button class="debug-tab active" data-tab="logs">Logs</button>
                <button class="debug-tab" data-tab="api">API Calls</button>
                <button class="debug-tab" data-tab="errors">Errors</button>
                <button class="debug-tab" data-tab="performance">Performance</button>
                <button class="debug-tab" data-tab="storage">Storage</button>
            </div>
            <div class="debug-content">
                <div id="debug-logs" class="debug-tab-content active"></div>
                <div id="debug-api" class="debug-tab-content"></div>
                <div id="debug-errors" class="debug-tab-content"></div>
                <div id="debug-performance" class="debug-tab-content"></div>
                <div id="debug-storage" class="debug-tab-content"></div>
            </div>
        `;

        const styles = `
            #debug-panel {
                position: fixed;
                top: 10px;
                right: 10px;
                width: 400px;
                max-height: 600px;
                background: rgba(0, 0, 0, 0.9);
                color: white;
                border-radius: 8px;
                z-index: 10000;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                overflow: hidden;
                transition: all 0.3s ease;
            }

            .debug-header {
                background: #333;
                padding: 10px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .debug-controls button {
                margin-left: 5px;
                padding: 2px 8px;
                font-size: 10px;
                background: #555;
                color: white;
                border: none;
                border-radius: 3px;
                cursor: pointer;
            }

            .debug-tabs {
                display: flex;
                background: #222;
            }

            .debug-tab {
                flex: 1;
                padding: 5px;
                background: #222;
                border: none;
                color: #ccc;
                cursor: pointer;
                font-size: 10px;
            }

            .debug-tab.active {
                background: #007bff;
                color: white;
            }

            .debug-content {
                max-height: 400px;
                overflow-y: auto;
            }

            .debug-tab-content {
                display: none;
                padding: 10px;
                max-height: 350px;
                overflow-y: auto;
            }

            .debug-tab-content.active {
                display: block;
            }

            .debug-log-entry {
                margin-bottom: 5px;
                padding: 5px;
                border-left: 3px solid #007bff;
                background: rgba(255, 255, 255, 0.1);
            }

            .debug-error {
                border-left-color: #dc3545;
                background: rgba(220, 53, 69, 0.2);
            }

            .debug-success {
                border-left-color: #28a745;
                background: rgba(40, 167, 69, 0.2);
            }

            .debug-warning {
                border-left-color: #ffc107;
                background: rgba(255, 193, 7, 0.2);
            }

            .debug-minimized {
                width: 50px;
                height: 30px;
                border-radius: 15px;
            }

            .debug-minimized .debug-header h4 {
                font-size: 10px;
            }
        `;

        const styleSheet = document.createElement('style');
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
        document.body.appendChild(panel);

        // Add event listeners
        document.querySelectorAll('.debug-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            });
        });
    }

    setupConsoleCommands() {
        // Add global debug commands to browser console
        window.debugger = {
            log: (message, type = 'info') => this.log(message, type),
            clear: () => this.clearLogs(),
            export: () => this.exportLogs(),
            api: () => this.showApiCalls(),
            errors: () => this.showErrors(),
            performance: () => this.showPerformance(),
            storage: () => this.showStorage(),
            testApi: (endpoint) => this.testApiCall(endpoint),
            reloadData: () => this.reloadAllData(),
            simulateError: () => this.simulateError(),
            toggle: () => this.toggleDebugMode(),
            help: () => this.showConsoleHelp()
        };

        console.log('🛠️ Investment Dashboard Debugger loaded!');
        console.log('Available commands: debugger.log(), debugger.clear(), debugger.export(), debugger.api(), debugger.errors(), debugger.performance(), debugger.storage(), debugger.testApi(), debugger.reloadData(), debugger.simulateError(), debugger.toggle(), debugger.help()');
    }

    setupNetworkMonitoring() {
        // Monitor fetch/XHR requests
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            const startTime = performance.now();
            const [url, options] = args;
            
            this.log(`🌐 Fetch: ${url}`, 'network');
            
            try {
                const response = await originalFetch(...args);
                const duration = performance.now() - startTime;
                
                this.apiCalls.push({
                    url,
                    method: options?.method || 'GET',
                    status: response.status,
                    duration,
                    timestamp: new Date().toISOString()
                });
                
                this.log(`✅ Fetch Success: ${url} (${response.status}) - ${duration.toFixed(2)}ms`, 'success');
                return response;
            } catch (error) {
                const duration = performance.now() - startTime;
                this.errors.push({
                    type: 'API Error',
                    url,
                    error: error.message,
                    timestamp: new Date().toISOString()
                });
                
                this.log(`❌ Fetch Error: ${url} - ${error.message}`, 'error');
                throw error;
            }
        };
    }

    setupErrorHandling() {
        window.addEventListener('error', (event) => {
            const error = {
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error?.stack,
                timestamp: new Date().toISOString()
            };
            
            this.errors.push(error);
            this.log(`❌ JavaScript Error: ${error.message} at ${error.filename}:${error.lineno}`, 'error');
        });

        window.addEventListener('unhandledrejection', (event) => {
            const error = {
                message: event.reason?.message || event.reason,
                stack: event.reason?.stack,
                timestamp: new Date().toISOString()
            };
            
            this.errors.push(error);
            this.log(`❌ Promise Rejection: ${error.message}`, 'error');
        });
    }

    startPerformanceMonitoring() {
        // Monitor page load performance
        if (window.performance) {
            window.addEventListener('load', () => {
                setTimeout(() => {
                    const perfData = window.performance.timing;
                    this.performanceMetrics = {
                        pageLoadTime: perfData.loadEventEnd - perfData.navigationStart,
                        domContentLoaded: perfData.domContentLoadedEventEnd - perfData.navigationStart,
                        firstPaint: this.getFirstPaint(),
                        resourceCount: performance.getEntriesByType('resource').length,
                        timestamp: new Date().toISOString()
                    };
                    
                    this.log(`📊 Performance: Page loaded in ${this.performanceMetrics.pageLoadTime}ms`, 'info');
                }, 100);
            });
        }

        // Monitor API response times
        this.startApiPerformanceMonitoring();
    }

    getFirstPaint() {
        try {
            const paintEntries = performance.getEntriesByType('paint');
            const firstPaint = paintEntries.find(entry => entry.name === 'first-paint');
            return firstPaint ? firstPaint.startTime : null;
        } catch (e) {
            return null;
        }
    }

    startApiPerformanceMonitoring() {
        // Monitor API calls made by the dashboard
        const apiEndpoints = [
            '/api/portfolio',
            '/api/positions',
            '/api/alerts',
            '/api/stocks',
            '/api/sector-allocations'
        ];

        apiEndpoints.forEach(endpoint => {
            const startTime = performance.now();
            fetch(endpoint)
                .then(response => response.json())
                .then(data => {
                    const duration = performance.now() - startTime;
                    this.apiCalls.push({
                        endpoint,
                        status: 'success',
                        duration,
                        timestamp: new Date().toISOString(),
                        dataSize: JSON.stringify(data).length
                    });
                })
                .catch(error => {
                    const duration = performance.now() - startTime;
                    this.apiCalls.push({
                        endpoint,
                        status: 'error',
                        duration,
                        error: error.message,
                        timestamp: new Date().toISOString()
                    });
                });
        });
    }

    log(message, type = 'info', data = null) {
        const entry = {
            message,
            type,
            data,
            timestamp: new Date().toISOString()
        };
        
        this.logs.push(entry);
        
        // Add color-coded console logging
        const colors = {
            info: '#007bff',
            success: '#28a745',
            warning: '#ffc107',
            error: '#dc3545',
            network: '#6f42c1'
        };
        
        console.log(`%c[${type.toUpperCase()}] ${message}`, `color: ${colors[type] || colors.info}`);
        
        if (data) {
            console.log(data);
        }

        this.updateDebugPanel();
    }

    updateDebugPanel() {
        const panel = document.getElementById('debug-panel');
        if (!panel || !this.isEnabled) return;

        // Update logs tab
        const logsContent = document.getElementById('debug-logs');
        if (logsContent) {
            logsContent.innerHTML = this.logs.slice(-50).map(log => `
                <div class="debug-log-entry debug-${log.type}">
                    <small>${new Date(log.timestamp).toLocaleTimeString()}</small><br>
                    ${log.message}
                    ${log.data ? `<pre>${JSON.stringify(log.data, null, 2)}</pre>` : ''}
                </div>
            `).join('');
        }

        // Update API tab
        const apiContent = document.getElementById('debug-api');
        if (apiContent) {
            apiContent.innerHTML = this.apiCalls.slice(-20).map(call => `
                <div class="debug-log-entry debug-${call.status === 'success' ? 'success' : 'error'}">
                    <strong>${call.endpoint || call.url}</strong><br>
                    Status: ${call.status}<br>
                    Duration: ${call.duration?.toFixed(2)}ms<br>
                    <small>${new Date(call.timestamp).toLocaleTimeString()}</small>
                </div>
            `).join('');
        }

        // Update errors tab
        const errorsContent = document.getElementById('debug-errors');
        if (errorsContent) {
            errorsContent.innerHTML = this.errors.slice(-20).map(error => `
                <div class="debug-log-entry debug-error">
                    <strong>${error.type || 'Error'}</strong><br>
                    ${error.message}<br>
                    <small>${new Date(error.timestamp).toLocaleTimeString()}</small>
                </div>
            `).join('');
        }

        // Update performance tab
        const perfContent = document.getElementById('debug-performance');
        if (perfContent) {
            perfContent.innerHTML = `
                <div class="debug-log-entry">
                    <strong>Performance Metrics</strong><br>
                    Page Load: ${this.performanceMetrics.pageLoadTime || 'N/A'}ms<br>
                    DOM Ready: ${this.performanceMetrics.domContentLoaded || 'N/A'}ms<br>
                    First Paint: ${this.performanceMetrics.firstPaint || 'N/A'}ms<br>
                    API Calls: ${this.apiCalls.length}<br>
                    Errors: ${this.errors.length}
                </div>
            `;
        }

        // Update storage tab
        const storageContent = document.getElementById('debug-storage');
        if (storageContent) {
            const storageData = {
                localStorage: Object.entries(localStorage),
                sessionStorage: Object.entries(sessionStorage),
                cookies: document.cookie.split(';').filter(c => c.trim())
            };
            
            storageContent.innerHTML = `
                <div class="debug-log-entry">
                    <strong>Local Storage (${storageData.localStorage.length} items)</strong><br>
                    ${storageData.localStorage.map(([k, v]) => `${k}: ${v}`).join('<br>')}
                </div>
                <div class="debug-log-entry">
                    <strong>Session Storage (${storageData.sessionStorage.length} items)</strong><br>
                    ${storageData.sessionStorage.map(([k, v]) => `${k}: ${v}`).join('<br>')}
                </div>
            `;
        }
    }

    // Console commands
    showConsoleHelp() {
        console.log(`
🔍 Investment Dashboard Debug Commands:
----------------------------------------
debugger.log(message, type) - Add custom log
Available types: info, success, warning, error, network

Examples:
debugger.log('Testing API', 'info')
debugger.log('User clicked button', 'success', {button: 'buy', timestamp: Date.now()})

Available functions:
- debugger.clear() - Clear all debug logs
- debugger.export() - Export logs to JSON file
- debugger.api() - View API call history
- debugger.errors() - View error logs
- debugger.performance() - View performance metrics
- debugger.storage() - View storage data
- debugger.testApi('/api/portfolio') - Test specific API endpoint
- debugger.reloadData() - Force reload all dashboard data
- debugger.simulateError() - Generate test error
- debugger.toggle() - Toggle debug mode on/off
        `);
    }

    testApiCall(endpoint) {
        const startTime = performance.now();
        
        fetch(endpoint)
            .then(response => response.json())
            .then(data => {
                const duration = performance.now() - startTime;
                this.log(`API Test Success: ${endpoint} - ${duration.toFixed(2)}ms`, 'success', data);
            })
            .catch(error => {
                const duration = performance.now() - startTime;
                this.log(`API Test Error: ${endpoint} - ${duration.toFixed(2)}ms - ${error.message}`, 'error');
            });
    }

    reloadAllData() {
        this.log('🔄 Reloading all dashboard data...', 'info');
        
        // Reload portfolio data
        if (window.InvestmentDashboard && window.InvestmentDashboard.refreshData) {
            window.InvestmentDashboard.refreshData('all');
        }
        
        // Reload page
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    }

    simulateError() {
        const errorTypes = [
            'Network Error',
            'Database Connection',
            'API Timeout',
            'Invalid Data Format',
            'Authentication Failed'
        ];
        
        const randomError = errorTypes[Math.floor(Math.random() * errorTypes.length)];
        const error = new Error(`Simulated ${randomError}`);
        
        this.errors.push({
            type: 'Simulated Error',
            message: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString()
        });
        
        this.log(`🧪 Simulated Error: ${error.message}`, 'error');
    }

    toggleDebugMode() {
        this.isEnabled = !this.isEnabled;
        localStorage.setItem('debugMode', this.isEnabled);
        
        if (this.isEnabled) {
            this.init();
            document.getElementById('debug-panel').style.display = 'block';
        } else {
            document.getElementById('debug-panel').style.display = 'none';
        }
        
        this.log(`Debug mode ${this.isEnabled ? 'enabled' : 'disabled'}`, 'info');
    }

    exportLogs() {
        const exportData = {
            logs: this.logs,
            errors: this.errors,
            apiCalls: this.apiCalls,
            performanceMetrics: this.performanceMetrics,
            exportTimestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `investment-dashboard-debug-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    showWelcomeMessage() {
        console.log(`
🛠️ Investment Dashboard Debugger v1.0
=====================================
Debug mode is ${this.isEnabled ? 'ON' : 'OFF'}
Type 'debugger.help()' for commands
Type 'debugger.toggle()' to toggle debug mode
        `);
    }
}

// Initialize debugger
const debuggerInstance = new InvestmentDashboardDebugger();