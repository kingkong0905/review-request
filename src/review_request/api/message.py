from fastapi import APIRouter, Form, Request
from review_request.services.send_message import SendMessage
from review_request.serializers.conversation_response import ConversationResponse
from review_request.services.rollbar_service import RollbarService
from fastapi.responses import JSONResponse
from typing import Union
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=ConversationResponse)
async def conversation(
    request: Request,
    token: str = Form(...),
    team_id: str = Form(...),
    team_domain: str = Form(...),
    channel_id: str = Form(...),
    channel_name: str = Form(...),
    user_id: str = Form(...),
    user_name: str = Form(...),
    command: str = Form(...),
    text: str = Form(...),
    response_url: str = Form(...),
    trigger_id: str = Form(...),
) -> Union[ConversationResponse, JSONResponse]:
    try:
        RollbarService.add_person_data(user_id=user_id, username=user_name)
        RollbarService.add_custom_data("team_id", team_id)
        RollbarService.add_custom_data("channel_id", channel_id)
        RollbarService.add_custom_data("command", command)

        logger.info(
            f"Processing request from user {user_id} ({user_name}) in channel {channel_name}"
        )

        message_service = SendMessage(user_id, text, channel_id)
        await message_service.send()

        logger.info(f"Successfully processed request from user {user_id}")

        return ConversationResponse(
            response_type="ephemeral",
            text=":white_check_mark: Your request has been submitted successfully.",
        )
    except ValueError as e:
        logger.warning(f"Validation error for user {user_id}: {str(e)}")

        RollbarService.report_error(
            exc=e,
            request=request,
            extra_data={
                "user_id": user_id,
                "user_name": user_name,
                "channel_name": channel_name,
                "error_type": "validation_error",
            },
            level="warning",
        )

        return JSONResponse(
            status_code=200,
            content=ConversationResponse(
                response_type="ephemeral", text=":alert: " + str(e)
            ).model_dump(),
        )
    except Exception as e:
        logger.error(
            f"Unexpected error processing request from user {user_id}: {str(e)}",
            exc_info=True,
        )

        RollbarService.report_error(
            exc=e,
            request=request,
            extra_data={
                "user_id": user_id,
                "user_name": user_name,
                "channel_name": channel_name,
                "error_type": "unexpected_error",
            },
        )

        return JSONResponse(
            status_code=200,
            content=ConversationResponse(
                response_type="ephemeral",
                text=":alert: An unexpected error occurred. Please try again.",
            ).model_dump(),
        )
    finally:
        RollbarService.clear_person_data()
        RollbarService.clear_custom_data()
