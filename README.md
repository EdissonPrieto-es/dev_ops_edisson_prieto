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
  static/openapi.json  # spec OpenAPI 3, servido en /docs con Swagger UI
tests/             # pytest (SQLite en memoria)
postman/           # colección y environments de Postman (escenarios de prueba)
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
| GET    | `/health` | Estado de la app y la BD, versión desplegada (`VERSION`) e instancia que responde |
| POST   | `/blacklists` | Agrega un email a la lista negra global (Bearer token) |
| GET    | `/blacklists/<email>` | Indica si un email está en la lista negra y el motivo (Bearer token) |

Documentación interactiva (Swagger UI) en **`/docs`**; el spec OpenAPI 3 está en `/static/openapi.json`
(`app/static/openapi.json`). Usa el botón **Authorize** con el valor de `API_TOKEN` para probar los endpoints.

Autorización: token estático `Authorization: Bearer <API_TOKEN>`, definido por la variable de entorno
`API_TOKEN` (en local por defecto `dev-static-token`). Sin token o con uno distinto la API responde `401`.

### POST `/blacklists`
```json
{ "email": "user@example.com", "app_uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "blocked_reason": "spam" }
```
- `email` y `app_uuid` (UUID) son obligatorios; `blocked_reason` es opcional (máx. 255).
- Se guardan además la IP de origen y la fecha/hora (UTC) de la solicitud.
- Respuestas: `201` creado · `400` datos inválidos · `401` sin token / token inválido · `409` el email ya existe.

```bash
curl -X POST localhost:5000/blacklists -H "Authorization: Bearer dev-static-token" \
  -H "Content-Type: application/json" -d '{"email":"user@example.com","app_uuid":"3fa85f64-5717-4562-b3fc-2c963f66afa6"}'
```

### GET `/blacklists/<email>`
```bash
curl localhost:5000/blacklists/user@example.com -H "Authorization: Bearer dev-static-token"
```
Responde `200` con `blacklisted: false` y `blocked_reason: null` si el email no está en la lista.

## Pruebas con Postman
`postman/` contiene la colección `blacklist.postman_collection.json` y dos environments:
`local.postman_environment.json` (`http://localhost:5000`, token `dev-static-token`) y
`aws.postman_environment.json` (URL de Elastic Beanstalk; el `api_token` va vacío y se completa en Postman,
nunca en el repo).

La colección tiene 15 escenarios con tests y un ejemplo de respuesta guardado en cada uno:
- **Health:** `GET /health`.
- **POST `/blacklists`:** agregar con y sin motivo (`201`), duplicado (`409`), email inválido, `app_uuid`
  inválido, campos ausentes y motivo de más de 255 caracteres (`400`), sin token y token inválido (`401`).
- **GET `/blacklists/:email`:** email en la lista con y sin motivo (`true`), email que no está (`false`),
  sin token y token inválido (`401`).

Córrela completa y en orden: los GET consultan los emails que crean los POST (se generan con un timestamp,
así que se puede correr varias veces).

```bash
npx newman run postman/blacklist.postman_collection.json -e postman/local.postman_environment.json
npx newman run postman/blacklist.postman_collection.json -e postman/aws.postman_environment.json \
  --env-var api_token=<API_TOKEN>
```

Documentación publicada en Postman: https://documenter.getpostman.com/view/14888456/2sBYHSxg4g

## Despliegue en AWS Elastic Beanstalk
Plataforma: **Python 3.12 en Amazon Linux 2023**. EB instala `requirements.txt` y arranca el `Procfile`
(gunicorn en `:8000` detrás de nginx). `.ebextensions/01-app.config` cambia el chequeo de salud a `/health`.

```bash
pip install awsebcli
eb init -p "python-3.12" dev-ops-app --region us-east-1
eb create dev-ops-env --database.engine postgres   # o sin --database y usar DATABASE_URL
eb setenv SECRET_KEY=<valor> JWT_SECRET_KEY=<valor-de-32+-caracteres> API_TOKEN=<token-estatico>
eb deploy        # sube el último commit (git), no los cambios sin commitear
eb open          # abrir /health
```

Base de datos: si usas la RDS acoplada a EB, la app arma la conexión con `RDS_HOSTNAME`, `RDS_PORT`,
`RDS_DB_NAME`, `RDS_USERNAME` y `RDS_PASSWORD`. Si usas una RDS independiente, define `DATABASE_URL`
(tiene prioridad). Las URLs `postgres://` se normalizan a `postgresql://`.
