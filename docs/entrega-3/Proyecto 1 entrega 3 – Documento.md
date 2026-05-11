# Proyecto 1 Entrega 3 – Documento

## 1. Pipeline de Integración Continua Fallido

### Descripción del escenario

Se ejecutó el pipeline CI/CD identificado como `bcd1b1d1` resultando en un fallo durante la etapa de Build debido a errores de permisos IAM y dependencias faltantes. El pipeline detuvo automáticamente su ejecución para prevenir el despliegue de código defectuoso en el ambiente de producción.

### Evidencias

#### Ejecución del Pipeline Fallida en CodePipeline

![Pipeline execution failed](images/pipeline-execution-failed.jpeg)

El pipeline detectó el error en la fase de Build y detuvo la ejecución automáticamente, previniendo que código defectuoso avanzara a las fases de Test y Deploy.

#### Logs Detallados del Build Fallido en CodeBuild

![CodeBuild failed logs](images/codebuild-failed-logs.jpeg)

Los logs muestran dos errores secuenciales: primero un `AccessDeniedException` por falta de permisos IAM, y segundo un error al intentar instalar dependencias con `requirements.txt` no encontrado.

### Análisis de los Hallazgos

**Problema 1: Error de Permisos IAM**

El rol de servicio de CodePipeline (`AWSCodePipelineServiceRole-us-east-1-pipeline-blacklist-fargate`) no cuenta con los permisos necesarios para invocar el proyecto de CodeBuild `codebuild-blacklist-tests`. Específicamente, falta la acción `codebuild:StartBuild` en la política de permisos del rol.

**Problema 2: Archivo requirements.txt No Encontrado**

Durante la fase de instalación (`INSTALL`), el comando `pip install -r requirements.txt` falló porque no pudo localizar el archivo requirements.txt en el directorio de trabajo esperado (`/codebuild/output/src2397884432/src`).

**Comportamiento del Pipeline**

El pipeline funcionó correctamente al:
- ✅ Detectar el error en la fase más temprana posible (Build)
- ✅ Detener inmediatamente la ejecución del pipeline
- ✅ Prevenir que se ejecuten las fases subsiguientes (Test y Deploy)
- ✅ No construir ninguna imagen Docker defectuosa
- ✅ No intentar ningún despliegue al ambiente de producción
- ✅ Mantener el servicio en producción sin afectación

**Solución Implementada**

1. Se agregó la política necesaria al rol de CodePipeline:
```bash
aws iam put-role-policy \
  --role-name AWSCodePipelineServiceRole-us-east-1-pipeline-blacklist-fargate \
  --policy-name AllowAllCodeBuildProjects \
  --policy-document '{
    "Version":"2012-10-17",
    "Statement":[{
      "Effect":"Allow",
      "Action":[
        "codebuild:StartBuild",
        "codebuild:BatchGetBuilds",
        "codebuild:BatchGetBuildBatches",
        "codebuild:StartBuildBatch"
      ],
      "Resource":"*"
    }]
  }'
```

2. Se configuró correctamente el artefacto de entrada para el proyecto de tests en el pipeline (usar `SourceArtifact` en lugar de `BuildArtifact`).

---

## 2. Pipeline de Integración Continua Exitoso y Entrega Continua Exitosa

### Descripción del escenario

Ejecución completa y exitosa del pipeline CI/CD de 4 etapas (Source → Build → Test → Deploy), desde la detección del cambio en GitHub hasta el despliegue en AWS ECS Fargate con estrategia Rolling Update. Todas las etapas completaron satisfactoriamente.

### Arquitectura del Pipeline Implementado

**Nota importante sobre CodeDeploy:** Debido a limitaciones del free tier de AWS Academy, no fue posible utilizar AWS CodeDeploy para implementar estrategias avanzadas como Blue/Green deployment. En su lugar, se utilizó la acción nativa de Amazon ECS en CodePipeline, que realiza Rolling Updates directamente sobre el servicio de Fargate.

**Componentes del pipeline:**

```
GitHub (rama main)
    ↓
CodePipeline (orchestration)
    ├─ Source: GitHub App connection
    ├─ Build: CodeBuild (build imagen Docker → push a ECR)
    ├─ Test: CodeBuild (pytest unitarios)
    └─ Deploy: Amazon ECS (Rolling Update en Fargate)
```

