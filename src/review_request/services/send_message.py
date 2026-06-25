import validators
from review_request.services.github import GitHub
from review_request.services.slack import Slack
from review_request.decorators.random_review_message import RandomReviewMessageDecorator
from review_request.services.cache_service import CacheService
from typing import List, Optional, Dict
import logging
import re
import asyncio

logger = logging.getLogger(__name__)

USER_ID_PATTERN = re.compile(r"<@([A-Z0-9]+)\|")
CHANNEL_ID_PATTERN = re.compile(r"<#([A-Z0-9]+)(?:\|[^>]*)?>")
GROUP_ID_PATTERN = re.compile(r"<!subteam\^([A-Z0-9]+)(?:\|[^>]*)?>")

PR_URL_PATTERN = re.compile(r"https://github.com/[^/]+/[^/]+/pull/\d+")
SCHEDULED_DATE_PATTERN = re.compile(
    r"--scheduled=(\d{4}/\d{2}/\d{2}\s\d{2}:\d{2}:\d{2})"
)
GITHUB_PR_URL_PATTERN = re.compile(r"^https://github.com/[^/]+/[^/]+/pull/\d+$")
GITHUB_URL_EXTRACT_PATTERN = re.compile(
    r"https://github.com/([^/]+)/([^/]+)/pull/(\d+)"
)


