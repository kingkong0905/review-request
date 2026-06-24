import random
from typing import List


class JiraOverdueMessageService:
    def __init__(self) -> None:
        pass

    def _format_team(self, slack_group_id: str) -> str:
        return f"<!subteam^{slack_group_id}>!" if slack_group_id else "team"

    def build_funny_intro(self, total_issues: int, slack_group_id: str) -> str:
        team_mention = self._format_team(slack_group_id)
        total_str = f"*{total_issues}*"
        templates: List[str] = [
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
        tpl = random.choice(templates)
        return tpl.format(team_mention=team_mention, total=total_str)
