# dev_ops_edisson_prieto

API REST en Python/Flask con PostgreSQL, pensada para desplegarse en un PaaS de nube pública.

## Stack
Flask · Flask-SQLAlchemy · Flask-RESTful · Flask-Marshmallow · Flask-JWT-Extended · Werkzeug · PostgreSQL

## Estructura
```
app/
  __init__.py      # create_app(): app factory, registra extensiones y recursos
  config.py        # configuración por variables de entorno
  extensions.py    # db, ma, jwt
  models/          # modelos SQLAlchemy
  schemas/         # esquemas Marshmallow
  resources/       # recursos Flask-RESTful (endpoints)
tests/             # pytest (SQLite en memoria)
wsgi.py            # punto de entrada (gunicorn wsgi:app)
Procfile           # comando web para el PaaS
docker-compose.yml # PostgreSQL local
```

## Ejecución local
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose up -d db
flask run
pytest -q
```

## Endpoints
| Método | Ruta      | Descripción              |
|--------|-----------|--------------------------|
| GET    | `/health` | Estado de la app y la BD |

## Despliegue en PaaS
Define `DATABASE_URL`, `SECRET_KEY` y `JWT_SECRET_KEY` (≥ 32 caracteres) como variables de entorno; el comando de arranque es `gunicorn wsgi:app`. Las URLs `postgres://` se normalizan automáticamente a `postgresql://`.
