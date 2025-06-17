from typing import Dict, Any, List
from langchain.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent
from app.core.logging import get_logger

logger = get_logger(__name__)

class ChatAgent(BaseAgent):
    """Agent for general chat and query classification"""
    
    def __init__(self):
        super().__init__()
        self.classification_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an AI assistant specializing in STEM graduate school admissions. 
            Analyze the user's query and classify it into one of these categories:
            
            1. faculty_search - Looking for professors, research advisors, or faculty information
            2. program_search - Asking about degree programs, requirements, or admissions
            3. research_analysis - Questions about research areas, trends, or academic fit
            4. general_chat - General questions, greetings, or conversational queries
            
            Examples:
            - "Find me CS professors at Stanford" -> faculty_search
            - "What are the requirements for MIT's PhD program?" -> program_search
            - "What's trending in machine learning research?" -> research_analysis
            - "How are you today?" -> general_chat
            
            Respond with just the category name and a brief reason."""),
            ("user", "{query}")
        ])
        
        self.response_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant for STEM graduate school admissions.
            Generate a comprehensive response based on the workflow state and agent findings.
            
            Guidelines:
            - Be specific and actionable
            - Include relevant details from faculty/program matches
            - Provide next steps when appropriate
            - Maintain an encouraging and supportive tone
            - If confidence is low, acknowledge limitations
            
            Available data:
            - Faculty matches: {faculty_matches}
            - Program matches: {program_matches}
            - Research insights: {research_insights}
            - User query: {user_query}
            - Confidence score: {confidence_score}"""),
            ("user", "Generate a helpful response based on the above information.")
        ])
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process general chat queries"""
        return await self.generate_response(state)
    
    async def classify_query(self, query: str) -> Dict[str, Any]:
        """Classify user query"""
        try:
            result = await self.llm.ainvoke(
                self.classification_prompt.format_messages(query=query)
            )
            
            classification = result.content.split('\n')[0].lower().strip()
            
            # Map to next action
            action_map = {
                "faculty_search": "faculty_search",
                "program_search": "program_search", 
                "research_analysis": "research_analysis",
                "general_chat": "general_chat"
            }
            
            return {
                "classification": classification,
                "next_action": action_map.get(classification, "general_chat")
            }
            
        except Exception as e:
            logger.error(f"Error classifying query: {e}")
            return {"classification": "general_chat", "next_action": "general_chat"}
    
    async def generate_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final response based on workflow state"""
        try:
            response = await self.llm.ainvoke(
                self.response_prompt.format_messages(
                    faculty_matches=state.get("faculty_matches", []),
                    program_matches=state.get("program_matches", []),
                    research_insights=state.get("research_insights", []),
                    user_query=state.get("user_query", ""),
                    confidence_score=state.get("confidence_score", 0.0)
                )
            )
            
            # Calculate confidence based on available data
            confidence = self._calculate_confidence(state)
            
            return {
                "response": response.content,
                "confidence_score": confidence
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "response": "I apologize, but I'm having trouble generating a response right now. Please try rephrasing your question.",
                "confidence_score": 0.0
            }
    
    def _calculate_confidence(self, state: Dict[str, Any]) -> float:
        """Calculate confidence score based on available data"""
        score = 0.0
        
        if state.get("faculty_matches"):
            score += 0.4
        if state.get("program_matches"):
            score += 0.4
        if state.get("research_insights"):
            score += 0.2
        
        return min(0.95, score)