# Proyecto 1 – Entrega 2: Integración Continua (CI)

**Universidad de los Andes – Curso DevOps**

---

## 1. Descripción General

Este documento registra la configuración y ejecución del pipeline de Integración Continua (CI) implementado para el microservicio de lista negra de correos (*Blacklist Microservice*). El pipeline fue construido sobre **AWS CodePipeline** y **AWS CodeBuild**, con el repositorio alojado en **GitHub**.

El proceso de CI cubre tres responsabilidades principales:

1. Instalación de dependencias en un entorno limpio (Python 3.11).
2. Ejecución automática de pruebas unitarias con **pytest**.
3. Generación del artefacto desplegable (`app.zip`) para AWS Elastic Beanstalk y su almacenamiento en **Amazon S3**.

---

## 2. Configuración del Pipeline de Integración Continua

### 2.1 Herramientas utilizadas

| Herramienta | Rol |
|---|---|
| **GitHub** | Repositorio de código fuente |
| **AWS CodePipeline** | Orquestación del pipeline (Source → Build) |
| **AWS CodeBuild** | Ejecución del build, pruebas y empaquetado |
| **Amazon S3** | Almacenamiento del artefacto generado (`app.zip`) |
| **AWS Elastic Beanstalk** | Plataforma destino del artefacto |

### 2.2 Estructura del pipeline

El pipeline `ebs-pipeline-final` consta de dos etapas:

```
Source (GitHub via GitHub App)
        │
        ▼
Build (AWS CodeBuild)
  ├── INSTALL    → Python 3.11, requirements.txt, requirements-dev.txt
  ├── PRE_BUILD  → pytest (pruebas unitarias)
  ├── BUILD      → zip -r build/app.zip (artefacto para Elastic Beanstalk)
  └── POST_BUILD → confirmación de fecha y hora del build
        │
        ▼
Artefacto: build/app.zip  →  Amazon S3
```

El pipeline se dispara automáticamente con cada *commit* a la rama `main`.

### 2.3 Archivo de configuración (`buildspec.yml`)

El archivo `buildspec.yml` en la raíz del repositorio define las instrucciones de build para AWS CodeBuild:

```yaml
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.11
    commands:
      - echo "Python version:" && python --version
      - python -m pip install --upgrade pip
      - pip install -r requirements.txt
      - pip install -r requirements-dev.txt

  pre_build:
    commands:
      - echo "Running unit tests with pytest..."
      - pytest -q --maxfail=1 --disable-warnings

  build:
    commands:
      - echo "Packaging application for Elastic Beanstalk..."
      - mkdir -p build
      - |
        zip -r build/app.zip . \
          -x "*.git*" \
          -x "tests/*" \
          -x "build/*" \
          -x "*.pyc" \
          -x "*__pycache__*" \
          -x ".venv/*" \
          -x "venv/*" \
          -x "*.zip"
      - echo "Artifact built at build/app.zip"

  post_build:
    commands:
      - echo "Build completed on $(date)"

artifacts:
  files:
    - build/app.zip
  discard-paths: yes
  name: blacklist-$(date +%Y-%m-%d-%H-%M-%S)
```

### 2.4 Escenarios de prueba de la API

Las pruebas unitarias están implementadas con `pytest` usando SQLite en memoria (sin dependencia de base de datos externa), lo que garantiza su ejecución en entornos de CI limpios.

#### Endpoint `POST /blacklists`

| # | Caso de prueba | Resultado esperado |
|---|---|---|
| 1 | Agregar email con motivo | `201 Created` |
| 2 | Agregar email sin motivo | `201 Created` |
| 3 | Email duplicado | `409 Conflict` |
| 4 | UUID de aplicación inválido | `400 Bad Request` |
| 5 | Formato de email inválido | `400 Bad Request` |
| 6 | Motivo con más de 255 caracteres | `400 Bad Request` |
| 7 | Cuerpo sin campo `email` | `400 Bad Request` |
| 8 | Cuerpo sin campo `app_uuid` | `400 Bad Request` |
| 9 | Cuerpo vacío | `400 Bad Request` |
| 10 | Sin token de autorización | `401 Unauthorized` |
| 11 | Token JWT inválido | `401/422` |

#### Endpoint `GET /blacklists/<email>`

| # | Caso de prueba | Resultado esperado |
|---|---|---|
| 12 | Email en lista negra | `200 OK` + `blacklisted: true` |
| 13 | Email no en lista negra | `200 OK` + `blacklisted: false` |
| 14 | Sin token de autorización | `401 Unauthorized` |

#### Endpoint `GET /health`

| # | Caso de prueba | Resultado esperado |
|---|---|---|
| 15 | Health check exitoso | `200 OK` + `status: healthy` |
| 16 | Health check sin autenticación | `200 OK` (endpoint público) |

**Total: 16 pruebas unitarias** cubriendo todos los endpoints de la API.

---

## 3. Ejecución Exitosa del Pipeline

### 3.1 Resumen de la ejecución

| Parámetro | Valor |
|---|---|
| **Pipeline** | `ebs-pipeline-final` |
| **Fecha de inicio** | 2026-04-26 02:08:49 UTC |
| **Fecha de finalización** | 2026-04-26 02:09:14 UTC |
| **Duración total** | ~25 segundos |
| **Estado final** | SUCCEEDED |
| **Artefacto generado** | `build/app.zip` |

