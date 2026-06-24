from dataclasses import dataclass
from typing import List, Optional, Dict
import logging
from slack_sdk.web.async_client import AsyncWebClient
from datetime import datetime, timedelta
import pytz
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio

logger = logging.getLogger(__name__)


class SlackError(Exception):
    pass


@dataclass
class MessageConfig:
    channel: str
    text: str
    post_at: Optional[int] = None


class Slack:
    """Service class for handling Slack API interactions."""

    def __init__(self, token: str, channel_ids: List[str]):
        self.token = token
        self.channel_ids = channel_ids
        self.client = self._init_client()

    def _init_client(self) -> AsyncWebClient:
        return AsyncWebClient(token=self.token)

    def _validate_message(self, message: str) -> None:
        if not message or not isinstance(message, str):
            raise SlackError("Invalid message content")

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_slack_usergroups(self) -> Dict[str, str]:
        try:
            result = await self.client.usergroups_list()
            return {f"@{ug['handle']}": ug["id"] for ug in result["usergroups"]}
        except Exception as e:
            logger.error(f"Failed to fetch usergroups: {e}")
            raise SlackError(f"Failed to fetch usergroups: {e}")

    async def _post_to_channel(
        self, channel: str, message: str, user_info: Dict
    ) -> None:
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=10),
        )
        async def _post():
            await self.client.chat_postMessage(
                channel=channel,
                text=message,
                icon_url=user_info["profile"]["image_48"],
                username=user_info["real_name"],
            )
            logger.info(f"Message posted to channel {channel}")

        await _post()

    async def chat_post_message(self, message: str, user_info: Dict) -> None:
        try:
            self._validate_message(message)

            if len(self.channel_ids) > 1:
                tasks = [
                    self._post_to_channel(channel, message, user_info)
                    for channel in self.channel_ids
                ]
                await asyncio.gather(*tasks, return_exceptions=False)
            elif len(self.channel_ids) == 1:
                await self._post_to_channel(self.channel_ids[0], message, user_info)

        except Exception as e:
            logger.error(f"Failed to post message: {e}")
            raise SlackError(f"Failed to post message: {e}")

    async def _schedule_to_channel(
        self, channel: str, message: str, post_at: int
    ) -> None:
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=10),
        )
        async def _schedule():
            await self.client.chat_scheduleMessage(
                channel=channel, text=message, post_at=post_at
            )
            logger.info(f"Message scheduled for channel {channel} at {post_at}")

        await _schedule()

    async def chat_schedule_message(self, message: str, delay_hours: float) -> None:
        try:
            self._validate_message(message)
            post_at = int((datetime.now() + timedelta(hours=delay_hours)).timestamp())

            if len(self.channel_ids) > 1:
                tasks = [
                    self._schedule_to_channel(channel, message, post_at)
                    for channel in self.channel_ids
                ]
                await asyncio.gather(*tasks, return_exceptions=False)
            elif len(self.channel_ids) == 1:
                await self._schedule_to_channel(self.channel_ids[0], message, post_at)

        except Exception as e:
            logger.error(f"Failed to schedule message: {e}")
            raise SlackError(f"Failed to schedule message: {e}")

    async def chat_schedule_message_with_timezone(
        self, message: str, scheduled_date: str
    ) -> None:
        try:
            self._validate_message(message)
            gmt7 = pytz.timezone("Asia/Bangkok")
            utc = pytz.UTC

            local_dt = datetime.strptime(scheduled_date, "%Y/%m/%d %H:%M:%S")
            local_dt = gmt7.localize(local_dt)
            utc_dt = local_dt.astimezone(utc)
            post_at = int(utc_dt.timestamp())

            if len(self.channel_ids) > 1:
                tasks = [
                    self._schedule_to_channel(channel, message, post_at)
                    for channel in self.channel_ids
                ]
                await asyncio.gather(*tasks, return_exceptions=False)
            elif len(self.channel_ids) == 1:
                await self._schedule_to_channel(self.channel_ids[0], message, post_at)

            logger.info(
                f"Message scheduled for {len(self.channel_ids)} channel(s) at {utc_dt}"
            )
        except Exception as e:
            logger.error(f"Failed to schedule message with timezone: {e}")
            raise SlackError(f"Failed to schedule message with timezone: {e}")

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_user_info(self, user_id: str) -> Dict:
        try:
            result = await self.client.users_info(user=user_id)
            return result["user"]
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            raise SlackError(f"Failed to get user info: {e}")

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def lookup_user_by_email(self, email: str) -> Optional[str]:
        try:
            result = await self.client.users_lookupByEmail(email=email)
            user = result.get("user")
            return user.get("id") if user else None
        except Exception as e:
            logger.warning(f"Failed to lookup user by email '{email}': {e}")
            return None

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_usergroup_members(self, usergroup_id: str) -> List[str]:
        try:
            result = await self.client.usergroups_users_list(usergroup=usergroup_id)
            return result.get("users", [])
        except Exception as e:
            logger.error(f"Failed to get usergroup members for {usergroup_id}: {e}")
            return []