**Infraestructura de ejecución:**
- **ECS Cluster:** cluster-grupo11-ecs-prod
- **ECS Service:** service-blacklist (launch type: FARGATE)
- **Task Definition:** blacklist-task (CPU: 256, RAM: 512MB)
- **ECR Repository:** grupo11_app
- **Application Load Balancer:** LB-python-app
- **Target Group:** tg-blacklist-1 (HTTP:5000)
- **RDS Database:** PostgreSQL (de entrega anterior)
- **Endpoint público:** http://LB-python-app-1142898639.us-east-1.elb.amazonaws.com

### Evidencias

#### Vista General del Pipeline Exitoso con 4 Etapas

![Pipeline all stages success](images/pipeline-all-stages-success.jpeg)

Ejecución completa exitosa de las 4 etapas del pipeline: Source → Build → Test → Deploy.

#### Timeline Detallado de la Ejecución

![Pipeline overview success](images/pipeline-overview-success.jpeg)

Duración total aproximada: 7 minutos desde trigger hasta deployment completo en producción.

#### Configuración del Pipeline

**Configuración General del Pipeline**

![Pipeline general config](images/pipeline-general-config.jpeg)

Configurado en modo "Reemplazadas" (superseded) para que commits nuevos cancelen ejecuciones previas en progreso.

**Etapa Source - Conexión con GitHub**

![Source stage config](images/pipeline-source-github-config.jpeg)

Integración mediante GitHub App con webhook habilitado para ejecución automática en eventos de push y pull request al branch main.

**Etapa Build - Construcción de Imagen Docker**

![Build stage config](images/pipeline-config-build-stage.jpeg)
![Build stage detailed config](images/pipeline-build-stage-config.jpeg)

CodeBuild ejecuta `buildspec.yml` que construye la imagen Docker, la sube a ECR con tag del commit hash, y genera `imagedefinitions.json` para la etapa de Deploy.

**Etapa Test - Pruebas Unitarias**

![Test stage config](images/pipeline-test-stage-config.jpeg)

Proyecto CodeBuild separado que ejecuta pytest con buildspec inline. **Importante:** Usa `SourceArtifact` como entrada (no `BuildArtifact`) para ejecutar tests sobre el código fuente directamente.

**Etapa Deploy - Despliegue en Fargate**

![Deploy stage config](images/pipeline-deploy-stage-config.jpeg)

Utiliza acción nativa de Amazon ECS para Rolling Update (no CodeDeploy por limitaciones de free tier). El deployment actualiza la Task Definition con la nueva imagen y realiza el switchover de manera gradual con health checks del ALB.

#### Configuración de ECS Fargate

**Creación del Cluster ECS**

![ECS cluster creation](images/ecs-create-cluster-fargate.jpeg)

Cluster configurado con infraestructura Fargate (serverless) para evitar la gestión de instancias EC2.

**Task Definition**

![Task definition config](images/ecs-task-definition-config.jpeg)

Task Definition con Fargate, rol `ecsTaskExecutionRole` para pull de imágenes de ECR y envío de logs a CloudWatch.

**Detalles del Contenedor**

![Container details](images/ecs-container-details-env-vars.jpeg)

Contenedor configurado con imagen de ECR privada, puerto 5000, y variables de entorno para conexión a RDS PostgreSQL, JWT secret y ambiente Flask. Logs enviados a CloudWatch `/ecs/blacklist-task`.

#### Application Load Balancer y Target Group

![Target group healthy](images/alb-target-group-healthy.jpeg)

Target Group tipo IP (requerido para Fargate awsvpc) con 1 target healthy. Health check configurado en path `/health` validando que la aplicación está respondiendo correctamente.

#### Infraestructura de Red (VPC, Subnets, Security Groups)

**VPC Configurada**

![VPC details](images/vpc-details.jpeg)

VPC con CIDR 10.0.0.0/16, 4 subnets (2 públicas y 2 privadas distribuidas en us-east-1a y us-east-1b), Internet Gateway, NAT Gateway, y VPC Endpoint para S3.

**Application Load Balancer**

![ALB details](images/alb-load-balancer-details.jpeg)

