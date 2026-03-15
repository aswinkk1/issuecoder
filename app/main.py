from fastapi import FastAPI
from app.api.webhooks import router as webhooks_router
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AutoResolver Webhook Server")

app.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}
