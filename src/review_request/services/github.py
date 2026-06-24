from typing import Dict, Optional, List
import aiohttp
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from review_request.services.cache_service import CacheService
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)


class GitHubError(Exception):
    pass


class GitHub:
    """Service class for handling GitHub API interactions."""

    _cache = CacheService(maxsize=200, ttl=300)

    def __init__(
        self,
        token: str,
        organization: str,
        repo: str,
        pull_request_number: str,
        use_cache: bool = True,
    ):
        self.token = token
        self.organization = organization
        self.repo = repo
        self.pull_request_number = pull_request_number
        self.use_cache = use_cache
        self._validate_inputs()
        self._session: Optional[aiohttp.ClientSession] = None

    def _validate_inputs(self) -> None:
        if not all(
            [self.token, self.organization, self.repo, self.pull_request_number]
        ):
            raise GitHubError("Missing required parameters")

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=50,
                limit_per_host=20,
                ttl_dns_cache=300,
                enable_cleanup_closed=True,
                force_close=False,
            )
            timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                raise_for_status=False,
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        return False

    def _generate_cache_key(self, url: str) -> str:
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return f"github_api_{url_hash}"

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def make_github_request(self, url: str) -> Dict:
        if self.use_cache:
            cache_key = self._generate_cache_key(url)
            cached_response = self._cache.get(cache_key)
            if cached_response is not None:
                logger.info(f"Cache hit for GitHub API: {url}")
                return cached_response

        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

        session = await self._get_session()
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()

                if self.use_cache:
                    cache_key = self._generate_cache_key(url)
                    self._cache.set(cache_key, data)
                    logger.info(f"Cached GitHub API response: {url}")

                return data
            else:
                error_msg = f"GitHub API error: {response.status} for URL: {url}"
                logger.error(error_msg)

                raise GitHubError(error_msg)

    def build_url(self) -> str:
        return f"https://api.github.com/repos/{self.organization}/{self.repo}"

    def build_pull_request_url(self) -> str:
        return f"{self.build_url()}/pulls/{self.pull_request_number}"

    async def get_pr_details(self) -> Dict:
        return await self.make_github_request(self.build_pull_request_url())

    async def get_pr_reviewers(self) -> str:
        pr_api_url = f"{self.build_pull_request_url()}/requested_reviewers"
        try:
            response = await self.make_github_request(pr_api_url)
            teams = response.get("teams", [])
            return ", ".join([f"@{team['name']}" for team in teams])
        except GitHubError as e:
            logger.error(f"Failed to get PR reviewers: {str(e)}")
            return ""

    async def get_open_prs(self, base_branch: str = "main") -> List[Dict]:
        url = (
            f"{self.build_url()}/pulls?state=open&base={base_branch}"
            "&sort=updated&direction=desc"
        )

        try:
            response = await self.make_github_request(url)
            return response if isinstance(response, list) else []
        except GitHubError as e:
            logger.error(f"Failed to get open PRs: {str(e)}")
            return []

    async def get_team_review_requests(
        self,
        team_slug: str,
        base_branch: str = "main",
        max_age_days: Optional[int] = None,
    ) -> List[Dict]:
        all_prs = await self.get_open_prs(base_branch)
        team_prs = []

        for pr in all_prs:
            try:
                author = pr.get("user", {}).get("login", "")
                if author == "dependabot[bot]":
                    logger.info(f"Skipping PR #{pr['number']} authored by {author}")
                    continue
                if pr.get("draft", False):
                    logger.info(f"Skipping draft PR #{pr['number']}")
                    continue

                if max_age_days is not None:
                    pr_age_days = self.calculate_pr_age_days(pr.get("created_at", ""))
                    if pr_age_days > max_age_days:
                        logger.info(
                            f"Skipping PR #{pr['number']} - age {pr_age_days} days exceeds max {max_age_days} days"
                        )
                        continue

                reviewers_url = (
                    f"{self.build_url()}/pulls/{pr['number']}/requested_reviewers"
                )
                reviewers_response = await self.make_github_request(reviewers_url)
                teams = reviewers_response.get("teams", [])
                if any(team["slug"] == team_slug for team in teams):
                    team_prs.append(pr)
            except GitHubError as e:
                logger.warning(
                    f"Failed to get reviewers for PR {pr['number']}: {str(e)}"
                )
                continue

        return team_prs

    def calculate_pr_age(self, created_at: str) -> str:
        try:
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            now = datetime.now(created.tzinfo)
            diff = now - created

            days = diff.days
            hours = diff.seconds // 3600

            if days > 0:
                return f"{days} day{'s' if days != 1 else ''} old"
            elif hours > 0:
                return f"{hours} hour{'s' if hours != 1 else ''} old"
            else:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes != 1 else ''} old"
        except Exception as e:
            logger.error(f"Failed to calculate PR age: {str(e)}")
            return "unknown age"

    def calculate_pr_age_days(self, created_at: str) -> int:
        try:
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            now = datetime.now(created.tzinfo)
            diff = now - created
            return diff.days
        except Exception as e:
            logger.error(f"Failed to calculate PR age in days: {str(e)}")
            return 0