ALB internet-facing distribuido en 2 AZs (us-east-1a y us-east-1b). Listeners en puertos 80 y 8080 reenviando tráfico a target groups.

**Target Group Detalles**

![Target Group details](images/alb-target-group-details.jpeg)

**Security Group - Fargate Tasks**

![Security Group Fargate](images/security-group-fargate.jpeg)

Permite tráfico TCP en puerto 5000 únicamente desde el Security Group del ALB, restringiendo el acceso directo a las tasks.

**Security Group - RDS Database**

![Security Group RDS](images/security-group-rds.jpeg)

Permite conexiones PostgreSQL (5432) desde las tasks de Fargate y una IP específica para administración.

**Security Group - Application Load Balancer**

![Security Group ALB](images/security-group-alb.jpeg)

Permite tráfico HTTP desde Internet (0.0.0.0/0) en puertos 80 y 8080. El flujo de red completo es: Internet → ALB (80/8080) → Fargate (5000) → RDS (5432).

### Validación del Deployment

**Verificación del endpoint público:**

```bash
curl http://LB-python-app-1142898639.us-east-1.elb.amazonaws.com/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "version": "all-at-once-v2"
}
```

**Status Code:** 200 OK

**Prueba de funcionalidad completa del microservicio:**

```bash
# 1. Generar token JWT
python generate_token.py

# 2. Agregar email a blacklist
curl -X POST http://LB-python-app-1142898639.us-east-1.elb.amazonaws.com/blacklists \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "app_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "blocked_reason": "Spam reiterado"
  }'

# Respuesta esperada: 201 Created
{
  "msg": "Email 'test@example.com' was successfully added to the blacklist.",
  "id": "uuid-generado"
}

# 3. Consultar email en blacklist
curl http://LB-python-app-1142898639.us-east-1.elb.amazonaws.com/blacklists/test@example.com \
  -H "Authorization: Bearer <token>"

# Respuesta esperada: 200 OK
{
  "blacklisted": true,
  "email": "test@example.com",
  "blocked_reason": "Spam reiterado",
  "created_at": "2026-05-09T04:45:00"
}
```

### Análisis del Flujo CI/CD Completo

El pipeline ejecuta automáticamente 4 fases en aproximadamente 7 minutos:

1. **Source:** Webhook de GitHub notifica a CodePipeline
2. **Build:** Construye imagen Docker, la tagea con commit hash, sube a ECR y genera `imagedefinitions.json`
3. **Test:** Ejecuta pytest con todas las dependencias
4. **Deploy:** ECS actualiza Task Definition, inicia nuevas tasks, valida health checks, y realiza switchover gradual terminando las tasks antiguas solo después de que las nuevas estén saludables

**Ventajas del pipeline implementado:**

1. ✅ **Automatización completa:** Cero intervención manual desde commit hasta producción
2. ✅ **Validación de calidad:** Pruebas unitarias ejecutadas en cada deployment
3. ✅ **Sin downtime:** Rolling Update mantiene servicio disponible durante deployment
4. ✅ **Trazabilidad:** Cada deployment ligado a commit específico de Git
5. ✅ **Segregación de responsabilidades:** Build y Test en etapas separadas
6. ✅ **Contenedorización:** Consistencia entre ambientes dev/prod
7. ✅ **Infraestructura serverless:** Fargate elimina gestión de servidores
8. ✅ **Health checks:** ALB garantiza que solo tasks saludables reciban tráfico
9. ✅ **Logs centralizados:** CloudWatch Logs para troubleshooting
10. ✅ **Seguridad:** Variables sensibles en Task Definition, no en código

---

## Implementación Paso a Paso del Pipeline CI/CD

Esta sección documenta el proceso completo de implementación del pipeline CI/CD para el microservicio Blacklist en AWS Fargate, desde la preparación del código hasta la validación del despliegue.

### Fase 0: Pre-requisitos

- Cuenta AWS personal (no Academy)
- AWS CLI v2 instalado y autenticado (`aws configure`)
- Repositorio Git en GitHub: `sfbarrera/4304-DEVOPS-Proyecto`
- Microservicio Flask funcional con tests pytest
- RDS PostgreSQL ya provisionado (de la entrega anterior)
- Región: `us-east-1`

