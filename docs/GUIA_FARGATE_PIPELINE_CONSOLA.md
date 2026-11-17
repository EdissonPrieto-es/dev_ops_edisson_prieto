# Guia: Entrega 3 (Fargate + CodePipeline + CodeDeploy) y capturas de pantalla

Pasos para desplegar el microservicio en AWS Fargate, armar el pipeline CI/CD y ejecutar los 3 escenarios del documento.
Cada paso termina con una **Evidencia** (captura). Los codigos `E-x.y` sirven para referenciarlas en el documento y en el video.

- Region: `us-east-1` (N. Virginia). Debe verse arriba a la derecha en cada captura.
- Repositorio: `https://github.com/EdissonPrieto-es/dev_ops_edisson_prieto` (GitHub, no CodeCommit; aclaralo en el documento).
- Rama: `main` (el enunciado dice `master`; aclaralo tambien).
- Nombres usados en esta guia (cambialos si quieres, pero se consistente):

| Recurso | Nombre |
|---|---|
| Repositorio ECR | `devops-flask-api` |
| Cluster ECS | `devops-flask-cluster` |
| Task definition | `devops-flask-task` |
| Servicio ECS | `devops-flask-service` |
| Load balancer | `devops-flask-alb` |
| Target groups | `devops-flask-tg-blue`, `devops-flask-tg-green` |
| CodeBuild | `devops-flask-build-img` |
| CodeDeploy app / grupo | `devops-flask-app` / `devops-flask-dg` |
| CodePipeline | `devops-flask-pipeline` |
| Log group | `/ecs/devops-flask` |

## Reglas generales para las capturas

1. Que se vea **region**, **nombre del recurso** y **estado** (Succeeded / Failed / RUNNING / Healthy).
2. Que se vea la **hora** de la ejecucion o el ID (commit, execution ID, deployment ID). Sirve para ligar capturas entre servicios.
3. Zoom del navegador al 80-90 % para que quepa todo. Usa PNG, nombra el archivo con el codigo (`E-3.2-pipeline-exitoso.png`).
4. **Oculta o recorta**: Account ID si te preocupa, `API_TOKEN`, contrasenas, `DATABASE_URL`, secretos en general.
5. Guarda las capturas en una carpeta fuera del repo (por ejemplo `~/Documents/MAIA/DevOps/Proyecto/Entrega 3/capturas/`). No las subas a Git.
6. Hazlas **en la misma sesion del lab** que el despliegue; si la sesion expira los recursos pueden desaparecer.

---

## Parte 0. Preparacion en AWS Academy

1. Inicia el lab, abre la consola y confirma la region `us-east-1`.
2. IAM -> Roles -> busca `LabRole`. Anota su ARN: se usa como rol de ejecucion de tareas, CodeBuild, CodeDeploy y CodePipeline.
3. Systems Manager -> **Parameter Store**: crea 4 parametros tipo `SecureString` con estos nombres exactos (los usa `taskdef.json`): `/devops-flask/SECRET_KEY`, `/devops-flask/JWT_SECRET_KEY` (32+ caracteres), `/devops-flask/API_TOKEN` y `/devops-flask/DATABASE_URL` (`postgresql://usuario:clave@<endpoint-rds>:5432/<db>`).

**E-0.1:** consola con la region visible y el rol `LabRole` (ARN con el Account ID tapado).
**E-0.2:** lista de parametros `/devops-flask/*` creados (sin mostrar valores).

## Parte 1. Imagen de contenedor y ECR

### 1.1 Dockerfile (en la raiz del repo)

```dockerfile
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY wsgi.py .
ARG APP_VERSION=local
RUN echo "$APP_VERSION" > VERSION
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "wsgi:app"]
```

Agrega un `.dockerignore` con `.venv`, `.git`, `dist`, `terraform`, `*.log`, `.env`, `tests`, `postman`.

Prueba local:

```bash
docker build -t devops-flask-api:local .
docker run --rm -p 8000:8000 --env-file .env devops-flask-api:local
curl localhost:8000/health
```

**E-1.1:** terminal con `docker build` exitoso y el `curl /health` respondiendo.

### 1.2 Repositorio ECR y primera imagen

