"""Utility module for date and day-based checks."""

import logging
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)


class DateChecker:
    """Utility class for date-based reminder checks."""

    DAY_NAME_MAP = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6,
    }

    @staticmethod
    def should_send_reminder(remind_dates: Optional[List[str]]) -> bool:
        if not remind_dates:
            return True

        try:
            today = datetime.now()
            current_weekday = today.weekday()
            current_day_name = list(DateChecker.DAY_NAME_MAP.keys())[current_weekday]
            is_reminder_day = current_day_name in remind_dates

            if is_reminder_day:
                logger.info(
                    f"Today is {current_day_name}, sending reminder. "
                    f"Configured reminder dates: {remind_dates}"
                )
            else:
                logger.info(
                    f"Today is {current_day_name}, skipping reminder. "
                    f"Configured reminder dates: {remind_dates}"
                )

            return is_reminder_day

        except Exception as e:
            logger.error(f"Error checking reminder date: {str(e)}")
            return True