### Fase 1: Preparar el Código para Containerización

**Archivos creados:**

1. **Dockerfile** - Imagen base python:3.11-slim, instala dependencias, expone puerto 5000, ejecuta con gunicorn
2. **.dockerignore** - Excluye `.git/`, `__pycache__/`, `tests/`, `.env*` para mantener imagen liviana
3. **taskdef.json** - Task Definition para Fargate (CPU 256, RAM 512, contenedor blacklist-app, puerto 5000, env vars DATABASE_URL y JWT_SECRET_KEY, logs a CloudWatch `/ecs/blacklist-task`)
4. **buildspec.yml** - Define fases: install (deps) → pre_build (pytest + login ECR) → build (docker build) → post_build (push + imagedefinitions.json)

Los archivos se subieron al repositorio para ser utilizados por el pipeline.

### Fase 2: Infraestructura Base AWS

**2.1 Crear repositorio ECR:**
```bash
aws ecr create-repository --repository-name grupo11_app --region us-east-1
```

**2.2 IAM Role ecsTaskExecutionRole:**
- Rol para que Fargate haga pull de ECR y envíe logs a CloudWatch
- Trust: `ecs-tasks.amazonaws.com`
- Policy: `AmazonECSTaskExecutionRolePolicy` + permiso `logs:CreateLogGroup`

```bash
aws iam create-service-linked-role --aws-service-name ecs.amazonaws.com

aws iam put-role-policy --role-name ecsTaskExecutionRole \
  --policy-name AllowCreateLogGroup \
  --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["logs:CreateLogGroup"],"Resource":"*"}]}'
```

**2.3 CloudWatch Log Group:**
```bash
aws logs create-log-group --log-group-name /ecs/blacklist-task --region us-east-1
```

**2.4 Application Load Balancer:**
- Nombre: `LB-python-app`
- Esquema: internet-facing, IPv4
- Subnets: 2 subnets públicas en AZs distintas
- Security Group: permite 0.0.0.0/0:80 y :8080 entrante
- Listener: HTTP 80 → forward a Target Group

**2.5 Target Group:**
- Nombre: `tg-blacklist-1`
- Tipo: IP (obligatorio para Fargate awsvpc)
- Protocolo: HTTP, puerto 5000
- Health check: path `/health`, intervalo 30s

**2.6 Security Groups:**
- **fargate-blacklist:** Permite tráfico desde ALB en puerto 5000
- **grupo11-rds-vpc:** Permite PostgreSQL (5432) desde Fargate
- **alb-blacklist:** Permite HTTP (80, 8080) desde Internet

### Fase 3: Provisionar ECS Fargate

**3.1 Crear ECS Cluster:**
```bash
aws ecs create-cluster --cluster-name cluster-grupo11-ecs-prod --region us-east-1
```

**3.2 Editar taskdef.json con valores reales:**
- Reemplazar `REPLACE_AWS_ACCOUNT_ID`
- Reemplazar `REPLACE_RDS_PASSWORD_URL_ENCODED`
- Reemplazar `REPLACE_RDS_ENDPOINT`
- Reemplazar `REPLACE_WITH_A_LONG_RANDOM_SECRET`

**Nota:** La versión en el repo tiene placeholders por seguridad

**3.3 Registrar Task Definition:**
```bash
aws ecs register-task-definition --cli-input-json file://taskdef.json --region us-east-1
```
Resultado: `blacklist-task:1`

**3.4 Crear ECS Service:**
```bash
aws ecs create-service \
  --cluster cluster-grupo11-ecs-prod \
  --service-name service-blacklist \
  --task-definition blacklist-task:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --deployment-controller type=ECS \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:799884780595:targetgroup/tg-blacklist-1/57ce64ace74a159c,containerName=blacklist-app,containerPort=5000" \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-0e95a90fd61db97b0,subnet-0efaab20187bd49cb],securityGroups=[sg-0d79ab186a6b5e803],assignPublicIp=ENABLED}" \
  --health-check-grace-period-seconds 60 \
  --region us-east-1
```

**3.5 Validar servicio:**
```bash
curl http://LB-python-app-1142898639.us-east-1.elb.amazonaws.com/health
```
Respuesta esperada: `{"status":"healthy","version":"all-at-once-v2"}`

