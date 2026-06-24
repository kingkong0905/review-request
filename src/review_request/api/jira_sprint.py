"""API endpoints for Jira sprint webhooks."""

import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from review_request.serializers.jira_sprint_webhook import (
    JiraSprintWebhook,
    SprintNotificationRequest,
)
from review_request.services.jira_sprint_notification_service import (
    JiraSprintNotificationService,
    SprintNotificationError,
)
from review_request.config.settings import settings
from review_request.services.rollbar_service import RollbarService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/webhook")
async def jira_sprint_webhook(
    request: Request,
    channel_id: str,
) -> JSONResponse:
    try:
        webhook_data = await request.json()
        webhook_event = webhook_data.get("webhookEvent", "")

        logger.info(f"Received Jira webhook: {webhook_event}")

        if webhook_event != "sprint_closed":
            logger.info(f"Ignoring non-sprint-closed event: {webhook_event}")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "ignored",
                    "message": f"Event type '{webhook_event}' is not processed",
                },
            )

        try:
            validated_webhook = JiraSprintWebhook(**webhook_data)
        except Exception as validation_error:
            logger.error(f"Webhook validation failed: {validation_error}")
            RollbarService.report_error(
                exc=validation_error,
                request=request,
                extra_data={
                    "operation": "webhook_validation",
                    "webhook_event": webhook_event,
                },
                level="warning",
            )
            raise HTTPException(
                status_code=400,
                detail=f"Invalid webhook payload: {str(validation_error)}",
            )

        sprint = validated_webhook.sprint

        logger.info(
            f"Processing sprint completion: {sprint.name} (State: {sprint.state})"
        )

        service = JiraSprintNotificationService(slack_token=settings.bot_token)

        result = await service.process_webhook(
            channel_id=channel_id,
            webhook_data=webhook_data,
        )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Sprint completion notification sent",
                "sprint_name": sprint.name,
                "channel_id": channel_id,
                "slack_response": result,
            },
        )

    except SprintNotificationError as e:
        logger.error(f"Sprint notification error: {str(e)}")

        RollbarService.report_error(
            exc=e,
            request=request,
            extra_data={
                "operation": "sprint_webhook",
                "channel_id": channel_id,
            },
        )

        raise HTTPException(
            status_code=500, detail=f"Failed to send notification: {str(e)}"
        )

    except Exception as e:
        logger.error(f"Unexpected error in sprint webhook: {str(e)}", exc_info=True)

        RollbarService.report_error(
            exc=e,
            request=request,
            extra_data={
                "operation": "sprint_webhook",
                "channel_id": channel_id,
            },
        )

        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/notify")
async def send_sprint_notification(
    request: Request,
    notification_request: SprintNotificationRequest,
) -> JSONResponse:
    try:
        logger.info(
            f"Manual sprint notification requested for: "
            f"{notification_request.sprint_name}"
        )

        service = JiraSprintNotificationService(slack_token=settings.bot_token)

        result = await service.send_notification(
            channel_id=notification_request.channel_id,
            sprint_name=notification_request.sprint_name,
            start_date=notification_request.start_date,
            end_date=notification_request.end_date,
            completed_by=notification_request.completed_by,
        )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Sprint notification sent successfully",
                "sprint_name": notification_request.sprint_name,
                "channel_id": notification_request.channel_id,
                "slack_response": result,
            },
        )

    except SprintNotificationError as e:
        logger.error(f"Failed to send manual notification: {str(e)}")

        RollbarService.report_error(
            exc=e,
            request=request,
            extra_data={
                "operation": "manual_sprint_notification",
                "sprint_name": notification_request.sprint_name,
            },
        )

        raise HTTPException(
            status_code=500, detail=f"Failed to send notification: {str(e)}"
        )

    except Exception as e:
        logger.error(
            f"Unexpected error in manual notification: {str(e)}", exc_info=True
        )

        RollbarService.report_error(
            exc=e,
            request=request,
            extra_data={
                "operation": "manual_sprint_notification",
                "sprint_name": notification_request.sprint_name,
            },
        )

        raise HTTPException(status_code=500, detail="Internal server error")
