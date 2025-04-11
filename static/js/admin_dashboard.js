/**
 * Admin Dashboard Functionality
 */

// Dashboard state
const dashboardState = {
    charts: {},
    metrics: {}
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log("Admin dashboard initializing...");
    
    // Fetch dashboard data
    fetchDashboardMetrics();
    fetchRecentTickets();
    
    // Set up chart period selector
    document.getElementById('ticket-chart-period').addEventListener('change', (e) => {
        fetchTicketActivity(e.target.value);
    });
    
    // Initialize charts
    initializeCharts();
});

// Initialize chart.js instances
function initializeCharts() {
    // Ticket activity chart
    const activityCtx = document.getElementById('ticket-activity-chart').getContext('2d');
    dashboardState.charts.activity = new Chart(activityCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'New Tickets',
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    data: [],
                    tension: 0.2,
                    fill: true
                },
                {
                    label: 'Resolved Tickets',
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    data: [],
                    tension: 0.2,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
    
    // Category chart
    const categoryCtx = document.getElementById('category-chart').getContext('2d');
    dashboardState.charts.category = new Chart(categoryCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Avg. Resolution Time (hours)',
                backgroundColor: 'rgba(99, 102, 241, 0.7)',
                data: []
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Hours'
                    }
                }
            }
        }
    });
    
    // Status distribution chart
    const statusCtx = document.getElementById('status-chart').getContext('2d');
    dashboardState.charts.status = new Chart(statusCtx, {
        type: 'doughnut',
        data: {
            labels: ['Open', 'In Progress', 'Resolved'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: [
                    '#f59e0b',  // warning (Open)
                    '#3b82f6',  // info (In Progress)
                    '#10b981'   // success (Resolved)
                ],
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
    
    // Load initial data for charts
    fetchTicketActivity('month');
    fetchCategoryData();
    fetchStatusDistribution();
}

// Fetch dashboard metrics
async function fetchDashboardMetrics() {
    try {
        const response = await fetch('/api/admin/metrics');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        dashboardState.metrics = data;
        
        // Update metrics display
        updateMetricsDisplay(data);
    } catch (error) {
        console.error('Error fetching dashboard metrics:', error);
        showToast('error', 'Error', 'Failed to load dashboard metrics');
    }
}

// Fetch ticket activity data for chart
async function fetchTicketActivity(period = 'month') {
    try {
        const response = await fetch(`/api/admin/charts/activity?period=${period}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update chart
        dashboardState.charts.activity.data.labels = data.labels;
        dashboardState.charts.activity.data.datasets[0].data = data.newTickets;
        dashboardState.charts.activity.data.datasets[1].data = data.resolvedTickets;
        dashboardState.charts.activity.update();
    } catch (error) {
        console.error('Error fetching ticket activity:', error);
        showToast('error', 'Error', 'Failed to load ticket activity data');
    }
}

// Fetch category data for chart
async function fetchCategoryData() {
    try {
        const response = await fetch('/api/admin/charts/categories');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update chart
        dashboardState.charts.category.data.labels = data.categories;
        dashboardState.charts.category.data.datasets[0].data = data.resolutionTimes;
        dashboardState.charts.category.update();
    } catch (error) {
        console.error('Error fetching category data:', error);
        showToast('error', 'Error', 'Failed to load category data');
    }
}

// Fetch status distribution for chart
async function fetchStatusDistribution() {
    try {
        const response = await fetch('/api/admin/charts/status');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update chart
        dashboardState.charts.status.data.datasets[0].data = [
            data.openCount || 0,
            data.inProgressCount || 0,
            data.resolvedCount || 0
        ];
        dashboardState.charts.status.update();
    } catch (error) {
        console.error('Error fetching status distribution:', error);
        showToast('error', 'Error', 'Failed to load status distribution data');
    }
}

// Fetch recent tickets
async function fetchRecentTickets() {
    try {
        const response = await fetch('/api/admin/tickets/recent');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const tickets = await response.json();
        
        // Update table
        renderRecentTickets(tickets);
    } catch (error) {
        console.error('Error fetching recent tickets:', error);
        showToast('error', 'Error', 'Failed to load recent tickets');
        
        document.getElementById('recent-tickets-table').innerHTML = `
            <tr>
                <td colspan="6" class="text-center">Error loading recent tickets.</td>
            </tr>
        `;
    }
}

// Render recent tickets table
function renderRecentTickets(tickets) {
    const tableBody = document.getElementById('recent-tickets-table');
    
    // Clear the table
    tableBody.innerHTML = '';
    
    if (!tickets || tickets.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">No recent tickets found.</td>
            </tr>
        `;
        return;
    }
    
    // Render each ticket
    tickets.forEach(ticket => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td><span class="ticket-id">${ticket.ticket_id}</span></td>
            <td>${ticket.issue_category || 'N/A'}</td>
            <td>${ticket.priority || 'N/A'}</td>
            <td>${formatStatusDisplay(ticket.resolution_status)}</td>
            <td>${formatDate(ticket.date_of_resolution)}</td>
            <td>
                <a href="/admin/tickets/${ticket.ticket_id}" class="action-link">View</a>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Update metrics display
function updateMetricsDisplay(data) {
    // Total tickets
    document.getElementById('total-tickets').textContent = data.totalTickets.toLocaleString();
    
    // Tickets delta
    const ticketsDelta = document.getElementById('tickets-delta');
    ticketsDelta.innerHTML = `
        <i class="fas ${data.ticketsDelta >= 0 ? 'fa-arrow-up' : 'fa-arrow-down'}"></i>
        <span>${Math.abs(data.ticketsDelta)}% from last month</span>
    `;
    if (data.ticketsDelta >= 0) {
        ticketsDelta.classList.add('positive');
        ticketsDelta.classList.remove('negative');
    } else {
        ticketsDelta.classList.add('negative');
        ticketsDelta.classList.remove('positive');
    }
    
    // Resolution rate
    document.getElementById('resolution-rate').textContent = `${data.resolutionRate}%`;
    
    // Resolution delta
    const resolutionDelta = document.getElementById('resolution-delta');
    resolutionDelta.innerHTML = `
        <i class="fas ${data.resolutionDelta >= 0 ? 'fa-arrow-up' : 'fa-arrow-down'}"></i>
        <span>${Math.abs(data.resolutionDelta)}% from last month</span>
    `;
    if (data.resolutionDelta >= 0) {
        resolutionDelta.classList.add('positive');
        resolutionDelta.classList.remove('negative');
    } else {
        resolutionDelta.classList.add('negative');
        resolutionDelta.classList.remove('positive');
    }
    
    // Average resolution time
    document.getElementById('avg-resolution-time').textContent = data.avgResolutionTime;
    
    // Time delta
    const timeDelta = document.getElementById('time-delta');
    timeDelta.innerHTML = `
        <i class="fas ${data.timeDelta <= 0 ? 'fa-arrow-down' : 'fa-arrow-up'}"></i>
        <span>${Math.abs(data.timeDelta)}% from last month</span>
    `;
    if (data.timeDelta <= 0) {
        timeDelta.classList.add('positive');
        timeDelta.classList.remove('negative');
    } else {
        timeDelta.classList.add('negative');
        timeDelta.classList.remove('positive');
    }
    
    // Critical issues
    document.getElementById('critical-issues').textContent = data.criticalIssues.toLocaleString();
    
    // Critical issues delta
    const criticalDelta = document.getElementById('critical-delta');
    criticalDelta.innerHTML = `
        <i class="fas ${data.criticalDelta <= 0 ? 'fa-arrow-down' : 'fa-arrow-up'}"></i>
        <span>${Math.abs(data.criticalDelta)}% from last month</span>
    `;
    if (data.criticalDelta <= 0) {
        criticalDelta.classList.add('positive');
        criticalDelta.classList.remove('negative');
    } else {
        criticalDelta.classList.add('negative');
        criticalDelta.classList.remove('positive');
    }
}

// Format date for display
function formatDate(dateString) {
    if (!dateString) return 'Not available';
    
    try {
        const date = new Date(dateString);
        
        if (isNaN(date.getTime())) {
            return dateString;
        }
        
        return date.toLocaleDateString();
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
