import os
from jira import JIRA
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class JiraService:
    def __init__(self):
        self.server_url = os.environ.get("JIRA_SERVER_URL", "https://your-domain.atlassian.net")
        self.email = os.environ.get("JIRA_EMAIL")
        self.api_token = os.environ.get("JIRA_API_TOKEN")
        
        if not self.email or not self.api_token:
            logger.warning("Jira credentials not fully configured. Some features may not work.")
            self.client = None
        else:
            try:
                self.client = JIRA(
                    server=self.server_url,
                    basic_auth=(self.email, self.api_token)
                )
                logger.info("Successfully connected to Jira API.")
            except Exception as e:
                logger.error(f"Failed to connect to Jira API: {e}")
                self.client = None

    def get_issue_details(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Fetch full details of an issue from Jira."""
        if not self.client:
            logger.error("Cannot fetch issue details: Jira client is not initialized.")
            return None
            
        try:
            issue = self.client.issue(issue_key)
            
            # Extract relevant info
            return {
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": issue.fields.description,
                "status": issue.fields.status.name,
                "labels": issue.fields.labels,
                "comments": [c.body for c in getattr(issue.fields.comment, 'comments', [])],
                "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
            }
        except Exception as e:
            logger.error(f"Error fetching issue details for {issue_key}: {e}")
            return None
