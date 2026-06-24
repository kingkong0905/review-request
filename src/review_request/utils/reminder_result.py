"""Result tracking for reminder scripts."""

from dataclasses import dataclass, field


@dataclass
class ReminderResult:
    """Tracks the results of reminder processing."""

    total_teams: int
    successful_teams: int = 0
    failed_teams: int = 0
    teams_with_issues: int = 0
    total_issues: int = 0
    errors: list[str] = field(default_factory=list)

    def has_failures(self) -> bool:
        return self.failed_teams > 0 or len(self.errors) > 0

    def get_summary(self) -> str:
        lines = [
            "Jira Overdue Reminder Script Summary:",
            f"  Total teams configured: {self.total_teams}",
            f"  Teams with overdue issues: {self.teams_with_issues}",
            f"  Successful teams: {self.successful_teams}",
            f"  Failed teams: {self.failed_teams}",
            f"  Total issues found: {self.total_issues}",
        ]
        if self.errors:
            lines.append("  Errors encountered:")
            for error in self.errors:
                lines.append(f"    - {error}")
        return "\n".join(lines)

    def add_error(self, error: str) -> None:
        self.errors.append(error)

    def increment_successful(self) -> None:
        self.successful_teams += 1

    def increment_failed(self) -> None:
        self.failed_teams += 1

    def increment_with_issues(self) -> None:
        self.teams_with_issues += 1

    def add_issues(self, count: int) -> None:
        self.total_issues += count