1. Consola -> **ECR** -> **Create repository** -> privado, nombre `devops-flask-api`, **Image scan on push** activado.
2. Entra al repo -> **View push commands** y ejecuta los comandos. En Mac ARM construye con `--platform linux/amd64`:

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker build --platform linux/amd64 -t devops-flask-api .
docker tag devops-flask-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/devops-flask-api:v1
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/devops-flask-api:v1
```

**E-1.2:** pantalla de creacion del repositorio ECR.
**E-1.3:** repositorio ECR mostrando la imagen `v1` (tag, tamano, fecha, digest).

## Parte 2. Red, base de datos y balanceador

1. **Security groups** (EC2 -> Security Groups):
   - `sg-alb`: entrada HTTP 80 desde `0.0.0.0/0` (y 8080 para el listener de prueba del blue/green).
   - `sg-fargate`: entrada TCP 8000 solo desde `sg-alb`.
   - `sg-rds`: entrada TCP 5432 solo desde `sg-fargate`.
2. **RDS** PostgreSQL (o reutiliza la existente) en la VPC por defecto, `sg-rds`, sin acceso publico. Anota el endpoint.
3. **Target groups** (EC2 -> Target Groups), tipo **IP**, protocolo HTTP, puerto **8000**, health check path `/health`:
   - `devops-flask-tg-blue` y `devops-flask-tg-green` (sin registrar targets).
4. **Application Load Balancer** `devops-flask-alb`, internet-facing, 2 subredes publicas, `sg-alb`:
   - Listener **HTTP 80** -> `devops-flask-tg-blue` (trafico de produccion).
   - Listener **HTTP 8080** -> `devops-flask-tg-green` (trafico de prueba).

**E-2.1:** security groups con sus reglas de entrada (alb, fargate, rds).
**E-2.2:** instancia RDS en estado *Available* (endpoint visible, sin acceso publico).
**E-2.3:** los dos target groups con el health check `/health`.
**E-2.4:** ALB con los dos listeners (80 y 8080) y su DNS name.

## Parte 3. Despliegue manual en Fargate (20 %)

### 3.1 Cluster

ECS -> **Clusters** -> **Create cluster** -> `devops-flask-cluster`, infraestructura **AWS Fargate**.

**E-3.1:** cluster creado (estado *Active*).

### 3.2 Task definition

ECS -> **Task definitions** -> **Create new** (JSON o formulario):

- Family `devops-flask-task`, launch type **Fargate**, SO Linux/**X86_64**, 0.25 vCPU / 0.5 GB.
- Task role y execution role: `LabRole`.
- Contenedor `devops-flask` (el nombre debe coincidir con `appspec.yaml`), imagen `<account-id>.dkr.ecr.us-east-1.amazonaws.com/devops-flask-api:v1`, puerto **8000**.
- Variables de entorno / secretos (tipo ValueFrom, desde los parametros SSM `/devops-flask/*`, con los mismos nombres que `taskdef.json`) y logs `awslogs` hacia `/ecs/devops-flask`.

**E-3.2:** task definition (revision 1) con imagen, puerto 8000, variables/secretos (valores ocultos) y configuracion de logs.

### 3.3 Servicio (listo para CodeDeploy)

ECS -> cluster -> **Services** -> **Create**:

- Launch type Fargate, task definition `devops-flask-task`, nombre `devops-flask-service`, 1 tarea deseada.
- **Deployment options -> Deployment type: Blue/green deployment (powered by AWS CodeDeploy)**. Si en la consola no aparece, creala con AWS CLI usando `--deployment-controller type=CODE_DEPLOY`.
- Red: VPC por defecto, subredes publicas, `sg-fargate`, **Public IP ON** (evita pagar NAT).
- Load balancer: `devops-flask-alb`, listener de produccion 80, listener de prueba 8080, target groups blue y green.

**E-3.3:** configuracion del servicio (deployment controller CODE_DEPLOY, red, load balancer).
**E-3.4:** pestana **Tasks** con la tarea en `RUNNING` / `Healthy`.
**E-3.5:** pestana **Logs** o CloudWatch `/ecs/devops-flask` mostrando el arranque de gunicorn.
**E-3.6:** target group con el target en estado **healthy**.

### 3.4 Validacion con Postman

1. En `postman/aws.postman_environment.json` pon `base_url` = `http://<DNS-del-ALB>` y completa `api_token` solo en Postman.
2. Ejecuta `GET /health` y despues la coleccion completa (Runner), o:

```bash
npx newman run postman/blacklist.postman_collection.json -e postman/aws.postman_environment.json --env-var api_token=<API_TOKEN>
```

**E-3.7:** Postman con `GET /health` -> 200 (se ve la URL del ALB, `version` e `instance`).
**E-3.8:** resultado del Runner/newman con los 15 escenarios en verde.

## Parte 4. Archivos de despliegue en el repo (10 %)

Estos archivos se versionan en `main`.

Los archivos ya estan en la raiz del repo; solo hay que hacer commit y merge a `main`:

- `Dockerfile` y `.dockerignore`: imagen `python:3.12-slim`, gunicorn en `:8000`, usuario sin privilegios; `APP_VERSION` se escribe en `VERSION` para que `/health` reporte el SHA.
- `taskdef.json`: task definition (Fargate, 0.25 vCPU / 0.5 GB, X86_64, `LabRole`, logs en `/ecs/devops-flask`, secretos desde SSM). Usa dos placeholders: `<IMAGE1_NAME>` (lo reemplaza CodePipeline con la imagen nueva) y `<ACCOUNT_ID>` (lo reemplaza `buildspec.yml`).
- `appspec.yaml`: contenedor `devops-flask`, puerto 8000 (el nombre del contenedor debe coincidir con el de la task definition manual de la Parte 3).
- `buildspec.yml`: pruebas -> login ECR -> `docker build` con tag = SHA corto -> `docker push` -> genera `imageDetail.json`. Si `pytest` falla, CodeBuild se detiene antes de construir la imagen (escenario 1). Variables del proyecto CodeBuild: `AWS_ACCOUNT_ID`, `AWS_DEFAULT_REGION=us-east-1`, `IMAGE_REPO_NAME=devops-flask-api`.

**E-4.1:** GitHub mostrando en `main` los archivos `Dockerfile`, `buildspec.yml`, `taskdef.json`, `appspec.yaml`.
**E-4.2:** contenido de `buildspec.yml` en GitHub (se ve la fase de pruebas y la de `docker build/push`).

## Parte 5. Proyecto de CodeBuild con Docker (10 %)

1. **CodeBuild** -> **Create build project** -> `devops-flask-build-img`.
2. Source: GitHub (usa la conexion existente), repo del proyecto, rama `main`. No actives webhook aqui: el disparo lo hara CodePipeline.
3. Environment: Managed image, Amazon Linux, runtime Standard, imagen reciente, **Privileged: ON** (necesario para Docker). Service role: `LabRole`.
4. Variables de entorno: `AWS_ACCOUNT_ID`, `AWS_DEFAULT_REGION`, `IMAGE_REPO_NAME`.
5. Buildspec: `buildspec.yml`. Logs en CloudWatch.

**E-5.1:** configuracion del environment (imagen, Privileged ON, rol, variables).
**E-5.2:** pagina del proyecto de CodeBuild con source GitHub y buildspec.

## Parte 6. CodeDeploy (blue/green para ECS)

1. **CodeDeploy** -> **Applications** -> **Create application** -> `devops-flask-app`, compute platform **Amazon ECS**.
2. **Create deployment group** -> `devops-flask-dg`:
   - Service role: `LabRole`.
   - Cluster `devops-flask-cluster`, servicio `devops-flask-service`.
   - Load balancer `devops-flask-alb`, listener de produccion 80, listener de prueba 8080, target groups blue y green.
   - Traffic rerouting: inmediato; **Original revision termination**: 5 minutos (menos para acortar la espera).
   - Deployment configuration: `CodeDeployDefault.ECSAllAtOnce`.
   - Rollback: **Roll back when a deployment fails** activado.

**E-6.1:** aplicacion de CodeDeploy (plataforma ECS).
**E-6.2:** deployment group con cluster, servicio, ALB, listeners, target groups, configuracion y rollback.

## Parte 7. CodePipeline (CI + CD automatico) (10 % + 40 %)

1. **CodePipeline** -> **Create pipeline** -> `devops-flask-pipeline`, tipo **V2**, rol `LabRole`, artefactos en el bucket por defecto.
2. **Source**: proveedor **GitHub (via GitHub App)**, conexion existente, repo `EdissonPrieto-es/dev_ops_edisson_prieto`, rama `main`, output `SourceArtifact`. **Trigger**: iniciar en push a `main` (habilitado).
3. **Build**: AWS CodeBuild, proyecto `devops-flask-build-img`, input `SourceArtifact`, output `BuildArtifact`.
4. **Deploy**: **Amazon ECS (Blue/Green)**:
   - Aplicacion `devops-flask-app`, grupo `devops-flask-dg`.
   - Task definition: `BuildArtifact` -> `taskdef.json`; AppSpec: `BuildArtifact` -> `appspec.yaml`.
   - Input de imagen dinamica: `BuildArtifact`, **Placeholder text** `IMAGE1_NAME` (usa `imageDetail.json`).
5. Crear. La primera ejecucion arranca sola: esperala completa.

**E-7.1:** resumen del pipeline (Source, Build, Deploy) antes de crear.
**E-7.2:** vista del pipeline con las 3 etapas y el trigger (Settings / Edit -> trigger en push a `main`).
**E-7.3:** detalle del trigger configurado (rama `main`, tipo push).

---

## Parte 8. Escenario 1 - CI fallido (4 %)

Objetivo: el pipeline se detiene en Build y **no** llega a Deploy.

1. Rama de trabajo, rompe una prueba a proposito (por ejemplo cambia un valor esperado en `tests/test_health.py`):

```bash
git switch -c escenario-1-ci-fallido
# editar tests/test_health.py para que falle
git commit -am "Escenario 1: prueba rota a proposito para CI fallido"
git push -u origin escenario-1-ci-fallido
```

2. Abre un PR y hazle merge a `main` (el pipeline solo escucha `main`). Anota el SHA corto.
3. Observa el pipeline.

**E-8.1:** el commit/PR en GitHub con el cambio que rompe la prueba (diff).
**E-8.2:** pipeline: Source en verde, **Build en rojo (Failed)** y Deploy sin ejecutar (gris). Se ve el execution ID y el commit.
**E-8.3:** CodeBuild -> build fallido: logs de `pytest` con la prueba que falla y la fase `PRE_BUILD` en *Failed*.
**E-8.4:** pestana **Reports** de CodeBuild con el reporte pytest con casos fallidos.
**E-8.5:** ECR: **no** aparece una imagen nueva con el tag de ese commit.
**E-8.6:** ECS: el servicio sigue con la task definition anterior (sin cambios) y `/health` sigue respondiendo.

**Hallazgos a documentar:** la prueba cae antes de construir la imagen, no se publica nada, la version en produccion no cambia, tiempo hasta el fallo.

Despues, **revierte** el commit y haz merge para dejar `main` sano.

## Parte 9. Escenario 2 - CI exitoso y CD exitoso (8 %)

Objetivo: commit valido -> imagen nueva -> despliegue blue/green completado.

1. Haz un cambio visible, por ejemplo una nueva version en `/health` o un texto, y mergealo a `main`:

```bash
git switch -c escenario-2-cd-exitoso
# cambio sencillo y valido
git commit -am "Escenario 2: cambio valido para CI/CD exitoso"
git push -u origin escenario-2-cd-exitoso
```

2. Haz merge a `main`. El pipeline debe arrancar solo (sin pulsar *Release change*).
3. Mientras corre, ve a CodeDeploy y a ECS para capturar el cambio de trafico.

**E-9.1:** GitHub: commit/PR mergeado en `main` (SHA visible).
**E-9.2:** pipeline en ejecucion mostrando que **arranco automaticamente** (trigger: push) y el commit que lo disparo.
**E-9.3:** pipeline terminado con **Source, Build y Deploy en verde (Succeeded)**.
**E-9.4:** CodeBuild: build exitoso con pruebas aprobadas (`pytest` OK) y `docker push`.
**E-9.5:** ECR con la imagen nueva (tag = SHA del commit).
**E-9.6:** CodeDeploy -> **Deployments** -> el despliegue en *Succeeded*, con los pasos (Install, Allow test traffic, Reroute, Terminate original). Idealmente una captura durante el *shift* de trafico.
**E-9.7:** ECS -> servicio: nueva revision de task definition y tareas `RUNNING` (durante el despliegue se ven 2 task sets: original y replacement).
**E-9.8:** target groups: el trafico paso de blue a green (o viceversa); target `healthy`.
**E-9.9:** Postman `GET /health` mostrando la **nueva version** (SHA) y la corrida de la coleccion en verde.
**E-9.10:** CloudWatch Logs de la tarea nueva.

**Hallazgos a documentar:** duracion de cada etapa, cero caidas (blue/green), la version cambio en `/health`, la tarea vieja se termino al final.

## Parte 10. Escenario 3 - CI exitoso y CD fallido (8 %)

Objetivo: las pruebas unitarias pasan, la imagen se construye y se sube, pero CodeDeploy **no logra** dejar el servicio sano y hace **rollback**.

Forma sugerida de provocarlo (las pruebas no lo detectan): en el `Dockerfile` cambia el puerto de gunicorn a uno distinto del que declara la task definition y el target group:

```dockerfile
CMD ["gunicorn", "-b", "0.0.0.0:9000", "wsgi:app"]
```

El contenedor arranca, pero el health check del target group (puerto 8000) falla -> las tareas nuevas se marcan `unhealthy` y ECS/CodeDeploy no pueden completar el despliegue.

```bash
git switch -c escenario-3-cd-fallido
# editar Dockerfile (puerto equivocado)
git commit -am "Escenario 3: puerto incorrecto para provocar fallo de despliegue"
git push -u origin escenario-3-cd-fallido
# merge a main
```

**E-10.1:** GitHub: el commit con el cambio del `Dockerfile` (diff).
**E-10.2:** pipeline: Source y Build en verde, **Deploy en rojo (Failed)**.
**E-10.3:** CodeBuild exitoso (`pytest` OK; la imagen se subio).
**E-10.4:** ECR con la imagen del commit defectuoso.
**E-10.5:** CodeDeploy -> despliegue *Failed* / *Stopped* con el motivo del error y el **rollback** (el evento de rollback). Incluye la pestana *Events* o el mensaje de error.
**E-10.6:** ECS -> servicio: **Events** con las tareas fallando (`unhealthy`, `failed container health checks`) y la tarea original sigue activa.
**E-10.7:** target group con los targets nuevos `unhealthy`.
**E-10.8:** Postman `GET /health` -> sigue 200 con la **version anterior** (el rollback protege produccion).
**E-10.9:** CloudWatch Logs de la tarea defectuosa.

**Hallazgos a documentar:** por que paso CI y fallo CD (las pruebas unitarias no validan puerto/health del contenedor), como se detecto, que hizo CodeDeploy (rollback), impacto sobre produccion (ninguno), y como corregirlo.

Despues, **revierte** el commit y haz merge para dejar `main` sano; verifica que el pipeline vuelve a pasar (captura opcional **E-10.10**).

---

## Parte 11. Capturas para el video y el documento final

Para el video (maximo 10 min, el tutor corta despues del minuto 10) ten abiertas estas pestanas, en este orden:

1. GitHub: repo, `Dockerfile`, `buildspec.yml`, `taskdef.json`, `appspec.yaml`, historial de commits (E-4.x).
2. Postman: coleccion y escenarios de los endpoints (E-3.7, E-3.8).
3. ECR, ECS (cluster, servicio, tareas), ALB y target groups (E-1.x a E-3.x).
4. CodeBuild y CodeDeploy: configuracion (E-5.x, E-6.x).
5. CodePipeline: configuracion y las 3 ejecuciones (E-7.x a E-10.x).

Sugerencia de tiempos: 1 min contexto, 2 min Fargate manual, 2 min archivos y configuracion del pipeline, 4 min los tres escenarios, 1 min cierre.

Estructura del documento `Proyecto 1 entrega 3 - Documento.pdf`:

1. Arquitectura (diagrama: GitHub -> CodePipeline -> CodeBuild -> ECR -> CodeDeploy -> ECS Fargate + ALB + RDS) y aclaracion GitHub vs CodeCommit, `main` vs `master`.
2. Despliegue manual en Fargate (E-3.x).
3. Escenario 1 - CI fallido (E-8.x, 4 %).
4. Escenario 2 - CI y CD exitosos (E-9.x, 8 %).
5. Escenario 3 - CI exitoso y CD fallido (E-10.x, 8 %).
6. Conclusiones y lecciones aprendidas.

## Checklist final

- [ ] E-0 a E-3: Fargate manual funcionando y probado con Postman.
- [ ] E-4 a E-7: archivos en `main`, CodeBuild, CodeDeploy y CodePipeline configurados con trigger en push.
- [ ] E-8: CI fallido capturado.
- [ ] E-9: CI + CD exitosos capturados.
- [ ] E-10: CI exitoso + CD fallido capturado.
- [ ] `main` quedo sano al terminar los escenarios.
- [ ] Secretos y tokens ocultos en todas las capturas.
- [ ] Documento exportado como `Proyecto 1 entrega 3 - Documento.pdf`.
- [ ] Video de maximo 10 min grabado.

## Limpieza (al terminar, para no gastar presupuesto del lab)

Baja el servicio ECS a 0 tareas o eliminalo, borra el ALB, la RDS y los repositorios ECR que ya no uses. Haz esto **despues** de tener todas las capturas y el video.
