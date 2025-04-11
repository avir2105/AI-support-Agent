/**
 * Admin UI functionality
 */

// Global admin state
const adminState = {
    darkMode: window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches,
    sidebarCollapsed: window.innerWidth < 768,
    connectionStatus: 'checking',
    serverUrl: window.location.origin
};

// Initialize UI elements
document.addEventListener('DOMContentLoaded', () => {
    console.log("Admin UI initializing...");
    
    // Set up theme toggle
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            toggleDarkMode(!document.body.classList.contains('dark-mode'));
        });
    }
    
    // Set up sidebar toggle
    const toggleSidebar = document.getElementById('toggle-sidebar');
    if (toggleSidebar) {
        toggleSidebar.addEventListener('click', () => {
            const sidebar = document.querySelector('.admin-sidebar');
            if (sidebar) {
                sidebar.classList.toggle('collapsed');
                sidebar.classList.toggle('expanded');
                adminState.sidebarCollapsed = sidebar.classList.contains('collapsed');
            }
        });
    }
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        toggleDarkMode(true);
    } else if (savedTheme === 'light') {
        toggleDarkMode(false);
    }
    
    // Initialize connection status
    checkServerConnection();
    
    // Apply initial sidebar state based on screen size
    if (window.innerWidth < 768) {
        const sidebar = document.querySelector('.admin-sidebar');
        if (sidebar && !sidebar.classList.contains('collapsed')) {
            sidebar.classList.add('collapsed');
            adminState.sidebarCollapsed = true;
        }
    }
});

// Toggle dark mode
function toggleDarkMode(isDark) {
    if (isDark) {
        document.body.classList.add('dark-mode');
        document.querySelector('.theme-toggle').innerHTML = '<i class="fas fa-sun"></i>';
        localStorage.setItem('theme', 'dark');
    } else {
        document.body.classList.remove('dark-mode');
        document.querySelector('.theme-toggle').innerHTML = '<i class="fas fa-moon"></i>';
        localStorage.setItem('theme', 'light');
    }
    adminState.darkMode = isDark;
}

// Check server connection
async function checkServerConnection() {
    const connectionIndicator = document.getElementById('connection-indicator');
    const connectionText = document.getElementById('connection-text');
    
    try {
        connectionIndicator.classList.add('connecting');
        connectionText.textContent = 'Checking connection...';
        
        const response = await fetch(`${adminState.serverUrl}/api/health`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.status === 'healthy') {
                updateConnectionStatus('connected');
                
                // Also check database status
                checkDatabaseStatus();
                
                return true;
            } else {
                updateConnectionStatus('disconnected');
                return false;
            }
        } else {
            updateConnectionStatus('disconnected');
            return false;
        }
    } catch (error) {
        console.error('Connection check failed:', error);
        updateConnectionStatus('disconnected');
        return false;
    }
}

// Check database connection status
async function checkDatabaseStatus() {
    try {
        const response = await fetch(`${adminState.serverUrl}/api/metrics`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Display connection status in UI if UI element exists
            if (data.db_status === 'Connected') {
                showToast('success', 'Database Connected', 'Successfully connected to Supabase database.');
            } else {
                showToast('error', 'Database Disconnected', 'Could not connect to Supabase database.');
            }
        }
    } catch (error) {
        console.error('Database status check failed:', error);
    }
}

// Update connection status indicator
function updateConnectionStatus(status) {
    const indicator = document.getElementById('connection-indicator');
    const statusText = document.getElementById('connection-text');
    
    if (!indicator || !statusText) return;
    
    indicator.className = 'status-indicator';
    
    switch (status) {
        case 'connected':
            indicator.classList.add('connected');
            statusText.textContent = 'Connected';
            adminState.connectionStatus = 'connected';
            break;
        case 'checking':
            indicator.classList.add('connecting');
            statusText.textContent = 'Checking connection...';
            adminState.connectionStatus = 'checking';
            break;
        case 'disconnected':
            indicator.classList.add('disconnected');
            statusText.textContent = 'Disconnected';
            adminState.connectionStatus = 'disconnected';
            showToast('error', 'Connection Lost', 'Could not connect to server.');
            break;
        default:
            indicator.classList.add('disconnected');
            statusText.textContent = 'Unknown';
            adminState.connectionStatus = 'unknown';
    }
}

// Show toast notification
function showToast(type, title, message, duration = 4000) {
    const toastContainer = document.getElementById('toast-container');
    
    if (!toastContainer) return;
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Set toast content
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fas fa-${getIconForToastType(type)}"></i>
        </div>
        <div class="toast-content">
            <strong>${title}</strong>
            <div>${message}</div>
        </div>
    `;
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // Remove after duration
    setTimeout(() => {
        toast.classList.remove('show');
        
        // Remove from DOM after animation completes
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, duration);
}

// Get icon for toast type
function getIconForToastType(type) {
    switch (type) {
        case 'success':
            return 'check-circle';
        case 'error':
            return 'exclamation-circle';
        case 'warning':
            return 'exclamation-triangle';
        case 'info':
        default:
            return 'info-circle';
    }
}

// Format date
function formatDate(dateString) {
    if (!dateString) return 'Not available';
    
    try {
        const date = new Date(dateString);
        
        if (isNaN(date.getTime())) {
            return dateString;
        }
        
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch (e) {
        console.error('Error formatting timestamp:', e);
        return dateString;
    }
}

// Format status for display
function formatStatusDisplay(status) {
    if (!status) return '';
    
    const statusClass = status.toLowerCase().replace(/\s+/g, '-');
    return `<span class="ticket-status ${statusClass}">${status}</span>`;
}

// Helper function to create a loading indicator
function createLoadingSpinner() {
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    spinner.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
    return spinner;
}

// Periodic connection check
setInterval(() => {
    if (document.visibilityState === 'visible') {
        checkServerConnection();
    }
}, 30000); // Every 30 seconds
