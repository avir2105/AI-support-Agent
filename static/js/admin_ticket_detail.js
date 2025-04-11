/**
 * Admin Ticket Detail Page Functionality
 */

// State management
const ticketState = {
    ticket: null,
    loading: true
};

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    console.log("Admin ticket detail page initializing...");
    
    // Get ticket ID from the URL
    const url = window.location.pathname;
    const ticketId = url.substring(url.lastIndexOf('/') + 1);
    
    // Set ticket ID in UI
    document.getElementById('ticket-id').textContent = ticketId;
    
    // Set up status update handler
    document.getElementById('update-status').addEventListener('click', updateTicketStatus);
    
    // Fetch ticket data
    fetchTicketDetails(ticketId);
});

// Fetch ticket details from API
async function fetchTicketDetails(ticketId) {
    try {
        // Show loading state
        ticketState.loading = true;
        
        const response = await fetch(`/api/admin/tickets/${ticketId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const ticket = await response.json();
        ticketState.ticket = ticket;
        ticketState.loading = false;
        
        // Render ticket details
        renderTicketDetails(ticket);
    } catch (error) {
        console.error('Error fetching ticket details:', error);
        showToast('warning', 'Using Demo Data', 'Failed to load real ticket data, showing demo content');
        
        // Use mock data in development
        const mockTicket = generateMockTicketData(ticketId);
        ticketState.ticket = mockTicket;
        ticketState.loading = false;
        
        // Render mock ticket details
        renderTicketDetails(mockTicket);
    }
}

// Render ticket details to the UI
function renderTicketDetails(ticket) {
    // Update ticket info
    document.getElementById('ticket-category').textContent = ticket.issue_category || 'Uncategorized';
    document.getElementById('ticket-priority').textContent = ticket.priority || 'Not set';
    document.getElementById('ticket-sentiment').textContent = ticket.sentiment || 'Neutral';
    document.getElementById('ticket-status-display').textContent = ticket.resolution_status || 'Open';
    document.getElementById('ticket-resolution-date').textContent = formatDate(ticket.date_of_resolution);
    
    // Set status dropdown to current value
    const statusSelect = document.getElementById('ticket-status');
    if (ticket.resolution_status) {
        for (let i = 0; i < statusSelect.options.length; i++) {
            if (statusSelect.options[i].value === ticket.resolution_status) {
                statusSelect.selectedIndex = i;
                break;
            }
        }
    }
    
    // Update agent insights
    document.getElementById('ticket-summary').textContent = ticket.summary || 'No summary available';
    document.getElementById('ticket-solution').textContent = ticket.solution || 'No solution recorded';
    
    // Format routing information
    let routingText = 'Not assigned';
    if (ticket.routing) {
        if (ticket.routing.primary_team) {
            routingText = `Primary: ${ticket.routing.primary_team}`;
            if (ticket.routing.additional_teams && ticket.routing.additional_teams.length > 0) {
                routingText += `<br>Additional: ${ticket.routing.additional_teams.join(', ')}`;
            }
        }
    }
    document.getElementById('ticket-routing').innerHTML = routingText;
    
    // Render conversation
    renderConversation(ticket.conversation || []);
}

// Render conversation messages
function renderConversation(conversation) {
    const conversationEl = document.getElementById('ticket-conversation');
    
    if (!conversation || conversation.length === 0) {
        conversationEl.innerHTML = '<p>No conversation history available.</p>';
        return;
    }
    
    // Sort conversation by timestamp if available
    const sortedConversation = [...conversation].sort((a, b) => {
        if (a.timestamp && b.timestamp) {
            return new Date(a.timestamp) - new Date(b.timestamp);
        }
        return 0;
    });
    
    // Clear previous conversation
    conversationEl.innerHTML = '';
    
    // Process and display messages
    sortedConversation.forEach(message => {
        const messageEl = document.createElement('div');
        messageEl.className = `chat-message ${message.role}`;
        
        // Process message content (convert Markdown to HTML if needed)
        let messageContent = '';
        try {
            if (typeof marked === 'function') {
                messageContent = marked.parse(message.content);
            } else {
                messageContent = `<p>${escapeHTML(message.content)}</p>`;
            }
        } catch (e) {
            console.error('Error parsing message content:', e);
            messageContent = `<p>${escapeHTML(message.content)}</p>`;
        }
        
        // Add message content and timestamp
        messageEl.innerHTML = `
            <div class="message-content">${messageContent}</div>
            <div class="message-timestamp">${formatDate(message.timestamp)}</div>
        `;
        
        // Add to conversation container
        conversationEl.appendChild(messageEl);
    });
    
    // Apply syntax highlighting to code blocks if available
    if (typeof hljs !== 'undefined') {
        document.querySelectorAll('pre code').forEach(block => {
            hljs.highlightElement(block);
        });
    }
}

// Update ticket status
async function updateTicketStatus() {
    const newStatus = document.getElementById('ticket-status').value;
    const ticketId = ticketState.ticket.ticket_id;
    
    try {
        // Disable button during update
        const updateButton = document.getElementById('update-status');
        updateButton.disabled = true;
        updateButton.textContent = 'Updating...';
        
        const response = await fetch(`/api/admin/tickets/${ticketId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ status: newStatus })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Update UI
        document.getElementById('ticket-status-display').textContent = newStatus;
        
        // Show success message
        showToast('success', 'Status Updated', `Ticket status changed to ${newStatus}`);
        
        // Refresh ticket data
        fetchTicketDetails(ticketId);
    } catch (error) {
        console.error('Error updating ticket status:', error);
        showToast('error', 'Update Failed', 'Failed to update ticket status');
    } finally {
        // Re-enable button
        const updateButton = document.getElementById('update-status');
        updateButton.disabled = false;
        updateButton.textContent = 'Update Status';
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
        
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch (e) {
        console.error('Error formatting timestamp:', e);
        return dateString;
    }
}

// Escape HTML to prevent XSS
function escapeHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show toast notification
function showToast(type, title, message) {
    // Check if toast container exists, create if needed
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-header">
            <strong>${title}</strong>
            <button type="button" class="toast-close">&times;</button>
        </div>
        <div class="toast-body">${message}</div>
    `;

    // Add to container
    toastContainer.appendChild(toast);

    // Add close functionality
    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.classList.add('toast-hiding');
        setTimeout(() => toast.remove(), 300);
    });

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.classList.add('toast-hiding');
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
}

// Generate mock ticket data when API fails
function generateMockTicketData(ticketId) {
    return {
        ticket_id: ticketId,
        issue_category: 'Account Access',
        priority: 'High',
        sentiment: 'Frustrated',
        resolution_status: 'In Progress',
        date_of_resolution: null,
        summary: 'User is unable to access their account after password reset.',
        solution: 'Investigating issue with authentication service.',
        routing: {
            primary_team: 'Authentication Team',
            additional_teams: ['User Management']
        },
        conversation: [
            {
                role: 'user',
                content: "I can't log in to my account after I reset my password. I've tried multiple times!",
                timestamp: new Date(Date.now() - 86400000).toISOString()
            },
            {
                role: 'agent',
                content: "I understand how frustrating this must be. Let me check what's happening with your account.",
                timestamp: new Date(Date.now() - 85000000).toISOString()
            },
            {
                role: 'agent',
                content: "I've identified the issue with your account. It appears there was a synchronization problem after your password reset. I'm working on fixing this now.",
                timestamp: new Date(Date.now() - 83000000).toISOString()
            }
        ]
    };
}
