/**
 * WebSocket communication module for real-time interaction with the server
 */

// WebSocket connection handler
let socket;
let sessionId;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

// Generate a session ID if needed
function generateSessionId() {
    return localStorage.getItem('sessionId') || Math.random().toString(36).substring(2, 15);
}

// Initialize WebSocket connection
function initWebSocket() {
    // Generate or retrieve session ID
    sessionId = generateSessionId();
    localStorage.setItem('sessionId', sessionId);
    
    // Determine WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;
    
    // Connect to WebSocket
    socket = new WebSocket(wsUrl);
    
    // Set up event handlers
    socket.onopen = handleSocketOpen;
    socket.onmessage = handleSocketMessage;
    socket.onclose = handleSocketClose;
    socket.onerror = handleSocketError;
}

// Handle WebSocket open event
function handleSocketOpen() {
    console.log('WebSocket connection established');
    updateConnectionStatus('connected');
    reconnectAttempts = 0;
    
    // Show empty state if appropriate
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages && chatMessages.children.length === 0) {
        document.getElementById('empty-state').classList.remove('hidden');
    }
}

// Handle incoming WebSocket messages
function handleSocketMessage(event) {
    try {
        const data = JSON.parse(event.data);
        console.log('Received message:', data);
        
        // Hide empty state when receiving any message
        document.getElementById('empty-state').classList.add('hidden');
        
        // Handle different message types
        switch(data.type) {
            case 'init':
                handleInitMessage(data);
                break;
            case 'message':
                // Ensure the timestamp is in the right format
                if (data.timestamp) {
                    // Append new message to chat
                    appendMessage({
                        role: data.role,
                        content: data.content,
                        timestamp: data.timestamp
                    });
                }
                break;
            case 'typing_indicator':
                toggleTypingIndicator(data.isTyping);
                break;
            case 'update_summary':
                updateSummary(data.data);
                break;
            case 'update_actions':
                updateActions(data.data);
                break;
            case 'update_recommendations':
                updateRecommendations(data.data);
                break;
            case 'update_routing':
                updateRouting(data.data);
                break;
            case 'update_time_estimate':
                updateTimeEstimate(data.data);
                break;
            case 'status_update_result':
                handleStatusUpdateResult(data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    } catch (error) {
        console.error('Error handling WebSocket message:', error);
    }
}

// Send a message via WebSocket
function sendMessage(message) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        const messageData = {
            type: 'message',
            content: message
        };
        socket.send(JSON.stringify(messageData));
        
        // Add the sent message to the UI immediately with current timestamp
        const now = new Date();
        const timestamp = now.toISOString().replace('T', ' ').substring(0, 19);
        
        appendMessage({
            role: 'user',
            content: message,
            timestamp: timestamp
        });
        
        return true;
    }
    return false;
}

// Other functions remain the same
function updateConnectionStatus(status) {
    const indicator = document.getElementById('connection-indicator');
    const statusText = document.getElementById('connection-text');
    
    indicator.className = 'status-indicator';
    
    switch (status) {
        case 'connected':
            indicator.classList.add('connected');
            statusText.textContent = 'Connected';
            break;
        case 'connecting':
            indicator.classList.add('connecting');
            statusText.textContent = 'Connecting...';
            break;
        case 'disconnected':
            indicator.classList.add('disconnected');
            statusText.textContent = 'Disconnected';
            break;
        default:
            indicator.classList.add('disconnected');
            statusText.textContent = 'Disconnected';
    }
}

function handleInitMessage(data) {
    console.log('Setting initial state from server');
    
    // Make sure app container is visible
    document.querySelector('.app-container').style.opacity = '1';
    
    // Update ticket ID
    if (data.ticket_id) {
        document.getElementById('ticket-id').textContent = data.ticket_id;
        appState.ticketId = data.ticket_id;
    }
    
    // Update conversation history
    if (data.conversation_history && Array.isArray(data.conversation_history)) {
        appState.conversationHistory = data.conversation_history;
        renderConversationHistory();
        
        // If we have messages, make sure they're visible
        if (data.conversation_history.length > 0) {
            const chatMessages = document.getElementById('chat-messages');
            const emptyState = document.getElementById('empty-state');
            
            if (chatMessages) chatMessages.classList.remove('hidden');
            if (emptyState) emptyState.classList.add('hidden');
        }
    }
    
    // Update insights panel sections
    if (data.current_summary) {
        updateSummary(data.current_summary);
    }
    
    if (data.actions && Array.isArray(data.actions)) {
        updateActions(data.actions);
    }
    
    if (data.recommendations && Array.isArray(data.recommendations)) {
        updateRecommendations(data.recommendations);
    }
    
    if (data.routing) {
        updateRouting(data.routing);
    }
    
    if (data.time_estimate) {
        updateTimeEstimate(data.time_estimate);
    }
    
    // Now that we've loaded data, update the empty state
    updateEmptyState();
    
    // Force a redraw to ensure visibility
    setTimeout(() => {
        const appContainer = document.querySelector('.app-container');
        appContainer.style.display = 'none';
        appContainer.offsetHeight; // Force reflow
        appContainer.style.display = 'flex';
        appContainer.style.opacity = '1';
    }, 50);
}

function appendMessage(message) {
    console.log('Appending message:', message);
    appState.conversationHistory.push(message);
    renderNewMessage(message);
}

function toggleTypingIndicator(isTyping) {
    const typingIndicator = document.getElementById('typing-indicator');
    
    if (isTyping) {
        appState.isTyping = true;
        typingIndicator.classList.remove('hidden');
        
        // Scroll to typing indicator
        setTimeout(() => {
            typingIndicator.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }, 100);
    } else {
        appState.isTyping = false;
        typingIndicator.classList.add('hidden');
    }
}

function handleStatusUpdateResult(message) {
    if (message.success) {
        showToast('success', 'Status updated', `Ticket status changed to ${message.status}`);
        
        // If status is Resolved, show additional toast
        if (message.status === 'Resolved') {
            setTimeout(() => {
                showToast('info', 'Ticket resolved', 'Thank you for using our support system!');
            }, 1000);
        }
    } else {
        showToast('error', 'Status update failed', 'Could not update ticket status');
    }
}
