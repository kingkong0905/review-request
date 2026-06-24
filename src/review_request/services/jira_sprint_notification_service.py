"""Service for handling Jira sprint completion notifications."""

import logging
from datetime import datetime
from typing import Dict, Optional
from slack_sdk.web.async_client import AsyncWebClient
from tenacity import retry, stop_after_attempt, wait_exponential

from review_request.decorators.message_templates import SprintCompletionMessageTemplates
from review_request.services.rollbar_service import RollbarService

logger = logging.getLogger(__name__)


class SprintNotificationError(Exception):
    pass


class JiraSprintNotificationService:
    """Service for sending Jira sprint completion notifications to Slack."""

    def __init__(self, slack_token: str):
        self.slack_token = slack_token
        self.client = AsyncWebClient(token=slack_token)

    def _format_date(self, date_str: Optional[str]) -> str:
        if not date_str:
            return "N/A"

        try:
            date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return date_obj.strftime("%B %d, %Y")
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse date {date_str}: {e}")
            return date_str

    def _build_message(
        self,
        sprint_name: str,
        start_date: str,
        end_date: str,
        completed_by: str,
    ) -> str:
        formatted_start = self._format_date(start_date)
        formatted_end = self._format_date(end_date)

        return SprintCompletionMessageTemplates.TEMPLATE.format(
            sprint_name=sprint_name,
            start_date=formatted_start,
            end_date=formatted_end,
            completed_by=completed_by,
        )

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def send_notification(
        self,
        channel_id: str,
        sprint_name: str,
        start_date: str,
        end_date: str,
        completed_by: str,
    ) -> Dict:
        try:
            message = self._build_message(
                sprint_name=sprint_name,
                start_date=start_date,
                end_date=end_date,
                completed_by=completed_by,
            )

            logger.info(
                f"Sending sprint completion notification for '{sprint_name}' "
                f"to channel {channel_id}"
            )

            response = await self.client.chat_postMessage(
                channel=channel_id,
                text=message,
                username="Jira Sprint Bot",
                icon_emoji=":jira:",
            )

            logger.info(
                f"Successfully sent sprint notification to channel {channel_id}"
            )

            return {
                "ok": response["ok"],
                "channel": response["channel"],
                "ts": response["ts"],
            }

        except Exception as e:
            error_msg = f"Failed to send sprint notification: {str(e)}"
            logger.error(error_msg, exc_info=True)

            RollbarService.report_error(
                exc=e,
                extra_data={
                    "operation": "send_sprint_notification",
                    "channel_id": channel_id,
                    "sprint_name": sprint_name,
                },
            )

            raise SprintNotificationError(error_msg) from e

    async def process_webhook(self, channel_id: str, webhook_data: Dict) -> Dict:
        try:
            sprint = webhook_data.get("sprint", {})
            user = webhook_data.get("user", {})

            sprint_name = sprint.get("name", "Unknown Sprint")
            start_date = sprint.get("startDate")
            end_date = sprint.get("endDate")
            completed_by = (
                user.get("displayName", "Unknown User") if user else "Unknown User"
            )

            logger.info(f"Processing sprint webhook for: {sprint_name}")

            return await self.send_notification(
                channel_id=channel_id,
                sprint_name=sprint_name,
                start_date=start_date,
                end_date=end_date,
                completed_by=completed_by,
            )

        except Exception as e:
            error_msg = f"Failed to process sprint webhook: {str(e)}"
            logger.error(error_msg, exc_info=True)

            RollbarService.report_error(
                exc=e,
                extra_data={
                    "operation": "process_sprint_webhook",
                    "channel_id": channel_id,
                    "webhook_event": webhook_data.get("webhookEvent"),
                },
            )

            raise SprintNotificationError(error_msg) from e
