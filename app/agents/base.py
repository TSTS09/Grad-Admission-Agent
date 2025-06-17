from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,
            api_key=settings.OPENAI_API_KEY
        )
        self.embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        self.vector_store = None
    
    async def initialize(self):
        """Initialize the agent"""
        try:
            self.vector_store = Chroma(
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
                embedding_function=self.embeddings
            )
            logger.info(f"Initialized {self.__class__.__name__}")
        except Exception as e:
            logger.error(f"Failed to initialize {self.__class__.__name__}: {e}")
            raise
    
    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the agent's task"""
        pass
    
    async def search_similar_documents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents in vector store"""
        if not self.vector_store:
            return []
        
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []