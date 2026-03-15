import os
import logging
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
        
    def create_pr(self, repo_name: str, branch_name: str, title: str, description: str) -> Optional[str]:
        """
        Commits changes (via local git command or agent), then uses API to open PR.
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
