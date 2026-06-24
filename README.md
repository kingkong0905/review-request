# review-request

A Python package for automating Slack code review requests and GitHub PR reminders. Call the services directly from any Python application — no web framework dependency.

## Features

- Send Slack review request messages from a slash command payload
- Daily digest of open GitHub PRs awaiting team review
- Slack notification when a Jira sprint closes
- Slack alert for in-progress Jira issues past their due date

## Installation

```bash
pip install review-request
```

Requires Python 3.11+.

## Configuration

The package reads configuration from environment variables or a `.env` file in the working directory:

```
GITHUB_TOKEN=...
BOT_TOKEN=xoxb-...
CHANNEL_ID=C...
SLACK_SIGNING_SECRET=...
ROLLBAR_ACCESS_TOKEN=...
JIRA_SITE=https://yourorg.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=...
APP_URL=https://your-service-url    # optional, used for bot icon URL
MAX_AGE_PR_DAYS=60                  # optional, default 60
```

Team mappings and repository lists are hardcoded in `review_request/config/settings.py` — edit `GITHUB_REPOSITORIES`, `GITHUB_TEAM_REMINDER_MAPPING`, `JIRA_TEAM_REMINDER_MAPPING`, and `SLACK_TEAM_MAPPINGS` to match your organisation.

## Usage

All services are async. Call them from a route handler, background task, or any async context in your service.

### Send a review request

`SendMessage` parses a Slack slash command `text` payload, fetches the PR from GitHub, and posts or schedules a message to Slack.

```python
from review_request.services.send_message import SendMessage

async def handle_review_request(user_id: str, text: str, channel_id: str) -> None:
    await SendMessage(user_id, text, channel_id).send()
```

The `text` format:

```
<PR_URL> [@user or #channel or @group] [--scheduled=YYYY/MM/DD HH:MM:SS]
```

| Example | Behaviour |
|---|---|
| `https://github.com/org/repo/pull/123 @alice` | Posts immediately, mentions `@alice` |
| `https://github.com/org/repo/pull/123 #code-review @squad` | Posts to `#code-review`, mentions `@squad` |
| `https://github.com/org/repo/pull/123 --scheduled=2025/12/01 09:00:00` | Schedules at 09:00 GMT+7 |

If no reviewer is specified, the service falls back to the teams already requested on the GitHub PR. Up to 2 PR URLs may be submitted at once.

Raises `ValueError` for invalid input (no URL, invalid URL, too many PRs). Handle it to return a user-facing error:

```python
try:
    await SendMessage(user_id, text, channel_id).send()
except ValueError as e:
    return {"error": str(e)}
```

---

### Send a daily PR reminder

`PRReminderService` scans GitHub for open PRs assigned to a team and posts a digest to Slack.

```python
from review_request.services.pr_reminder_service import PRReminderService
from review_request.config.settings import settings

async def send_pr_reminder() -> None:
    service = PRReminderService(
        github_token=settings.github_token,
        slack_token=settings.bot_token,
    )
    team_config = {
        "channel_id": "C123456",         # Slack channel to post to
        "slack_group_id": "S123456",     # Slack usergroup to mention
        "github_team": "my-team",        # GitHub team slug
        "max_age_pr_days": 30,           # ignore PRs older than this
        "remind_date": ["Monday", "Wednesday", "Friday"],  # days to send
    }
    await service.send_reminder(team_config)
```

`send_reminder` skips posting if today is not in `remind_date` and returns `True` when nothing needs sending.

---

### Notify on Jira sprint completion

`JiraSprintNotificationService` posts a formatted sprint summary to a Slack channel.

```python
from review_request.services.jira_sprint_notification_service import (
    JiraSprintNotificationService,
    SprintNotificationError,
)
from review_request.config.settings import settings

async def notify_sprint_complete(
    channel_id: str,
    sprint_name: str,
    start_date: str,
    end_date: str,
    completed_by: str,
) -> None:
    service = JiraSprintNotificationService(slack_token=settings.bot_token)
    await service.send_notification(
        channel_id=channel_id,
        sprint_name=sprint_name,
        start_date=start_date,
        end_date=end_date,
        completed_by=completed_by,
    )

# Or process a raw Jira webhook payload (only acts on "sprint_closed" events)
async def handle_jira_webhook(channel_id: str, webhook_data: dict) -> None:
    service = JiraSprintNotificationService(slack_token=settings.bot_token)
    await service.process_webhook(channel_id=channel_id, webhook_data=webhook_data)
```

---

### Send a Jira overdue reminder

`JiraOverdueReminderService` queries Jira for in-progress issues past their due date and posts a Slack alert.

```python
from review_request.services.jira_overdue_reminder_service import JiraOverdueReminderService
from review_request.config.settings import settings

async def send_jira_overdue_reminder() -> None:
    service = JiraOverdueReminderService(
        jira_site=settings.jira_site,
        jira_email=settings.jira_email,
        jira_api_token=settings.jira_api_token,
        slack_token=settings.bot_token,
    )
    team_config = {
        "channel_id": "C123456",
        "slack_group_id": "S123456",
        "jira_jql": 'project = ET AND statusCategory = "In Progress" AND duedate < now()',
        "remind_date": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    }
    await service.send_reminder(team_config)
```

---

## CLI scripts

The package also ships two CLI commands for running reminders directly (e.g. from a cron job):

```bash
pr-reminder             # send PR digest for all configured teams
pr-reminder --dry-run   # print messages without posting to Slack
jira-overdue-reminder   # send Jira overdue alerts for all configured teams
```

---

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest                           # run all tests
pytest tests/path/test.py::fn    # run a single test
ruff check src/ && black src/    # lint and format
mypy src/                         # type check
pre-commit run --all-files        # run all pre-commit hooks
```

## Publishing

Merging to `main` automatically publishes to PyPI via GitHub Actions (OIDC trusted publishing, no stored token required).

Always bump the version before merging to avoid a duplicate version rejection:

```bash
./scripts/bump_version.sh           # patch  0.1.2 → 0.1.3
./scripts/bump_version.sh minor     # minor  0.1.2 → 0.2.0
./scripts/bump_version.sh major     # major  0.1.2 → 1.0.0
```

This updates both `pyproject.toml` and `src/review_request/__init__.py`.
