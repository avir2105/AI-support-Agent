/**
 * Chat functionality for customer support interface
 */

// Initialize chat functionality
function initChat() {
  const messageInput = document.getElementById('message-input');
  const sendButton = document.getElementById('send-button');
  const chatMessages = document.getElementById('chat-messages');
  
  // Send message on button click
  sendButton.addEventListener('click', sendMessage);
  
  // Send message on Enter key (but allow Shift+Enter for new lines)
  messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  
  // Auto-resize textarea as user types
  messageInput.addEventListener('input', () => {
    // Reset height to auto to correctly calculate scrollHeight
    messageInput.style.height = 'auto';
    
    // Set new height based on content, with a maximum
    const newHeight = Math.min(Math.max(60, messageInput.scrollHeight), 150);
    messageInput.style.height = `${newHeight}px`;
    
    // Enable/disable send button based on content
    if (messageInput.value.trim()) {
      sendButton.disabled = false;
    } else {
      sendButton.disabled = true;
    }
  });
  
  // Disable send button initially
  sendButton.disabled = true;
  
  // Set initial focus on message input
  setTimeout(() => {
    messageInput.focus();
  }, 500);
}

// Send a message
function sendMessage() {
  const messageInput = document.getElementById('message-input');
  const content = messageInput.value.trim();
  
  if (!content) return;
  
  // Get current timestamp
  const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
  
  // Create message object
  const message = {
    role: 'user',
    content: content,
    timestamp: timestamp
  };
  
  // Add to conversation history
  appState.conversationHistory.push(message);
  
  // Important: Ensure chat messages container is visible before rendering
  const chatMessages = document.getElementById('chat-messages');
  const emptyState = document.getElementById('empty-state');
  
  // Make sure empty state is hidden and chat messages visible
  if (emptyState) emptyState.classList.add('hidden');
  if (chatMessages) chatMessages.classList.remove('hidden');
  
  // Render the message immediately - BEFORE sending to server
  renderNewMessage(message);
  
  // Send to server via WebSocket
  const sent = sendWebSocketMessage('message', { content });
  
  if (sent) {
    // Clear input field and reset height
    messageInput.value = '';
    messageInput.style.height = '60px';
    messageInput.focus();
    
    // Disable send button
    document.getElementById('send-button').disabled = true;
  } else {
    // If sending fails, show error but keep the message in the UI
    showToast('error', 'Message not sent', 'Connection issue. Please try again.');
  }
}

// Render the entire conversation history
function renderConversationHistory() {
  const chatMessages = document.getElementById('chat-messages');
  chatMessages.innerHTML = ''; // Clear existing messages
  
  if (!appState.conversationHistory || appState.conversationHistory.length === 0) {
    return;
  }
  
  // Group messages by date
  const messagesByDate = groupMessagesByDate(appState.conversationHistory);
  
  // Render each group
  Object.keys(messagesByDate).forEach(date => {
    // Add date header
    const dateHeader = document.createElement('div');
    dateHeader.className = 'message-time-header';
    dateHeader.textContent = formatDateHeader(date);
    chatMessages.appendChild(dateHeader);
    
    // Add messages for this date
    messagesByDate[date].forEach(message => {
      const messageElement = createMessageElement(message);
      chatMessages.appendChild(messageElement);
    });
  });
  
  // Scroll to bottom after rendering
  setTimeout(() => {
    scrollToBottom(false);
  }, 100);
}

// Render a new message
function renderNewMessage(message) {
  const chatMessages = document.getElementById('chat-messages');
  const wasAtBottom = isScrolledToBottom();
  
  // Make sure the chat messages container is visible
  chatMessages.classList.remove('hidden');
  
  // Check if we need a new date header
  const lastDateHeader = chatMessages.querySelector('.message-time-header:last-of-type');
  const messageDate = new Date(message.timestamp).toLocaleDateString();
  
  if (!lastDateHeader || lastDateHeader.getAttribute('data-date') !== messageDate) {
    const dateHeader = document.createElement('div');
    dateHeader.className = 'message-time-header';
    dateHeader.textContent = formatDateHeader(messageDate);
    dateHeader.setAttribute('data-date', messageDate);
    chatMessages.appendChild(dateHeader);
  }
  
  // Create and append the message element
  const messageElement = createMessageElement(message);
  chatMessages.appendChild(messageElement);
  
  // Process code blocks with syntax highlighting
  processCodeBlocks();
  
  // Scroll to bottom if already at bottom before new message
  if (wasAtBottom) {
    scrollToBottom();
  } else {
    // Show new messages indicator
    document.getElementById('new-messages-indicator').classList.remove('hidden');
  }
  
  // Update empty state - ensure it's hidden when messages exist
  updateEmptyState();
  
  // Force a layout recalculation to ensure the message is visible
  chatMessages.offsetHeight;
}

