from flask import Blueprint

docs_bp = Blueprint("docs", __name__)

SWAGGER_UI_VERSION = "5.17.14"

SWAGGER_HTML = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Blacklist API</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@{SWAGGER_UI_VERSION}/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@{SWAGGER_UI_VERSION}/swagger-ui-bundle.js"></script>
  <script>SwaggerUIBundle({{ url: "/static/openapi.json", dom_id: "#swagger-ui" }});</script>
</body>
</html>"""


@docs_bp.get("/docs")
def swagger_ui():
    return SWAGGER_HTML
