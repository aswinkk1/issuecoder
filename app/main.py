from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from app.api.webhooks import router as webhooks_router
from app.services.jira_service import JiraService
from app.services.analyzer import IssueAnalyzer
from app.core.agent import CodeResolverAgent
from app.core.validator import Validator
from app.core.test_generator import TestGenerator
from app.services.git_service import PRCreator
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AutoResolver Webhook Server")

# Serve UI static files (CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup Jinja2 templates for the manual trigger UI
templates = Jinja2Templates(directory="app/templates")

app.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])

class ResolveRequest(BaseModel):
    issue_key: str

@app.get("/")
async def serve_ui(request: Request):
    """Serve the manual trigger UI interface."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/resolve")
async def manual_trigger_resolve(payload: ResolveRequest):
    """Endpoint triggered by the frontend UI to resolve a manual Jira issue ID."""
    try:
        logger.info(f"Manual trigger received for issue: {payload.issue_key}")
        
        # Instantiate services
        workspace = "."
        jira_service = JiraService()
        analyzer = IssueAnalyzer()
        agent = CodeResolverAgent(workspace_path=workspace)
        validator = Validator(workspace_path=workspace)
        test_gen = TestGenerator(workspace_path=workspace)
        pr_creator = PRCreator(workspace_path=workspace)
        
        # 1. Fetch Jira Context
        issue_details = jira_service.get_issue_details(payload.issue_key)
        if not issue_details:
            return {"status": "error", "detail": f"Could not fetch details for {payload.issue_key} from Jira."}
            
        # 2. Analyze
        analysis = analyzer.analyze_issue(issue_details)
        
        # 3. Agent Execution
        success_agent = agent.resolve_issue(analysis)
        if not success_agent:
            return {"status": "error", "detail": "Agent failed to resolve the issue logic."}
            
        # 4. Validation & Self-Healing Loop
        success_validation = validator.run_validation_with_healing(agent, analysis)
        if not success_validation:
            return {"status": "error", "detail": "Code failed validation and could not be self-healed."}
            
        # 5. Generate Unit Tests
        # Placeholder diff/files
        test_gen.generate_tests("Mock Diff", ["mock_file.cpp"])
        
        # 6. Commit & PR
        branch_name = f"feature/autoresolver-{payload.issue_key.lower()}"
        commit_msg = f"Fix: Resolve {payload.issue_key} - {analysis.get('primary_goal')}"
        
        if pr_creator.commit_and_push(branch_name, commit_msg):
            pr_url = pr_creator.create_pr(
                repo_name="your_org/your_repo", # Ideally from config
                branch_name=branch_name,
                title=f"AutoResolver: {payload.issue_key}",
                description=analysis.get('context', 'Auto-generated PR.')
            )
            return {
                "status": "success", 
                "message": f"Successfully resolved {payload.issue_key}!",
                "pr_url": pr_url or "#"
            }
        else:
            return {"status": "error", "detail": "Failed to push branches or create PR."}

    except Exception as e:
        logger.error(f"Error during manual resolution: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
