/**
 * Insights panel functionality
 */

// Initialize insights panel functionality
function initInsights() {
  // Set up update status button
  const updateStatusButton = document.getElementById('update-status');
  updateStatusButton.addEventListener('click', updateTicketStatus);
}

// Update ticket status
function updateTicketStatus() {
  const statusSelect = document.getElementById('ticket-status');
  const newStatus = statusSelect.value;
  
  // Send status update to server
  sendWebSocketMessage('update_status', {
    status: newStatus,
    with_db: true  // Update in database
  });
  
  // Show loading state
  updateStatusButton.disabled = true;
  updateStatusButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
  
  // Reset after 2 seconds (in case we don't get a response)
  setTimeout(() => {
    updateStatusButton.disabled = false;
    updateStatusButton.textContent = 'Update';
  }, 2000);
}

// Update summary section with new data
function updateSummarySection(summary) {
  const summaryContent = document.getElementById('summary-content');
  
  if (summary && summaryContent) {
    summaryContent.textContent = summary;
    highlightSectionUpdate(summaryContent.closest('.insights-card'));
    
    // Store in app state
    appState.currentSummary = summary;
  }
}

// Update actions section with new data
function updateActionsSection(actions) {
  const actionsList = document.getElementById('actions-list');
  
  if (actions && actionsList) {
    // Clear existing content
    actionsList.innerHTML = '';
    
    if (actions.length === 0) {
      actionsList.innerHTML = '<li class="empty-list-message">No actions identified yet.</li>';
    } else {
      // Add each action
      actions.forEach(action => {
        const actionItem = document.createElement('li');
        actionItem.textContent = action;
        actionsList.appendChild(actionItem);
      });
    }
    
    highlightSectionUpdate(actionsList.closest('.insights-card'));
    
    // Store in app state
    appState.actions = actions;
  }
}

// Update recommendations section with new data
function updateRecommendationsSection(recommendations) {
  const recommendationsList = document.getElementById('recommendations-list');
  
  if (recommendations && recommendationsList) {
    // Clear existing content
    recommendationsList.innerHTML = '';
    
    if (recommendations.length === 0) {
      recommendationsList.innerHTML = '<li class="empty-list-message">No recommendations available yet.</li>';
    } else {
      // Add each recommendation
      recommendations.forEach(recommendation => {
        const recommendationItem = document.createElement('li');
        recommendationItem.textContent = recommendation;
        recommendationsList.appendChild(recommendationItem);
      });
    }
    
    highlightSectionUpdate(recommendationsList.closest('.insights-card'));
    
    // Store in app state
    appState.recommendations = recommendations;
  }
}

// Update routing section with new data
function updateRoutingSection(routing) {
  const routingContent = document.getElementById('routing-content');
  
  if (routing && routingContent) {
    // Clear existing content
    routingContent.innerHTML = '';
    
    if (!routing.primary_team) {
      routingContent.innerHTML = '<p>No routing determined yet.</p>';
    } else {
      // Add primary team
      const primaryTeam = document.createElement('p');
      primaryTeam.innerHTML = `<strong>Primary Team:</strong> <span class="routing-team">${routing.primary_team}</span>`;
      routingContent.appendChild(primaryTeam);
      
      // Add additional teams if any
      if (routing.additional_teams && routing.additional_teams.length > 0) {
        const additionalTeamsContainer = document.createElement('div');
        additionalTeamsContainer.className = 'routing-additional';
        
        const additionalTeamsTitle = document.createElement('p');
        additionalTeamsTitle.innerHTML = '<strong>Additional Teams:</strong>';
        additionalTeamsContainer.appendChild(additionalTeamsTitle);
        
        const teamsList = document.createElement('ul');
        routing.additional_teams.forEach(team => {
          const teamItem = document.createElement('li');
          teamItem.textContent = team;
          teamsList.appendChild(teamItem);
        });
        
        additionalTeamsContainer.appendChild(teamsList);
        routingContent.appendChild(additionalTeamsContainer);
      }
    }
    
    highlightSectionUpdate(routingContent.closest('.insights-card'));
    
    // Store in app state
    appState.routing = routing;
  }
}

// Update time estimate section with new data
function updateTimeEstimateSection(timeEstimate) {
  const timeEstimateContent = document.getElementById('time-estimate-content');
  
  if (timeEstimate && timeEstimateContent) {
    timeEstimateContent.textContent = timeEstimate;
    highlightSectionUpdate(timeEstimateContent.closest('.insights-card'));
    
    // Store in app state
    appState.timeEstimate = timeEstimate;
  }
}

// Highlight a section that has been updated
function highlightSectionUpdate(element) {
  if (!element) return;
  
  // Remove any existing highlight
  element.classList.remove('highlight-update');
  
  // Force browser reflow
  void element.offsetWidth;
  
  // Add highlight class
  element.classList.add('highlight-update');
  
  // Ensure card is expanded
  if (element.classList.contains('collapsible') && element.classList.contains('collapsed')) {
    // Simulate click on collapse button to expand
    const collapseButton = element.querySelector('.collapse-button');
    if (collapseButton) {
      collapseButton.click();
    }
  }
}
