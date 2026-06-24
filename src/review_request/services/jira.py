from typing import Any, Dict, Optional
import aiohttp


class JiraError(Exception):
    pass


class Jira:
    """Minimal async Jira Cloud client supporting JQL search."""

    def __init__(self, site: str, email: str, api_token: str):
        self.site = site.rstrip("/")
        self.email = email
        self.api_token = api_token
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        if self._session is None:
            auth = aiohttp.BasicAuth(self.email, self.api_token)
            self._session = aiohttp.ClientSession(auth=auth)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def search_issues(self, jql: str, max_results: int = 100) -> Dict[str, Any]:
        if self._session is None:
            raise JiraError(
                "Jira session is not initialized. Use 'async with Jira(...)'."
            )

        url = f"{self.site}/rest/api/3/search/jql"
        payload = {
            "jql": jql,
            "maxResults": max_results,
            "fields": [
                "summary",
                "assignee",
                "duedate",
                "status",
                "project",
                "issuetype",
            ],
        }
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        async with self._session.post(url, json=payload, headers=headers) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise JiraError(f"Jira search failed: {resp.status} {text}")
            return await resp.json()
