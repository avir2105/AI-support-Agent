/**
 * Admin Analytics Page Functionality
 */

// Analytics state
const analyticsState = {
    charts: {},
    period: 30 // Default to 30 days
};

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    console.log("Admin analytics page initializing...");
    
    // Set up date range selector
    document.getElementById('date-range').addEventListener('change', (e) => {
        analyticsState.period = parseInt(e.target.value);
        loadAllAnalytics();
    });
    
    // Set up refresh button
    document.getElementById('refresh-analytics').addEventListener('click', () => {
        loadAllAnalytics();
        showToast('info', 'Refreshing', 'Refreshing analytics data...');
    });
    
    // Initialize charts
    initializeCharts();
    
    // Load initial data
    loadAllAnalytics();
});

// Initialize charts
function initializeCharts() {
    // Categories chart
    const categoryCtx = document.getElementById('analytics-category-chart').getContext('2d');
    analyticsState.charts.category = new Chart(categoryCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Number of Tickets',
                backgroundColor: 'rgba(99, 102, 241, 0.7)',
                data: []
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top'
                },
                title: {
                    display: true,
                    text: 'Tickets by Category'
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
    
    // Resolution time chart
    const timeCtx = document.getElementById('analytics-time-chart').getContext('2d');
    analyticsState.charts.time = new Chart(timeCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Average Resolution Time (hours)',
                backgroundColor: 'rgba(16, 185, 129, 0.7)',
                data: []
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top'
                },
                title: {
                    display: true,
                    text: 'Resolution Time by Category'
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
    
    // Sentiment chart
    const sentimentCtx = document.getElementById('analytics-sentiment-chart').getContext('2d');
    analyticsState.charts.sentiment = new Chart(sentimentCtx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Neutral', 'Negative'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: [
                    '#10b981',  // success (Positive)
                    '#6b7280',  // neutral (Neutral)
                    '#ef4444'   // error (Negative)
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                },
                title: {
                    display: true,
                    text: 'Customer Sentiment Distribution'
                }
            }
        }
    });
    
    // Trend chart
    const trendCtx = document.getElementById('analytics-trend-chart').getContext('2d');
    analyticsState.charts.trend = new Chart(trendCtx, {
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
                title: {
                    display: true,
                    text: 'Ticket Creation and Resolution Trend'
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
    
    // Priority chart
    const priorityCtx = document.getElementById('analytics-priority-chart').getContext('2d');
    analyticsState.charts.priority = new Chart(priorityCtx, {
        type: 'polarArea',
        data: {
            labels: ['Critical', 'High', 'Medium', 'Low'],
            datasets: [{
                data: [0, 0, 0, 0],
                backgroundColor: [
                    'rgba(239, 68, 68, 0.7)',   // Critical
                    'rgba(245, 158, 11, 0.7)',  // High
                    'rgba(59, 130, 246, 0.7)',  // Medium
                    'rgba(16, 185, 129, 0.7)'   // Low
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                },
                title: {
                    display: true,
                    text: 'Tickets by Priority'
                }
            }
        }
    });
}

// Load all analytics data
function loadAllAnalytics() {
    fetchAnalyticsMetrics();
    fetchCategories();
    fetchResolutionTimes();
    fetchSentiment();
    fetchTrend();
    fetchPriority();
}

// Fetch analytics metrics
async function fetchAnalyticsMetrics() {
    try {
        const response = await fetch(`/api/admin/analytics/metrics?days=${analyticsState.period}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update metrics display
        document.getElementById('analytics-resolution-rate').textContent = `${data.resolutionRate}%`;
        document.getElementById('analytics-avg-time').textContent = data.avgResolutionTime;
        document.getElementById('analytics-sentiment').textContent = data.sentiment;
        
        // Update deltas
        updateDelta('analytics-resolution-delta', data.resolutionDelta);
        updateDelta('analytics-time-delta', data.timeDelta, true); // True means negative is good
        updateDelta('analytics-sentiment-delta', data.sentimentDelta);
    } catch (error) {
        console.error('Error fetching analytics metrics:', error);
        showToast('error', 'Error', 'Failed to load analytics metrics');
    }
}

// Fetch category distribution
async function fetchCategories() {
    try {
        const response = await fetch(`/api/admin/analytics/categories?days=${analyticsState.period}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update chart
        analyticsState.charts.category.data.labels = data.categories;
        analyticsState.charts.category.data.datasets[0].data = data.counts;
        analyticsState.charts.category.update();
    } catch (error) {
        console.error('Error fetching categories:', error);
        showToast('error', 'Error', 'Failed to load category data');
    }
}

// Fetch resolution times
async function fetchResolutionTimes() {
    try {
        const response = await fetch(`/api/admin/analytics/resolution-times?days=${analyticsState.period}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update chart
        analyticsState.charts.time.data.labels = data.categories;
        analyticsState.charts.time.data.datasets[0].data = data.times;
        analyticsState.charts.time.update();
    } catch (error) {
        console.error('Error fetching resolution times:', error);
        showToast('error', 'Error', 'Failed to load resolution time data');
    }
}

// Fetch sentiment distribution
async function fetchSentiment() {
    try {
        const response = await fetch(`/api/admin/analytics/sentiment?days=${analyticsState.period}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update chart
        analyticsState.charts.sentiment.data.labels = data.labels;
        analyticsState.charts.sentiment.data.datasets[0].data = data.counts;
        analyticsState.charts.sentiment.update();
    } catch (error) {
        console.error('Error fetching sentiment data:', error);
        showToast('error', 'Error', 'Failed to load sentiment data');
    }
}

// Fetch ticket trend
async function fetchTrend() {
    try {
        const response = await fetch(`/api/admin/analytics/trend?days=${analyticsState.period}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update chart
        analyticsState.charts.trend.data.labels = data.labels;
        analyticsState.charts.trend.data.datasets[0].data = data.created;
        analyticsState.charts.trend.data.datasets[1].data = data.resolved;
        analyticsState.charts.trend.update();
    } catch (error) {
        console.error('Error fetching trend data:', error);
        showToast('error', 'Error', 'Failed to load trend data');
    }
}

// Fetch priority distribution
async function fetchPriority() {
    try {
        const response = await fetch(`/api/admin/analytics/priority?days=${analyticsState.period}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update chart
        analyticsState.charts.priority.data.labels = data.labels;
        analyticsState.charts.priority.data.datasets[0].data = data.counts;
        analyticsState.charts.priority.update();
    } catch (error) {
        console.error('Error fetching priority data:', error);
        showToast('error', 'Error', 'Failed to load priority data');
    }
}

// Update delta display
function updateDelta(elementId, value, negativeIsGood = false) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    // Reset classes
    element.classList.remove('positive', 'negative');
    
    // Skip if no value
    if (value === undefined || value === null) {
        element.innerHTML = '<i class="fas fa-equals"></i> <span>No change</span>';
        return;
    }
    
    // Determine if this is positive or negative
    const isPositive = negativeIsGood ? value < 0 : value > 0;
    const icon = isPositive ? 'fa-arrow-up' : (value === 0 ? 'fa-equals' : 'fa-arrow-down');
    
    // Add appropriate class
    if (value !== 0) {
        element.classList.add(isPositive ? 'positive' : 'negative');
    }
    
    // Update HTML
    element.innerHTML = `
        <i class="fas ${icon}"></i>
        <span>${Math.abs(value)}% from previous period</span>
    `;
}
