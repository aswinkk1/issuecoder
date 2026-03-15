import os
import logging
import re
from typing import List, Tuple

logger = logging.getLogger(__name__)

class FileEditor:
    """Provides methods for the agent to safely read and edit the codebase."""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        
    def read_file(self, rel_path: str) -> str:
        full_path = self._get_safe_path(rel_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read {rel_path}: {e}")
            return ""
            
    def write_file(self, rel_path: str, content: str) -> bool:
        full_path = self._get_safe_path(rel_path)
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Successfully wrote to {rel_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write to {rel_path}: {e}")
            return False
            
    def replace_in_file(self, rel_path: str, old_str: str, new_str: str) -> bool:
        content = self.read_file(rel_path)
        if not content:
            return False
        if old_str not in content:
            logger.warning(f"String to replace not found in {rel_path}")
            return False
            
        new_content = content.replace(old_str, new_str)
        return self.write_file(rel_path, new_content)

    def search_codebase(self, keyword: str) -> List[Tuple[str, int]]:
        """
        Simple grep-like search across the workspace for specific keywords.
        Returns a list of (file_path, line_number) tuples.
        """
        results = []
        for root, _, files in os.walk(self.workspace_path):
            if '.git' in root or 'venv' in root or '__pycache__' in root:
                continue
            for file in files:
                if file.endswith(('.cpp', '.h', '.hpp', '.c', '.py')):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.workspace_path)
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            for idx, line in enumerate(f):
                                if keyword in line:
                                    results.append((rel_path, idx + 1))
                    except (UnicodeDecodeError, FileNotFoundError):
                        continue
        return results

    def _get_safe_path(self, rel_path: str) -> str:
        """Ensure the path stays within the workspace."""
        full_path = os.path.abspath(os.path.join(self.workspace_path, rel_path))
        if not full_path.startswith(os.path.abspath(self.workspace_path)):
            raise ValueError(f"Path traversal attempt blocked: {rel_path}")
        return full_path
