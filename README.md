# recipe-explorer-217614-217623

## Backend (FastAPI) run notes

- Start the API with uvicorn bound to 0.0.0.0:3001:
  uvicorn src.api.main:app --host 0.0.0.0 --port 3001

- Health:
  - GET /health -> {"status":"ok"}
  - GET /       -> {"status":"ok","service":"Recipe Explorer API"}
  Both are public and require no authentication.

- CORS: Allowed origins are configured using the environment variable CORS_ALLOWED_ORIGINS (comma-separated).
  Example for local dev allowing the React app:
  CORS_ALLOWED_ORIGINS=http://localhost:3000

  If not set, the backend defaults to allowing http://localhost:3000.
  Preflight OPTIONS requests are handled by CORSMiddleware.

- Public endpoints:
  - GET /recipes/search
  - GET /recipes/{recipe_id}
  These do not require authentication and will return JSON errors with a "detail" property when Spoonacular fails
  (e.g. missing/invalid API key or upstream errors).

- Spoonacular configuration:
  Set SPOONACULAR_API_KEY in the backend .env to enable recipe search/details.

- Quick verification (from your browser/React app console or curl):
  curl "http://localhost:3001/health"
  curl "http://localhost:3001/recipes/search?q=pasta"

  If you see a JSON response, CORS/network is good. If you see:
  {"detail":"Unauthorized: missing or invalid Spoonacular API key. Please set SPOONACULAR_API_KEY in backend .env."}
  then CORS is fine but you need to configure the API key.