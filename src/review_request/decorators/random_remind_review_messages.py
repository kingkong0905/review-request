"""Random remind review messages decorator."""

from typing import Dict, Any, List
from .base_message_decorator import BaseMessageDecorator
from .message_templates import RemindReviewMessageTemplates


class RandomRemindReviewMessagesDecorator(BaseMessageDecorator):
    def __init__(self, review_message: Dict[str, Any]) -> None:
        super().__init__(review_message)
        self.team_id: str = review_message.get("team_id", "")
        self.total_pr: int = review_message.get("total_pr", 0)

    def get_templates(self) -> List[str]:
        return RemindReviewMessageTemplates.TEMPLATES

    def get_template_placeholders(self) -> Dict[str, Any]:
        return self.formatter.format_remind_message_placeholders(
            team_id=self.team_id, total_pr=self.total_pr
        )
