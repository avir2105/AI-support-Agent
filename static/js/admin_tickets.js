/**
 * Admin Tickets Page Functionality
 */

// State management
const ticketsState = {
    allTickets: [],
    filteredTickets: [],
    currentPage: 1,
    pageSize: 10,
    totalPages: 1,
    sortField: 'ticket_id',
    sortDirection: 'desc',
    filters: {
        status: 'all',
        priority: 'all',
        search: ''
    }
};

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    console.log("Admin tickets page initializing...");
    
    // Add event listeners for filters
    document.getElementById('status-filter').addEventListener('change', updateFilters);
    document.getElementById('priority-filter').addEventListener('change', updateFilters);
    document.getElementById('ticket-search').addEventListener('input', updateFilters);
    
    // Add pagination event listeners
    document.getElementById('prev-page').addEventListener('click', () => {
        if (ticketsState.currentPage > 1) {
            ticketsState.currentPage--;
            renderTickets();
        }
    });
    
    document.getElementById('next-page').addEventListener('click', () => {
        if (ticketsState.currentPage < ticketsState.totalPages) {
            ticketsState.currentPage++;
            renderTickets();
        }
    });
    
    // Fetch tickets data
    fetchTickets();
});

// Fetch tickets data from API
async function fetchTickets() {
    try {
        const response = await fetch('/api/admin/tickets');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        ticketsState.allTickets = data;
        
        // Apply initial filters and display tickets
        applyFilters();
    } catch (error) {
        console.error('Error fetching tickets:', error);
        showToast('error', 'Error', 'Failed to load tickets data');
        
        document.getElementById('tickets-table').innerHTML = `
            <tr>
                <td colspan="7" class="text-center">
                    Error loading tickets. Please try again.
                </td>
            </tr>
        `;
    }
}

// Update filter values in state
function updateFilters() {
    ticketsState.filters.status = document.getElementById('status-filter').value;
    ticketsState.filters.priority = document.getElementById('priority-filter').value;
    ticketsState.filters.search = document.getElementById('ticket-search').value.toLowerCase();
    
    ticketsState.currentPage = 1; // Reset to first page when filters change
    applyFilters();
}

// Apply filters to the tickets data
function applyFilters() {
    const { status, priority, search } = ticketsState.filters;
    
    ticketsState.filteredTickets = ticketsState.allTickets.filter(ticket => {
        // Status filter
        if (status !== 'all' && ticket.resolution_status !== status) {
            return false;
        }
        
        // Priority filter
        if (priority !== 'all' && ticket.priority !== priority) {
            return false;
        }
        
        // Search filter (check multiple fields)
        if (search) {
            const searchFields = [
                ticket.ticket_id,
                ticket.issue_category,
                ticket.priority,
                ticket.resolution_status
            ];
            
            return searchFields.some(field => 
                field && field.toLowerCase().includes(search)
            );
        }
        
        return true;
    });
    
    // Calculate pagination
    ticketsState.totalPages = Math.ceil(ticketsState.filteredTickets.length / ticketsState.pageSize);
    
    renderTickets();
}

// Render tickets to the table
function renderTickets() {
    const tableBody = document.getElementById('tickets-table');
    
    // Clear the table
    tableBody.innerHTML = '';
    
    // Pagination logic
    const startIndex = (ticketsState.currentPage - 1) * ticketsState.pageSize;
    const endIndex = startIndex + ticketsState.pageSize;
    const displayedTickets = ticketsState.filteredTickets.slice(startIndex, endIndex);
    
    // Check if we have tickets to display
    if (displayedTickets.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">No tickets found matching the selected filters.</td>
            </tr>
        `;
    } else {
        // Render each ticket
        displayedTickets.forEach(ticket => {
            const row = document.createElement('tr');
            
            row.innerHTML = `
                <td><span class="ticket-id">${ticket.ticket_id}</span></td>
                <td>${ticket.issue_category || 'N/A'}</td>
                <td>${ticket.sentiment || 'N/A'}</td>
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
    
    // Update pagination controls
    updatePaginationControls();
}

// Update the pagination controls
function updatePaginationControls() {
    const prevButton = document.getElementById('prev-page');
    const nextButton = document.getElementById('next-page');
    const paginationInfo = document.getElementById('pagination-info');
    
    // Disable/enable prev button
    prevButton.disabled = ticketsState.currentPage === 1;
    
    // Disable/enable next button
    nextButton.disabled = ticketsState.currentPage >= ticketsState.totalPages;
    
    // Update page info text
    paginationInfo.textContent = `Page ${ticketsState.currentPage} of ${ticketsState.totalPages || 1}`;
}

// Format date for display
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
