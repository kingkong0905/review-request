"""Abstract base class for message decorators."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import random
from .message_formatters import MessageFormatter


class BaseMessageDecorator(ABC):
    """Abstract base class for message decorators."""

    def __init__(self, review_message: Dict[str, Any]) -> None:
        self.review_message = review_message
        self.formatter = MessageFormatter()

    @abstractmethod
    def get_templates(self) -> List[str]:
        pass

    @abstractmethod
    def get_template_placeholders(self) -> Dict[str, Any]:
        pass

    def _select_random_template(self) -> str:
        templates = self.get_templates()
        return random.choice(templates)

    def _format_template(self, template: str) -> str:
        placeholders = self.get_template_placeholders()
        return template.format(**placeholders)

    def message(self) -> str:
        selected_template = self._select_random_template()
        return self._format_template(selected_template)
