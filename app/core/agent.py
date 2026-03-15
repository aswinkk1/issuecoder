import os
import logging
from typing import Dict, Any, List

from app.services.llm_service import LLMFactory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_text_splitters import Language
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)

class CodeResolverAgent:
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.llm = LLMFactory.get_llm()
        
        if not self.llm:
            logger.error("Failed to initialize Agent: LLM is not configured properly.")
            
    def resolve_issue(self, analysis: Dict[str, Any]) -> bool:
        """
        Main execution loop for resolving an issue.
        """
        if not self.llm:
            return False
            
        logger.info(f"Agent starting resolution for: {analysis.get('primary_goal')}")
        
        # 1. Retrieve Context (Search codebase)
        context = self._retrieve_code_context(analysis.get('context', ''))
        
        # 2. Formulate execution plan using LLM
        plan = self._create_execution_plan(analysis, context)
        
        # 3. Apply file changes
        success = self._apply_changes(plan)
        
        return success
        
    def _retrieve_code_context(self, query: str) -> str:
        """
        Loads the C++ codebase, creates an ephemeral vector index, and returns the top relevant chunks.
        """
        logger.info(f"Retrieving code context for query: {query[:50]}...")
        
        try:
            # 1. Load C++ source files from the workspace
            loader = GenericLoader.from_filesystem(
                self.workspace_path,
                glob="**/*",
                suffixes=[".cpp", ".c", ".h", ".hpp"],
                parser=LanguageParser(language=Language.CPP, parser_threshold=500),
            )
            documents = loader.load()
            
            if not documents:
                return "No C++ files found in the workspace context."
                
            # 2. Split documents into chunk sizes
            python_splitter = RecursiveCharacterTextSplitter.from_language(
                language=Language.CPP, chunk_size=2000, chunk_overlap=200
            )
            texts = python_splitter.split_documents(documents)
            
            # 3. Create ephemeral Chroma VectorDB (in-memory)
            # Defaulting to OpenAI Embeddings; could be made configurable via factory similar to LLMs
            target_embeddings = OpenAIEmbeddings()
            
            # 4. Embed and search
            db = Chroma.from_documents(texts, target_embeddings)
            retriever = db.as_retriever(
                search_type="mmr", # Maximum marginal relevance for diverse chunks
                search_kwargs={"k": 5},
            )
            
            relevant_docs = retriever.invoke(query)
            
            # 5. Format output for the LLM prompt
            context_string = "\n\n---\n\n".join(
                f"File: {doc.metadata.get('source', 'Unknown')}\nCode:\n{doc.page_content}" 
                for doc in relevant_docs
            )
            return context_string
            
        except Exception as e:
            logger.error(f"Error during code context retrieval: {e}")
            return "Error retrieving extended codebase context."
        
    def _create_execution_plan(self, analysis: Dict[str, Any], context: str) -> str:
        """Ask the LLM what specific file modifications to make."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an autonomous AI software engineer resolving a Jira ticket in a C++ codebase."),
            ("human", f"Issue Goal: {analysis.get('primary_goal')}\n\nContext: {analysis.get('context')}\n\nCode Context:\n{context}\n\nPlease provide a list of file modifications needed.")
        ])
        
        try:
            response = self.llm.invoke(prompt.format_messages())
            return response.content
        except Exception as e:
            logger.error(f"Error querying LLM: {e}")
            return ""
            
    def _apply_changes(self, plan: str) -> bool:
        """Parse LLM output and rewrite files (Placeholder)"""
        if not plan:
            return False
            
        logger.info(f"Applying AI proposed changes (placeholder):\n{plan[:100]}...")
        return True
