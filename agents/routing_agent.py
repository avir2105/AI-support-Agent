import requests
import json
from .base_agent import BaseAgent

class RoutingAgent(BaseAgent):
    """Agent responsible for determining the optimal routing for customer issues."""
    
    def __init__(self):
        super().__init__("Routing Agent")
        # Define available teams
        self.available_teams = [
            "Level 1 Support",
            "Level 2 Support",
            "Technical Engineering",
            "Product Management",
            "Billing Department",
            "Account Management",
            "Security Team",
            "Network Operations",
            "Development Team",
            "Quality Assurance"
        ]
    
    def determine_routing(self, conversation, actions=None):
        """
        Determine the optimal team(s) to route this customer issue to.
        
        Args:
            conversation (str): The formatted conversation history
            actions (list, optional): The extracted action items if available
            
        Returns:
            dict: Routing information including primary team and additional teams if needed
        """
        # Format actions for context
        actions_context = ""
        if actions:
            actions_context = "Identified action items:\n" + "\n".join([f"- {action}" for action in actions])
        
        teams_list = "\n".join([f"- {team}" for team in self.available_teams])
        
        prompt = f"""
        You are a customer support routing specialist. Your task is to determine the most 
        appropriate team(s) to handle a customer issue based on the conversation and actions needed.
        
        Available teams:
        {teams_list}
        
        {actions_context}
        
        Conversation:
        {conversation}
        
        Based on the issue and required actions, determine:
        1. The primary team that should handle this issue
        2. Any additional teams that need to be involved (if applicable)
        
        Return your answer in the following format:
        Primary Team: [team name]
        Additional Teams: [team name], [team name] (or "None" if no additional teams)
        """
        
        response = self.query_llm(prompt)
        
        # Process the response to extract routing information
        routing_info = {"primary_team": "", "additional_teams": []}
        
        for line in response.strip().split('\n'):
            if line.startswith('Primary Team:'):
                primary_team = line.split('Primary Team:')[1].strip()
                if primary_team in self.available_teams:
                    routing_info["primary_team"] = primary_team
                else:
                    # Default to Level 1 Support if the primary team isn't recognized
                    routing_info["primary_team"] = "Level 1 Support"
            
            if line.startswith('Additional Teams:'):
                teams_text = line.split('Additional Teams:')[1].strip()
                if teams_text.lower() != "none":
                    teams = [team.strip() for team in teams_text.split(',')]
                    routing_info["additional_teams"] = [team for team in teams if team in self.available_teams]
        
        return routing_info
    
    def evaluate_routing_accuracy(self, issue_summary, assigned_team):
        """
        Evaluate whether an issue was routed to the appropriate team.
        
        Args:
            issue_summary (str): Summary of the customer issue
            assigned_team (str): The team the issue was assigned to
            
        Returns:
            bool: Whether the routing appears correct
            str: Explanation of the evaluation
        """
        prompt = f"""
        You are a customer support quality analyst. Your task is to evaluate whether 
        an issue was routed to the appropriate team.
        
        Available teams:
        {', '.join(self.available_teams)}
        
        Issue summary: {issue_summary}
        Assigned team: {assigned_team}
        
        Evaluate whether this issue appears to be correctly routed to the appropriate team.
        If not, suggest which team would be more appropriate.
        
        Return your evaluation as:
        Correct Routing: [Yes/No]
        Explanation: [brief explanation]
        Suggested Team: [only if routing is incorrect]
        """
        
        response = self.query_llm(prompt)
        
        # Extract evaluation
        lines = response.strip().split('\n')
        correct = "yes" in lines[0].lower()
        explanation = lines[1].split('Explanation:')[1].strip() if len(lines) > 1 else ""
        
        suggested_team = None
        if len(lines) > 2 and lines[2].startswith('Suggested Team:'):
            suggested_team = lines[2].split('Suggested Team:')[1].strip()
        
        return correct, explanation, suggested_team
