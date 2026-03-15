import os
import logging
import subprocess
from github import Github
from atlassian import Bitbucket
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PRCreator:
    """Handles creating branches, committing changes, and opening Pull Requests."""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.vcs_provider = os.environ.get("VCS_PROVIDER", "github").lower()
        
        # GitHub specific
        self.gh_token = os.environ.get("GITHUB_TOKEN")
        
        # Bitbucket specific
        self.bb_url = os.environ.get("BITBUCKET_URL", "https://api.bitbucket.org")
        self.bb_user = os.environ.get("BITBUCKET_USER")
        self.bb_pass = os.environ.get("BITBUCKET_APP_PASSWORD")
        self.bb_workspace = os.environ.get("BITBUCKET_WORKSPACE")
        
    def commit_and_push(self, branch_name: str, commit_message: str) -> bool:
        """
        Executes local git commands to branch, stage, commit, and push changes to origin.
        """
        logger.info(f"Committing changes to local branch: {branch_name}")
        cmds = [
            f"git checkout -b {branch_name}",
            "git add .",
            f'git commit -m "{commit_message}"',
            f"git push origin {branch_name}"
        ]
        
        for cmd in cmds:
            try:
                logger.debug(f"Running: {cmd}")
                result = subprocess.run(cmd, cwd=self.workspace_path, shell=True, capture_output=True, text=True)
                if result.returncode != 0 and "nothing to commit" not in result.stdout:
                    logger.error(f"Git command failed: {cmd}\nError: {result.stderr}")
                    return False
            except Exception as e:
                logger.error(f"Failed to execute git command {cmd}: {e}")
                return False
                
        return True

    def create_pr(self, repo_name: str, branch_name: str, title: str, description: str) -> Optional[str]:
        """
        Uses API to open PR. Assumes commit_and_push() was already successfully called.
        Returns the PR URL if successful.
        """
        if self.vcs_provider == "github":
            return self._create_github_pr(repo_name, branch_name, title, description)
        elif self.vcs_provider == "bitbucket":
            return self._create_bitbucket_pr(repo_name, branch_name, title, description)
        else:
            logger.error(f"Unsupported VCS provider: {self.vcs_provider}")
            return None

    def _create_github_pr(self, repo_name: str, branch_name: str, title: str, description: str) -> Optional[str]:
        if not self.gh_token:
            logger.error("GitHub token not set.")
            return None
            
        try:
            g = Github(self.gh_token)
            repo = g.get_repo(repo_name) # e.g., "org/repo"
            
            # Assuming changes are already committed and pushed to `branch_name`
            pr = repo.create_pull(
                title=title,
                body=description,
                head=branch_name,
                base="main" # Or master
            )
            logger.info(f"Successfully created GitHub PR: {pr.html_url}")
            return pr.html_url
        except Exception as e:
            logger.error(f"Error creating GitHub PR: {e}")
            return None

    def _create_bitbucket_pr(self, repo_name: str, branch_name: str, title: str, description: str) -> Optional[str]:
        if not self.bb_user or not self.bb_pass or not self.bb_workspace:
            logger.error("Bitbucket credentials or workspace not fully set.")
            return None
            
        try:
            bitbucket = Bitbucket(
                url=self.bb_url,
                username=self.bb_user,
                password=self.bb_pass
            )
            
            # Using Atlassian Python API for Bitbucket
            pr = bitbucket.open_pull_request(
                workspace=self.bb_workspace,
                repo=repo_name,
                source_branch=branch_name,
                destination_branch="main", # Or master
                title=title,
                description=description
            )
            pr_url = pr.get('links', {}).get('html', {}).get('href', 'Unknown PR URL')
            logger.info(f"Successfully created Bitbucket PR: {pr_url}")
            return pr_url
        except Exception as e:
            logger.error(f"Error creating Bitbucket PR: {e}")
            return None
