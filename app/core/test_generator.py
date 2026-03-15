import os
import logging
from typing import Dict, Any, List

from app.services.llm_service import LLMFactory
from langchain_core.prompts import ChatPromptTemplate
from app.core.file_editor import FileEditor

logger = logging.getLogger(__name__)

class TestGenerator:
    """Uses the LLM to write corresponding unit tests for code modifiers."""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.llm = LLMFactory.get_llm()
        self.editor = FileEditor(workspace_path)
        
    def generate_tests(self, diff: str, related_files: List[str]) -> bool:
        """
        Takes the proposed git diff along with recently modified filenames,
        and generates a unit test covering the changes.
        """
        if not self.llm:
            logger.warning("No LLM available to generate tests.")
            return False
            
        logger.info("Generating C++ Unit Tests based on diff.")
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert C++ developer. Given a code diff and related context, generate or update a modern C++ unit test (ex. using Google Test / GTest) covering the new logic and all modified branches. Provide the absolute file path as the first line starting with 'FILE:', then output the C++ TEST content below."),
            ("human", f"Code Diff:\n{diff}\n\nModified Files Context: {related_files}")
        ])
        
        try:
            response = self.llm.invoke(prompt.format_messages())
            
            # Simple parsing of the LLM output to write it directly to the workspace
            return self._parse_and_write_test(response.content)
            
        except Exception as e:
            logger.error(f"Error generating unit tests: {e}")
            return False

    def _parse_and_write_test(self, ai_output: str) -> bool:
        lines = ai_output.strip().split('\n')
        target_file = ""
        content_lines = []
        in_content = False
        
        for line in lines:
            if line.startswith("FILE:"):
                target_file = line.replace("FILE:", "").strip()
                in_content = True
            elif in_content:
                if line.startswith("```"):
                    continue # Strip markdown wrapper
                content_lines.append(line)
                
        if target_file and content_lines:
            test_content = "\n".join(content_lines)
            return self.editor.write_file(target_file, test_content)
        
        logger.warning(f"Could not parse test file destination from AI. Raw Output: {ai_output[:50]}...")
        return False
