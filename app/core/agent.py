import os
import logging
from typing import Dict, Any, List

from app.services.llm_service import LLMFactory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

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
        TODO: Implement ast parsing, grep, or vector search.
        For C++, ctags or grep often work best locally.
        """
        logger.info("Retrieving code context (placeholder).")
        return "class SampleCPP { void doSomething(); };"
        
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
