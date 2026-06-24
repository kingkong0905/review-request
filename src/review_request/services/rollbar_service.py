"""Rollbar error monitoring service."""

import rollbar
import logging
from typing import Any, Dict, Optional
from review_request.config.settings import settings

logger = logging.getLogger(__name__)


class RollbarService:
    """Service for error monitoring and reporting with Rollbar."""

    _initialized = False

    @classmethod
    def initialize(cls) -> None:
        if cls._initialized:
            return

        if not settings.rollbar_access_token:
            logger.warning(
                "Rollbar access token not configured. Error monitoring disabled."
            )
            return

        try:
            rollbar.init(
                access_token=settings.rollbar_access_token,
                environment=settings.environment,
                code_version="1.0.0",
                server_root="/app",
                capture_locals=True,
                capture_ip=True,
                capture_username=True,
            )
            cls._initialized = True
            logger.info("Rollbar initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Rollbar: {e}")

    @classmethod
    def report_error(
        cls,
        exc: Exception,
        request: Optional[Any] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        level: str = "error",
    ) -> None:
        if not cls._initialized:
            logger.warning("Rollbar not initialized. Error not reported.")
            return

        try:
            request_data = None
            if request:
                request_data = {
                    "url": str(request.url),
                    "method": request.method,
                    "headers": dict(request.headers),
                    "user_id": getattr(request, "user_id", None),
                }

            rollbar.report_exc_info(
                exc_info=(type(exc), exc, exc.__traceback__),
                request=request_data,
                extra_data=extra_data,
                level=level,
            )
            logger.info(f"Error reported to Rollbar: {type(exc).__name__}")
        except Exception as e:
            logger.error(f"Failed to report error to Rollbar: {e}")

    @classmethod
    def add_person_data(
        cls,
        user_id: str,
        username: str,
        email: Optional[str] = None,
    ) -> None:
        if not cls._initialized:
            return

        try:
            person_data: Dict[str, str] = {"id": user_id, "username": username}
            if email:
                person_data["email"] = email
            rollbar.set_person_data(person_data)
            logger.debug(f"Person data added to Rollbar: {user_id}")
        except Exception as e:
            logger.error(f"Failed to add person data to Rollbar: {e}")

    @classmethod
    def clear_person_data(cls) -> None:
        if not cls._initialized:
            return
        try:
            rollbar.clear_person_data()
            logger.debug("Person data cleared from Rollbar")
        except Exception as e:
            logger.error(f"Failed to clear person data from Rollbar: {e}")

    @classmethod
    def add_custom_data(cls, key: str, value: Any) -> None:
        if not cls._initialized:
            return
        try:
            rollbar.set_custom_data({key: value})
            logger.debug(f"Custom data added to Rollbar: {key}")
        except Exception as e:
            logger.error(f"Failed to add custom data to Rollbar: {e}")

    @classmethod
    def clear_custom_data(cls) -> None:
        if not cls._initialized:
            return
        try:
            rollbar.clear_custom_data()
            logger.debug("Custom data cleared from Rollbar")
        except Exception as e:
            logger.error(f"Failed to clear custom data from Rollbar: {e}")
