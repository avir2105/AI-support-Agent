def format_conversation_history(conversation_history):
    """
    Format the conversation history for agent consumption.
    
    Args:
        conversation_history (list): List of conversation messages
        
    Returns:
        str: Formatted conversation string
    """
    print(f"[UTILS] Formatting conversation history with {len(conversation_history)} messages")
    formatted_conversation = ""
    
    for message in conversation_history:
        role = message.get("role", "unknown")
        content = message.get("content", "")
        timestamp = message.get("timestamp", "")
        
        if role == "user":
            formatted_conversation += f"Customer [{timestamp}]: {content}\n\n"
        elif role == "assistant":
            formatted_conversation += f"Support Agent [{timestamp}]: {content}\n\n"
    
    print(f"[UTILS] Formatted conversation is {len(formatted_conversation)} characters long")
    return formatted_conversation

def extract_key_points(conversation_text):
    """
    Extract key points from a conversation text.
    
    Args:
        conversation_text (str): The full conversation text
        
    Returns:
        list: List of key points
    """
    # Split into sentences
    sentences = [s.strip() for s in conversation_text.split('.') if s.strip()]
    
    # Enhanced heuristics to identify important sentences
    importance_keywords = [
        "need", "issue", "problem", "error", "can't", "cannot", "doesn't", 
        "failed", "help", "support", "urgent", "critical", "important", 
        "broken", "bug", "feature", "request", "want", "would like",
        "login", "account", "password", "reset", "access", "payment",
        "billing", "subscription", "cancel", "refund", "money", "charge",
        "upgrade", "downgrade", "plan", "service", "question"
    ]
    
    key_points = []
    for sentence in sentences:
        # Check if the sentence contains any importance keywords or ends with a question mark
        if any(keyword in sentence.lower() for keyword in importance_keywords) or sentence.strip().endswith('?'):
            key_points.append(sentence.strip() + ".")
    
    return key_points

def calculate_sentiment(conversation_text):
    """
    Calculate the sentiment of a conversation (positive, negative, neutral).
    
    Args:
        conversation_text (str): The full conversation text
        
    Returns:
        str: Sentiment category
        float: Sentiment score (-1 to 1)
    """
    print(f"[UTILS] Calculating sentiment for text of length {len(conversation_text)}")
    # This is a simplified sentiment analysis based on keyword counting
    # A real implementation would use a proper sentiment analysis model
    
    positive_words = [
        "thanks", "thank you", "appreciate", "good", "great", "excellent", 
        "awesome", "wonderful", "happy", "pleased", "satisfied", "love", 
        "like", "helpful", "resolved", "solution", "fixed"
    ]
    
    negative_words = [
        "bad", "terrible", "awful", "disappointed", "frustrating", "annoying", 
        "angry", "upset", "issue", "problem", "error", "bug", "broken", "can't", 
        "cannot", "doesn't", "failed", "wrong", "unhappy", "useless"
    ]
    
    # Count occurrences
    text_lower = conversation_text.lower()
    
    positive_count = sum(text_lower.count(word) for word in positive_words)
    negative_count = sum(text_lower.count(word) for word in negative_words)
    
    total_count = positive_count + negative_count
    if total_count == 0:
        print("[UTILS] No sentiment keywords found, returning neutral")
        return "neutral", 0.0
    
    sentiment_score = (positive_count - negative_count) / max(total_count, 1)
    
    if sentiment_score > 0.2:
        sentiment = "positive"
    elif sentiment_score < -0.2:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    print(f"[UTILS] Sentiment calculated: {sentiment} ({sentiment_score:.2f})")
    return sentiment, sentiment_score

def get_conversation_metadata(conversation_history):
    """
    Extract metadata from a conversation.
    
    Args:
        conversation_history (list): List of message dictionaries
        
    Returns:
        dict: Conversation metadata
    """
    if not conversation_history:
        return {}
    
    # Format the conversation text
    conversation_text = format_conversation_history(conversation_history)
    
    # Extract key points
    key_points = extract_key_points(conversation_text)
    
    # Calculate sentiment
    sentiment, sentiment_score = calculate_sentiment(conversation_text)
    
    # Count messages
    customer_messages = sum(1 for msg in conversation_history if msg.get("role") == "user")
    agent_messages = sum(1 for msg in conversation_history if msg.get("role") == "assistant")
    
    # Calculate conversation duration
    duration_minutes = None
    if len(conversation_history) >= 2:
        start_time = conversation_history[0].get("timestamp")
        end_time = conversation_history[-1].get("timestamp")
        
        if start_time and end_time:
            try:
                from datetime import datetime
                start = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                end = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                duration_minutes = (end - start).total_seconds() / 60
            except Exception as e:
                print(f"[UTILS] Error calculating duration: {e}")
                duration_minutes = None
    
    return {
        "message_count": len(conversation_history),
        "customer_message_count": customer_messages,
        "agent_message_count": agent_messages,
        "key_points": key_points,
        "sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "duration_minutes": duration_minutes
    }

def validate_ticket_data(ticket_data):
    """
    Validate ticket data before saving to database.
    
    Args:
        ticket_data (dict): Ticket data to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    required_fields = ['ticket_id']
    
    # Check required fields
    for field in required_fields:
        if field not in ticket_data or not ticket_data[field]:
            return False, f"Missing required field: {field}"
    
    # Validate data types
    if not isinstance(ticket_data.get('conversation', []), list):
        return False, "Conversation must be a list"
    
    if not isinstance(ticket_data.get('actions', []), list):
        return False, "Actions must be a list"
        
    if not isinstance(ticket_data.get('recommendations', []), list):
        return False, "Recommendations must be a list"
        
    if not isinstance(ticket_data.get('routing', {}), dict):
        return False, "Routing must be a dictionary"
    
    return True, ""

def analyze_conversation_trends(conversations):
    """
    Analyze conversation data to extract trends.
    
    Args:
        conversations (list): List of conversation dictionaries
        
    Returns:
        dict: Trend analysis
    """
    if not conversations or not isinstance(conversations, list):
        return {
            "average_response_time": 0,
            "common_issues": [],
            "sentiment_trend": "neutral"
        }
    
    # Calculate average time between user message and response
    response_times = []
    issues = []
    sentiments = []
    
    for conv in conversations:
        # Extract sentiment
        if isinstance(conv, dict) and "conversation_history" in conv:
            conv_text = format_conversation_history(conv["conversation_history"])
            sentiment, _ = calculate_sentiment(conv_text)
            sentiments.append(sentiment)
        
        # Extract key points as issues
        if isinstance(conv, dict) and "summary" in conv:
            key_points = extract_key_points(conv["summary"])
            issues.extend(key_points)
    
    # Get most common issues
    common_issues = []
    if issues:
        # In a real implementation, we would use nlp to cluster similar issues
        # For now, just take the first few
        common_issues = issues[:min(3, len(issues))]
    
    # Determine overall sentiment trend
    sentiment_trend = "neutral"
    if sentiments:
        positive_count = sentiments.count("positive")
        negative_count = sentiments.count("negative")
        neutral_count = sentiments.count("neutral")
        
        if positive_count > negative_count and positive_count > neutral_count:
            sentiment_trend = "positive"
        elif negative_count > positive_count and negative_count > neutral_count:
            sentiment_trend = "negative"
    
    return {
        "average_response_time": 2.5,  # mock value in minutes
        "common_issues": common_issues,
        "sentiment_trend": sentiment_trend
    }
