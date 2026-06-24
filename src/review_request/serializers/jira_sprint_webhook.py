"""Serializers for Jira sprint webhook payloads."""

from pydantic import BaseModel, Field
from typing import Optional


class SprintData(BaseModel):
    """Sprint data from Jira webhook."""

    id: int
    name: str
    state: str
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    completeDate: Optional[str] = None
    originBoardId: Optional[int] = None


class UserData(BaseModel):
    """User data from Jira webhook."""

    accountId: str
    displayName: str
    emailAddress: Optional[str] = None


class JiraSprintWebhook(BaseModel):
    """Jira sprint webhook payload."""

    timestamp: int
    webhookEvent: str
    sprint: SprintData
    user: Optional[UserData] = None


class SprintNotificationRequest(BaseModel):
    """Request payload for manual sprint notification."""

    channel_id: str = Field(..., description="Slack channel ID to send notification")
    sprint_name: str = Field(..., description="Name of the sprint")
    start_date: str = Field(..., description="Sprint start date (ISO format)")
    end_date: str = Field(..., description="Sprint end date (ISO format)")
    completed_by: str = Field(..., description="User who completed the sprint")
