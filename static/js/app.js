/**
 * Main application initialization
 */

// Generate a session ID for this user/browser
const generateSessionId = () => {
  const existingSessionId = localStorage.getItem('supportSystemSessionId');
  if (existingSessionId) {
    return existingSessionId;
  }
  
  const newSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substring(2, 15);
  localStorage.setItem('supportSystemSessionId', newSessionId);
  return newSessionId;
};

// Session ID for this user
const SESSION_ID = generateSessionId();

// Application state
const appState = {
  ticketId: null,
  conversationHistory: [],
  currentSummary: '',
  actions: [],
  recommendations: [],
  routing: {},
  timeEstimate: '',
  isConnected: false,
  darkMode: window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches,
  isTyping: false,
  isInitializing: true // Add flag to track initialization state
};

// Initialize components
document.addEventListener('DOMContentLoaded', () => {
  console.log("DOM fully loaded, initializing application");
  
  // Make sure app container is visible immediately
  document.querySelector('.app-container').style.opacity = '1';
  
  // Add initializing class to body to control initial rendering states
  document.body.classList.add('initializing');
  
  // Force layout recalculation to prevent blur
  document.body.offsetHeight;
  
  // Hide empty state until we determine if it should be visible
  const emptyState = document.getElementById('empty-state');
  if (emptyState) {
    emptyState.classList.add('hidden');
  }
  
  // Initialize web socket connection
  initWebSocket(SESSION_ID);
  
  // Initialize UI elements
  initUI();
  
  // Initialize chat functionality
  initChat();
  
  // Initialize insights panel
  initInsights();
  
  // Fetch initial metrics data
  fetchMetricsData();
  
  // Listen for system theme changes
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem('theme')) {
        toggleDarkMode(e.matches);
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
  
  // Remove initializing class after short delay to ensure everything is rendered
  setTimeout(() => {
    document.body.classList.remove('initializing');
    appState.isInitializing = false;
    
    // Now check if we should show empty state
    updateEmptyState();
    
    // Force a redraw to fix any blurry elements
    document.body.style.display = 'none';
    document.body.offsetHeight; // Force reflow
    document.body.style.display = '';
    
    console.log("Application initialization complete");
  }, 500);
});

// Toggle dark mode
function toggleDarkMode(isDark) {
  if (isDark) {
    document.body.classList.add('dark-mode');
    document.getElementById('theme-toggle').innerHTML = '<i class="fas fa-sun"></i>';
    localStorage.setItem('theme', 'dark');
  } else {
    document.body.classList.remove('dark-mode');
    document.getElementById('theme-toggle').innerHTML = '<i class="fas fa-moon"></i>';
    localStorage.setItem('theme', 'light');
  }
  appState.darkMode = isDark;
}

// Update empty state visibility with improved logic
function updateEmptyState() {
  const emptyState = document.getElementById('empty-state');
  const chatMessages = document.getElementById('chat-messages');
  const appContainer = document.querySelector('.app-container');
  
  if (!emptyState) return;
  
  console.log("Updating empty state. Connected:", appState.isConnected, 
              "Messages:", appState.conversationHistory ? appState.conversationHistory.length : 0);
  
  // Always ensure app container is visible
  appContainer.style.opacity = '1';
  
  // When we have messages, ALWAYS show the chat regardless of connection status
  if (appState.conversationHistory && appState.conversationHistory.length > 0) {
    // We have messages, always show them
    emptyState.classList.add('hidden');
    chatMessages.classList.remove('hidden');
    // Make sure display style is set correctly
    chatMessages.style.display = 'flex';
    console.log("Showing chat messages");
  } else {
    // Only show empty state when connected but with no messages
    if (appState.isConnected) {
      emptyState.classList.remove('hidden');
      chatMessages.classList.add('hidden');
      console.log("Showing empty state");
    } else {
      // Hide both when not connected yet
      emptyState.classList.add('hidden');
      chatMessages.classList.add('hidden');
      console.log("Hiding empty state and chat messages");
    }
  }
}

// Set up periodic metrics refresh
setInterval(() => {
  if (appState.isConnected) {
    fetchMetricsData();
  }
}, 30000); // Refresh every 30 seconds
