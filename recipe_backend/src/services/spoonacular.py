import os
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

SPOONACULAR_API_KEY: Optional[str] = os.getenv("SPOONACULAR_API_KEY")

DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0, read=10.0)  # total, connect, read timeouts
BASE_URL = "https://api.spoonacular.com"


class SpoonacularServiceError(Exception):
    """Base exception for Spoonacular service errors."""


class SpoonacularAuthError(SpoonacularServiceError):
    """Raised when API key is missing or invalid."""


class SpoonacularClient:
    """HTTP client for interacting with the Spoonacular API."""

    def __init__(self, api_key: Optional[str] = None, timeout: Optional[httpx.Timeout] = None) -> None:
        self.api_key = api_key or SPOONACULAR_API_KEY
        self.timeout = timeout or DEFAULT_TIMEOUT
        if not self.api_key:
            # Defer raising until first request so app can still start;
            # endpoints will raise a clear error if key is missing.
            pass

        # A single shared client for connection pooling
        self._client = httpx.Client(base_url=BASE_URL, timeout=self.timeout)

    def _require_key(self) -> None:
        if not self.api_key:
            raise SpoonacularAuthError(
                "SPOONACULAR_API_KEY not set. Please configure it in the .env file for the backend container."
            )

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform a GET request to the Spoonacular API with API key injected."""
        self._require_key()
        params = params.copy() if params else {}
        params["apiKey"] = self.api_key
        try:
            resp = self._client.get(path, params=params)
        except httpx.TimeoutException as te:
            raise SpoonacularServiceError(f"Spoonacular request timed out: {te}") from te
        except httpx.HTTPError as he:
            raise SpoonacularServiceError(f"Spoonacular request failed: {he}") from he

        if resp.status_code == 401 or resp.status_code == 403:
            raise SpoonacularAuthError("Unauthorized: invalid or expired Spoonacular API key.")
        if resp.status_code >= 400:
            # Attempt to include error message from API
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise SpoonacularServiceError(f"Spoonacular error {resp.status_code}: {detail}")

        try:
            return resp.json()
        except ValueError as ve:
            raise SpoonacularServiceError(f"Invalid JSON from Spoonacular: {ve}") from ve

    # PUBLIC_INTERFACE
    def search_recipes(
        self,
        query: str,
        number: int = 10,
        offset: int = 0,
        diet: Optional[str] = None,
        cuisine: Optional[str] = None,
        intolerances: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Search recipes using Spoonacular complexSearch endpoint.

        Args:
            query: Search phrase
            number: Number of results to return
            offset: Offset for pagination
            diet: Optional diet filter (e.g., vegetarian, vegan)
            cuisine: Optional cuisine filter (e.g., italian, mexican)
            intolerances: Optional comma-separated intolerances (e.g., gluten, dairy)

        Returns:
            dict: JSON payload returned by Spoonacular
        """
        params: Dict[str, Any] = {
            "query": query,
            "number": max(1, min(number, 50)),  # limit results per request
            "offset": max(0, offset),
            "addRecipeInformation": "true",  # include rich info like summary, sourceUrl, etc.
        }
        if diet:
            params["diet"] = diet
        if cuisine:
            params["cuisine"] = cuisine
        if intolerances:
            params["intolerances"] = intolerances

        return self._get("/recipes/complexSearch", params=params)

    # PUBLIC_INTERFACE
    def get_recipe_information(self, recipe_id: int, include_nutrition: bool = False) -> Dict[str, Any]:
        """Get detailed recipe information.

        Args:
            recipe_id: The Spoonacular recipe ID.
            include_nutrition: Whether to include nutrition info.

        Returns:
            dict: JSON payload with recipe details.
        """
        path = f"/recipes/{recipe_id}/information"
        params = {"includeNutrition": "true" if include_nutrition else "false"}
        return self._get(path, params=params)


# Provide a module-level singleton client for convenience
_client_singleton = SpoonacularClient()


# PUBLIC_INTERFACE
def get_spoonacular_client() -> SpoonacularClient:
    """Return a shared Spoonacular client instance."""
    return _client_singleton