### 3.2 Resultado por fase

| Fase | Estado | Detalle |
|---|---|---|
| `DOWNLOAD_SOURCE` | SUCCEEDED | Código descargado del repositorio |
| `INSTALL` | SUCCEEDED | Python 3.11.15, dependencias instaladas |
| `PRE_BUILD` | SUCCEEDED | **16 pruebas pasadas**, 22 advertencias |
| `BUILD` | SUCCEEDED | `app.zip` generado correctamente |
| `POST_BUILD` | SUCCEEDED | Confirmación de fecha |
| `UPLOAD_ARTIFACTS` | SUCCEEDED | Artefacto subido a S3 |

### 3.3 Hallazgos

**Instalación de dependencias:**
CodeBuild instaló todas las dependencias correctamente desde `requirements.txt` (Flask, SQLAlchemy, Flask-JWT-Extended, psycopg2, gunicorn, entre otras) y `requirements-dev.txt` (pytest 8.3.3).

**Ejecución de pruebas:**
```
................                                                         [100%]
16 passed, 22 warnings in 1.33s
```
Las 16 pruebas unitarias pasaron en 1.33 segundos. Las advertencias corresponden a versiones de dependencias pero no afectan la funcionalidad.

**Generación del artefacto:**
El artefacto `build/app.zip` fue generado empaquetando el código fuente de la aplicación, excluyendo archivos de desarrollo (tests, cache, entornos virtuales). El artefacto fue subido exitosamente a Amazon S3.

**Mensaje de finalización:**
```
Build successfully completed on Sun Apr 26 02:09:14 AM UTC 2026
```

### 3.4 Evidencia

**Figura 1:** Vista de la consola de AWS CodeBuild mostrando el log completo del build exitoso.

![Pipeline CI Exitoso](images/success.png)

---

## 4. Ejecución Fallida del Pipeline

### 4.1 Resumen de la ejecución

| Parámetro | Valor |
|---|---|
| **Pipeline** | `ebs-pipeline-final` |
| **ID de ejecución** | `532cdcbf-9ff4-4a11-8065-db921742e0cc` |
| **Disparador** | `CreatePipeline – root` |
| **Duración** | 1 minuto 9 segundos |
| **Estado final** | ERROR |
| **Fase con fallo** | `DOWNLOAD_SOURCE` |

### 4.2 Descripción del error

```
Build terminated with state: FAILED.
Phase: DOWNLOAD_SOURCE
Code: YAML_FILE_ERROR
Message: stat /codebuild/output/src816743214/src/buildspec.yml: no such file or directory
```

### 4.3 Análisis de la causa raíz

El fallo ocurrió durante la fase `DOWNLOAD_SOURCE`, antes de que el build comenzara. AWS CodeBuild intentó leer el archivo de configuración `buildspec.yml` en la raíz del repositorio descargado, pero no lo encontró.

**Causa:** El pipeline `ebs-pipeline-final` fue creado y ejecutado por primera vez antes de que el archivo `buildspec.yml` fuera confirmado (*committed*) en la rama `main` del repositorio. Como resultado, AWS CodeBuild descargó el código fuente pero no pudo localizar el archivo de instrucciones de build.

**Flujo del fallo:**

```
Source (GitHub) → SUCCEEDED  ✅
        │
        ▼
Build (AWS CodeBuild)
  └── DOWNLOAD_SOURCE → FAILED ❌
        Razón: buildspec.yml no encontrado en el directorio fuente
        (el archivo aún no existía en la rama main del repositorio)
```

### 4.4 Hallazgos

- La etapa **Source** completó exitosamente: el código fue descargado desde GitHub sin problemas.
- El fallo ocurrió en la etapa **Build**, específicamente en la subfase de descarga del archivo de configuración (`YAML_FILE_ERROR`).
- El error es determinista: CodeBuild no puede continuar sin el `buildspec.yml`, ya que este archivo define todas las instrucciones del build.
- El fallo fue resuelto agregando el archivo `buildspec.yml` a la raíz del repositorio y realizando un nuevo commit a `main`, lo que disparó automáticamente una ejecución exitosa posterior.

### 4.5 Evidencia

**Figura 2:** Vista de la consola de AWS CodePipeline mostrando la ejecución fallida `532cdcbf` con el mensaje de error `YAML_FILE_ERROR` en la etapa de Build.

![Pipeline CI Fallido](images/failed.jpeg)

---

## 5. Conclusiones

| Aspecto | Resultado |
|---|---|
| Configuración del pipeline (CodePipeline + CodeBuild) | Implementada correctamente |
| Trigger automático en commits a `main` | Funcional |
| Ejecución de pruebas unitarias en CI | 16/16 pruebas pasadas |
| Generación del artefacto en CI | `app.zip` generado y subido a S3 |
| Documentación de ejecución exitosa | Registrada con log y captura de pantalla |
| Documentación de ejecución fallida | Registrada con análisis de causa raíz y captura de pantalla |

El pipeline de CI implementado cumple con todos los requisitos de la entrega: ejecuta pruebas unitarias automáticamente ante cada commit, genera el artefacto listo para despliegue en Elastic Beanstalk, y no realiza despliegue automatizado (CI únicamente, sin CD).
