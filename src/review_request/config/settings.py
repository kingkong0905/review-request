from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import Dict, List, Any

load_dotenv()


class Settings(BaseSettings):
    github_token: str = ""
    bot_token: str = ""
    channel_id: str = ""
    slack_signing_secret: str = ""
    rollbar_access_token: str = ""
    environment: str = "development"
    max_age_pr_days: int = 60
    app_url: str = ""
    jira_site: str = ""
    jira_email: str = ""
    jira_api_token: str = ""

    class Config:
        env_file = ".env"


settings = Settings()

SLACK_TEAM_MAPPINGS: Dict[str, str] = {
    "@ai-hero-bot": "S0AQB912TSQ",
    "@engineering-managers": "S05FPFUQKK6",
    "@squad-yoshi": "S04FX4MPVHU",
    "@hr-integrations": "S06ENMV00FJ",
    "@squad-bounty-hunters": "S04SB339XED",
    "@talent-seniors": "S085MRPUE5A",
    "@squad-night-s-watch": "SQ0LZDLBY",
    "@pre-payroll": "S03MB6L10AU",
    "@core-security": "S063WTUH4J2",
    "@QA team": "S0841B04Q68",
    "@squad-ai-implementation-ml": "S08SJ45EP9V",
    "@squad-eternals-ml": "S07F62YVB8S",
    "@squad-alchemist-ml": "S089EMP46GM",
    "@core-tech": "S063WTUH4J2",
    "@hr-corepayroll": "S06ENMV00FJ",
    "@squad-maplemoney": "S0AHBRANQQM",
    "@squad-wasabi": "S092KN5DQLC",
}

GITHUB_REPOSITORIES: List[Dict[str, Any]] = [
    {
        "url": "https://github.com/Thinkei/ats",
        "base_branch": "master",
    },
    {
        "url": "https://github.com/Thinkei/employment-hero",
        "base_branch": "master",
    },
    {
        "url": "https://github.com/Thinkei/frontend-core",
        "base_branch": "master",
    },
    {
        "url": "https://github.com/Thinkei/career-page",
        "base_branch": "master",
    },
    {
        "url": "https://github.com/Thinkei/smart-match",
        "base_branch": "main",
    },
]

GITHUB_TEAM_REMINDER_MAPPING: List[Dict[str, Any]] = [
    {
        "channel_id": "C066UGGS2PJ",
        "slack_group_id": "S06DU7PTYLW",
        "github_team": "squad-eternals",
        "max_age_pr_days": settings.max_age_pr_days,
        "remind_date": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    },
    {
        "channel_id": "C09Q56D8VGX",
        "slack_group_id": "S01T1977RBK",
        "github_team": "squad-helios",
        "max_age_pr_days": settings.max_age_pr_days,
        "remind_date": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    },
    {
        "channel_id": "C07EU03AEEL",
        "slack_group_id": "S07EBNZ4PRB",
        "github_team": "squad-alchemist",
        "max_age_pr_days": settings.max_age_pr_days,
        "remind_date": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    },
]

JIRA_TEAM_REMINDER_MAPPING: List[Dict[str, Any]] = [
    {
        "channel_id": "C066UGGS2PJ",
        "slack_group_id": "S06DU7PTYLW",
        "jira_jql": 'project = ET AND statusCategory = "In Progress" AND duedate < now() ORDER BY duedate ASC',
        "remind_date": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    },
]
