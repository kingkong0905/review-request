"""Jira Overdue Message Decorator."""

from typing import Dict, Any, List
from .base_message_decorator import BaseMessageDecorator


class JiraOverdueMessageDecorator(BaseMessageDecorator):
    """Decorator for generating Jira overdue reminder intro messages."""

    def __init__(self, team_config: Dict[str, Any]) -> None:
        self.team_config = team_config
        self.slack_group_id = team_config.get("slack_group_id", "")
        self.total_issues = team_config.get("total_issues", 0)
        super().__init__({"type": "jira_overdue"})

    def get_templates(self) -> List[str]:
        return [
            (
                "Hey {team_mention} 👋\n"
                "⏰ {total} Jira issues are past their due date…\n"
                "Before they start a support group, let's move them forward."
            ),
            (
                "Hey {team_mention} 👋\n"
                "🧟 {total} overdue issues shambling in 'In Progress'…\n"
                "Only your action can lay them to rest."
            ),
            (
                "Hey {team_mention} 👋\n"
                "🐢 {total} tasks moving slower than Monday mornings…\n"
                "A tiny push today saves a big panic tomorrow."
            ),
            (
                "Hey {team_mention} 👋\n"
                "🧀 {total} aging like cheese… and not the fancy kind.\n"
                "Change the status before it gets… aromatic."
            ),
            (
                "Hey {team_mention} 👋\n"
                "🚨 {total} overdue issues pinging the timeline radar\n"
                "Let's clear the airspace."
            ),
            (
                "Hey {team_mention} 👋\n"
                "📦 {total} stories waiting in the delivery truck…\n"
                "A quick update and they're on the road."
            ),
            (
                "Hey {team_mention} 👋\n"
                "🕰️ {total} tickets time-traveled past their due date…\n"
                "Send them back to the present with an update."
            ),
            (
                "Hey {team_mention} 👋\n"
                "🔥 {total} smoldering tasks in 'In Progress'…\n"
                "A quick status douses the flames."
            ),
            (
                "Hey {team_mention} 👋\n"
                "🧩 {total} pieces waiting to click into Done…\n"
                "One move from you completes the puzzle."
            ),
            (
                "Hey {team_mention} 👋\n"
                "🌧️ {total} clouds hanging over the sprint…\n"
                "Mark some sunshine with a status change."
            ),
            (
                "Hey {team_mention} 👋\n"
                "📣 {total} issues calling from the backlog hotline…\n"
                "They'd like to speak to a human."
            ),
            (
                "Hey {team_mention} 👋\n"
                "🛰️ {total} signals from overdue orbit…\n"
                "Bring them back to Earth with an update."
            ),
            (
                "Hey {team_mention} 👋\n"
                "🏃 {total} tasks stuck at mile 25…\n"
                "A tiny push gets them over the finish line."
            ),
            (
                "Hey {team_mention} 👋\n"
                "🔧 {total} work-in-progress needing a quick tune-up…\n"
                "Tighten a bolt, change a status, done."
            ),
            (
                "Hey {team_mention} 👋\n"
                "📅 {total} dates came and went…\n"
                "Let's not let the sprint retrospective do all the talking."
            ),
            (
                "Hey {team_mention} 👋\n"
                "🧭 {total} tasks looking for direction…\n"
                "Point them to Done with a quick update."
            ),
        ]

    def get_template_placeholders(self) -> Dict[str, Any]:
        return {
            "team_mention": self._format_team_mention(),
            "total": f"*{self.total_issues}*",
        }

    def _format_team_mention(self) -> str:
        return f"<!subteam^{self.slack_group_id}>!" if self.slack_group_id else "team"

    def build_intro(self) -> str:
        return self.message()
