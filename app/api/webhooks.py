from fastapi import APIRouter, HTTPException, Request
from app.models.jira import JiraWebhookPayload
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/jira")
async def handle_jira_webhook(payload: JiraWebhookPayload):
    try:
        logger.info(f"Received Jira webhook event: {payload.webhookEvent}")
        
        # We only care about issue creation or updates
        if payload.webhookEvent in ["jira:issue_created", "jira:issue_updated"]:
            logger.info(f"Issue {payload.issue.key}: {payload.issue.fields.summary}")
            
            # TODO: Trigger background task to process the issue
            
        return {"status": "success", "message": "Jira webhook received and validated."}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