class SendMessage:
    """Service for sending review request messages to Slack."""

    def __init__(
        self,
        user_id: str,
        message: str,
        github_token: str,
        bot_token: str,
        default_channel_id: str = "",
        channel_id: Optional[str] = None,
        slack_team_mappings: Optional[Dict[str, str]] = None,
    ) -> None:
        self.message: str = message
        self.user_id: str = user_id
        self.github_token: str = github_token
        self.bot_token: str = bot_token
        self.default_channel_id: str = default_channel_id
        self.channel_id: Optional[str] = channel_id
        self.slack_team_mappings: Dict[str, str] = slack_team_mappings or {}

    async def send(self) -> None:
        (
            user_ids,
            channel_ids,
            pr_urls,
            group_ids,
            scheduled_date,
        ) = await self._parse_slack_message()

        if not pr_urls:
            raise ValueError("Please provide a valid URL")

        for pr_url in pr_urls:
            if not validators.url(pr_url):
                raise ValueError("Please provide a valid URL")

        if self.user_id in user_ids:
            user_ids.remove(self.user_id)

        invalid_urls = [u for u in pr_urls if not re.match(GITHUB_PR_URL_PATTERN, u)]
        if invalid_urls:
            raise ValueError(
                "Invalid Pull Request URL. Please provide a valid GitHub PR URL."
            )

        pr_urls = list(dict.fromkeys(pr_urls))

        if len(pr_urls) > 2:
            raise ValueError(
                "You can only request a review for up to 2 pull requests at a time."
            )

        await asyncio.gather(
            *[
                self._execute_send_message(
                    channel_ids, user_ids, pr_url, group_ids, scheduled_date
                )
                for pr_url in pr_urls
            ]
        )

    async def _parse_slack_message(
        self,
    ) -> tuple[List[str], List[str], List[str], List[str], Optional[str]]:
        user_ids = USER_ID_PATTERN.findall(self.message)
        channel_ids = CHANNEL_ID_PATTERN.findall(self.message)
        group_ids = GROUP_ID_PATTERN.findall(self.message)
        pr_urls = PR_URL_PATTERN.findall(self.message)

        scheduled_date_match = SCHEDULED_DATE_PATTERN.search(self.message)
        scheduled_date = scheduled_date_match.group(1) if scheduled_date_match else None

        return user_ids, channel_ids, pr_urls, group_ids, scheduled_date

    def valid_pr_url(self, pr_detail: Dict) -> None:
        title = pr_detail.get("title")
        if not title:
            raise ValueError("Pull request do not have a title.")

    def convert_group_ids_to_subteam_format(self, group_ids: List[str]) -> str:
        return " ".join(f"<!subteam^{group_id}>" for group_id in group_ids)

    def convert_reviewers_to_subteam_format(
        self, reviewers: str, usergroup_map: Dict[str, str]
    ) -> str:
        subteams = []
        for reviewer in reviewers.split(", "):
            reviewer = reviewer.strip()
            external_id = self.slack_team_mappings.get(
                reviewer, usergroup_map.get(reviewer)
            )
            subteams.append(f"<!subteam^{external_id}>" if external_id else reviewer)
        return " ".join(subteams)

    def convert_reviewers_user_format(self, user_ids: List[str]) -> str:
        return " ".join(f"<@{user_id}>" for user_id in user_ids)

    async def _execute_send_message(
        self,
        channel_ids: List[str],
        user_ids: List[str],
        pr_url: str,
        group_ids: List[str],
        scheduled_date: Optional[str] = None,
    ) -> None:
        pr_details = await self._get_pr_details(pr_url)
        channel_ids = self._get_channel_ids(channel_ids)
        reviewers = await self._get_formatted_reviewers(
            user_ids, group_ids, pr_details["reviewers"]
        )
        message = self._create_message(pr_details, reviewers)
        await self._send_message(message, channel_ids, self.user_id, scheduled_date)

    async def _get_pr_details(self, pr_url: str) -> Dict:
        match = GITHUB_URL_EXTRACT_PATTERN.match(pr_url)
        if not match:
            raise ValueError("Invalid PR URL format")

        organization, repo, pr_number = match.groups()

        async with GitHub(self.github_token, organization, repo, pr_number) as github:
            pr_detail, pr_reviewers = await asyncio.gather(
                github.get_pr_details(),
                github.get_pr_reviewers(),
                return_exceptions=False,
            )

            self.valid_pr_url(pr_detail)

            return {
                "number": pr_number,
                "detail": pr_detail,
                "reviewers": pr_reviewers,
                "url": pr_url,
            }

    def _get_channel_ids(self, channel_ids: List[str]) -> List[str]:
        if channel_ids:
            return channel_ids
        if self.channel_id:
            return [self.channel_id]
        return [self.default_channel_id] if self.default_channel_id else []

    async def _get_formatted_reviewers(
        self, user_ids: List[str], group_ids: List[str], pr_reviewers: str
    ) -> str:
        reviewer_parts = []

        if user_ids:
            reviewer_parts.append(self.convert_reviewers_user_format(user_ids))

        if group_ids:
            reviewer_parts.append(self.convert_group_ids_to_subteam_format(group_ids))

        if reviewer_parts:
            return " ".join(reviewer_parts)

        usergroup_map = await self._get_usergroup_map()
        return self.convert_reviewers_to_subteam_format(pr_reviewers, usergroup_map)

    async def _get_usergroup_map(self) -> Dict[str, str]:
        cache_service = CacheService(ttl=86400)
        key_caching = "usergroup_map_caching"
        usergroup_map = cache_service.get(key_caching)

        if not usergroup_map:
            slack = Slack(self.bot_token, [])
            usergroup_map = await slack.get_slack_usergroups()
            if usergroup_map:
                cache_service.set(key_caching, usergroup_map)

        return usergroup_map or {}

    def _create_message(self, pr_details: Dict, reviewers: str) -> str:
        match = GITHUB_URL_EXTRACT_PATTERN.match(pr_details["url"])
        repo_name = match.group(2) if match else ""

        return RandomReviewMessageDecorator(
            review_message={
                "id": pr_details["number"],
                "user_id": self.user_id,
                "pr_url": pr_details["url"],
                "title": pr_details["detail"].get("title"),
                "repo_name": repo_name,
                "formatted_reviewers": reviewers,
            }
        ).message()

    async def _send_message(
        self,
        message: str,
        channel_ids: List[str],
        user_id: str,
        scheduled_date: Optional[str] = None,
    ) -> None:
        slack = Slack(self.bot_token, channel_ids)
        user_info = await slack.get_user_info(user_id)
        if scheduled_date:
            await slack.chat_schedule_message_with_timezone(message, scheduled_date)
        else:
            await slack.chat_post_message(message, user_info)
