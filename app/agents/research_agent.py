from typing import Dict, Any, List
from langchain.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent
from app.core.logging import get_logger

logger = get_logger(__name__)

class ResearchAgent(BaseAgent):
    """Agent specialized in research trend analysis and academic insights"""
    
    def __init__(self):
        super().__init__()
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a research analyst specializing in STEM academic trends.
            Analyze research areas, trends, and provide insights for graduate school applicants.
            
            Your analysis should include:
            1. Current trends in the research area
            2. Top universities and labs working in this area
            3. Key researchers and recent breakthroughs
            4. Future directions and opportunities
            5. Skills and background needed
            6. Career prospects
            
            Base your analysis on academic knowledge and industry trends.
            Be specific and provide actionable insights."""),
            ("user", "Analyze this research query: {query}")
        ])
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process research analysis request"""
        return await self.analyze_research(
            state["user_query"],
            user_context=state.get("context", {})
        )
    
    async def analyze_research(self, query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze research areas and trends"""
        try:
            # Get research insights from LLM
            insights = await self._generate_research_insights(query)
            
            # Search for relevant documents
            similar_docs = await self.search_similar_documents(query, k=5)
            
            # Combine insights with document context
            enriched_insights = await self._enrich_with_documents(insights, similar_docs)
            
            return {
                "insights": enriched_insights,
                "sources": [
                    {"type": "ai_analysis", "confidence": 0.8},
                    {"type": "document_search", "documents": len(similar_docs)}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in research analysis: {e}")
            return {"insights": [], "sources": []}
    
    async def _generate_research_insights(self, query: str) -> List[Dict[str, Any]]:
        """Generate research insights using LLM"""
        try:
            result = await self.llm.ainvoke(
                self.analysis_prompt.format_messages(query=query)
            )
            
            # Parse the response into structured insights
            insights = self._parse_insights(result.content)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating research insights: {e}")
            return []
    
    def _parse_insights(self, content: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured insights"""
        insights = []
        
        # Split content into sections (simplified parsing)
        sections = content.split('\n\n')
        
        for i, section in enumerate(sections):
            if section.strip():
                insights.append({
                    "type": "analysis",
                    "content": section.strip(),
                    "priority": len(sections) - i,  # Earlier sections have higher priority
                    "source": "ai_analysis"
                })
        
        return insights
    
    async def _enrich_with_documents(self, insights: List[Dict[str, Any]], documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich insights with document context"""
        enriched = insights.copy()
        
        # Add document-based insights
        for doc in documents:
            enriched.append({
                "type": "document_insight",
                "content": doc["content"][:500] + "..." if len(doc["content"]) > 500 else doc["content"],
                "priority": 3,
                "source": "document_search",
                "metadata": doc.get("metadata", {})
            })
        
        # Sort by priority
        enriched.sort(key=lambda x: x.get("priority", 0), reverse=True)
        
        return enriched[:10]  # Return top 10 insights