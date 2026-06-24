#!/usr/bin/env python3
"""
Jira Overdue Reminder Script

Queries Jira for in-progress issues past their due date and sends Slack alerts.

Usage:
    jira-overdue-reminder [--dry-run] [--config PATH]
    python -m review_request.scripts.jira_overdue_reminder [--dry-run] [--config PATH]

Config file format (JSON):
    {
        "jira_team_reminder_mapping": [
            {
                "channel_id": "C123456",
                "slack_group_id": "S123456",
                "jira_jql": "project = ET AND statusCategory = \\"In Progress\\" AND duedate < now()",
                "remind_date": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            }
        ]
    }
"""

import sys
import os
import json
import asyncio
import logging
import argparse
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv

from review_request.services.jira_overdue_reminder_service import (
    JiraOverdueReminderService,
)
from review_request.utils.logger_setup import LoggerSetup
from review_request.utils.reminder_result import ReminderResult

load_dotenv()


def setup_logging() -> logging.Logger:
    return LoggerSetup.setup_logger(name=__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    if not os.path.exists(config_path):
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)
    with open(config_path) as f:
        return json.load(f)


def validate(
    jira_site: str,
    jira_email: str,
    jira_api_token: str,
    bot_token: str,
    team_mapping: List,
) -> bool:
    errors = []
    if not jira_site:
        errors.append("Missing JIRA_SITE")
    if not jira_email:
        errors.append("Missing JIRA_EMAIL")
    if not jira_api_token:
        errors.append("Missing JIRA_API_TOKEN")
    if not bot_token:
        errors.append("Missing BOT_TOKEN")
    if not team_mapping:
        errors.append("'jira_team_reminder_mapping' is empty in config")
    for err in errors:
        print(f"Error: {err}")
    return len(errors) == 0


def initialize_service(
    jira_site: str,
    jira_email: str,
    jira_api_token: str,
    bot_token: str,
    app_url: str,
    logger: logging.Logger,
) -> Optional[JiraOverdueReminderService]:
    try:
        return JiraOverdueReminderService(
            jira_site=jira_site,
            jira_email=jira_email,
            jira_api_token=jira_api_token,
            slack_token=bot_token,
            app_url=app_url,
        )
    except Exception as e:
        logger.error(f"Failed to initialize service: {str(e)}")
        return None


async def process_team_reminders(
    service: JiraOverdueReminderService,
    team_mapping: List[Dict[str, Any]],
    dry_run: bool = False,
) -> ReminderResult:
    results = ReminderResult(total_teams=len(team_mapping))
    logger = logging.getLogger(__name__)

    for i, team_config in enumerate(team_mapping):
        team_name = team_config.get("name", f"team_{i}")
        logger.info(f"Processing team: {team_name}")
        try:
            message = await service.generate_reminder_message(team_config)
            if message:
                issue_count = sum(
                    1 for line in message.splitlines() if line.startswith("• ")
                )
                results.add_issues(issue_count)
                results.increment_with_issues()
                success = await service.send_reminder(team_config, dry_run)
                if success:
                    results.increment_successful()
                else:
                    results.increment_failed()
                    results.add_error(f"Failed to send reminder for {team_name}")
            else:
                results.increment_successful()
                logger.info(f"No overdue issues for team {team_name}")
        except Exception as e:
            results.increment_failed()
            error_msg = f"Error processing {team_name}: {str(e)}"
            results.add_error(error_msg)
            logger.error(error_msg)

    return results


async def main() -> None:
    parser = argparse.ArgumentParser(description="Send Jira overdue reminders to Slack")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be sent without posting"
    )
    parser.add_argument(
        "--config",
        default="review_request_config.json",
        help="Path to JSON config file (default: review_request_config.json)",
    )
    args = parser.parse_args()

    logger = setup_logging()
    logger.info("Starting Jira overdue reminder script")

    config = load_config(args.config)
    team_mapping = config.get("jira_team_reminder_mapping", [])

    jira_site = os.environ.get("JIRA_SITE", "")
    jira_email = os.environ.get("JIRA_EMAIL", "")
    jira_api_token = os.environ.get("JIRA_API_TOKEN", "")
    bot_token = os.environ.get("BOT_TOKEN", "")
    app_url = os.environ.get("APP_URL", "")

    if not validate(jira_site, jira_email, jira_api_token, bot_token, team_mapping):
        sys.exit(1)

    service = initialize_service(
        jira_site, jira_email, jira_api_token, bot_token, app_url, logger
    )
    if service is None:
        sys.exit(1)

    try:
        results = await process_team_reminders(service, team_mapping, args.dry_run)
        for line in results.get_summary().split("\n"):
            logger.info(line)
        sys.exit(1 if results.has_failures() else 0)
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        sys.exit(1)


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
