from .base_agent import BaseAgent

class IntentClassifierAgent(BaseAgent):
    """Agent responsible for classifying the intent of user messages."""
    
    def __init__(self):
        super().__init__("Intent Classifier Agent")
    
    def classify_intent(self, message):
        """
        Classify the intent of a user message to determine if it requires agent processing.
        
        Args:
            message (str): The user's message
            
        Returns:
            dict: Classification results including intent type and confidence
        """
        if not message or not isinstance(message, str):
            print(f"[AGENT] {self.name} received invalid message input")
            return {"intent": "unknown", "requires_agents": False, "confidence": 0.0}
        
        print(f"[AGENT] {self.name} classifying intent for: '{message[:50]}...' if longer")
        
        # Pre-classification for very short or simple messages
        message_lower = message.lower().strip()
        
        # Check for very short or vague issue mentions
        if message_lower in ["i have an issue", "i have a issue", "i have a problem", "i have problem", "help me"]:
            print(f"[AGENT] {self.name} detected vague issue mention")
            return {"intent": "casual", "confidence": 0.9, "is_question": False, "reasoning": "Vague mention of an issue without specific details"}
            
        # Check for common greetings
        common_greetings = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]
        if any(message_lower == greeting or message_lower == greeting + "!" for greeting in common_greetings):
            return {"intent": "greeting", "confidence": 0.95, "is_question": False, "reasoning": "Simple greeting detected"}
            
        # Check for common farewells
        common_farewells = ["bye", "goodbye", "farewell", "see you", "thanks", "thank you"]
        if any(farewell in message_lower for farewell in common_farewells) and len(message_lower.split()) <= 5:
            return {"intent": "farewell", "confidence": 0.8, "is_question": False, "reasoning": "Farewell detected"}
        
        # Use LLM classification for more complex messages
        prompt = f"""
        Carefully analyze this customer support message and classify it into one of these categories:

        1. "issue" - Contains a SPECIFIC customer problem with clear details that requires troubleshooting or support
        2. "greeting" - Simple hello, hi, or conversation starter without specific issues
        3. "casual" - General conversation, small talk, or VAGUE mentions of issues without specific details
        4. "farewell" - Goodbye, thanks, or conversation ender
        5. "unknown" - Unclear intent

        Critical classification rules:
        - "issue" classification REQUIRES specific details about a problem (error messages, specific symptoms, clear questions about functionality)
        - Short, vague statements like "I have an issue" or "I have a problem" without details MUST be "casual", not "issue"
        - "greeting" is for simple introductory messages like "hello", "hi there", "good morning", with NO other content
        - Messages consisting of ONLY a greeting word or phrase (hello, hi, hey, etc.) must ALWAYS be classified as "greeting" with high confidence
        - "casual" includes vague mentions of problems WITHOUT details (e.g., "I have an issue", "something's wrong", "need help")
        - Messages like "I have a problem with my account" without specific details should be "casual", not "issue"
        - "farewell" indicates the user is ending the conversation
        - A message must have CONCRETE DETAILS about a specific problem to be classified as an "issue"
        - Length alone does not determine classification - short messages with specific details are "issues"

        Examples:
        - "hello" → "greeting" (confidence: 0.95)
        - "hi there" → "greeting" (confidence: 0.95)
        - "I have an issue" → "casual" (confidence: 0.9) 
        - "I have a problem" → "casual" (confidence: 0.9)
        - "hello, I'm having trouble logging in" → "casual" (confidence: 0.8)
        - "I'm getting error code 404 when trying to log in" → "issue" (confidence: 0.9)
        - "thank you, goodbye" → "farewell" (confidence: 0.9)

        Customer message: "{message}"

        Respond with JSON only:
        {{
          "intent": "[category]",
          "confidence": [0.0-1.0],
          "is_question": true/false,
          "reasoning": "[brief explanation of why you classified it this way]"
        }}
        """
        
        try:
            response = self.query_llm(prompt)
            
            try:
                import json
                # Find JSON block in the response if there's extra text
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    classification = json.loads(json_str)
                    
                    # Ensure all expected fields are present
                    if "intent" not in classification:
                        classification["intent"] = "unknown"
                    if "confidence" not in classification:
                        classification["confidence"] = 0.5
                    if "is_question" not in classification:
                        classification["is_question"] = False
                    
                    # Safety check for common greetings to avoid misclassification
                    simple_greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "greetings"]
                    if message.lower().strip() in simple_greetings or message.lower().strip() in [g + "!" for g in simple_greetings]:
                        if classification["intent"] != "greeting":
                            print(f"[AGENT] {self.name} correcting misclassification of simple greeting")
                            classification["intent"] = "greeting"
                            classification["confidence"] = 0.95
                            classification["reasoning"] = "Simple greeting detected with no other content"
                    
                    # Safety check for vague issue mentions
                    vague_issues = ["i have an issue", "i have a issue", "i have a problem", "i have problem", 
                                   "got an issue", "having an issue", "need help", "help me"]
                    if message.lower().strip() in vague_issues:
                        if classification["intent"] != "casual":
                            print(f"[AGENT] {self.name} correcting misclassification of vague issue mention")
                            classification["intent"] = "casual"
                            classification["confidence"] = 0.9
                            classification["reasoning"] = "Vague mention of an issue without specific details"
                    
                    # Log the classification decision
                    reasoning = classification.get("reasoning", "No reasoning provided")
                    print(f"[AGENT] {self.name} classification: {classification['intent']}, confidence: {classification['confidence']}")
                    print(f"[AGENT] {self.name} reasoning: {reasoning}")
                        
                    return classification
                        
            except Exception as json_error:
                print(f"[AGENT] {self.name} JSON parsing error: {str(json_error)}")
            
            # Fallback if JSON parsing fails
            print(f"[AGENT] {self.name} using fallback classification logic")
            
            # Simple message-based checks for common patterns
            message_lower = message.lower().strip()
            
            # Check for very short or vague issue mentions
            vague_issues = ["i have an issue", "i have a issue", "i have a problem", "i have problem", 
                           "got an issue", "having an issue", "need help", "help me"]
            if message_lower in vague_issues or (len(message_lower) < 30 and ("issue" in message_lower or "problem" in message_lower)):
                return {"intent": "casual", "confidence": 0.9, "is_question": False, "reasoning": "Vague mention of an issue without specific details"}
            
            # Check for common greetings
            common_greetings = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]
            if any(message_lower == greeting or message_lower == greeting + "!" for greeting in common_greetings):
                return {"intent": "greeting", "confidence": 0.95, "is_question": False, "reasoning": "Simple greeting detected"}
                
            # Check for common farewells
            common_farewells = ["bye", "goodbye", "farewell", "see you", "thanks", "thank you"]
            if any(farewell in message_lower for farewell in common_farewells) and len(message_lower.split()) <= 5:
                return {"intent": "farewell", "confidence": 0.8, "is_question": False, "reasoning": "Farewell detected"}
                
            # Check for question marks and specific issue markers
            has_question = "?" in message
            has_specific_details = any(marker in message_lower for marker in ["error", "failed", "doesn't work", "cannot", "can't", "issue with", "problem with", "bug"])
            
            # For messages to be classified as issues, require more evidence of specificity
            if has_specific_details and len(message_lower) > 30:
                return {"intent": "issue", "confidence": 0.7, "is_question": has_question, "reasoning": "Contains specific issue details"}
            else:
                return {"intent": "casual", "confidence": 0.6, "is_question": has_question, "reasoning": "General conversation or vague issue mention"}
            
        except Exception as e:
            print(f"[AGENT] {self.name} error classifying intent: {str(e)}")
            # In case of any error, default to a conservative classification
            return {"intent": "casual", "confidence": 0.3, "is_question": "?" in message}
    
    def generate_casual_response(self, message, conversation_history):
        """
        Generate a casual response to greeting or farewell messages.
        
        Args:
            message (str): The user's message
            conversation_history (list): Previous conversation messages
            
        Returns:
            str: A casual response appropriate for the message intent
        """
        # First classify the message to determine its intent
        classification = self.classify_intent(message)
        intent = classification.get("intent", "unknown")
        
        # Format a short conversation history for context
        recent_messages = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
        context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages])
        
        prompt = f"""
        You are a friendly customer support chatbot. The user has sent a {intent} message.
        Generate a brief, friendly response appropriate for their message.
        
        Recent conversation context:
        {context}
        
        User's message: {message}
        
        Write a short, friendly response (1-2 sentences) that:
        - Maintains a professional but warm tone
        - Acknowledges their {intent} appropriately
        - For greetings, ask how you can help them today
        - For farewells, thank them for reaching out
        
        Your response should be brief and conversational.
        Don't include text like "Here's a possible response:" or any extra text, just strictly act as a customer support agent.
        """
        
        try:
            response = self.query_llm(prompt)
            return response.strip()
        except Exception as e:
            print(f"[AGENT] {self.name} error generating casual response: {str(e)}")
            
            # Fallback responses based on intent
            if intent == "greeting":
                return "Hello! How can I assist you today?"
            elif intent == "farewell":
                return "Thank you for reaching out. Have a great day!"
            else:
                return "Is there something specific I can help you with today?"
    
    def generate_probing_response(self, message, conversation_history):
        """
        Generate a response for casual conversations or vague problem mentions,
        probing for more specific details.
        
        Args:
            message (str): The user's message
            conversation_history (list): Previous conversation messages
            
        Returns:
            str: A response that probes for more specific details
        """
        # Format a short conversation history for context
        recent_messages = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
        context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages])
        
        prompt = f"""
        You are a customer support agent. The user has mentioned a problem or request,
        but hasn't provided enough specific details for you to fully understand or address it.
        
        Recent conversation context:
        {context}
        
        User's message: {message}
        
        Write a response that:
        1. Acknowledges their message in a friendly, professional way
        2. Gently asks for more specific details about their issue/request
        3. Provides guidance about what kind of information would be helpful (error messages, specific symptoms, when the issue started, etc.)
        
        Keep your response friendly and helpful, focusing on getting more details without sounding like a template.
        Your response should be 2-3 sentences only.
        """
        
        try:
            response = self.query_llm(prompt)
            return response.strip()
        except Exception as e:
            print(f"[AGENT] {self.name} error generating probing response: {str(e)}")
            return "I'd like to help you with that. Could you please provide more specific details about what you're experiencing so I can better assist you?"
