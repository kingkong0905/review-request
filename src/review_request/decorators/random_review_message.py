"""Random review message decorator."""

from typing import Dict, Any, List
from .base_message_decorator import BaseMessageDecorator
from .message_templates import ReviewMessageTemplates


class RandomReviewMessageDecorator(BaseMessageDecorator):
    def __init__(self, review_message: Dict[str, Any]) -> None:
        super().__init__(review_message)
        self.user_id: str = review_message.get("user_id", "")
        self.title: str = review_message.get("title", "")
        self.pr_url: str = review_message.get("pr_url", "")
        self.repo_name: str = review_message.get("repo_name", "")
        self.formatted_reviewers: str = review_message.get("formatted_reviewers", "")

    def get_templates(self) -> List[str]:
        return ReviewMessageTemplates.TEMPLATES

    def get_template_placeholders(self) -> Dict[str, Any]:
        return self.formatter.format_review_message_placeholders(
            user_id=self.user_id,
            pr_url=self.pr_url,
            title=self.title,
            repo_name=self.repo_name,
            formatted_reviewers=self.formatted_reviewers,
        )
