"""Message formatters for handling dynamic content in message templates."""

from typing import Optional
from review_request.services.shuffle_service import ShuffleService


class UserMentionFormatter:
    @staticmethod
    def format_user_mention(user_id: Optional[str]) -> str:
        return f"<@{user_id}> " if user_id else ""


class TeamMentionFormatter:
    @staticmethod
    def format_team_mention(team_id: str) -> str:
        return f"<!subteam^{team_id}>!"


class ReviewersFormatter:
    @staticmethod
    def format_reviewers(formatted_reviewers: Optional[str]) -> str:
        return f"cc {formatted_reviewers}\n" if formatted_reviewers else ""


class IconFormatter:
    @staticmethod
    def get_random_icon() -> str:
        shuffled_icons = ShuffleService.shuffle_icons()
        return shuffled_icons[0] if shuffled_icons else "🎉"


class MessageFormatter:
    """Main formatter that combines all formatting utilities."""

    def __init__(self):
        self.user_formatter = UserMentionFormatter()
        self.team_formatter = TeamMentionFormatter()
        self.reviewers_formatter = ReviewersFormatter()
        self.icon_formatter = IconFormatter()

    def format_review_message_placeholders(self, **kwargs) -> dict:
        return {
            "user_mention": self.user_formatter.format_user_mention(
                kwargs.get("user_id")
            ),
            "pr_url": kwargs.get("pr_url", ""),
            "title": kwargs.get("title", ""),
            "repo_name": kwargs.get("repo_name", "").upper(),
            "reviewers_section": self.reviewers_formatter.format_reviewers(
                kwargs.get("formatted_reviewers")
            ),
            "icon": self.icon_formatter.get_random_icon(),
        }

    def format_remind_message_placeholders(self, **kwargs) -> dict:
        return {
            "team_mention": self.team_formatter.format_team_mention(
                kwargs.get("team_id", "")
            ),
            "total_pr": f"*{kwargs.get('total_pr', 0)}*",
        }
