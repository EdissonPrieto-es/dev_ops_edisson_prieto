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
Procfile           # comando web (gunicorn en :8000)
.ebextensions/     # configuración de Elastic Beanstalk
docker-compose.yml # PostgreSQL local
```

## Ejecución local
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
docker compose up -d db
flask run
pytest -q
```

## Endpoints
| Método | Ruta      | Descripción              |
|--------|-----------|--------------------------|
| GET    | `/health` | Estado de la app y la BD |
| POST   | `/blacklists` | Agrega un email a la lista negra global (Bearer token) |

### POST `/blacklists`
```json
{ "email": "user@example.com", "app_uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "blocked_reason": "spam" }
```
- `email` y `app_uuid` (UUID) son obligatorios; `blocked_reason` es opcional (máx. 255).
- Se guardan además la IP de origen y la fecha/hora (UTC) de la solicitud.
- Respuestas: `201` creado · `400` datos inválidos · `401` sin token / token inválido · `409` el email ya existe.

Generar un token para un sistema cliente (firmado con `JWT_SECRET_KEY`, sin expiración):
```bash
flask create-token <nombre-sistema>
curl -X POST localhost:5000/blacklists -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" -d '{"email":"user@example.com","app_uuid":"3fa85f64-5717-4562-b3fc-2c963f66afa6"}'
```

## Despliegue en AWS Elastic Beanstalk
Plataforma: **Python 3.12 en Amazon Linux 2023**. EB instala `requirements.txt` y arranca el `Procfile`
(gunicorn en `:8000` detrás de nginx). `.ebextensions/01-app.config` cambia el chequeo de salud a `/health`.

```bash
pip install awsebcli
eb init -p "python-3.12" dev-ops-app --region us-east-1
eb create dev-ops-env --database.engine postgres   # o sin --database y usar DATABASE_URL
eb setenv SECRET_KEY=<valor> JWT_SECRET_KEY=<valor-de-32+-caracteres>
eb deploy        # sube el último commit (git), no los cambios sin commitear
eb open          # abrir /health
```

Base de datos: si usas la RDS acoplada a EB, la app arma la conexión con `RDS_HOSTNAME`, `RDS_PORT`,
`RDS_DB_NAME`, `RDS_USERNAME` y `RDS_PASSWORD`. Si usas una RDS independiente, define `DATABASE_URL`
(tiene prioridad). Las URLs `postgres://` se normalizan a `postgresql://`.
