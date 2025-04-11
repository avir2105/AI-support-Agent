/**
 * UI utility functions for the support system
 */

// Initialize UI elements
function initUI() {
  console.log("Initializing UI elements");
  
  // Ensure app container is visible
  document.querySelector('.app-container').style.opacity = '1';
  
  // Set up theme toggle
  const themeToggle = document.getElementById('theme-toggle');
  themeToggle.addEventListener('click', () => {
    toggleDarkMode(!appState.darkMode);
  });
  
  // Set up insights panel toggle
  const toggleInsights = document.getElementById('toggle-insights');
  const insightsPanel = document.querySelector('.insights-panel');
  
  toggleInsights.addEventListener('click', () => {
    insightsPanel.classList.toggle('collapsed');
    
    // Update icon
    const icon = toggleInsights.querySelector('i');
    if (insightsPanel.classList.contains('collapsed')) {
      icon.className = 'fas fa-chevron-left';
    } else {
      icon.className = 'fas fa-chevron-right';
    }
  });
  
  // Set up collapsible cards
  document.querySelectorAll('.insights-card.collapsible').forEach(card => {
    const header = card.querySelector('.insights-card-header');
    const button = header.querySelector('.collapse-button');
    
    button.addEventListener('click', () => {
      card.classList.toggle('collapsed');
      
      // Update icon
      const icon = button.querySelector('i');
      if (card.classList.contains('collapsed')) {
        icon.className = 'fas fa-chevron-right';
      } else {
        icon.className = 'fas fa-chevron-down';
      }
    });
  });
  
  // Set up "New messages" indicator
  const newMessagesIndicator = document.getElementById('new-messages-indicator');
  newMessagesIndicator.addEventListener('click', () => {
    scrollToBottom();
    newMessagesIndicator.classList.add('hidden');
  });
  
  // Set up scroll detection for "New messages" indicator
  const chatContainer = document.querySelector('.chat-container');
  chatContainer.addEventListener('scroll', () => {
    // Check if scrolled to bottom
    const isAtBottom = chatContainer.scrollHeight - chatContainer.scrollTop <= chatContainer.clientHeight + 100;
    
    // Hide indicator if at bottom
    if (isAtBottom && !newMessagesIndicator.classList.contains('hidden')) {
      newMessagesIndicator.classList.add('hidden');
    }
  });
  
  // Setup file upload
  setupFileUpload();
}

// Show toast notification
function showToast(type, title, message, duration = 4000) {
  const toastContainer = document.getElementById('toast-container');
  
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

// Set up file upload functionality
function setupFileUpload() {
  const fileInput = document.getElementById('file-input');
  const fileDropZone = document.getElementById('file-drop-zone');
  const filePreviewContainer = document.getElementById('file-preview-container');
  
  // Handle file selection
  fileInput.addEventListener('change', () => {
    handleSelectedFiles(fileInput.files);
  });
  
  // Setup drag and drop
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    fileDropZone.addEventListener(eventName, preventDefaults, false);
  });
  
  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }
  
  // Highlight drop zone on drag over
  ['dragenter', 'dragover'].forEach(eventName => {
    fileDropZone.addEventListener(eventName, () => {
      fileDropZone.classList.add('highlight');
    });
  });
  
  // Remove highlight on drag leave
  ['dragleave', 'drop'].forEach(eventName => {
    fileDropZone.addEventListener(eventName, () => {
      fileDropZone.classList.remove('highlight');
    });
  });
  
  // Handle dropped files
  fileDropZone.addEventListener('drop', (e) => {
    const droppedFiles = e.dataTransfer.files;
    handleSelectedFiles(droppedFiles);
  });
}

// Handle selected files
function handleSelectedFiles(files) {
  const filePreviewContainer = document.getElementById('file-preview-container');
  
  if (files.length > 0) {
    filePreviewContainer.classList.remove('hidden');
    filePreviewContainer.innerHTML = '';
    
    Array.from(files).forEach(file => {
      const preview = createFilePreview(file);
      filePreviewContainer.appendChild(preview);
    });
  } else {
    filePreviewContainer.classList.add('hidden');
  }
}

// Create file preview element
function createFilePreview(file) {
  const previewContainer = document.createElement('div');
  previewContainer.className = 'file-preview';
  
  // Create preview based on file type
  if (file.type.startsWith('image/')) {
    const img = document.createElement('img');
    img.src = URL.createObjectURL(file);
    previewContainer.appendChild(img);
  } else {
    // Generic file icon for non-images
    const fileIcon = document.createElement('i');
    fileIcon.className = 'fas fa-file';
    fileIcon.style.fontSize = '24px';
    fileIcon.style.margin = '18px';
    previewContainer.appendChild(fileIcon);
  }
  
  // Add remove button
  const removeButton = document.createElement('span');
  removeButton.className = 'file-remove';
  removeButton.innerHTML = '<i class="fas fa-times"></i>';
  removeButton.addEventListener('click', () => {
    previewContainer.remove();
    
    // Hide container if no more previews
    if (document.querySelectorAll('.file-preview').length === 0) {
      document.getElementById('file-preview-container').classList.add('hidden');
    }
  });
  
  previewContainer.appendChild(removeButton);
  return previewContainer;
}

