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

    def run_validation_with_healing(self, agent_instance, original_analysis: Dict[str, Any], max_retries: int = 3) -> bool:
        """
        Runs tests and if they fail, asks the agent to fix the code based on the compiler/test error.
        """
        for attempt in range(max_retries):
            logger.info(f"Validation Attempt {attempt + 1}/{max_retries}")
            
            success, output = self.run_tests()
            if success:
                logger.info("Validation passed!")
                return True
                
            logger.warning(f"Validation failed. Attempting self-healing... Error snippet: {output[:200]}")
            
            # Format a healing plan request for the agent
            healing_analysis = original_analysis.copy()
            healing_analysis['primary_goal'] = f"Fix failing tests/compilation for: {original_analysis.get('primary_goal')}"
            healing_analysis['context'] = f"The previous changes failed validation. The error output was:\n{output}\n\nPlease analyze this error, find the bug in the modified codebase, and apply a fix."
            
            # Ask the agent to try again with the error context
            agent_success = agent_instance.resolve_issue(healing_analysis)
            if not agent_success:
                logger.error("Agent failed to apply a healing patch.")
                return False
                
        logger.error(f"Validation failed after {max_retries} healing attempts.")
        return False
            
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
