import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
import time
import json
import pandas as pd
import uvicorn
import csv
from fastapi.responses import RedirectResponse
from agents.summary_agent import SummaryAgent
from agents.action_agent import ActionAgent
from agents.recommendation_agent import RecommendationAgent
from agents.routing_agent import RoutingAgent
from agents.time_agent import TimeEstimationAgent
from agents.intent_classifier_agent import IntentClassifierAgent
from database.supabase_client import SupabaseClient
from utils.conversation_utils import format_conversation_history

# Create FastAPI app
app = FastAPI(title="AI-Driven Customer Support System")

# Initialize Supabase client
print("Initializing Supabase client...")
supabase_client = SupabaseClient()
print("Supabase client initialized.")

# Initialize agents
print("Initializing agents...")
summary_agent = SummaryAgent()
action_agent = ActionAgent()
recommendation_agent = RecommendationAgent()
routing_agent = RoutingAgent()
time_agent = TimeEstimationAgent()
intent_classifier = IntentClassifierAgent()
print("All agents initialized successfully.")

# Create a templates directory for HTML templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)

# Create a static directory for static assets (CSS, JS, images)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Mount static files directory
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory=templates_dir)

# In-memory session storage - in production, use Redis or another persistence layer
active_sessions = {}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

manager = ConnectionManager()

def get_or_create_session(session_id):
    """Get or create a new user session"""
    if session_id not in active_sessions:
        # Generate a base ticket ID
        base_ticket_id = f"TICKET-{int(time.time())}"
        # Make sure it's unique in the database
        ticket_id = supabase_client.generate_unique_ticket_id(base_ticket_id)
        print(f"[APP] Generated unique ticket ID: {ticket_id}")

        active_sessions[session_id] = {
            "ticket_id": ticket_id,
            "conversation_history": [],
            "current_summary": "",
            "actions": [],
            "recommendations": [],
            "routing": {},
            "time_estimate": ""
        }
    return active_sessions[session_id]

@app.get("/", response_class=HTMLResponse)
async def get_home_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/user", response_class=HTMLResponse)
async def get_user_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/screen-sharing", response_class=RedirectResponse)
async def get_screen_sharing_page():
    """Redirect to screen sharing page on localhost:7000"""
    return RedirectResponse(url="http://localhost:7000")

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def get_admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "active_page": "dashboard"})

@app.get("/admin/tickets", response_class=HTMLResponse)
async def get_admin_tickets(request: Request):
    return templates.TemplateResponse("admin_tickets.html", {"request": request, "active_page": "tickets"})

@app.get("/admin/tickets/{ticket_id}", response_class=HTMLResponse)
async def get_ticket_detail(request: Request, ticket_id: str):
    return templates.TemplateResponse("admin_ticket_detail.html", {"request": request, "active_page": "tickets", "ticket_id": ticket_id})

@app.get("/admin/analytics", response_class=HTMLResponse)
async def get_admin_analytics(request: Request):
    return templates.TemplateResponse("admin_analytics.html", {"request": request, "active_page": "analytics"})

# Admin API Endpoints
@app.get("/api/admin/metrics")
async def get_admin_metrics():
    """Get dashboard metrics data"""
    try:
        # Query tickets data directly from database
        tickets_data = supabase_client.get_all_tickets()
        
        if not tickets_data:
            print("No ticket data found in database")
            return {
                "totalTickets": 0,
                "ticketsDelta": 0,
                "resolutionRate": 0,
                "resolutionDelta": 0,
                "avgResolutionTime": "0h",
                "timeDelta": 0,
                "criticalIssues": 0,
                "criticalDelta": 0
            }
            
        # Calculate metrics
        total_tickets = len(tickets_data)
        resolved_tickets = sum(1 for ticket in tickets_data if ticket.get('resolution_status') == 'Resolved')
        resolution_rate = int((resolved_tickets / total_tickets * 100)) if total_tickets > 0 else 0
        
        # Calculate average resolution time
        avg_resolution_time = "2.4h"  # Default value
        
        # Count critical issues
        critical_issues = sum(1 for ticket in tickets_data if ticket.get('priority') == 'Critical')
        
        return {
            "totalTickets": total_tickets,
            "ticketsDelta": 8,  # Sample data
            "resolutionRate": resolution_rate,
            "resolutionDelta": 5,  # Sample data
            "avgResolutionTime": avg_resolution_time,
            "timeDelta": -15,  # Sample improvement (negative is good)
            "criticalIssues": critical_issues,
            "criticalDelta": -2  # Sample improvement
        }
    except Exception as e:
        print(f"Error getting admin metrics: {e}")
        return {"error": str(e)}

