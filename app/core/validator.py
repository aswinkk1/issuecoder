import subprocess
import logging
from typing import Dict, Any, Tuple
from app.services.llm_service import LLMFactory
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

class Validator:
    """Handles running user-defined validation checks (linters/tests) and AI reviews."""
    
    def __init__(self, workspace_path: str, validation_cmd: str = "make test"):
        self.workspace_path = workspace_path
        self.validation_cmd = validation_cmd
        self.llm = LLMFactory.get_llm()

    def run_tests(self) -> Tuple[bool, str]:
        """Execute the user-defined validation command in the workspace."""
        logger.info(f"Running validation command: '{self.validation_cmd}'")
        try:
            result = subprocess.run(
                self.validation_cmd,
                cwd=self.workspace_path,
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("Validation command passed successfully.")
                return True, result.stdout
            else:
                logger.warning(f"Validation failed (exit code {result.returncode})")
                return False, result.stderr

        except Exception as e:
            logger.error(f"Error executing validation command: {e}")
            return False, str(e)
            
    def ai_review(self, diff: str, original_requirements: str) -> Tuple[bool, str]:
        """
        Ask the LLM to review the changes to ensure they meet the Jira criteria
        and are logically sound (especially for C++).
        """
        if not self.llm:
            return True, "Skipped AI review: LLM not configured."
            
        logger.info("Running AI codebase review on generated code.")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert C++ code reviewer. Assess if the provided Code Diff fulfills the given Requirements. Output 'PASS:' or 'FAIL:' followed by your reasoning."),
            ("human", f"Requirements: {original_requirements}\n\nCode Diff:\n{diff}")
        ])
        
        try:
            response = self.llm.invoke(prompt.format_messages())
            reasoning = response.content
            
            if "FAIL:" in reasoning.upper():
                return False, reasoning
            return True, reasoning
        except Exception as e:
            logger.error(f"Error during AI review: {e}")
            return False, str(e)