// Format timestamp to a more readable format
function formatTimestamp(timestamp) {
    if (!timestamp) return '';
    
    try {
        const date = new Date(timestamp);
        
        // Check if the date is valid
        if (isNaN(date.getTime())) {
            // Try parsing a format like "2025-03-15 10:30:00"
            const parts = timestamp.split(' ');
            if (parts.length === 2) {
                const datePart = parts[0].split('-');
                const timePart = parts[1].split(':');
                
                if (datePart.length === 3 && timePart.length >= 2) {
                    date = new Date(
                        parseInt(datePart[0]), // Year
                        parseInt(datePart[1]) - 1, // Month (0-based)
                        parseInt(datePart[2]), // Day
                        parseInt(timePart[0]), // Hour
                        parseInt(timePart[1]), // Minute
                        timePart[2] ? parseInt(timePart[2]) : 0 // Second (optional)
                    );
                }
            }
            
            // If still invalid, return the original timestamp
            if (isNaN(date.getTime())) {
                return timestamp;
            }
        }
        
        // Format time with hours and minutes
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        
        // Format based on whether it's today or another day
        const now = new Date();
        const isToday = date.getDate() === now.getDate() && 
                        date.getMonth() === now.getMonth() &&
                        date.getFullYear() === now.getFullYear();
                        
        if (isToday) {
            return `Today at ${hours}:${minutes}`;
        } else {
            const day = date.getDate().toString().padStart(2, '0');
            const month = (date.getMonth() + 1).toString().padStart(2, '0');
            return `${day}/${month} at ${hours}:${minutes}`;
        }
    } catch (error) {
        console.error("Error formatting timestamp:", error);
        return timestamp; // Return original on error
    }
}

// Create a message element
function createMessageElement(message) {
    const { role, content, timestamp } = message;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = content;
    messageDiv.appendChild(contentDiv);
    
    const timestampDiv = document.createElement('div');
    timestampDiv.className = 'message-timestamp formatted-timestamp';
    timestampDiv.textContent = formatTimestamp(timestamp);
    messageDiv.appendChild(timestampDiv);
    
    return messageDiv;
}

// This function should be called when receiving a message from WebSocket
function appendMessage(message) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    const messageElement = createMessageElement(message);
    chatMessages.appendChild(messageElement);
    
    // Scroll to the new message
    messageElement.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

// Group messages by date
function groupMessagesByDate(messages) {
  const groups = {};
  
  messages.forEach(message => {
    const date = new Date(message.timestamp).toLocaleDateString();
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(message);
  });
  
  return groups;
}

// Format date header
function formatDateHeader(dateString) {
  const date = new Date(dateString);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);
  
  if (date.toDateString() === today.toDateString()) {
    return 'Today';
  } else if (date.toDateString() === yesterday.toDateString()) {
    return 'Yesterday';
  } else {
    return date.toLocaleDateString(undefined, { 
      weekday: 'long', 
      month: 'long', 
      day: 'numeric',
      year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined
    });
  }
}

// Process code blocks and apply syntax highlighting
function processCodeBlocks() {
  // Find all code blocks that haven't been highlighted yet
  document.querySelectorAll('pre code:not(.hljs)').forEach(block => {
    hljs.highlightElement(block);
  });
}

// Escape HTML to prevent XSS
function escapeHTML(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Additional helper function to ensure message visibility
function ensureMessageVisibility() {
  const chatMessages = document.getElementById('chat-messages');
  const emptyState = document.getElementById('empty-state');
  
  if (appState.conversationHistory && appState.conversationHistory.length > 0) {
    // We have messages, make sure they're visible
    if (emptyState) emptyState.classList.add('hidden');
    if (chatMessages) {
      chatMessages.classList.remove('hidden');
      chatMessages.style.display = 'flex';
    }
  }
  
  // Force layout recalculation
  if (chatMessages) chatMessages.offsetHeight;
}

// Export functions if using modules
if (typeof module !== 'undefined') {
    module.exports = {
        formatTimestamp,
        createMessageElement,
        appendMessage
    };
}