### Fase 4: CodeBuild - Integración Continua

**4.1 Proyecto Build: codebuild-blacklist-build**
- Source: GitHub (vía GitHub App) → repo, rama main
- Environment: Managed image, Ubuntu, runtime estándar
- **Privileged mode: ✅ ON** (necesario para docker build)
- Service role: con permisos ECR push y CloudWatch Logs
- Buildspec: `buildspec.yml` del repo

**Variables de entorno:**
```
AWS_DEFAULT_REGION = us-east-1
AWS_ACCOUNT_ID = 799884780595
IMAGE_REPO_NAME = grupo11_app
CONTAINER_NAME = blacklist-app
```

**4.2 Proyecto Test: codebuild-blacklist-tests**
- Source: CODEPIPELINE (invocado por pipeline)
- Environment: Ubuntu, sin privileged mode
- Buildspec inline (ver sección anterior)

### Fase 5: CodePipeline - Entrega Continua

**5.1 Crear pipeline: pipeline-blacklist-fargate**
- Tipo: V2
- Service role: creado automáticamente

**5.2 Stage Source:**
- Provider: GitHub (Version 2) vía GitHub App
- Repo: `sfbarrera/4304-DEVOPS-Proyecto`, branch `main`
- Output artifact: `SourceArtifact`

**5.3 Stage Build:**
- Action: AWS CodeBuild
- Project: `codebuild-blacklist-build`
- Input: `SourceArtifact`
- Output: `BuildArtifact` (contiene imagedefinitions.json)

**5.4 Stage Test:**
- Action: AWS CodeBuild
- Project: `codebuild-blacklist-tests`
- Input: `SourceArtifact` (clave: NO usar BuildArtifact)
- Output: ninguno

**5.5 Stage Deploy:**
- Action: Amazon ECS (no CodeDeploy)
- Cluster: `cluster-grupo11-ecs-prod`
- Service: `service-blacklist`
- Input: `BuildArtifact`
- Image definitions file: `imagedefinitions.json`

**Nota sobre CodeDeploy:** Debido a limitaciones del free tier de AWS Academy, no se pudo utilizar AWS CodeDeploy. Se utilizó la acción nativa de Amazon ECS que realiza Rolling Updates.

**5.6 Permiso adicional para service role:**
```bash
aws iam put-role-policy \
  --role-name AWSCodePipelineServiceRole-us-east-1-pipeline-blacklist-fargate \
  --policy-name AllowAllCodeBuildProjects \
  --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["codebuild:StartBuild","codebuild:BatchGetBuilds","codebuild:BatchGetBuildBatches","codebuild:StartBuildBatch"],"Resource":"*"}]}'
```

### Fase 6: Ejecución y Validación

**6.1 Lanzar primera ejecución:**
```bash
aws codepipeline start-pipeline-execution --name pipeline-blacklist-fargate --region us-east-1
```

**6.2 Verificar etapas:**
```bash
aws codepipeline get-pipeline-state --name pipeline-blacklist-fargate --region us-east-1 \
  --query "stageStates[].{stage:stageName,status:latestExecution.status}"
```
Resultado esperado: Source ✓, Build ✓, Test ✓, Deploy ✓

**6.3 Verificar Rolling Update:**
```bash
aws ecs describe-services --cluster cluster-grupo11-ecs-prod --services service-blacklist --region us-east-1 \
  --query "services[0].deployments[].{status:status,taskDef:taskDefinition,rolloutState:rolloutState}"
```
Deployment PRIMARY con `rolloutState: COMPLETED`

**6.4 Validar servicio:**
```bash
curl http://LB-python-app-1142898639.us-east-1.elb.amazonaws.com/health
```

**6.5 Listar revisiones de Task Definition:**
```bash
aws ecs list-task-definitions --family-prefix blacklist-task --region us-east-1 --query "taskDefinitionArns"
```
La revisión `:1` fue creada manualmente, de `:2` en adelante las genera el pipeline automáticamente.

### Consideraciones Importantes

**Limitaciones del Free Tier:**
- No hay acceso a CodeDeploy en AWS Academy
- No se puede implementar Blue/Green deployment
- Se utiliza Rolling Update de ECS como alternativa

