from typing import Dict, List, Any, Optional
import logging
from urllib.parse import urlparse
from review_request.services.github import GitHub
from review_request.services.slack import Slack
from review_request.decorators.random_remind_review_messages import (
    RandomRemindReviewMessagesDecorator,
)
from review_request.utils.date_checker import DateChecker

logger = logging.getLogger(__name__)


class PRReminderError(Exception):
    pass


class PRReminderService:
    """Service for fetching and formatting PR reminders for Slack."""

    def __init__(
        self,
        github_token: str,
        slack_token: str,
        repositories: List[Dict[str, str]],
        app_url: str = "",
    ):
        self.github_token = github_token
        self.slack_token = slack_token
        self.repositories = repositories
        self.app_url = app_url

    def _get_bot_icon_url(self) -> str:
        base = self.app_url.strip().rstrip("/")
        if base:
            return f"{base}/bot-icon.png"
        return "https://github.com/github.png"

    def _parse_repo_url(self, repo_url: str) -> tuple[str, str]:
        try:
            if repo_url.startswith("https://github.com/"):
                path = urlparse(repo_url).path.strip("/")
            elif repo_url.startswith("git@github.com:"):
                path = repo_url.replace("git@github.com:", "").replace(".git", "")
            else:
                raise PRReminderError(f"Unsupported repository URL format: {repo_url}")

            parts = path.split("/")
            if len(parts) != 2:
                raise PRReminderError(f"Invalid repository path: {path}")

            return parts[0], parts[1]
        except Exception as e:
            raise PRReminderError(
                f"Failed to parse repository URL {repo_url}: {str(e)}"
            )

    async def _get_prs_for_repo(
        self,
        repo_config: Dict[str, str],
        team_slug: str,
        max_age_days: Optional[int] = None,
    ) -> List[Dict]:
        try:
            repo_url = repo_config["url"]
            base_branch = repo_config["base_branch"]
            org, repo = self._parse_repo_url(repo_url)

            try:
                async with GitHub(self.github_token, org, repo, "dummy") as github:
                    prs = await github.get_team_review_requests(
                        team_slug, base_branch, max_age_days
                    )
                    return prs
            except Exception as e:
                logger.warning(
                    f"Failed to get PRs for {org}/{repo} base {base_branch}: {str(e)}"
                )
                return []

        except PRReminderError as e:
            logger.error(f"Failed to process repository {repo_config}: {str(e)}")
            return []

    def _format_pr_message(self, pr: Dict, repo_name: str) -> str:
        try:
            title = pr.get("title", "Untitled")
            author = pr.get("user", {}).get("login", "Unknown")
            html_url = pr.get("html_url", "#")
            created_at = pr.get("created_at", "")

            github = GitHub(self.github_token, "dummy", "dummy", "dummy")
            age = github.calculate_pr_age(created_at)
            review_status = self._get_review_status(pr)

            return f"• <{html_url}|{title}> - by @{author} - {age} - {review_status}"
        except Exception as e:
            logger.error(f"Failed to format PR {pr.get('number', 'unknown')}: {str(e)}")
            return f"• [Error formatting PR] - {pr.get('html_url', '#')}"

    def _get_review_status(self, pr: Dict) -> str:
        reviews = pr.get("reviews", [])
        if any(review.get("state") == "APPROVED" for review in reviews):
            return "Approved"
        elif any(review.get("state") == "CHANGES_REQUESTED" for review in reviews):
            return "Changes requested"
        else:
            return "Waiting for review"

    async def _get_slack_group_id(self, slack_group_id: str) -> str:
        try:
            slack = Slack(self.slack_token, [])
            usergroups = await slack.get_slack_usergroups()
            return usergroups.get(slack_group_id, slack_group_id)
        except Exception as e:
            logger.warning(
                f"Failed to get Slack group ID for {slack_group_id}: {str(e)}"
            )
            return slack_group_id

    async def generate_reminder_message(
        self, team_config: Dict[str, Any]
    ) -> Optional[str]:
        try:
            channel_id = team_config.get("channel_id")
            slack_group_id = team_config.get("slack_group_id", "")
            github_team = team_config.get("github_team", "")
            max_age_days = team_config.get("max_age_pr_days")

            if not all([channel_id, github_team]):
                logger.warning(f"Incomplete team configuration: {team_config}")
                return None

            repos = self.repositories
            slack_subteam_id = await self._get_slack_group_id(slack_group_id)

            all_prs_by_repo = {}
            total_prs = 0

            for repo_config in repos:
                try:
                    prs = await self._get_prs_for_repo(
                        repo_config, github_team, max_age_days
                    )
                    if prs:
                        repo_name = self._parse_repo_url(repo_config["url"])[1]
                        all_prs_by_repo[repo_name] = prs
                        total_prs += len(prs)
                except Exception as e:
                    logger.error(f"Failed to get PRs for {repo_config}: {str(e)}")
                    continue

            if total_prs == 0:
                return None

            review_message_data = {"team_id": slack_subteam_id, "total_pr": total_prs}
            decorator = RandomRemindReviewMessagesDecorator(review_message_data)
            header_message = decorator.message()

            message_parts = [header_message, ""]

            for repo_name, prs in all_prs_by_repo.items():
                message_parts.append(f"Repository: {repo_name}")
                for pr in prs:
                    pr_line = self._format_pr_message(pr, repo_name)
                    message_parts.append(pr_line)
                message_parts.append("")

            return "\n".join(message_parts).strip()

        except Exception as e:
            logger.error(f"Failed to generate reminder message: {str(e)}")
            return None

    async def send_reminder(
        self, team_config: Dict[str, Any], dry_run: bool = False
    ) -> bool:
        try:
            remind_dates = team_config.get("remind_date", [])
            if not DateChecker.should_send_reminder(remind_dates):
                logger.info(
                    f"Skipping reminder for team {team_config.get('github_team', 'unknown')} - "
                    f"not a configured reminder day"
                )
                return True

            message = await self.generate_reminder_message(team_config)
            if not message:
                logger.info(
                    f"No PRs found for team {team_config.get('github_team', 'unknown')}"
                )
                return True

            if dry_run:
                logger.info(
                    f"DRY RUN - Would send message to {team_config.get('channel_id')}:"
                )
                logger.info(f"Message: {message}")
                return True

            channel_id = team_config.get("channel_id")
            if not channel_id:
                raise PRReminderError("Channel ID is required for sending messages")
            slack = Slack(self.slack_token, [channel_id])

            bot_icon_url = self._get_bot_icon_url()
            user_info = {
                "real_name": "Code Review",
                "profile": {"image_48": bot_icon_url},
            }

            await slack.chat_post_message(message, user_info)
            logger.info(f"Sent reminder message to {channel_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send reminder: {str(e)}")
            return False