@app.get("/api/admin/tickets")
async def get_all_tickets():
    """Get all tickets"""
    try:
        # Query tickets directly from database
        tickets = supabase_client.get_all_tickets()
        
        # Format the data
        formatted_tickets = []
        for ticket in tickets:
            formatted_tickets.append({
                "ticket_id": ticket.get("ticket_id", "") if ticket.get("ticket_id") is not None else "",
                "issue_category": ticket.get("issue_category", "") if ticket.get("issue_category") is not None else "",
                "sentiment": ticket.get("sentiment", "") if ticket.get("sentiment") is not None else "",
                "priority": ticket.get("priority", "") if ticket.get("priority") is not None else "",
                "resolution_status": ticket.get("resolution_status", "") if ticket.get("resolution_status") is not None else "",
                "date_of_resolution": ticket.get("date_of_resolution", "") if ticket.get("date_of_resolution") is not None else ""
            })
            
        return formatted_tickets
    except Exception as e:
        print(f"Error getting all tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/tickets/recent")
async def get_recent_tickets(limit: int = 5):
    """Get recent tickets"""
    try:
        # Get recent tickets directly from database
        tickets = supabase_client.get_recent_tickets(limit)
        return tickets
    except Exception as e:
        print(f"Error getting recent tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/tickets/{ticket_id}")
async def get_ticket_details(ticket_id: str):
    """Get details of a specific ticket"""
    try:
        # Get ticket details directly from database
        ticket = supabase_client.get_ticket(ticket_id)
        
        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        
        # Enhance with conversation data if available in database
        ticket_conversations = supabase_client.get_ticket_conversations(ticket_id)
        if ticket_conversations:
            ticket["conversation"] = ticket_conversations
        else:
            # Fallback mock conversation data
            ticket["conversation"] = [
                {"role": "user", "content": "I'm having trouble installing your software.", "timestamp": "2025-03-15 10:30:00"},
                {"role": "assistant", "content": "I'm sorry to hear that. Could you tell me what error you're encountering?", "timestamp": "2025-03-15 10:31:00"},
                {"role": "user", "content": "It says 'Installation failed due to antivirus blocking the process'", "timestamp": "2025-03-15 10:32:00"},
                {"role": "assistant", "content": "I understand. This is a common issue. Let me help you resolve this.", "timestamp": "2025-03-15 10:33:00"}
            ]
        
        # Get agent insights from database if available
        insights = supabase_client.get_ticket_insights(ticket_id)
        if insights:
            ticket.update(insights)
        else:
            # Fallback mock insights
            ticket["summary"] = f"Customer is having trouble installing the software. Their antivirus is blocking the installation process."
            ticket["solution"] = ticket.get("solution", "No solution recorded")
            ticket["routing"] = {
                "primary_team": "Technical Support",
                "additional_teams": ["Software Development"]
            }
        
        return ticket
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error getting ticket details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/admin/tickets/{ticket_id}/status")
async def update_ticket_status(ticket_id: str, data: dict):
    """Update a ticket's status"""
    try:
        status = data.get("status")
        if not status:
            raise HTTPException(status_code=400, detail="Status is required")
            
        # Update status in database
        success = supabase_client.update_ticket_status(ticket_id, status)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update ticket status")
        
        return {"success": True, "message": f"Ticket {ticket_id} status updated to {status}"}
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error updating ticket status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/charts/activity")
async def get_ticket_activity(period: str = "month"):
    """Get ticket activity data for the chart"""
    try:
        # Determine time period to query
        from datetime import datetime, timedelta
        end_date = datetime.now()
        
        if period == "week":
            start_date = end_date - timedelta(days=7)
            label_format = "%a"  # Day of week abbreviation
            days = 7
        elif period == "month":
            start_date = end_date - timedelta(days=30)
            label_format = "%d %b"  # Day and month abbreviation
            days = 30
        elif period == "quarter":
            start_date = end_date - timedelta(days=90)
            label_format = "%b"  # Month abbreviation
            days = 90
        else:
            start_date = end_date - timedelta(days=30)
            label_format = "%d %b"
            days = 30
        
        # Get activity data from database
        activity_data = supabase_client.get_ticket_activity(start_date, end_date)
        
        if not activity_data:
            # Generate sample data if no data is available
            labels = []
            new_tickets = []
            resolved_tickets = []
            
            for i in range(days, 0, -1):
                date = end_date - timedelta(days=i)
                labels.append(date.strftime(label_format))
                
                # Generate some random data for demonstration
                import random
                new_count = random.randint(3, 15)
                resolved_count = random.randint(2, new_count)
                
                new_tickets.append(new_count)
                resolved_tickets.append(resolved_count)
            
            return {
                "labels": labels,
                "newTickets": new_tickets,
                "resolvedTickets": resolved_tickets
            }
        
        return activity_data
    except Exception as e:
        print(f"Error getting ticket activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/charts/categories")