**Fargate como Servicio Serverless:**
- AWS gestiona automáticamente direcciones IP y configuración de red
- No hay acceso directo a las máquinas subyacentes
- A diferencia de ECS con EC2, no se puede acceder con SSH

**Variables Sensibles:**
- `taskdef.json` con credenciales NO se sube a GitHub
- Se guardan en Task Definition de forma similar a Kubernetes Secrets
- Las variables pueden cargarse vía JSON o configurarse en consola

**Arquitectura de Red:**
- Fargate usa puerto 5000 (contenedor)
- ALB maneja tráfico en puertos 80 y 8080
- Security Groups habilitan conexión: ALB → Fargate → RDS
- Target Groups permiten que ALB vea el servicio Fargate

---

## 3. Pipeline de Integración Continua Exitoso y Entrega Continua Fallida con Rollback Automático

### Descripción del escenario

Las fases de CI (Source, Build, Test) se completan exitosamente, pero el deployment en ECS Fargate falla. El Deployment Circuit Breaker de AWS ECS detecta el fallo y realiza un rollback automático a la versión estable anterior, protegiendo el servicio en producción.

### Configuración del Deployment Circuit Breaker

Para proteger el servicio en producción contra deployments defectuosos, se habilitó el **Deployment Circuit Breaker** en el servicio ECS:

```bash
aws ecs update-service \
  --cluster cluster-grupo11-ecs-prod \
  --service service-blacklist \
  --deployment-configuration "deploymentCircuitBreaker={enable=true,rollback=true},maximumPercent=200,minimumHealthyPercent=100" \
  --region us-east-1
```

**Parámetros configurados:**
- **enable=true:** Activa el circuit breaker
- **rollback=true:** Realiza rollback automático si el deployment falla
- **maximumPercent=200:** Permite hasta 2x tasks durante el deployment (Rolling Update)
- **minimumHealthyPercent=100:** Mantiene 100% de capacidad healthy en todo momento

### Configuración de las Etapas CI que Pasaron

**Buildspec de la etapa Test (codebuild-blacklist-tests):**

```yaml
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.11
    commands:
      - python -m pip install --upgrade pip
      - pip install -r requirements.txt
      - pip install -r requirements-dev.txt
  build:
    commands:
      - echo "==== Ejecutando pruebas unitarias ===="
      - pytest -v --maxfail=1 --disable-warnings
      - echo "==== Pruebas finalizadas ===="
```

Las pruebas pasaron exitosamente, pero el deployment posterior falló.

**Task Definition que intentó desplegarse (revisión 4):**

```json
{
  "taskDefinitionArn": "arn:aws:ecs:us-east-1:799884780595:task-definition/blacklist-task:4",
  "containerDefinitions": [
    {
      "name": "blacklist-app",
      "image": "799884780595.dkr.ecr.us-east-1.amazonaws.com/grupo11_app:524aaad",
      "cpu": 0,
      "portMappings": [
        {
          "containerPort": 5000,
          "hostPort": 5000,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "environment": [
        {
          "name": "JWT_SECRET_KEY",
          "value": "wAnVKqcsE0Mle9dg7WNJikUpOYtCxhuGrDSHT8B1XLIaZ6jz"
        },
        {
          "name": "FLASK_ENV",
          "value": "production"
        },
        {
          "name": "DATABASE_URL",
          "value": "postgresql://postgres:ip%3ACqP-8H%21e8S2L@grupo11-rds.c8tw88iy01de.us-east-1.rds.amazonaws.com:5432/postgres?sslmode=require"
        }
      ],
      "mountPoints": [],
      "volumesFrom": [],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/blacklist-task",
          "awslogs-create-group": "true",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "systemControls": []
    }
  ],
  "family": "blacklist-task",
  "executionRoleArn": "arn:aws:iam::799884780595:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "revision": 4,
  "volumes": [],
  "status": "ACTIVE",
  "requiresAttributes": [
    {
      "name": "com.amazonaws.ecs.capability.logging-driver.awslogs"
    },
    {
      "name": "ecs.capability.execution-role-awslogs"
    },
    {
      "name": "com.amazonaws.ecs.capability.ecr-auth"
    },
    {
      "name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"
    },
    {
      "name": "ecs.capability.execution-role-ecr-pull"
    },
    {
      "name": "com.amazonaws.ecs.capability.docker-remote-api.1.18"
    },
    {
      "name": "ecs.capability.task-eni"
    },
    {
      "name": "com.amazonaws.ecs.capability.docker-remote-api.1.29"
    }
  ],
  "placementConstraints": [],
  "compatibilities": [
    "EC2",
    "FARGATE",
    "MANAGED_INSTANCES"
  ],
  "requiresCompatibilities": [
    "FARGATE"
  ],
  "cpu": "256",
  "memory": "512",
  "registeredAt": "2026-05-11T01:59:18.808Z",
  "registeredBy": "arn:aws:sts::799884780595:assumed-role/AWSCodePipelineServiceRole-us-east-1-pipeline-blacklist-fargate/1778464758388",
  "tags": []
}
```

