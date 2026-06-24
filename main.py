from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
import logging.handlers
from datetime import datetime
from review_request.routes.api import api_router
from slack_sdk.signature import SignatureVerifier
from review_request.config.settings import settings
from review_request.services.rollbar_service import RollbarService
import sys


def setup_logging() -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        "app.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(detailed_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logging()

RollbarService.initialize()

app = FastAPI(title="Slack bot request review", debug=False)
app.include_router(api_router)

app.mount("/static", StaticFiles(directory="."), name="static")


@app.get("/bot-icon.png")
async def get_bot_icon():
    return FileResponse("bot-icon.png")


@app.get("/jira-overdue-bot.png")
async def get_jira_overdue_bot_icon():
    return FileResponse("jira-overdue-bot.png")


@app.middleware("http")
async def verify_slack_request(request: Request, call_next):
    slack_signature = request.headers.get("x-slack-signature")
    slack_request_timestamp = request.headers.get("x-slack-request-timestamp")

    if not settings.slack_signing_secret or not request.url.path.startswith(
        "/conversation"
    ):
        response = await call_next(request)
        return response

    if not slack_signature or not slack_request_timestamp:
        raise HTTPException(
            status_code=400, detail="Missing Slack signature or timestamp"
        )

    request_body = await request.body()
    request.state.body = request_body

    verifier = SignatureVerifier(signing_secret=settings.slack_signing_secret)
    if not verifier.is_valid(
        body=request_body, timestamp=slack_request_timestamp, signature=slack_signature
    ):
        raise HTTPException(status_code=400, detail="Invalid Slack signature")

    response = await call_next(request)
    return response


@app.middleware("http")
async def log_traffic(request: Request, call_next):
    start_time = datetime.now()

    request_body = getattr(request.state, "body", b"")
    if not request_body:
        request_body = await request.body()

    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()
    client_host = request.client.host if request.client else "unknown"

    log_params = {
        "request_method": request.method,
        "request_url": str(request.url),
        "request_size": request.headers.get("content-length"),
        "request_headers": dict(request.headers),
        "request_body": request_body.decode("utf-8", errors="ignore"),
        "response_status": response.status_code,
        "response_size": response.headers.get("content-length"),
        "response_headers": dict(response.headers),
        "process_time": process_time,
        "client_host": client_host,
    }
    logger.info(log_params)
    return response


@app.middleware("http")
async def error_monitoring(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        RollbarService.report_error(
            exc=exc,
            request=request,
            extra_data={
                "endpoint": str(request.url),
                "method": request.method,
                "user_agent": request.headers.get("user-agent"),
            },
        )
        raise exc
