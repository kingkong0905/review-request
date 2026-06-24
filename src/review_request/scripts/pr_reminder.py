#!/usr/bin/env python3
"""
PR Reminder Script

Fetches open pull requests from configured GitHub repositories
and sends reminder messages to Slack channels for teams with pending reviews.

Usage:
    pr-reminder [--dry-run] [--config PATH]
    python -m review_request.scripts.pr_reminder [--dry-run] [--config PATH]

Config file format (JSON):
    {
        "repositories": [
            {"url": "https://github.com/org/repo", "base_branch": "main"}
        ],
        "team_reminder_mapping": [
            {
                "channel_id": "C123456",
                "slack_group_id": "S123456",
                "github_team": "my-team",
                "max_age_pr_days": 60,
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
from typing import Dict, Any, List

from dotenv import load_dotenv

from review_request.services.pr_reminder_service import PRReminderService

load_dotenv()


def setup_logging() -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    file_handler = logging.FileHandler("pr_reminder.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


def load_config(config_path: str) -> Dict[str, Any]:
    if not os.path.exists(config_path):
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)
    with open(config_path) as f:
        return json.load(f)


def validate(
    github_token: str, bot_token: str, repositories: List, team_mapping: List
) -> bool:
    errors = []
    if not github_token:
        errors.append("Missing GITHUB_TOKEN")
    if not bot_token:
        errors.append("Missing BOT_TOKEN")
    if not repositories:
        errors.append("'repositories' is empty in config")
    if not team_mapping:
        errors.append("'team_reminder_mapping' is empty in config")
    for err in errors:
        print(f"Error: {err}")
    return len(errors) == 0


async def process_team_reminders(
    reminder_service: PRReminderService,
    team_mapping: List[Dict[str, Any]],
    dry_run: bool = False,
) -> Dict[str, Any]:
    results: Dict[str, Any] = {
        "total_teams": len(team_mapping),
        "successful_teams": 0,
        "failed_teams": 0,
        "total_prs": 0,
        "errors": [],
    }
    logger = logging.getLogger(__name__)

    for i, team_config in enumerate(team_mapping):
        team_name = team_config.get("github_team", f"team_{i}")
        logger.info(f"Processing team: {team_name}")
        try:
            message = await reminder_service.generate_reminder_message(team_config)
            if message:
                results["total_prs"] += message.count("• [")
                success = await reminder_service.send_reminder(team_config, dry_run)
                if success:
                    results["successful_teams"] += 1
                else:
                    results["failed_teams"] += 1
                    results["errors"].append(f"Failed to send reminder for {team_name}")
            else:
                results["successful_teams"] += 1
                logger.info(f"No PRs found for team {team_name}")
        except Exception as e:
            results["failed_teams"] += 1
            results["errors"].append(f"Error processing {team_name}: {str(e)}")
            logger.error(f"Error processing {team_name}: {str(e)}")

    return results


async def main() -> None:
    parser = argparse.ArgumentParser(description="Send PR reminders to Slack teams")
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
    logger.info("Starting PR reminder script")

    config = load_config(args.config)
    repositories = config.get("repositories", [])
    team_mapping = config.get("team_reminder_mapping", [])

    github_token = os.environ.get("GITHUB_TOKEN", "")
    bot_token = os.environ.get("BOT_TOKEN", "")
    app_url = os.environ.get("APP_URL", "")

    if not validate(github_token, bot_token, repositories, team_mapping):
        sys.exit(1)

    try:
        service = PRReminderService(
            github_token=github_token,
            slack_token=bot_token,
            repositories=repositories,
            app_url=app_url,
        )
        results = await process_team_reminders(service, team_mapping, args.dry_run)

        logger.info(
            f"Teams processed: {results['total_teams']}, "
            f"successful: {results['successful_teams']}, "
            f"failed: {results['failed_teams']}, "
            f"total PRs: {results['total_prs']}"
        )

        if results["errors"]:
            for err in results["errors"]:
                logger.error(f"  - {err}")

        sys.exit(1 if results["failed_teams"] > 0 else 0)

    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        sys.exit(1)


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
