"""Configuration validator for Jira overdue reminder script."""

from review_request.config.settings import settings, JIRA_TEAM_REMINDER_MAPPING


class ConfigValidator:
    """Validates configuration for the Jira overdue reminder script."""

    REQUIRED_ENV_VARS = ["jira_site", "jira_email", "jira_api_token", "bot_token"]
    REQUIRED_TEAM_CONFIG_KEYS = ["channel_id", "slack_group_id"]

    @staticmethod
    def validate_environment_variables() -> tuple[bool, list[str]]:
        errors = []

        missing = [
            name.upper()
            for name in ConfigValidator.REQUIRED_ENV_VARS
            if not getattr(settings, name, None)
        ]
        if missing:
            errors.append(
                f"Missing required environment variables: {', '.join(missing)}"
            )
            errors.append("Please set these variables in your .env file or environment")

        return (len(errors) == 0, errors)

    @staticmethod
    def validate_team_mappings() -> tuple[bool, list[str]]:
        errors = []

        if not JIRA_TEAM_REMINDER_MAPPING:
            errors.append("JIRA_TEAM_REMINDER_MAPPING is empty or not configured")
            return (False, errors)

        for i, team_config in enumerate(JIRA_TEAM_REMINDER_MAPPING):
            missing_keys = [
                k
                for k in ConfigValidator.REQUIRED_TEAM_CONFIG_KEYS
                if k not in team_config
            ]
            if missing_keys:
                errors.append(
                    f"Team configuration {i} is missing required keys: {', '.join(missing_keys)}"
                )

        return (len(errors) == 0, errors)

    @staticmethod
    def validate_all() -> tuple[bool, list[str]]:
        all_errors = []

        env_valid, env_errors = ConfigValidator.validate_environment_variables()
        all_errors.extend([f"[ENV] {err}" for err in env_errors])

        config_valid, config_errors = ConfigValidator.validate_team_mappings()
        all_errors.extend([f"[CONFIG] {err}" for err in config_errors])

        return (env_valid and config_valid, all_errors)