async def get_category_data():
    """Get data for the categories chart"""
    try:
        # Get category data from database
        category_data = supabase_client.get_category_data()
        
        if not category_data:
            # Query all tickets to calculate categories
            all_tickets = await get_all_tickets()
            
            # Extract unique categories
            categories = list(set(ticket.get("issue_category", "Uncategorized").strip() for ticket in all_tickets))
            
            # Calculate resolution times by category (mocked data)
            resolution_times = []
            for category in categories:
                # In a real implementation, calculate actual resolution times
                import random
                resolution_times.append(round(random.uniform(0.5, 4.5), 1))
                
            return {
                "categories": categories,
                "resolutionTimes": resolution_times
            }
        
        return category_data
    except Exception as e:
        print(f"Error getting category data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/charts/status")
async def get_status_distribution():
    """Get data for the status distribution chart"""
    try:
        # Get status distribution from database
        status_data = supabase_client.get_status_distribution()
        
        if not status_data:
            # Query all tickets to calculate status distribution
            all_tickets = await get_all_tickets()
            
            # Count tickets by status
            open_count = sum(1 for ticket in all_tickets if ticket.get("resolution_status", "").strip() == "Open")
            in_progress_count = sum(1 for ticket in all_tickets if ticket.get("resolution_status", "").strip() == "In Progress")
            resolved_count = sum(1 for ticket in all_tickets if ticket.get("resolution_status", "").strip() == "Resolved")
            
            return {
                "openCount": open_count,
                "inProgressCount": in_progress_count,
                "resolvedCount": resolved_count
            }
        
        return status_data
    except Exception as e:
        print(f"Error getting status distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics API endpoints
@app.get("/api/admin/analytics/metrics")
async def get_analytics_metrics(days: int = 30):
    """Get analytics metrics for the specified time period"""
    try:
        # Get analytics metrics from database
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        metrics_data = supabase_client.get_analytics_metrics(start_date, end_date)
        
        if not metrics_data:
            # Provide fallback sample data
            return {
                "resolutionRate": 85,
                "resolutionDelta": 7,
                "avgResolutionTime": "2.1h",
                "timeDelta": -12,  # Negative means improvement
                "sentiment": "Positive",
                "sentimentDelta": 5
            }
        
        return metrics_data
    except Exception as e:
        print(f"Error getting analytics metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/analytics/categories")
async def get_analytics_categories(days: int = 30):
    """Get category distribution for the analytics page"""
    try:
        # Get category distribution from database
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        category_data = supabase_client.get_analytics_categories(start_date, end_date)
        
        if not category_data:
            # Calculate from all tickets
            all_tickets = await get_all_tickets()
            
            # Extract categories and count tickets in each
            category_counts = {}
            for ticket in all_tickets:
                category = ticket.get("issue_category", "Uncategorized").strip()
                if category not in category_counts:
                    category_counts[category] = 0
                category_counts[category] += 1
                
            categories = list(category_counts.keys())
            counts = [category_counts[cat] for cat in categories]
            
            return {
                "categories": categories,
                "counts": counts
            }
        
        return category_data
    except Exception as e:
        print(f"Error getting analytics categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/analytics/resolution-times")
async def get_analytics_resolution_times(days: int = 30):
    """Get resolution times by category"""
    try:
        # Get resolution times from database
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        resolution_data = supabase_client.get_analytics_resolution_times(start_date, end_date)
        
        if not resolution_data:
            # Fallback to calculated data
            category_data = await get_category_data()
            
            # Use the same categories, but generate slightly different data
            import random
            times = [round(t + random.uniform(-0.5, 0.5), 1) for t in category_data["resolutionTimes"]]
            
            return {
                "categories": category_data["categories"],
                "times": times
            }
        
        return resolution_data
    except Exception as e:
        print(f"Error getting resolution times: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/analytics/sentiment")
async def get_analytics_sentiment(days: int = 30):
    """Get sentiment distribution"""
    try:
        # Get sentiment distribution from database
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        sentiment_data = supabase_client.get_analytics_sentiment(start_date, end_date)
        
        if not sentiment_data:
            # Calculate from all tickets
            all_tickets = await get_all_tickets()
            
            # Count tickets by sentiment
            sentiment_counts = {}
            for ticket in all_tickets:
                sentiment = ticket.get("sentiment", "Neutral").strip()
                if sentiment not in sentiment_counts:
                    sentiment_counts[sentiment] = 0
                sentiment_counts[sentiment] += 1
                
            # Ensure we have all three standard sentiments
            standard_sentiments = ["Positive", "Neutral", "Negative"]
            for sentiment in standard_sentiments:
                if sentiment not in sentiment_counts:
                    sentiment_counts[sentiment] = 0
            
            return {
                "labels": list(sentiment_counts.keys()),
                "counts": list(sentiment_counts.values())
            }
        
        return sentiment_data
    except Exception as e:
        print(f"Error getting sentiment distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/analytics/trend")
async def get_analytics_trend(days: int = 30):
    """Get ticket creation and resolution trend"""
    try:
        # Get trend data from database
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        trend_data = supabase_client.get_analytics_trend(start_date, end_date)
        
        if not trend_data:
            # Generate sample trend data
            labels = []
            created_data = []
            resolved_data = []
            
            for i in range(days):
                date = datetime.now() - timedelta(days=(days-i-1))
                labels.append(date.strftime("%d %b"))
                
                # Generate some random data for demonstration
                import random
                created = random.randint(3, 15)
                resolved = random.randint(2, created)
                
                created_data.append(created)
                resolved_data.append(resolved)
                
            return {
                "labels": labels,
                "created": created_data,
                "resolved": resolved_data
            }
        
        return trend_data
    except Exception as e:
        print(f"Error getting trend data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/analytics/priority")
async def get_analytics_priority(days: int = 30):
    """Get priority distribution"""
    try:
        # Get priority distribution from database
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        priority_data = supabase_client.get_analytics_priority(start_date, end_date)
        
        if not priority_data:
            # Calculate from all tickets
            all_tickets = await get_all_tickets()
            
            # Count tickets by priority
            priority_counts = {}
            for ticket in all_tickets:
                priority = ticket.get("priority", "Medium").strip()
                if priority not in priority_counts:
                    priority_counts[priority] = 0
                priority_counts[priority] += 1
                
            # Ensure we have all standard priorities
            standard_priorities = ["Critical", "High", "Medium", "Low"]
            for priority in standard_priorities:
                if priority not in priority_counts:
                    priority_counts[priority] = 0
            
            return {
                "labels": list(priority_counts.keys()),
                "counts": list(priority_counts.values())
            }
        
        return priority_data
    except Exception as e:
        print(f"Error getting priority distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    session = get_or_create_session(client_id)
    await manager.connect(websocket, client_id)
    
    try:
        # Send initial state to the client
        await manager.send_message(client_id, {
            "type": "init",
            "data": {
                "ticket_id": session["ticket_id"],
                "conversation_history": session["conversation_history"],
                "current_summary": session["current_summary"],
                "actions": session["actions"],
                "recommendations": session["recommendations"],
                "routing": session["routing"],
                "time_estimate": session["time_estimate"]
            }
        })
        
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "message":
                user_input = data["content"]
                # Add user message to conversation history
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[WORKFLOW] Received user input at {timestamp}")
                
                session["conversation_history"].append({
                    "role": "user",
                    "content": user_input,
                    "timestamp": timestamp
                })
                
                # Send acknowledgment that message was received
                await manager.send_message(client_id, {
                    "type": "message_received",
                    "timestamp": timestamp
                })
                
                # Classify user intent before processing
                print("[WORKFLOW] Classifying user intent")
                classification = intent_classifier.classify_intent(user_input)
                intent_type = classification.get("intent", "unknown")
                confidence = classification.get("confidence", 0.0)
                
                print(f"[WORKFLOW] Classified intent: {intent_type}, Confidence: {confidence}")
                
                # Format conversation for agents
                formatted_conversation = format_conversation_history(session["conversation_history"])
                
                # Generate response based on intent classification
                if intent_type == "greeting" and confidence > 0.6:
                    # Simple greeting - no need for agent pipeline
                    print("[WORKFLOW] Handling as simple greeting")
                    # Send typing indicator
                    await manager.send_message(client_id, {"type": "typing_indicator", "isTyping": True})
                    response = intent_classifier.generate_casual_response(
                        user_input, 
                        session["conversation_history"]
                    )
                    # Stop typing indicator
                    await manager.send_message(client_id, {"type": "typing_indicator", "isTyping": False})
                
                elif intent_type == "farewell" and confidence > 0.6:
                    # Simple farewell - no need for agent pipeline
                    print("[WORKFLOW] Handling as farewell")
                    # Send typing indicator
                    await manager.send_message(client_id, {"type": "typing_indicator", "isTyping": True})
                    response = intent_classifier.generate_casual_response(
                        user_input, 
                        session["conversation_history"]
                    )
                    # Stop typing indicator
                    await manager.send_message(client_id, {"type": "typing_indicator", "isTyping": False})
                
                elif intent_type == "casual" or (intent_type == "issue" and confidence < 0.8):
                    # Casual conversation or vague mention of a problem - don't activate full pipeline
                    print("[WORKFLOW] Handling as casual conversation or vague problem mention")
                    # Send typing indicator
                    await manager.send_message(client_id, {"type": "typing_indicator", "isTyping": True})
                    response = intent_classifier.generate_probing_response(
                        user_input,
                        session["conversation_history"]
                    )
                    # Stop typing indicator
                    await manager.send_message(client_id, {"type": "typing_indicator", "isTyping": False})
                
                elif intent_type == "issue" and confidence >= 0.7:
                    # Specific support issue - activate full agent pipeline
                    print("[WORKFLOW] Processing specific support issue with full agent pipeline")
                    # Send typing indicator
                    await manager.send_message(client_id, {"type": "typing_indicator", "isTyping": True})
                    
                    try:
                        # Activate all agents in parallel
                        print("[WORKFLOW] Starting agent processing sequence")
                        
                        # Summary Generation
                        print("[WORKFLOW] Calling Summary Agent")
                        summary = summary_agent.generate_summary(formatted_conversation)
                        session["current_summary"] = summary
                        print(f"[WORKFLOW] Summary generated: {summary[:50]}...")
                        await manager.send_message(client_id, {
                            "type": "update_summary",
                            "data": summary
                        })
                        
                        # Action Extraction
                        print("[WORKFLOW] Calling Action Agent")
                        actions = action_agent.extract_actions(formatted_conversation, summary)
                        session["actions"] = actions
                        print(f"[WORKFLOW] Actions extracted: {len(actions)} actions found")
                        await manager.send_message(client_id, {
                            "type": "update_actions",
                            "data": actions
                        })
                        
                        # Resolution Recommendation
                        print("[WORKFLOW] Calling Recommendation Agent")
                        try:
                            # Ensure summary is a string and not None
                            summary_text = summary if summary and isinstance(summary, str) else "No summary available"
                            recommendations = recommendation_agent.generate_recommendations(
                                formatted_conversation, 
                                summary_text, 
                                actions if actions else []
                            )
                            session["recommendations"] = recommendations
                            print(f"[WORKFLOW] Recommendations generated: {len(recommendations)} recommendations found")
                            await manager.send_message(client_id, {
                                "type": "update_recommendations",
                                "data": recommendations
                            })
                        except Exception as rec_error:
                            print(f"[WORKFLOW] ERROR in Recommendation Agent: {str(rec_error)}")
                            session["recommendations"] = ["Unable to generate recommendations at this time."]
                            await manager.send_message(client_id, {
                                "type": "update_recommendations",
                                "data": session["recommendations"]
                            })
                        
                        # Task Routing
                        print("[WORKFLOW] Calling Routing Agent")
                        routing = routing_agent.determine_routing(formatted_conversation, actions)
                        session["routing"] = routing
                        print(f"[WORKFLOW] Routing determined: Primary team - {routing.get('primary_team', 'None')}")
                        await manager.send_message(client_id, {
                            "type": "update_routing",
                            "data": routing
                        })
                        
                        # Time Estimation
                        print("[WORKFLOW] Calling Time Estimation Agent")
                        try:
                            time_estimate = time_agent.estimate_resolution_time(formatted_conversation, actions, routing)
                            session["time_estimate"] = time_estimate
                            print(f"[WORKFLOW] Time estimated: {time_estimate[:50] if time_estimate else 'None'}...")
                            await manager.send_message(client_id, {
                                "type": "update_time_estimate",
                                "data": time_estimate
                            })
                        except Exception as time_error:
                            print(f"[WORKFLOW] ERROR in Time Estimation Agent: {str(time_error)}")
                            session["time_estimate"] = "Unable to estimate resolution time at this moment."
                            await manager.send_message(client_id, {
                                "type": "update_time_estimate",
                                "data": session["time_estimate"]
                            })
                        
                        # Generate response based on agent outputs
                        print("[WORKFLOW] Generating response to user")
                        try:
                            # Create a more detailed response using the available information
                            response_parts = ["Thank you for your message."]
                            
                            # Add recommendations with proper formatting
                            if session['recommendations'] and len(session['recommendations']) > 0:
                                # Include the first recommendation
                                first_rec = session['recommendations'][0]
                                response_parts.append(f"I recommend you: {first_rec}")
                                
                                # Add second recommendation if available
                                if len(session['recommendations']) > 1:
                                    response_parts.append(f"Additionally, you could try: {session['recommendations'][1]}")
                            else:
                                response_parts.append("I'll look into this for you and provide a solution shortly.")
                            
                            # Add time estimate if available
                            if session['time_estimate'] and "Estimated Resolution Time:" in session['time_estimate']:
                                time_line = next((line for line in session['time_estimate'].split('\n') if "Estimated Resolution Time:" in line), None)
                                if time_line:
                                    estimated_time = time_line.split("Estimated Resolution Time:")[1].strip()
                                    response_parts.append(f"I expect this will take approximately {estimated_time} to resolve.")
                            
                            # Combine parts with proper spacing
                            response = " ".join(response_parts)
                            print(f"[WORKFLOW] Response generated: {response}")
                        except Exception as resp_error:
                            print(f"[WORKFLOW] Error generating response: {str(resp_error)}")
                            response = "Thank you for providing those details. I'll analyze your issue and work on a solution for you."

                        # Stop typing indicator
                        await manager.send_message(client_id, {"type": "typing_indicator", "isTyping": False})
                        
                        # Save to database
                        try:
                            print("[WORKFLOW] Saving ticket to database")
                            ticket_data = {
                                "ticket_id": session["ticket_id"],
                                "conversation": session["conversation_history"],
                                "summary": summary,
                                "actions": actions,
                                "recommendations": session["recommendations"],
                                "routing": routing,
                                "time_estimate": session["time_estimate"],
                                "timestamp": timestamp
                            }
                            save_success = supabase_client.save_ticket(ticket_data)
                            if save_success:
                                print(f"[WORKFLOW] Ticket saved successfully: {session['ticket_id']}")
                            else:
                                print(f"[WORKFLOW] Failed to save ticket: {session['ticket_id']}")
                        except Exception as db_error:
                            print(f"[WORKFLOW] ERROR: Database save failed: {str(db_error)}")
                    except Exception as agent_error:
                        print(f"[WORKFLOW] ERROR: Agent processing failed: {str(agent_error)}")
                        response = "I apologize, but I encountered an error processing your request. Please try again or contact our technical support team."
                else:
                    # Handle uncertain or low confidence classifications with a probing response
                    print(f"[WORKFLOW] Uncertain intent classification ({intent_type}, confidence: {confidence})")
                    # Send typing indicator
                    await manager.send_message(client_id, {"type": "typing_indicator", "isTyping": True})
                    response = intent_classifier.generate_probing_response(
                        user_input,
                        session["conversation_history"]
                    )
                    # Stop typing indicator
                    await manager.send_message(client_id, {"type": "typing_indicator", "isTyping": False})
                
                # Add assistant response to conversation history
                print("[WORKFLOW] Adding assistant response to conversation history")
                response_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                session["conversation_history"].append({            
                    "role": "assistant",
                    "content": response,
                    "timestamp": response_timestamp
                })
                
                # Send the response back to the client
                await manager.send_message(client_id, {
                    "type": "message",
                    "role": "assistant",
                    "content": response,
                    "timestamp": response_timestamp
                })
            
            elif data["type"] == "update_status":
                new_status = data["status"]
                with_db = data.get("with_db", False)
                
                if with_db:
                    success = supabase_client.update_ticket_status(session["ticket_id"], new_status)
                    await manager.send_message(client_id, {
                        "type": "status_update_result",
                        "success": success,
                        "status": new_status
                    })
                else:
                    # Just update the UI without database update
                    await manager.send_message(client_id, {
                        "type": "status_update_result",
                        "success": True,
                        "status": new_status
                    })
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        print(f"[WEBSOCKET] Client #{client_id} disconnected")
    except Exception as e:
        print(f"[WEBSOCKET] Error: {str(e)}")
        manager.disconnect(client_id)

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get session data for a given session ID"""
    session = get_or_create_session(session_id)
    return {
        "ticket_id": session["ticket_id"],
        "conversation_history": session["conversation_history"],
        "current_summary": session["current_summary"],
        "actions": session["actions"],
        "recommendations": session["recommendations"],
        "routing": session["routing"],
        "time_estimate": session["time_estimate"]
    }

@app.get("/api/metrics")
async def get_metrics():
    """Get performance metrics data"""
    try:
        # Get metrics from database
        metrics_data = supabase_client.get_performance_metrics()
        
        if not metrics_data:
            # Fallback to sample data
            return {
                "avg_resolution_time": "1.8 hrs",
                "avg_resolution_time_delta": "-0.3 hrs",
                "first_response_time": "4.2 min",
                "first_response_time_delta": "-1.5 min",
                "customer_satisfaction": "92%",
                "customer_satisfaction_delta": "+3%",
                "db_status": "Connected" if supabase_client._initialized and supabase_client.client else "Disconnected"
            }
            
        # Ensure database status is included
        metrics_data["db_status"] = "Connected" if supabase_client._initialized and supabase_client.client else "Disconnected"
        return metrics_data
    except Exception as e:
        print(f"Error getting metrics: {e}")
        return {
            "error": str(e),
            "db_status": "Connected" if supabase_client._initialized and supabase_client.client else "Disconnected"
        }

@app.get("/api/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy", 
        "database": "connected" if supabase_client._initialized and supabase_client.client else "disconnected"
    }

# Run the FastAPI app when executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
