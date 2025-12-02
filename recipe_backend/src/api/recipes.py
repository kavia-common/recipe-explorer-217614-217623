from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.services.spoonacular import (
    SpoonacularAuthError,
    SpoonacularServiceError,
    get_spoonacular_client,
)

router = APIRouter(prefix="/recipes", tags=["Recipes"])


class SpoonacularErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message describing the failure")


@router.get(
    "/search",
    summary="Search recipes",
    description="Search for recipes using Spoonacular complexSearch. Supports optional filters and pagination.",
    responses={
        200: {"description": "Search results"},
        400: {"model": SpoonacularErrorResponse, "description": "Invalid request"},
        401: {"model": SpoonacularErrorResponse, "description": "Unauthorized (missing/invalid API key)"},
        502: {"model": SpoonacularErrorResponse, "description": "Upstream Spoonacular error"},
    },
)
def search_recipes(
    q: str = Query(..., description="Search query"),
    number: int = Query(10, ge=1, le=50, description="Number of results to return (max 50)"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    diet: Optional[str] = Query(None, description="Diet filter, e.g., vegetarian, vegan"),
    cuisine: Optional[str] = Query(None, description="Cuisine filter, e.g., italian, mexican"),
    intolerances: Optional[str] = Query(None, description="Comma-separated intolerances, e.g., gluten,dairy"),
):
    """Search recipes endpoint.

    Query parameters:
        q: search query
        number: number of results (1-50)
        offset: pagination offset
        diet: optional diet filter
        cuisine: optional cuisine filter
        intolerances: optional intolerances list

    Returns:
        JSON results from Spoonacular complexSearch (addRecipeInformation=true).
    """
    client = get_spoonacular_client()
    try:
        data = client.search_recipes(
            query=q,
            number=number,
            offset=offset,
            diet=diet,
            cuisine=cuisine,
            intolerances=intolerances,
        )
        return data
    except SpoonacularAuthError as ae:
        # Provide a standardized JSON error for missing/invalid API key
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: missing or invalid Spoonacular API key. Please set SPOONACULAR_API_KEY in backend .env.",
        ) from ae
    except SpoonacularServiceError as se:
        # Treat service errors as upstream issues and expose concise message
        raise HTTPException(status_code=502, detail=f"Spoonacular error: {se}") from se
    except Exception as e:
        # Unexpected errors
        raise HTTPException(status_code=502, detail=f"Unexpected error contacting Spoonacular: {e}") from e


@router.get(
    "/{recipe_id}",
    summary="Get a recipe's details",
    description="Fetch detailed recipe information by Spoonacular recipe ID.",
    responses={
        200: {"description": "Recipe details"},
        400: {"model": SpoonacularErrorResponse, "description": "Invalid request"},
        401: {"model": SpoonacularErrorResponse, "description": "Unauthorized (missing/invalid API key)"},
        404: {"model": SpoonacularErrorResponse, "description": "Recipe not found"},
        502: {"model": SpoonacularErrorResponse, "description": "Upstream Spoonacular error"},
    },
)
def get_recipe_details(
    recipe_id: int,
    include_nutrition: bool = Query(False, description="Whether to include nutrition information"),
):
    """Get recipe detail endpoint.

    Path parameters:
        recipe_id: Spoonacular recipe ID.

    Query parameters:
        include_nutrition: include nutrition info.

    Returns:
        Recipe information from Spoonacular.
    """
    client = get_spoonacular_client()
    try:
        data = client.get_recipe_information(recipe_id=recipe_id, include_nutrition=include_nutrition)
        # If Spoonacular returns an empty object or missing id, treat as not found
        if not data or (isinstance(data, dict) and "id" not in data):
            raise HTTPException(status_code=404, detail="Recipe not found")
        return data
    except SpoonacularAuthError as ae:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: missing or invalid Spoonacular API key. Please set SPOONACULAR_API_KEY in backend .env.",
        ) from ae
    except SpoonacularServiceError as se:
        # In case Spoonacular returns 404 internally we would have raised above only on empty,
        # but here we generalize service errors to 502.
        raise HTTPException(status_code=502, detail=f"Spoonacular error: {se}") from se
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Unexpected error contacting Spoonacular: {e}") from e
