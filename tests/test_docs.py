import re


def test_swagger_ui(client):
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert b"/static/openapi.json" in resp.data


def test_openapi_documents_every_api_route(client):
    spec = client.get("/static/openapi.json").get_json()
    documented = {(path, method.upper()) for path, ops in spec["paths"].items() for method in ops}

    registered = set()
    for rule in client.application.url_map.iter_rules():
        if rule.endpoint in ("static", "docs.swagger_ui"):
            continue
        path = re.sub(r"<(?:\w+:)?(\w+)>", r"{\1}", rule.rule)
        registered |= {(path, m) for m in rule.methods - {"HEAD", "OPTIONS"}}

    assert documented == registered