// Scroll to bottom of chat
function scrollToBottom(animated = true) {
  const chatContainer = document.querySelector('.chat-container');
  chatContainer.scrollTo({
    top: chatContainer.scrollHeight,
    behavior: animated ? 'smooth' : 'auto'
  });
}

// Check if chat is scrolled to bottom
function isScrolledToBottom() {
  const chatContainer = document.querySelector('.chat-container');
  return chatContainer.scrollHeight - chatContainer.scrollTop <= chatContainer.clientHeight + 100;
}

// Update the empty state visibility with improved checks
function updateEmptyState() {
  const emptyState = document.getElementById('empty-state');
  const chatMessages = document.getElementById('chat-messages');
  const appContainer = document.querySelector('.app-container');
  
  if (!emptyState) return;
  
  console.log("UI: Updating empty state. Connected:", appState.isConnected, 
              "Messages:", appState.conversationHistory ? appState.conversationHistory.length : 0);
  
  // Always ensure the app container is visible
  appContainer.style.opacity = '1';
  
  if (appState.conversationHistory && appState.conversationHistory.length > 0) {
    // We have messages, show them and hide empty state
    emptyState.classList.add('hidden');
    chatMessages.classList.remove('hidden');
    console.log("UI: Showing chat messages");
  } else if (appState.isConnected) {
    // We're connected but have no messages, show empty state
    emptyState.classList.remove('hidden');
    chatMessages.classList.add('hidden');
    console.log("UI: Showing empty state");
  } else {
    // We're not connected yet, show app UI but hide empty state
    emptyState.classList.add('hidden');
    chatMessages.classList.add('hidden');
    console.log("UI: Waiting for connection...");
  }
}

// Format timestamp for display
function formatTimestamp(timestamp) {
  if (!timestamp) return '';
  
  try {
    const date = new Date(timestamp);
    
    // Check if valid date
    if (isNaN(date.getTime())) {
      return timestamp;
    }
    
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    
    if (isToday) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' }) + 
             ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
  } catch (e) {
    console.error('Error formatting timestamp:', e);
    return timestamp;
  }
}

// Fetch metrics data from API
async function fetchMetricsData() {
  try {
    const response = await fetch('/api/metrics');
    const data = await response.json();
    
    updateMetricsDisplay(data);
  } catch (error) {
    console.error('Failed to fetch metrics data:', error);
    showToast('error', 'Error', 'Failed to load metrics data');
  }
}

// Update metrics display with data
function updateMetricsDisplay(data) {
  // Update resolution time
  const avgResolutionTime = document.getElementById('avg-resolution-time');
  const avgResolutionTimeDelta = document.getElementById('avg-resolution-time-delta');
  
  if (avgResolutionTime) avgResolutionTime.textContent = data.avg_resolution_time || '-';
  if (avgResolutionTimeDelta) {
    avgResolutionTimeDelta.textContent = data.avg_resolution_time_delta || '';
    
    // Add color class based on delta value
    if (data.avg_resolution_time_delta) {
      if (data.avg_resolution_time_delta.startsWith('-')) {
        avgResolutionTimeDelta.classList.add('positive');
      } else {
        avgResolutionTimeDelta.classList.add('negative');
      }
    }
  }
  
  // Update first response time
  const firstResponseTime = document.getElementById('first-response-time');
  const firstResponseTimeDelta = document.getElementById('first-response-time-delta');
  
  if (firstResponseTime) firstResponseTime.textContent = data.first_response_time || '-';
  if (firstResponseTimeDelta) {
    firstResponseTimeDelta.textContent = data.first_response_time_delta || '';
    
    // Add color class based on delta value
    if (data.first_response_time_delta) {
      if (data.first_response_time_delta.startsWith('-')) {
        firstResponseTimeDelta.classList.add('positive');
      } else {
        firstResponseTimeDelta.classList.add('negative');
      }
    }
  }
  
  // Update customer satisfaction
  const customerSatisfaction = document.getElementById('customer-satisfaction');
  const customerSatisfactionDelta = document.getElementById('customer-satisfaction-delta');
  
  if (customerSatisfaction) customerSatisfaction.textContent = data.customer_satisfaction || '-';
  if (customerSatisfactionDelta) {
    customerSatisfactionDelta.textContent = data.customer_satisfaction_delta || '';
    
    // Add color class based on delta value
    if (data.customer_satisfaction_delta) {
      if (data.customer_satisfaction_delta.startsWith('+')) {
        customerSatisfactionDelta.classList.add('positive');
      } else {
        customerSatisfactionDelta.classList.add('negative');
      }
    }
  }
  
  // Update database status
  const dbStatus = document.getElementById('db-status');
  
  if (dbStatus) {
    dbStatus.textContent = data.db_status || 'Unknown';
    dbStatus.classList.remove('connected', 'disconnected');
    
    if (data.db_status === 'Connected') {
      dbStatus.classList.add('connected');
    } else {
      dbStatus.classList.add('disconnected');
    }
  }
}
