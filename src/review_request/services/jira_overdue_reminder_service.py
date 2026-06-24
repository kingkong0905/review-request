import logging
from typing import Any, Dict, List, Optional
from review_request.services.jira import Jira
from review_request.services.slack import Slack
from review_request.decorators.jira_overdue_message import JiraOverdueMessageDecorator
from review_request.utils.date_checker import DateChecker

logger = logging.getLogger(__name__)


class JiraOverdueReminderError(Exception):
    pass


DEFAULT_JQL = 'statusCategory = "In Progress" AND duedate < now() AND type != Epic ORDER BY duedate ASC'


class JiraOverdueReminderService:
    def __init__(
        self,
        jira_site: str,
        jira_email: str,
        jira_api_token: str,
        slack_token: str,
        app_url: str = "",
    ):
        self.jira_site = jira_site
        self.jira_email = jira_email
        self.jira_api_token = jira_api_token
        self.slack_token = slack_token
        self.app_url = app_url

    def _get_bot_icon_url(self) -> str:
        base = self.app_url.strip().rstrip("/")
        if base:
            return f"{base}/jira-overdue-bot.png"
        return "https://github.com/github.png"

    def _format_issue_line(
        self,
        issue: Dict[str, Any],
        assignee_mention: str,
    ) -> str:
        key = issue.get("key", "")
        fields = issue.get("fields", {})
        summary = fields.get("summary", "Untitled")
        status = (fields.get("status") or {}).get("name", "")
        duedate = fields.get("duedate") or ""
        url = f"{self.jira_site}/browse/{key}" if key else "#"
        due_str = duedate or "no due date"
        return f"• [{key}] <{url}|{summary}> – status {status} – due {due_str} – assignee {assignee_mention}"

    async def _resolve_assignee_mention(
        self,
        slack: Slack,
        slack_group_id: str,
        assignee: Optional[Dict[str, Any]],
    ) -> str:
        if not assignee:
            return "Unassigned"
        email = assignee.get("emailAddress")
        display = assignee.get("displayName") or email or "Unassigned"
        if not email:
            return display
        try:
            uid = await slack.lookup_user_by_email(email)
            if not uid:
                return display
            members = await slack.get_usergroup_members(slack_group_id)
            if uid in members:
                return f"<@{uid}>"
            return display
        except Exception as e:
            logger.warning(f"Failed to resolve Slack mention for {email}: {e}")
            return display

    async def generate_reminder_message(
        self, team_config: Dict[str, Any]
    ) -> Optional[str]:
        try:
            channel_id = team_config.get("channel_id")
            slack_group_id = team_config.get("slack_group_id", "")
            jql = team_config.get("jira_jql") or DEFAULT_JQL

            if not channel_id:
                logger.warning(f"Incomplete team configuration: {team_config}")
                return None

            async with Jira(
                self.jira_site, self.jira_email, self.jira_api_token
            ) as jira:
                data = await jira.search_issues(jql)

            issues = data.get("issues", [])
            if not issues:
                return None

            slack = Slack(self.slack_token, [])

            total_issues = len(issues)
            decorator = JiraOverdueMessageDecorator(
                {
                    "slack_group_id": slack_group_id,
                    "total_issues": total_issues,
                }
            )
            intro = decorator.build_intro()

            lines: List[str] = [intro, ""]

            for issue in issues:
                assignee = (issue.get("fields") or {}).get("assignee")
                mention = await self._resolve_assignee_mention(
                    slack, slack_group_id, assignee
                )
                lines.append(self._format_issue_line(issue, mention))

            return "\n".join(lines).strip()
        except Exception as e:
            logger.error(f"Failed to generate Jira reminder message: {e}")
            return None

    async def send_reminder(
        self, team_config: Dict[str, Any], dry_run: bool = False
    ) -> bool:
        try:
            remind_dates = team_config.get("remind_date", [])
            if not DateChecker.should_send_reminder(remind_dates):
                logger.info(
                    "Skipping Jira reminder for team - not a configured reminder day"
                )
                return True

            message = await self.generate_reminder_message(team_config)
            if not message:
                logger.info("No overdue in-progress Jira issues for team config")
                return True

            if dry_run:
                logger.info(
                    f"DRY RUN - Would send message to {team_config.get('channel_id')}:\n{message}"
                )
                return True

            channel_id_value = team_config.get("channel_id") or ""
            if not channel_id_value:
                logger.warning("Missing channel_id in team_config")
                return False
            slack = Slack(self.slack_token, [channel_id_value])
            bot_icon_url = self._get_bot_icon_url()
            user_info = {
                "real_name": "Jira Reminder",
                "profile": {"image_48": bot_icon_url},
            }
            await slack.chat_post_message(message, user_info)
            logger.info(f"Sent Jira overdue reminder to {channel_id_value}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Jira reminder: {e}")
            return False
