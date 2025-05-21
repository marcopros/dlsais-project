from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
import yaml

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

# Carica spec da YAML
with open("openapi.yaml", "r") as f:
    openapi_schema = yaml.safe_load(f)

@app.get("/openapi.json", include_in_schema=False)
async def custom_openapi():
    return openapi_schema

# Rimappa Swagger UI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
@app.get("/docs", include_in_schema=False)
async def swagger_ui_html():
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <title>Docs</title>
      <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist/swagger-ui.css" />
    </head>
    <body>
      <div id="swagger-ui"></div>
      <script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>
      <script>
        SwaggerUIBundle({{
          url: '/openapi.json',
          dom_id: '#swagger-ui',
        }});
      </script>
    </body>
    </html>
    """
    return HTMLResponse(html)
