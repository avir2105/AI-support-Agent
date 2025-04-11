import requests
import json
from .base_agent import BaseAgent
from database.supabase_client import SupabaseClient

class TimeEstimationAgent(BaseAgent):
    """Agent responsible for estimating resolution time for customer issues."""
    
    def __init__(self):
        super().__init__("Time Estimation Agent")
        self.supabase = SupabaseClient()
    
    def estimate_resolution_time(self, conversation, actions=None, routing=None):
        """
        Estimate the expected resolution time for the customer issue.
        
        Args:
            conversation (str): The formatted conversation history
            actions (list, optional): The extracted action items if available
            routing (dict, optional): The routing information if available
            
        Returns:
            str: Estimated resolution time with confidence level
        """
        # Get historical resolution times for similar issues
        historical_data = self.supabase.get_resolution_time_data(conversation)
        
        # Format actions for context
        actions_context = ""
        if actions and isinstance(actions, list):
            actions_context = "Required actions:\n" + "\n".join([f"- {action}" for action in actions])
        
        # Format routing for context
        routing_context = ""
        if routing and isinstance(routing, dict):
            primary_team = routing.get("primary_team", "Unknown")
            additional_teams = routing.get("additional_teams", [])
            
            routing_context = f"Primary team: {primary_team}\n"
            if additional_teams:
                routing_context += f"Additional teams involved: {', '.join(additional_teams)}\n"
        
        # Format historical data for context (safely handling empty or None values)
        historical_context = ""
        if historical_data and isinstance(historical_data, list) and len(historical_data) > 0:
            # Filter out None values
            valid_data = [t for t in historical_data if t is not None]
            
            if valid_data:
                avg_time = sum(valid_data) / len(valid_data)
                min_time = min(valid_data)
                max_time = max(valid_data)
                
                historical_context = f"""
                Historical resolution times for similar issues:
                - Average: {avg_time:.1f} hours
                - Minimum: {min_time:.1f} hours
                - Maximum: {max_time:.1f} hours
                - Sample size: {len(valid_data)} similar issues
                """
            else:
                historical_context = "No valid historical resolution time data available."
        else:
            historical_context = "No historical resolution time data available."
        
        prompt = f"""
        You are a customer support time estimation specialist. Your task is to estimate 
        how long it will take to resolve a customer issue based on the conversation, 
        required actions, team assignment, and historical data.
        
        Conversation:
        {conversation}
        
        {actions_context}
        
        {routing_context}
        
        {historical_context}
        
        Based on this information, estimate how long it will likely take to fully resolve 
        this customer's issue. Consider the complexity of the issue, the number and type of 
        actions required, the teams involved, and historical resolution times.
        
        Provide your estimate in the following format:
        Estimated Resolution Time: [time range or specific time]
        Confidence Level: [High/Medium/Low]
        Factors: [brief explanation of key factors affecting the estimate]
        """
        
        response = self.query_llm(prompt)
        
        # Format the response
        formatted_estimate = ""
        for line in response.strip().split('\n'):
            if line.strip():
                formatted_estimate += line.strip() + "\n"
        
        return formatted_estimate.strip()
    
    def optimize_resolution_process(self, actions, current_estimate):
        """
        Suggest optimizations to reduce the estimated resolution time.
        
        Args:
            actions (list): List of action items
            current_estimate (str): Current resolution time estimate
            
        Returns:
            list: Suggested optimizations to reduce resolution time
        """
        if not actions:
            return ["No actions to optimize"]
            
        actions_text = "\n".join([f"- {action}" for action in actions])
        
        prompt = f"""
        You are a customer support efficiency specialist. Your task is to identify 
        ways to optimize the resolution process to reduce the time needed to resolve a customer issue.
        
        Current action items:
        {actions_text}
        
        Current estimated resolution time:
        {current_estimate}
        
        Analyze these actions and suggest specific optimizations that could reduce the 
        resolution time. Consider opportunities for:
        - Parallelization (actions that could be done simultaneously)
        - Automation (actions that could be automated)
        - Prioritization (changing the order of actions)
        - Delegation (reassigning actions to more appropriate teams)
        - Simplification (simpler alternatives to achieve the same outcome)
        
        Return 2-4 specific optimization suggestions, each with an estimate of how much 
        time it could save.
        """
        
        response = self.query_llm(prompt)
        
        # Process the response into a list of optimizations
        optimizations = []
        current_optimization = ""
        
        for line in response.strip().split('\n'):
            if line.strip():
                current_optimization += line.strip() + " "
            else:
                if current_optimization:
                    optimizations.append(current_optimization.strip())
                    current_optimization = ""
        
        if current_optimization:
            optimizations.append(current_optimization.strip())
        
        return optimizations if optimizations else ["No clear optimization opportunities identified"]