Esta Task Definition se registró manualmente con el siguiente comando:

```bash
aws ecs register-task-definition --cli-input-json file://taskdef.json --region us-east-1
```

El pipeline automáticamente intentó desplegar esta revisión 4, pero falló, causando que el circuit breaker activara el rollback.

### Evidencias del Deployment Fallido

#### Pipeline con Deploy Fallido

![Pipeline deploy failed with rollback message](images/pipeline-deploy-failed-rollback-message.jpeg)

Ejecución 7afaffad: Source y Build exitosos, pero Deploy falló. El mensaje indica "The new deployment has failed and rolled back."

#### Vista Detallada del Pipeline con Rollback

![Pipeline execution failed deploy detail](images/pipeline-execution-failed-deploy-detail.jpeg)

Vista completa mostrando Test exitoso pero Deploy fallido. Mensaje de error: "The new deployment has failed and rolled back". Duración total: 25 minutos 2 segundos.

#### Pipeline Mostrando Reversión en Etapa Deploy

![Pipeline deploy stage reverting](images/pipeline-deploy-stage-reverting.jpeg)

Vista del pipeline donde la etapa Deploy muestra el badge "Reversión", indicando que el circuit breaker activó el rollback automático.

#### Tasks de ECS Fallidas y Detenidas

![ECS tasks stopped and failed](images/ecs-tasks-stopped-failed.jpeg)

Lista de tasks en el cluster mostrando múltiples tasks detenidas por el circuit breaker. Se observan tasks en estado "Detenido" con diferentes timestamps indicando los intentos de deployment que fallaron.

### Deployment Fallido y Rollback Automático

**Task Definition desplegada:**
- **Revisión:** blacklist-task:4
- **Imagen:** 799884780595.dkr.ecr.us-east-1.amazonaws.com/grupo11_app:524aaad
- **Registrada:** 2026-05-11T01:59:18.808Z
- **CPU:** 256, **Memory:** 512

**Secuencia del deployment fallido:**

1. **Pipeline ejecuta etapas CI:** Source, Build y Test completan exitosamente
2. **Deploy inicia:** CodePipeline despliega Task Definition revisión 4
3. **ECS inicia nuevas tasks:** Tasks con la nueva imagen 524aaad se levantan
4. **Health checks fallan:** Las tasks no pasan los health checks del ALB en `/health`
5. **Circuit Breaker detecta fallo:** ECS detecta que el deployment no progresa
6. **Rollback automático:** Circuit Breaker revierte al deployment anterior (revisión 3)
7. **Tasks detenidas:** Las tasks fallidas se detienen automáticamente
8. **Servicio estable:** Tasks de la revisión 3 continúan sirviendo tráfico sin interrupción

**Resultado:**
- ✅ El servicio en producción no experimentó downtime
- ✅ La versión estable anterior (revisión 3) continuó operando
- ✅ El pipeline se marcó como FAILED en la etapa de Deploy
- ✅ El circuit breaker protegió la producción automáticamente

### Validación del Servicio Post-Rollback

```bash
curl http://LB-python-app-1142898639.us-east-1.elb.amazonaws.com/health
```

**Respuesta (versión estable tras rollback):**
```json
{
  "status": "healthy",
  "version": "all-at-once-v2"
}
```

El servicio continuó respondiendo correctamente con la versión anterior, confirmando que el rollback automático funcionó correctamente y los usuarios no fueron afectados.
