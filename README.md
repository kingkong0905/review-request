# review-request

A Slack bot and GitHub integration for automating code review requests. Engineers use a Slack slash command to broadcast a PR review request to their channel; a scheduled script scans GitHub for open PRs and reminds teams daily; a Jira webhook posts sprint completion summaries.

## Features

- **Slash command** — `/review [PR URL] [@reviewer or #channel] [--scheduled=YYYY/MM/DD HH:MM:SS]`
- **Daily PR reminder** — scans configured GitHub repositories, finds open PRs assigned to a team, and posts a Slack digest
- **Jira sprint webhook** — posts a summary when a Jira sprint closes
- **Jira overdue reminder** — alerts a team about Jira issues that are in-progress past their due date

## Setup

**Requirements:** Python 3.11+

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Create a `.env` file:

```
GITHUB_TOKEN=...
BOT_TOKEN=xoxb-...
CHANNEL_ID=C...
SLACK_SIGNING_SECRET=...
ROLLBAR_ACCESS_TOKEN=...
JIRA_SITE=https://yourorg.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=...
APP_URL=https://your-deployment-url    # optional, for bot icon
MAX_AGE_PR_DAYS=60                     # optional, default 60
```

## Running

```bash
# Web server (Slack slash command + Jira webhooks)
uvicorn main:app --reload

# Scheduled scripts (typically run via cron)
pr-reminder [--dry-run]
jira-overdue-reminder
```

## Slash Command Usage

The bot accepts a slash command payload with the following format in the `text` field:

```
<PR_URL> [@user or #channel or @group] [--scheduled=2025/12/01 09:00:00]
```

Examples:
- `https://github.com/org/repo/pull/123 @alice #code-review` — post immediately to `#code-review` tagging `@alice`
- `https://github.com/org/repo/pull/123 @squad-eternals` — post to the invoking channel tagging the usergroup
- `https://github.com/org/repo/pull/123 --scheduled=2025/12/01 09:00:00` — schedule delivery (GMT+7)

If no reviewer is specified, the bot falls back to the team(s) already requested on the GitHub PR. Up to 2 PR URLs can be submitted in a single command.

## Configuration

Team-to-channel mappings, the list of GitHub repositories to scan, and reminder schedules are all hardcoded in `src/review_request/config/settings.py`:

- `GITHUB_REPOSITORIES` — repos scanned by `pr-reminder`
- `GITHUB_TEAM_REMINDER_MAPPING` — maps a GitHub team slug to a Slack channel and usergroup, with the days reminders should fire
- `JIRA_TEAM_REMINDER_MAPPING` — JQL query + channel mapping for the Jira overdue reminder
- `SLACK_TEAM_MAPPINGS` — overrides for Slack `@handle → group ID` when a reviewer handle appears in GitHub PR reviewer lists

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/conversation/` | Slack slash command handler |
| `POST` | `/jira/sprint/webhook?channel_id=...` | Jira sprint-closed webhook |
| `POST` | `/jira/sprint/notify` | Manual sprint completion notification |

## Development

```bash
pytest                          # run all tests
pytest tests/path/test.py::fn   # run a single test
ruff check src/ && black src/   # lint and format
mypy src/                        # type check
pre-commit run --all-files       # run all pre-commit hooks
```

## Publishing

Merging to `main` automatically publishes to PyPI via GitHub Actions using OIDC trusted publishing (no stored token required).
