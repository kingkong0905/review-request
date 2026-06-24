# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (first time)
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run server
uvicorn main:app --reload

# Run CLI scripts
pr-reminder [--dry-run]
jira-overdue-reminder

# Tests
pytest                                          # all tests
pytest tests/path/test_file.py::test_name       # single test

# Lint / format / type-check
ruff check src/
black src/
mypy src/

# Pre-commit (runs all of the above)
pre-commit run --all-files
```

## Environment

Copy `.env.example` (or create `.env`) with these keys:

| Variable | Purpose |
|---|---|
| `GITHUB_TOKEN` | GitHub API auth |
| `BOT_TOKEN` | Slack bot token |
| `CHANNEL_ID` | Default Slack channel |
| `SLACK_SIGNING_SECRET` | Validates incoming Slack requests |
| `ROLLBAR_ACCESS_TOKEN` | Error monitoring |
| `JIRA_SITE` / `JIRA_EMAIL` / `JIRA_API_TOKEN` | Jira API access |
| `APP_URL` | Public URL for bot icon (optional) |
| `MAX_AGE_PR_DAYS` | Filter PRs older than this (default: 60) |

## Architecture

### Entry Points

Two separate entry points share the same `review_request` package:

1. **FastAPI web server** (`main.py`) — receives Slack slash commands and Jira webhooks.
2. **CLI scripts** (`pr-reminder`, `jira-overdue-reminder`) — run on a schedule to push reminders proactively.

### Request Flow (Slash Command)

```
Slack slash command
  → POST /conversation/
  → middleware: verify_slack_request (HMAC signature check, only for /conversation/)
  → api/message.py: conversation()
  → services/send_message.py: SendMessage.send()
      → parse Slack message text (regex for user/channel/group/PR URL mentions)
      → services/github.py: GitHub.get_pr_details() + get_pr_reviewers()
      → decorators/random_review_message.py: build randomised message string
      → services/slack.py: Slack.chat_post_message() or chat_schedule_message_with_timezone()
```

The `--scheduled=YYYY/MM/DD HH:MM:SS` flag in the slash command text schedules delivery via Slack's API (GMT+7 timezone assumed).

### Request Flow (PR Reminder Script)

```
pr-reminder (cron)
  → scripts/pr_reminder.py: iterates GITHUB_TEAM_REMINDER_MAPPING
  → services/pr_reminder_service.py: PRReminderService
      → checks DateChecker.should_send_reminder() against configured days
      → services/github.py: GitHub.get_team_review_requests() across all GITHUB_REPOSITORIES
      → decorators/random_remind_review_messages.py: build header message
      → services/slack.py: Slack.chat_post_message()
```

### Middleware Chain (`main.py`)

Applied outermost-first (FastAPI executes last-registered first):

1. `error_monitoring` — catches unhandled exceptions, reports to Rollbar, re-raises.
2. `log_traffic` — logs full request/response metadata at INFO.
3. `verify_slack_request` — validates Slack HMAC signature; only active when `SLACK_SIGNING_SECRET` is set and path starts with `/conversation`.

### Configuration (`src/review_request/config/settings.py`)

- `Settings` (Pydantic `BaseSettings`) — reads from env / `.env` file.
- `SLACK_TEAM_MAPPINGS` — hardcoded `@handle → Slack group ID` lookup used when a Slack handle appears in a PR's reviewer list.
- `GITHUB_REPOSITORIES` — list of repos to scan for the reminder script.
- `GITHUB_TEAM_REMINDER_MAPPING` / `JIRA_TEAM_REMINDER_MAPPING` — per-team config (channel, Slack group, GitHub team slug, reminder days).

### Message Decorator Pattern (`src/review_request/decorators/`)

`BaseMessageDecorator` defines a template method: `get_templates()` returns a list of format strings, `get_template_placeholders()` returns the values. `message()` picks a random template and formats it. Subclasses implement these two methods to produce varied, friendly messages.

### Caching & Retry

- `services/cache_service.py` wraps `cachetools.TTLCache`; used by `GitHub` (TTL 300 s, max 200 entries) and `SendMessage` (usergroup map, TTL 24 h).
- All external API calls (GitHub, Slack) use `tenacity` with 3 attempts and exponential back-off (4–10 s).

### Publishing

Merging to `main` triggers `.github/workflows/publish.yml`, which builds the package and publishes to PyPI via OIDC trusted publishing (no stored token needed).
