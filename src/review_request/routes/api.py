"""All API Routers."""

from fastapi import APIRouter

from review_request.api import message, jira_sprint

api_router = APIRouter()
api_router.include_router(
    message.router,
    prefix="/conversation",
    tags=["conversation"],
)
api_router.include_router(
    jira_sprint.router,
    prefix="/jira/sprint",
    tags=["jira-sprint"],
)
