#!/usr/bin/env python3
"""
PR Reminder Script

Fetches open pull requests from configured GitHub repositories
and sends reminder messages to Slack channels for teams with pending reviews.

Usage:
    pr-reminder [--dry-run]
    python -m review_request.scripts.pr_reminder [--dry-run]
"""

import sys
import asyncio
import logging
import argparse
from typing import Dict, Any

from review_request.config.settings import (
    settings,
    GITHUB_TEAM_REMINDER_MAPPING,
    GITHUB_REPOSITORIES,
)
from review_request.services.pr_reminder_service import PRReminderService
from review_request.services.rollbar_service import RollbarService


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


def validate_environment() -> bool:
    required_vars = ["GITHUB_TOKEN", "BOT_TOKEN"]
    missing_vars = [
        var for var in required_vars if not getattr(settings, var.lower(), None)
    ]

    if missing_vars:
        print(
            f"Error: Missing required environment variables: {', '.join(missing_vars)}"
        )
        print("Please set these variables in your .env file or environment")
        return False

    return True


def validate_config() -> bool:
    if not GITHUB_REPOSITORIES:
        print("Error: GITHUB_REPOSITORIES is empty or not configured")
        return False

    for i, repo in enumerate(GITHUB_REPOSITORIES):
        if not isinstance(repo, dict):
            print(f"Error: Repository {i} is not a dictionary")
            return False
        if "url" not in repo or "base_branch" not in repo:
            print(f"Error: Repository {i} missing 'url' or 'base_branch'")
            return False

    if not GITHUB_TEAM_REMINDER_MAPPING:
        print("Error: GITHUB_TEAM_REMINDER_MAPPING is empty or not configured")
        return False

    for i, team_config in enumerate(GITHUB_TEAM_REMINDER_MAPPING):
        required_keys = ["channel_id", "slack_group_id", "github_team"]
        missing_keys = [key for key in required_keys if key not in team_config]

        if missing_keys:
            print(
                f"Error: Team configuration {i} is missing required keys: {', '.join(missing_keys)}"
            )
            return False

    return True


async def process_team_reminders(
    reminder_service: PRReminderService, dry_run: bool = False
) -> Dict[str, Any]:
    results: Dict[str, Any] = {
        "total_teams": len(GITHUB_TEAM_REMINDER_MAPPING),
        "successful_teams": 0,
        "failed_teams": 0,
        "teams_with_prs": 0,
        "total_prs": 0,
        "errors": [],
    }

    logger = logging.getLogger(__name__)

    for i, team_config in enumerate(GITHUB_TEAM_REMINDER_MAPPING):
        team_name = team_config.get("github_team", f"team_{i}")
        logger.info(f"Processing team: {team_name}")

        try:
            message = await reminder_service.generate_reminder_message(team_config)

            if message:
                pr_count = message.count("• [")
                results["total_prs"] += pr_count
                results["teams_with_prs"] += 1

                logger.info(f"Found {pr_count} PRs for team {team_name}")

                success = await reminder_service.send_reminder(team_config, dry_run)

                if success:
                    results["successful_teams"] += 1
                    logger.info(f"Successfully processed team {team_name}")
                else:
                    results["failed_teams"] += 1
                    results["errors"].append(
                        f"Failed to send reminder for team {team_name}"
                    )
                    logger.error(f"Failed to send reminder for team {team_name}")
            else:
                results["successful_teams"] += 1
                logger.info(f"No PRs found for team {team_name}")

        except Exception as e:
            results["failed_teams"] += 1
            error_msg = f"Error processing team {team_name}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)

    return results


async def main() -> None:
    parser = argparse.ArgumentParser(description="Send PR reminders to Slack teams")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually send messages, just show what would be sent",
    )
    args = parser.parse_args()

    logger = setup_logging()

    RollbarService.initialize()

    logger.info("Starting PR reminder script")
    logger.info(f"Dry run mode: {args.dry_run}")

    if not validate_environment():
        sys.exit(1)

    if not validate_config():
        sys.exit(1)

    try:
        reminder_service = PRReminderService(settings.github_token, settings.bot_token)
        results = await process_team_reminders(reminder_service, args.dry_run)

        logger.info("PR Reminder Script Summary:")
        logger.info(f"  Total teams configured: {results['total_teams']}")
        logger.info(f"  Teams with PRs: {results['teams_with_prs']}")
        logger.info(f"  Successful teams: {results['successful_teams']}")
        logger.info(f"  Failed teams: {results['failed_teams']}")

        if results["errors"]:
            logger.error("Errors encountered:")
            for error in results["errors"]:
                logger.error(f"  - {error}")

        if results["failed_teams"] > 0:
            logger.error("Script completed with errors")
            sys.exit(1)
        else:
            logger.info("Script completed successfully")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Script failed with error: {str(e)}")
        RollbarService.report_error(
            exc=e, extra_data={"script": "pr_reminder", "dry_run": args.dry_run}
        )
        sys.exit(1)


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
