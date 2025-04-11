import requests
import json
from .base_agent import BaseAgent
from database.supabase_client import SupabaseClient

class RecommendationAgent(BaseAgent):
    """Agent responsible for recommending solutions based on historical data."""
    
    def __init__(self):
        super().__init__("Recommendation Agent")
        self.supabase = SupabaseClient()
    
    def generate_recommendations(self, conversation, summary=None, actions=None):
        """
        Generate solution recommendations based on the conversation and historical data.
        
        Args:
            conversation (str): The formatted conversation history
            summary (str, optional): The conversation summary if available
            actions (list, optional): The extracted action items if available
            
        Returns:
            list: A list of recommended solutions
        """
        # Input validation
        if not conversation or not isinstance(conversation, str):
            print(f"[AGENT] {self.name} received invalid conversation input")
            return ["Unable to process the conversation data."]
            
        # Safely handle summary
        if summary is None or not isinstance(summary, str) or not summary.strip():
            context = "No summary available."
            print(f"[AGENT] {self.name} using default summary context")
        else:
            context = summary
            
        # Safely handle actions
        if not actions or not isinstance(actions, list):
            actions = []
            actions_context = "No action items identified."
            print(f"[AGENT] {self.name} using empty actions list")
        else:
            actions_context = "Identified action items:\n" + "\n".join([f"- {action}" for action in actions])
        
        try:
            # Get similar historical tickets from the database
            similar_tickets = self.supabase.get_similar_tickets(conversation)
            
            # Format similar tickets for context
            historical_context = ""
            if similar_tickets and isinstance(similar_tickets, list) and len(similar_tickets) > 0:
                historical_context = "Similar past issues and their solutions:\n"
                for idx, ticket in enumerate(similar_tickets[:3]):  # Limit to top 3 most similar
                    if isinstance(ticket, dict):
                        ticket_summary = ticket.get('summary', 'No summary available')
                        ticket_resolution = ticket.get('resolution', 'No resolution recorded')
                        historical_context += f"Issue {idx+1}: {ticket_summary}\n"
                        historical_context += f"Solution: {ticket_resolution}\n\n"
            else:
                historical_context = "No similar historical tickets found.\n"
        except Exception as db_error:
            print(f"[AGENT] {self.name} database error: {str(db_error)}")
            historical_context = "Unable to retrieve historical data.\n"
        
        prompt = f"""
        You are a customer support solution specialist. Your task is to recommend the most appropriate 
        solutions for the current customer issue based on the conversation and similar past issues.
        
        Current issue summary: {context}
        
        {actions_context}
        
        {historical_context}
        
        Current conversation:
        {conversation}
        
        Based on this information, provide a list of 2-3 specific recommendations to resolve the customer's issue.
        Each recommendation should be:
        1. Clear and detailed (not just a few words)
        2. Actionable with specific steps
        3. Directly addressing the customer's problem
        4. Formatted as complete sentences with proper punctuation
        
        Return ONLY a list of recommendations, one per line, with no numbering or prefixes.
        Make each recommendation at least 10-15 words and be specific about what actions to take.
        """
        
        try:
            response = self.query_llm(prompt)
            
            # Process the response into a list of recommendations
            recommendations = [rec.strip() for rec in response.strip().split('\n') if rec.strip()]
            
            # Ensure recommendations are complete sentences and sufficiently detailed
            validated_recommendations = []
            for rec in recommendations:
                # Add period if missing at the end
                if not rec.endswith('.') and not rec.endswith('!') and not rec.endswith('?'):
                    rec = rec + '.'
                    
                # Only keep recommendations that are substantial
                if len(rec.split()) >= 5:
                    validated_recommendations.append(rec)
            
            return validated_recommendations if validated_recommendations else ["Unable to generate specific recommendations based on the current information."]
        except Exception as llm_error:
            print(f"[AGENT] {self.name} LLM error: {str(llm_error)}")
            return ["Unable to generate recommendations due to a processing error."]
    
    def evaluate_recommendation_effectiveness(self, recommendation, issue_summary):
        """
        Evaluate the likely effectiveness of a recommendation for the given issue.
        
        Args:
            recommendation (str): The recommended solution
            issue_summary (str): Summary of the customer issue
            
        Returns:
            float: Score between 0-1 indicating likely effectiveness
            str: Explanation of the score
        """
        prompt = f"""
        You are a customer support quality analyst. Your task is to evaluate the likely effectiveness 
        of a proposed solution for a given customer issue.
        
        Customer issue: {issue_summary}
        
        Proposed solution: {recommendation}
        
        Evaluate how well this solution addresses the customer's issue. Consider factors such as:
        - Completeness (does it fully address the issue?)
        - Clarity (is it clear and understandable?)
        - Appropriateness (is it the right approach for this issue?)
        
        Return your evaluation as:
        1. A score from 0 to 1 (with 1 being perfect)
        2. A brief explanation of your rating
        
        Format: Score: [number between 0-1]
        Explanation: [your brief explanation]
        """
        
        response = self.query_llm(prompt)
        
        # Extract score and explanation
        try:
            score_line = [line for line in response.strip().split('\n') if line.startswith('Score:')][0]
            score = float(score_line.split('Score:')[1].strip())
            
            explanation_line = [line for line in response.strip().split('\n') if line.startswith('Explanation:')][0]
            explanation = explanation_line.split('Explanation:')[1].strip()
            
            return score, explanation
        except:
            return 0.5, "Could not parse evaluation properly"
