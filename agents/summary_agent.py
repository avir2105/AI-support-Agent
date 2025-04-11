import requests
import json
from .base_agent import BaseAgent

class SummaryAgent(BaseAgent):
    """Agent responsible for generating concise summaries of customer conversations."""
    
    def __init__(self):
        super().__init__("Summary Agent")

    def generate_summary(self, conversation):
        """
        Generate a concise summary of the conversation.
        
        Args:
            conversation (str): The formatted conversation history
            
        Returns:
            str: A concise summary of the key points in the conversation
        """
        if not conversation or not isinstance(conversation, str):
            print(f"[AGENT] {self.name} received invalid conversation input")
            return "No conversation provided to summarize."
        
        prompt = f"""
        You are a customer support summary specialist. Your task is to create a concise, 
        factual summary of the following customer support conversation. 
        Focus on the main customer issue, relevant details, and current status.
        
        Conversation:
        {conversation}
        
        Create a brief, objective summary (3-5 sentences) that captures the essence of this conversation:
        """
        
        try:
            response = self.query_llm(prompt)
            return response.strip()
        except Exception as e:
            print(f"[AGENT] {self.name} error generating summary: {str(e)}")
            return "Unable to generate conversation summary at this time."
    
    def update_summary(self, previous_summary, new_messages):
        """
        Update an existing summary with new conversation messages.
        
        Args:
            previous_summary (str): The existing conversation summary
            new_messages (str): New messages to incorporate into the summary
            
        Returns:
            str: Updated summary
        """
        if not previous_summary or not isinstance(previous_summary, str):
            return self.generate_summary(new_messages)
            
        if not new_messages or not isinstance(new_messages, str):
            return previous_summary
        
        prompt = f"""
        You have an existing summary of a customer support conversation:
        
        Existing Summary:
        {previous_summary}
        
        Here are new messages from the conversation:
        {new_messages}
        
        Update the summary to incorporate the new information while keeping it concise (3-5 sentences):
        Strictly dont include (here is the summary) type extra messages 
        """
        
        try:
            response = self.query_llm(prompt)
            return response.strip()
        except Exception as e:
            print(f"[AGENT] {self.name} error updating summary: {str(e)}")
            return previous_summary
