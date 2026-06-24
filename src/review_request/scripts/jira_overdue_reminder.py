#!/usr/bin/env python3
"""
Jira Overdue Reminder Script

Queries Jira Cloud for In Progress issues that are overdue,
then sends reminder messages to Slack channels tagging assignees
who are members of the team's Slack usergroup.

Usage:
    jira-overdue-reminder [--dry-run]
    python -m review_request.scripts.jira_overdue_reminder [--dry-run]
"""

import sys
import asyncio
import logging
import argparse
from typing import Optional

from review_request.config.settings import settings, JIRA_TEAM_REMINDER_MAPPING
from review_request.services.jira_overdue_reminder_service import (
    JiraOverdueReminderService,
)
from review_request.services.rollbar_service import RollbarService
from review_request.utils.config_validator import ConfigValidator
from review_request.utils.logger_setup import LoggerSetup
from review_request.utils.reminder_result import ReminderResult


def setup_logging() -> logging.Logger:
    return LoggerSetup.setup_logger(name=__name__)


def validate_all_prerequisites() -> bool:
    logger = logging.getLogger(__name__)

    is_valid, errors = ConfigValidator.validate_all()
    for error in errors:
        logger.error(error)

    return is_valid


def initialize_services(
    logger: logging.Logger,
) -> Optional[JiraOverdueReminderService]:
    try:
        logger.info("Initializing Rollbar error tracking")
        RollbarService.initialize()
    except Exception as e:
        logger.warning(f"Failed to initialize Rollbar: {str(e)}")

    try:
        logger.info("Initializing Jira reminder service")
        reminder_service = JiraOverdueReminderService(
            settings.jira_site,
            settings.jira_email,
            settings.jira_api_token,
            settings.bot_token,
        )
        logger.info("Services initialized successfully")
        return reminder_service
    except Exception as e:
        logger.error(f"Failed to initialize reminder service: {str(e)}")
        RollbarService.report_error(
            exc=e,
            extra_data={
                "stage": "service_initialization",
                "error_type": type(e).__name__,
            },
        )
        return None


async def process_team_reminders(
    reminder_service: JiraOverdueReminderService, dry_run: bool = False
) -> ReminderResult:
    results = ReminderResult(total_teams=len(JIRA_TEAM_REMINDER_MAPPING))
    logger = logging.getLogger(__name__)

    for i, team_config in enumerate(JIRA_TEAM_REMINDER_MAPPING):
        team_name = team_config.get("name", f"team_{i}")
        logger.info(f"Processing team: {team_name}")

        try:
            try:
                message = await reminder_service.generate_reminder_message(team_config)
            except Exception as e:
                error_msg = f"Failed to generate reminder message for team {team_name}: {str(e)}"
                results.increment_failed()
                results.add_error(error_msg)
                logger.error(error_msg)
                RollbarService.report_error(
                    exc=e,
                    extra_data={
                        "team": team_name,
                        "stage": "message_generation",
                        "error_type": type(e).__name__,
                    },
                )
                continue

            if message:
                issue_count = sum(
                    1 for line in message.splitlines() if line.startswith("• ")
                )
                results.add_issues(issue_count)
                results.increment_with_issues()
                logger.info(f"Found {issue_count} overdue issues for team {team_name}")

                try:
                    success = await reminder_service.send_reminder(team_config, dry_run)
                except Exception as e:
                    error_msg = (
                        f"Failed to send reminder for team {team_name}: {str(e)}"
                    )
                    results.increment_failed()
                    results.add_error(error_msg)
                    logger.error(error_msg)
                    RollbarService.report_error(
                        exc=e,
                        extra_data={
                            "team": team_name,
                            "stage": "send_reminder",
                            "error_type": type(e).__name__,
                        },
                    )
                    continue

                if success:
                    results.increment_successful()
                    logger.info(f"Successfully processed team {team_name}")
                else:
                    results.increment_failed()
                    error_msg = f"Failed to send reminder for team {team_name}"
                    results.add_error(error_msg)
                    logger.error(error_msg)
            else:
                results.increment_successful()
                logger.info(f"No overdue issues found for team {team_name}")
        except Exception as e:
            results.increment_failed()
            error_msg = f"Unexpected error processing team {team_name}: {str(e)}"
            results.add_error(error_msg)
            logger.error(error_msg)
            RollbarService.report_error(
                exc=e,
                extra_data={
                    "team": team_name,
                    "stage": "processing",
                    "error_type": type(e).__name__,
                },
            )

    return results


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send Jira overdue reminders to Slack teams"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually send messages, just show what would be sent",
    )
    args = parser.parse_args()

    logger = setup_logging()

    logger.info("Starting Jira overdue reminder script")
    logger.info(f"Dry run mode: {args.dry_run}")

    if not validate_all_prerequisites():
        sys.exit(1)

    try:
        reminder_service = initialize_services(logger)
        if reminder_service is None:
            sys.exit(1)

        results = await process_team_reminders(reminder_service, args.dry_run)

        for line in results.get_summary().split("\n"):
            logger.info(line)

        if results.has_failures():
            logger.error("Script completed with errors")
            sys.exit(1)
        else:
            logger.info("Script completed successfully")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Script failed with error: {str(e)}")
        RollbarService.report_error(
            exc=e,
            extra_data={
                "script": "jira_overdue_reminder",
                "dry_run": args.dry_run,
                "stage": "main",
                "error_type": type(e).__name__,
            },
        )
        sys.exit(1)


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
