# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (first time)
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run CLI scripts
pr-reminder [--dry-run]
jira-overdue-reminder

# Bump package version before merging to main
./scripts/bump_version.sh [major|minor|patch]   # defaults to patch

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

Create a `.env` file with these keys:

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

### Package Structure

The installable package lives in `src/review_request/`. It has no web framework dependency — consumers call the services directly from their own application.

```
services/       core business logic (GitHub, Slack, SendMessage, PRReminderService, …)
decorators/     randomised Slack message templates (BaseMessageDecorator pattern)
serializers/    pydantic models for Slack and Jira payloads
config/         settings (pydantic-settings) + hardcoded team/channel/repo mappings
utils/          date checking, logging helpers, validation
scripts/        CLI entry points (pr-reminder, jira-overdue-reminder)
```

### Key Services

**`SendMessage`** (`services/send_message.py`) — orchestrates a slash command review request end-to-end:
1. Parses Slack message text via regex (extracts user IDs, channel IDs, group IDs, PR URLs, optional `--scheduled=` date)
2. Fetches PR title + requested reviewer teams from GitHub
3. Formats reviewers (Slack user mentions, subteam mentions, or falls back to GitHub PR reviewers)
4. Posts or schedules the message via Slack

**`PRReminderService`** (`services/pr_reminder_service.py`) — daily reminder flow:
1. Checks `DateChecker.should_send_reminder()` against configured days
2. Fetches open PRs for a GitHub team across all `GITHUB_REPOSITORIES`
3. Builds a digest message via `RandomRemindReviewMessagesDecorator`
4. Posts to the team's Slack channel

### Message Decorator Pattern (`decorators/`)

`BaseMessageDecorator` selects a random template from `get_templates()` and fills it using `get_template_placeholders()`. Subclasses implement those two methods. This produces varied, friendly messages without branching logic in callers.

### Configuration (`config/settings.py`)

- `Settings` (pydantic `BaseSettings`) — reads from env / `.env` file.
- `SLACK_TEAM_MAPPINGS` — hardcoded `@handle → Slack group ID` used when a GitHub PR reviewer handle needs to be mentioned in Slack.
- `GITHUB_REPOSITORIES` — list of repos scanned by the reminder script.
- `GITHUB_TEAM_REMINDER_MAPPING` / `JIRA_TEAM_REMINDER_MAPPING` — per-team config (channel, Slack group, GitHub team slug, reminder days).

### Caching & Retry

- `services/cache_service.py` wraps `cachetools.TTLCache`; used by `GitHub` (TTL 300 s, max 200 entries) and `SendMessage` (usergroup map, TTL 24 h).
- All external API calls (GitHub, Slack) use `tenacity` with 3 attempts and exponential back-off (4–10 s).

### Publishing

Merging to `main` triggers `.github/workflows/publish.yml`, which builds the package and publishes to PyPI via OIDC trusted publishing. Always run `./scripts/bump_version.sh` before merging so PyPI does not reject a duplicate version.
