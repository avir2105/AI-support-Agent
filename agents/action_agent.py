import requests
import json
from .base_agent import BaseAgent

class ActionAgent(BaseAgent):
    """Agent responsible for extracting actionable items from customer conversations."""
    
    def __init__(self):
        super().__init__("Action Agent")
    
    def extract_actions(self, conversation, summary=None):
        """
        Extract actionable items from the conversation.
        
        Args:
            conversation (str): The formatted conversation history
            summary (str, optional): The conversation summary if available
            
        Returns:
            list: A list of action items that need to be addressed
        """
        # Input validation
        if not conversation or not isinstance(conversation, str):
            print(f"[AGENT] {self.name} received invalid conversation input")
            return []
            
        # Safely handle summary
        if summary is None or not isinstance(summary, str) or not summary.strip():
            context = "No summary available."
            print(f"[AGENT] {self.name} using default summary context")
        else:
            context = summary
        
        prompt = f"""
        You are a customer support action item specialist. Your task is to analyze a customer 
        conversation and identify specific actions that need to be taken to resolve the issue.
        
        Conversation summary: {context}
        
        Full conversation:
        {conversation}
        
        List the specific action items that need to be completed to resolve this customer's issue. 
        Each action should be clear, specific, and actionable. Include only actions that a support 
        agent or another team needs to take, not actions the customer needs to take.
        
        Return ONLY a list of action items, one per line, with no numbering or prefixes.
        """
        
        try:
            response = self.query_llm(prompt)
            
            # Process the response into a list of action items
            actions = [action.strip() for action in response.strip().split('\n') if action.strip()]
            return actions if actions else []
        except Exception as e:
            print(f"[AGENT] {self.name} error extracting actions: {str(e)}")
            return []
    
    def prioritize_actions(self, actions):
        """
        Prioritize the list of actions based on urgency and impact.
        
        Args:
            actions (list): List of action items
            
        Returns:
            list: Prioritized list of action items with priority levels
        """
        if not actions:
            return []
            
        actions_text = "\n".join(actions)
        prompt = f"""
        You are a customer support prioritization specialist. Your task is to prioritize 
        the following list of action items based on urgency and impact on customer satisfaction.
        
        Action items:
        {actions_text}
        
        For each action item, assign a priority level (High, Medium, Low) and return the 
        prioritized list in the format:
        Priority: Action item
        
        Start with High priority items, then Medium, then Low.
        """
        
        response = self.query_llm(prompt)
        
        # Process the response into a prioritized list
        prioritized_actions = []
        for line in response.strip().split('\n'):
            if line.strip():
                prioritized_actions.append(line.strip())
                
        return prioritized_actions
