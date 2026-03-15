from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class JiraProject(BaseModel):
    key: str
    name: str

class JiraIssueType(BaseModel):
    name: str
    description: Optional[str] = None

class JiraIssueFields(BaseModel):
    summary: str
    description: Optional[str] = None
    project: JiraProject
    issuetype: JiraIssueType
    labels: Optional[List[str]] = []

class JiraIssue(BaseModel):
    id: str
    key: str
    fields: JiraIssueFields

class JiraWebhookPayload(BaseModel):
    webhookEvent: str
    issue_event_type_name: Optional[str] = None
    issue: JiraIssue
    timestamp: Optional[int] = None
