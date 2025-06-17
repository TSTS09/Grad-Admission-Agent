from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated
import asyncio
from app.agents.chat_agent import ChatAgent
from app.agents.faculty_agent import FacultyAgent
from app.agents.program_agent import ProgramAgent
from app.agents.research_agent import ResearchAgent
from app.core.logging import get_logger

logger = get_logger(__name__)

class WorkflowState(TypedDict):
    """State passed between agents"""
    messages: Annotated[list, add_messages]
    user_query: str
    user_id: Optional[int]
    session_id: Optional[str]
    context: Dict[str, Any]
    
    # Agent outputs
    query_classification: str
    faculty_matches: List[Dict[str, Any]]
    program_matches: List[Dict[str, Any]]
    research_insights: List[Dict[str, Any]]
    
    # Response
    response: str
    confidence_score: float
    sources: List[Dict[str, Any]]
    agent_type: str
    next_action: str

class STEMAdmissionsWorkflow:
    """Main workflow orchestrator for STEM admissions assistance"""
    
    def __init__(self):
        self.chat_agent = ChatAgent()
        self.faculty_agent = FacultyAgent()
        self.program_agent = ProgramAgent()
        self.research_agent = ResearchAgent()
        self.workflow = None
    
    async def initialize(self):
        """Initialize all agents and build workflow"""
        logger.info("Initializing STEM Admissions Workflow")
        
        # Initialize all agents
        await self.chat_agent.initialize()
        await self.faculty_agent.initialize()
        await self.program_agent.initialize()
        await self.research_agent.initialize()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        
        logger.info("Workflow initialization complete")
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("query_analyzer", self._analyze_query)
        workflow.add_node("faculty_search", self._search_faculty)
        workflow.add_node("program_search", self._search_programs)
        workflow.add_node("research_analysis", self._analyze_research)
        workflow.add_node("response_generator", self._generate_response)
        
        # Add edges
        workflow.add_edge(START, "query_analyzer")
        workflow.add_conditional_edges(
            "query_analyzer",
            self._route_query,
            {
                "faculty_search": "faculty_search",
                "program_search": "program_search",
                "research_analysis": "research_analysis",
                "general_chat": "response_generator"
            }
        )
        
        # All specialized nodes lead to response generation
        workflow.add_edge("faculty_search", "response_generator")
        workflow.add_edge("program_search", "response_generator")
        workflow.add_edge("research_analysis", "response_generator")
        workflow.add_edge("response_generator", END)
        
        return workflow.compile()
    
    async def process_query(
        self,
        query: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Process a user query through the workflow"""
        try:
            initial_state = WorkflowState(
                messages=[{"role": "user", "content": query}],
                user_query=query,
                user_id=user_id,
                session_id=session_id,
                context=context or {},
                query_classification="",
                faculty_matches=[],
                program_matches=[],
                research_insights=[],
                response="",
                confidence_score=0.0,
                sources=[],
                agent_type="",
                next_action=""
            )
            
            # Run the workflow
            result = await self.workflow.ainvoke(initial_state)
            
            return {
                "response": result["response"],
                "faculty_matches": result["faculty_matches"],
                "program_matches": result["program_matches"],
                "confidence_score": result["confidence_score"],
                "sources": result["sources"],
                "agent_type": result["agent_type"]
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "faculty_matches": [],
                "program_matches": [],
                "confidence_score": 0.0,
                "sources": [],
                "agent_type": "error"
            }
    
    async def _analyze_query(self, state: WorkflowState) -> WorkflowState:
        """Analyze and classify the user query"""
        result = await self.chat_agent.classify_query(state["user_query"])
        state["query_classification"] = result["classification"]
        state["next_action"] = result["next_action"]
        return state
    
    def _route_query(self, state: WorkflowState) -> str:
        """Route query to appropriate agent based on classification"""
        classification = state["query_classification"]
        
        if "faculty" in classification.lower():
            return "faculty_search"
        elif "program" in classification.lower():
            return "program_search"
        elif "research" in classification.lower():
            return "research_analysis"
        else:
            return "general_chat"
    
    async def _search_faculty(self, state: WorkflowState) -> WorkflowState:
        """Search for faculty members"""
        result = await self.faculty_agent.search_faculty(
            state["user_query"],
            user_context=state["context"]
        )
        state["faculty_matches"] = result["matches"]
        state["sources"].extend(result["sources"])
        state["agent_type"] = "faculty_agent"
        return state
    
    async def _search_programs(self, state: WorkflowState) -> WorkflowState:
        """Search for academic programs"""
        result = await self.program_agent.search_programs(
            state["user_query"],
            user_context=state["context"]
        )
        state["program_matches"] = result["matches"]
        state["sources"].extend(result["sources"])
        state["agent_type"] = "program_agent"
        return state
    
    async def _analyze_research(self, state: WorkflowState) -> WorkflowState:
        """Analyze research areas and trends"""
        result = await self.research_agent.analyze_research(
            state["user_query"],
            user_context=state["context"]
        )
        state["research_insights"] = result["insights"]
        state["sources"].extend(result["sources"])
        state["agent_type"] = "research_agent"
        return state
    
    async def _generate_response(self, state: WorkflowState) -> WorkflowState:
        """Generate final response"""
        result = await self.chat_agent.generate_response(state)
        state["response"] = result["response"]
        state["confidence_score"] = result["confidence_score"]
        return state
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up workflow resources")

# Global workflow instance
_workflow_instance: Optional[STEMAdmissionsWorkflow] = None

def get_workflow() -> Optional[STEMAdmissionsWorkflow]:
    """Get global workflow instance"""
    return _workflow_instance

def set_workflow(workflow: STEMAdmissionsWorkflow):
    """Set global workflow instance"""
    global _workflow_instance
    _workflow_instance = workflow