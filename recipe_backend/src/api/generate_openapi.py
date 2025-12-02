import json
import os

from src.api.main import app

"""
Utility script to generate the OpenAPI spec for the running FastAPI application.

Run in the backend root:
    python -m src.api.generate_openapi

It writes the schema to interfaces/openapi.json
"""

# Generate the OpenAPI schema from app
openapi_schema = app.openapi()

# Ensure output directory exists
output_dir = "interfaces"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "openapi.json")

# Write schema to file
with open(output_path, "w") as f:
    json.dump(openapi_schema, f, indent=2, sort_keys=False)
