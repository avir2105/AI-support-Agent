import os
import json
import supabase
from supabase import create_client, Client

class SupabaseClient:
    """Client for interacting with Supabase database."""
    
    # Singleton instance
    _instance = None
    
    def __new__(cls):
        """Create or return the singleton instance."""
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the Supabase client (only once)."""
        # Skip initialization if already done
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        print("[DATABASE] Initializing Supabase client...")
        
        # Use environment variables if available, otherwise use default values
        self.url = os.environ.get("SUPABASE_URL", "https://ovqvblbfvdritxelijkg.supabase.co")
        self.key = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im92cXZibGJmdmRyaXR4ZWxpamtnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQwNTU5OTMsImV4cCI6MjA1OTYzMTk5M30.d32JTYYGhZZrw2W4XuSzLw2t03lc-JJykuTU1YmhyoM")
        self.table_name = os.environ.get("SUPABASE_TABLE", "Historical_ticket_data")
            
        try:
            self.client = create_client(self.url, self.key)
            print(f"[DATABASE] Supabase client initialized successfully. Using table: {self.table_name}")
        except Exception as e:
            print(f"[DATABASE] Error initializing Supabase client: {str(e)}")
            self.client = None
            
        self._initialized = True
    
    def check_ticket_exists(self, ticket_id):
        """
        Check if a ticket with the given ID already exists.
        
        Args:
            ticket_id (str): The ticket ID to check
            
        Returns:
            bool: True if ticket exists, False otherwise
        """
        print(f"[DATABASE] Checking if ticket {ticket_id} already exists...")
        if self.client:
            try:
                response = self.client.table(self.table_name).select('ticket_id').eq('ticket_id', ticket_id).execute()
                exists = response.data and len(response.data) > 0
                print(f"[DATABASE] Ticket {ticket_id} exists: {exists}")
                return exists
            except Exception as e:
                print(f"[DATABASE] Error checking if ticket exists: {str(e)}")
                return False
        else:
            print("[DATABASE] Client not initialized, cannot check if ticket exists")
            return False
    
    def generate_unique_ticket_id(self, base_ticket_id):
        """
        Generate a unique ticket ID by incrementing the number if the base ID already exists.
        
        Args:
            base_ticket_id (str): The base ticket ID to check
            
        Returns:
            str: A unique ticket ID
        """
        print(f"[DATABASE] Generating unique ticket ID from base: {base_ticket_id}")
        
        if not self.client:
            print(f"[DATABASE] Client not initialized, cannot check ticket ID uniqueness")
            return base_ticket_id
            
        # If the base ID doesn't contain a hyphen and number suffix, add "-1"
        if "-" not in base_ticket_id:
            current_id = f"{base_ticket_id}-1"
        else:
            current_id = base_ticket_id
            
        max_attempts = 100  # Safety limit for iteration
        attempt = 0
        
        while attempt < max_attempts:
            if not self.check_ticket_exists(current_id):
                print(f"[DATABASE] Generated unique ticket ID: {current_id}")
                return current_id
                
            # Extract the prefix and number
            parts = current_id.rsplit('-', 1)
            prefix = parts[0]
            try:
                number = int(parts[1])
                # Increment the number
                current_id = f"{prefix}-{number + 1}"
            except (IndexError, ValueError):
                # If there's an issue with the format, append "-1"
                current_id = f"{current_id}-1"
                
            attempt += 1
            print(f"[DATABASE] Checking uniqueness of ticket ID: {current_id} (attempt {attempt})")
            
        print(f"[DATABASE] Warning: Reached maximum attempts to generate unique ID. Using {current_id}")
        return current_id

    def save_ticket(self, ticket_data):
        """
        Save a ticket to the database.
        
        Args:
            ticket_data (dict): Ticket data to save
            
        Returns:
            bool: Success status
        """
        # Get the ticket ID or generate a unique one if it's a duplicate
        original_ticket_id = ticket_data.get('ticket_id', 'unknown')
        
        # Ensure we have a unique ticket ID
        unique_ticket_id = self.generate_unique_ticket_id(original_ticket_id)
        
        # Update the ticket data with the unique ID if it changed
        if unique_ticket_id != original_ticket_id:
            print(f"[DATABASE] Updated ticket ID from {original_ticket_id} to {unique_ticket_id} to avoid duplication")
            ticket_data['ticket_id'] = unique_ticket_id
            
        print(f"[DATABASE] Attempting to save ticket {unique_ticket_id}...")
        
        if not self.client:
            print(f"[DATABASE] Client not initialized, cannot save ticket {unique_ticket_id}")
            return False
            
        try:
            # Transform the complex ticket data into a format matching our table schema
            simplified_data = {
                'ticket_id': unique_ticket_id,
                'issue_category': ticket_data.get('summary', '')[:100] if ticket_data.get('summary') else 'Uncategorized',
                'sentiment': 'Neutral',  # Default sentiment
                'priority': self._determine_priority(ticket_data),
                'solution': ', '.join(ticket_data.get('recommendations', []))[:200] if ticket_data.get('recommendations') else 'Pending',
                'resolution_status': 'Open',  # Default status for new tickets
                'date_of_resolution': None  # Will be filled when resolved
            }
            
            print(f"[DATABASE] Formatted ticket data: {simplified_data}")
            
            # No need to check if ticket exists again since we already have a unique ID
            # Insert new ticket
            response = self.client.table(self.table_name).insert(simplified_data).execute()
            print(f"[DATABASE] Ticket {unique_ticket_id} saved successfully to Supabase.")
            return True
                
        except Exception as e:
            error_str = str(e)
            print(f"[DATABASE] Error saving ticket to Supabase: {error_str}")
            return False

    def _determine_priority(self, ticket_data):
        """
        Determine ticket priority based on content.
        
        Args:
            ticket_data (dict): The ticket data
            
        Returns:
            str: Priority level (Critical, High, Medium, Low)
        """
        # Default to Medium priority
        priority = "Medium"
        
        # Check if actions contain any critical keywords
        critical_keywords = ['outage', 'down', 'broken', 'urgent', 'immediately', 'security', 'breach']
        actions = ticket_data.get('actions', [])
        
        if any(keyword in ' '.join(actions).lower() for keyword in critical_keywords):
            priority = "High"
            
        # If routing is to security team, elevate priority
        routing = ticket_data.get('routing', {})
        if routing.get('primary_team') == 'Security Team':
            priority = "Critical"
            
        return priority
    
    def get_ticket(self, ticket_id):
        """
        Retrieve a ticket by ID.
        
        Args:
            ticket_id (str): The ticket ID to retrieve
            
        Returns:
            dict: The ticket data or None if not found
        """
        print(f"[DATABASE] Attempting to retrieve ticket {ticket_id}...")
        if self.client:
            try:
                response = self.client.table(self.table_name).select('*').eq('ticket_id', ticket_id).execute()
                if response.data and len(response.data) > 0:
                    print(f"[DATABASE] Ticket {ticket_id} retrieved successfully.")
                    return response.data[0]
                print(f"[DATABASE] Ticket {ticket_id} not found.")
                return None
            except Exception as e:
                print(f"[DATABASE] Error retrieving ticket from Supabase: {str(e)}")
                return None
        else:
            print(f"[DATABASE] Client not initialized, cannot retrieve ticket {ticket_id}")
            return None
    
    def get_similar_tickets(self, conversation, limit=5):
        """
        Get tickets similar to the current conversation.
        
        Args:
            conversation (str): The current conversation text
            limit (int): Maximum number of similar tickets to return
            
        Returns:
            list: List of similar tickets
        """
        print(f"[DATABASE] Attempting to retrieve up to {limit} similar tickets...")
        if self.client:
            try:
                # For now, just returning random tickets as we don't have full-text search
                # In a production system, this would use embeddings or keyword matching
                response = self.client.table(self.table_name).select('*').limit(limit).execute()
                print(f"[DATABASE] Retrieved {len(response.data)} tickets from {self.table_name}.")
                
                # Format the response to match expected structure in recommendation_agent.py
                formatted_tickets = []
                for ticket in response.data:
                    formatted_tickets.append({
                        'summary': ticket.get('issue_category', 'Unknown issue'),
                        'resolution': ticket.get('solution', 'No solution recorded')
                    })
                
                return formatted_tickets
            except Exception as e:
                print(f"[DATABASE] Error retrieving similar tickets from Supabase: {str(e)}")
                return []
        else:
            print("[DATABASE] Client not initialized, cannot retrieve similar tickets")
            return []
    
    def get_resolution_time_data(self, conversation, limit=10):
        """
        Get historical resolution time data for similar issues.
        
        Args:
            conversation (str): The current conversation text
            limit (int): Maximum number of data points to return
            
        Returns:
            list: List of resolution times in hours
        """
        print(f"[DATABASE] Attempting to retrieve resolution time data for up to {limit} similar issues...")
        if self.client:
            try:
                # In the actual implementation, we'd need to convert date_of_resolution to hours
                # For now, we'll just return some estimated values based on resolution_status
                response = self.client.table(self.table_name).select('*').eq('resolution_status', 'Resolved').limit(limit).execute()
                
                if response.data:
                    print(f"[DATABASE] Retrieved {len(response.data)} resolved tickets for time estimation.")
                    # Convert priority to estimated hours as a simple proxy
                    # In a real system, we would calculate actual resolution times from timestamps
                    resolution_times = []
                    for item in response.data:
                        priority = item.get('priority', 'Medium')
                        # Simple mapping of priority to hours
                        if priority == 'Critical':
                            resolution_times.append(4.0)
                        elif priority == 'High':
                            resolution_times.append(2.5)
                        elif priority == 'Medium':
                            resolution_times.append(1.5)
                        else:  # Low or undefined
                            resolution_times.append(1.0)
                    
                    return resolution_times
                print("[DATABASE] No resolution time data found.")
                return []
            except Exception as e:
                print(f"[DATABASE] Error retrieving resolution time data from Supabase: {str(e)}")
                return []
        else:
            print("[DATABASE] Client not initialized, cannot retrieve resolution time data")
            return []
    
    def update_ticket(self, ticket_id, update_data):
        """
        Update an existing ticket.
        
        Args:
            ticket_id (str): The ticket ID to update
            update_data (dict): The data to update
            
        Returns:
            bool: Success status
        """
        print(f"[DATABASE] Attempting to update ticket {ticket_id}...")
        if self.client:
            try:
                # Ensure update_data matches the table schema
                valid_fields = {
                    'ticket_id', 'issue_category', 'sentiment', 'priority', 
                    'solution', 'resolution_status', 'date_of_resolution'
                }
                
                # Filter out any fields not in our schema
                filtered_data = {k: v for k, v in update_data.items() if k in valid_fields}
                
                response = self.client.table(self.table_name).update(filtered_data).eq('ticket_id', ticket_id).execute()
                print(f"[DATABASE] Ticket {ticket_id} updated successfully.")
                return True
            except Exception as e:
                print(f"[DATABASE] Error updating ticket in Supabase: {str(e)}")
                return False
        else:
            print(f"[DATABASE] Client not initialized, cannot update ticket {ticket_id}")
            return False
    
    def update_ticket_status(self, ticket_id, status):
        """
        Update a ticket's resolution status.
        
        Args:
            ticket_id (str): The ticket ID to update
            status (str): The new status ('Open', 'In Progress', 'Resolved')
            
        Returns:
            bool: Success status
        """
        print(f"[DATABASE] Updating ticket {ticket_id} status to {status}...")
        
        if self.client:
            try:
                update_data = {
                    'resolution_status': status
                }
                
                # If status is 'Resolved', add the current date as date_of_resolution
                if status.lower() == 'resolved':
                    from datetime import datetime
                    update_data['date_of_resolution'] = datetime.now().isoformat()
                
                response = self.client.table(self.table_name).update(update_data).eq('ticket_id', ticket_id).execute()
                print(f"[DATABASE] Ticket {ticket_id} status updated to {status} successfully.")
                return True
            except Exception as e:
                print(f"[DATABASE] Error updating ticket status in Supabase: {str(e)}")
                return False
        else:
            print(f"[DATABASE] Client not initialized, cannot update ticket {ticket_id} status")
            return False

    def get_all_tickets(self):
        """
        Get all tickets from the database.
        
        Returns:
            list: All tickets or empty list if error
        """
        print("[DATABASE] Getting all tickets from database...")
        if self.client:
            try:
                response = self.client.table(self.table_name).select('*').execute()
                print(f"[DATABASE] Retrieved {len(response.data)} tickets")
                
                # Process the data to ensure no None values that might cause issues
                processed_data = []
                for ticket in response.data:
                    processed_ticket = {}
                    for key, value in ticket.items():
                        processed_ticket[key] = value if value is not None else ""
                        
                    processed_data.append(processed_ticket)
                
                return processed_data
            except Exception as e:
                print(f"[DATABASE] Error getting all tickets: {str(e)}")
                # Return sample data in case of error
                return self._generate_sample_tickets(15)
        else:
            print("[DATABASE] Client not initialized, returning sample data")
            return self._generate_sample_tickets(15)

    def get_recent_tickets(self, limit=5):
        """
        Get the most recent tickets.
        
        Args:
            limit (int): Maximum number of tickets to return
            
        Returns:
            list: Recent tickets
        """
        print(f"[DATABASE] Getting {limit} recent tickets...")
        if self.client:
            try:
                response = self.client.table(self.table_name).select('*').order('date_of_resolution', desc=True).limit(limit).execute()
                print(f"[DATABASE] Retrieved {len(response.data)} recent tickets")
                return response.data
            except Exception as e:
                print(f"[DATABASE] Error getting recent tickets: {str(e)}")
                # Return sample data in case of error
                return self._generate_sample_tickets(limit)
        else:
            print("[DATABASE] Client not initialized, returning sample data")
            return self._generate_sample_tickets(limit)
    
    def get_ticket_conversations(self, ticket_id):
        """
        Get conversations for a specific ticket.
        
        Args:
            ticket_id (str): The ticket ID
            
        Returns:
            list: Conversations or None if not found
        """
        print(f"[DATABASE] Getting conversations for ticket {ticket_id}...")
        # In a real implementation, we would query a conversations table
        # For now, return sample conversation
        return [
            {"role": "user", "content": "I can't access my account after the update.", "timestamp": "2025-03-15 10:30:00"},
            {"role": "assistant", "content": "I'm sorry to hear that. Could you tell me what error message you're seeing?", "timestamp": "2025-03-15 10:31:00"},
            {"role": "user", "content": "It says 'Invalid credentials' even though I'm sure my password is correct.", "timestamp": "2025-03-15 10:32:00"},
            {"role": "assistant", "content": "Thank you for that information. Let me check what's happening with the authentication system.", "timestamp": "2025-03-15 10:33:00"}
        ]
        
    def get_ticket_insights(self, ticket_id):
        """
        Get additional insights for a ticket.
        
        Args:
            ticket_id (str): The ticket ID
            
        Returns:
            dict: Ticket insights or empty dict if not found
        """
        print(f"[DATABASE] Getting insights for ticket {ticket_id}...")
        # In a real implementation, we would query an insights table
        return {
            "summary": "User is experiencing login issues after the recent update. Authentication system may need to be checked.",
            "routing": {
                "primary_team": "Authentication Team",
                "additional_teams": ["User Management"]
            }
        }
    
    def get_ticket_activity(self, start_date, end_date):
        """
        Get ticket activity data for a time period.
        
        Args:
            start_date (datetime): Start date
            end_date (datetime): End date
            
        Returns:
            dict: Activity data with labels, new tickets, and resolved tickets
        """
        print(f"[DATABASE] Getting ticket activity from {start_date} to {end_date}...")
        
        if self.client:
            try:
                # In a real implementation, we would query the database for this date range
                # For now, generate sample data
                return self._generate_sample_activity(start_date, end_date)
            except Exception as e:
                print(f"[DATABASE] Error getting ticket activity: {str(e)}")
                return self._generate_sample_activity(start_date, end_date)
        else:
            print("[DATABASE] Client not initialized, returning sample activity data")
            return self._generate_sample_activity(start_date, end_date)
    
    def get_category_data(self):
        """
        Get category distribution data.
        
        Returns:
            dict: Category data with labels and values
        """
        print("[DATABASE] Getting category distribution data...")
        
        if self.client:
            try:
                # In a real implementation, we would calculate this from the database
                # For now, return sample data
                categories = ["Account Access", "Billing Issues", "Technical Support", "Feature Requests", "General Inquiries"]
                resolution_times = [2.5, 1.8, 3.2, 4.0, 0.8]
                
                return {
                    "categories": categories,
                    "resolutionTimes": resolution_times
                }
            except Exception as e:
                print(f"[DATABASE] Error getting category data: {str(e)}")
                return None
        else:
            print("[DATABASE] Client not initialized, returning sample category data")
            categories = ["Account Access", "Billing Issues", "Technical Support", "Feature Requests", "General Inquiries"]
            resolution_times = [2.5, 1.8, 3.2, 4.0, 0.8]
            
            return {
                "categories": categories,
                "resolutionTimes": resolution_times
            }
    
    def get_status_distribution(self):
        """
        Get the distribution of ticket statuses.
        
        Returns:
            dict: Status counts for open, in progress, and resolved
        """
        print("[DATABASE] Getting status distribution...")
        
        if self.client:
            try:
                # In a real implementation, we would query the database
                # For now, return sample data
                return {
                    "openCount": 12,
                    "inProgressCount": 8,
                    "resolvedCount": 25
                }
            except Exception as e:
                print(f"[DATABASE] Error getting status distribution: {str(e)}")
                return None
        else:
            print("[DATABASE] Client not initialized, returning sample status data")
            return {
                "openCount": 12,
                "inProgressCount": 8,
                "resolvedCount": 25
            }
    
    def get_performance_metrics(self):
        """
        Get system performance metrics.
        
        Returns:
            dict: Performance metrics
        """
        print("[DATABASE] Getting performance metrics...")
        
        # This would be calculated from real data in production
        return {
            "avg_resolution_time": "2.3 hrs",
            "avg_resolution_time_delta": "-0.5 hrs",
            "first_response_time": "3.8 min",
            "first_response_time_delta": "-1.2 min",
            "customer_satisfaction": "89%",
            "customer_satisfaction_delta": "+4%"
        }
    
    def get_analytics_metrics(self, start_date, end_date):
        """
        Get analytics metrics for a specific time period.
        
        Args:
            start_date (datetime): Start date
            end_date (datetime): End date
            
        Returns:
            dict: Analytics metrics
        """
        print(f"[DATABASE] Getting analytics metrics from {start_date} to {end_date}...")
        
        # This would be calculated from real data in production
        return {
            "resolutionRate": 85,
            "resolutionDelta": 7,
            "avgResolutionTime": "2.1h",
            "timeDelta": -12,
            "sentiment": "Positive",
            "sentimentDelta": 5
        }
    
    def get_analytics_categories(self, start_date, end_date):
        """
        Get category distribution for analytics.
        
        Args:
            start_date (datetime): Start date
            end_date (datetime): End date
            
        Returns:
            dict: Category names and counts
        """
        print(f"[DATABASE] Getting analytics categories from {start_date} to {end_date}...")
        
        # This would be calculated from real data in production
        categories = ["Account Access", "Billing Issues", "Technical Support", "Feature Requests", "General Inquiries"]
        counts = [28, 15, 32, 8, 12]
        
        return {
            "categories": categories,
            "counts": counts
        }
    
    def get_analytics_resolution_times(self, start_date, end_date):
        """
        Get resolution times by category.
        
        Args:
            start_date (datetime): Start date
            end_date (datetime): End date
            
        Returns:
            dict: Category names and resolution times
        """
        print(f"[DATABASE] Getting resolution times from {start_date} to {end_date}...")
        
        # This would be calculated from real data in production
        categories = ["Account Access", "Billing Issues", "Technical Support", "Feature Requests", "General Inquiries"]
        times = [2.7, 1.5, 3.4, 4.2, 0.9]
        
        return {
            "categories": categories,
            "times": times
        }
    
    def get_analytics_sentiment(self, start_date, end_date):
        """
        Get sentiment distribution.
        
        Args:
            start_date (datetime): Start date
            end_date (datetime): End date
            
        Returns:
            dict: Sentiment labels and counts
        """
        print(f"[DATABASE] Getting sentiment distribution from {start_date} to {end_date}...")
        
        # This would be calculated from real data in production
        return {
            "labels": ["Positive", "Neutral", "Negative"],
            "counts": [42, 30, 18]
        }
    
    def get_analytics_trend(self, start_date, end_date):
        """
        Get ticket creation and resolution trend.
        
        Args:
            start_date (datetime): Start date
            end_date (datetime): End date
            
        Returns:
            dict: Trend data
        """
        print(f"[DATABASE] Getting ticket trend from {start_date} to {end_date}...")
        
        # Generate sample data for the specified date range
        from datetime import datetime, timedelta
        
        days = (end_date - start_date).days
        labels = []
        created = []
        resolved = []
        
        for i in range(days):
            day = start_date + timedelta(days=i)
            labels.append(day.strftime("%d %b"))
            
            # Generate realistic looking data
            import random
            created_count = random.randint(3, 15)
            resolved_count = random.randint(2, created_count)
            
            created.append(created_count)
            resolved.append(resolved_count)
        
        return {
            "labels": labels,
            "created": created,
            "resolved": resolved
        }
    
    def get_analytics_priority(self, start_date, end_date):
        """
        Get priority distribution.
        
        Args:
            start_date (datetime): Start date
            end_date (datetime): End date
            
        Returns:
            dict: Priority labels and counts
        """
        print(f"[DATABASE] Getting priority distribution from {start_date} to {end_date}...")
        
        # This would be calculated from real data in production
        return {
            "labels": ["Critical", "High", "Medium", "Low"],
            "counts": [8, 22, 45, 15]
        }

    def _generate_sample_tickets(self, count):
        """
        Generate sample ticket data for testing.
        
        Args:
            count (int): Number of sample tickets to generate
            
        Returns:
            list: Sample tickets
        """
        sample_tickets = []
        
        # Issue categories
        categories = [
            "Account Access", "Login Problems", "Password Reset", 
            "Billing Issue", "Subscription", "Payment Failed", 
            "Software Bug", "Feature Request", "Performance Issue",
            "Installation Problem", "Update Issue", "Compatibility Problem"
        ]
        
        # Status options
        statuses = ["Open", "In Progress", "Resolved"]
        
        # Priority options
        priorities = ["Low", "Medium", "High", "Critical"]
        
        # Sentiment options
        sentiments = ["Positive", "Neutral", "Negative"]
        
        from datetime import datetime, timedelta
        import random
        
        for i in range(count):
            # Generate a random ticket ID
            ticket_id = f"TICKET-{10000 + i}"
            
            # Random category
            category = random.choice(categories)
            
            # Random status
            status = random.choice(statuses)
            
            # Random priority
            priority = random.choice(priorities)
            
            # Random sentiment
            sentiment = random.choice(sentiments)
            
            # Random date of resolution (if resolved)
            date_of_resolution = None
            if status == "Resolved":
                days_ago = random.randint(0, 30)
                date_of_resolution = (datetime.now() - timedelta(days=days_ago)).isoformat()
            
            # Create ticket
            ticket = {
                "ticket_id": ticket_id,
                "issue_category": category,
                "sentiment": sentiment,
                "priority": priority,
                "resolution_status": status,
                "date_of_resolution": date_of_resolution
            }
            
            sample_tickets.append(ticket)
        
        return sample_tickets

    def _generate_sample_activity(self, start_date, end_date):
        """
        Generate sample activity data.
        
        Args:
            start_date (datetime): Start date
            end_date (datetime): End date
            
        Returns:
            dict: Sample activity data
        """
        from datetime import datetime, timedelta
        import random
        
        days = (end_date - start_date).days + 1
        labels = []
        new_tickets = []
        resolved_tickets = []
        
        for i in range(days):
            day = start_date + timedelta(days=i)
            labels.append(day.strftime("%d %b"))
            
            # Generate random but realistic data
            new_count = random.randint(3, 15)
            resolved_count = random.randint(2, new_count)
            
            new_tickets.append(new_count)
            resolved_tickets.append(resolved_count)
        
        return {
            "labels": labels,
            "newTickets": new_tickets,
            "resolvedTickets": resolved_tickets
        }
