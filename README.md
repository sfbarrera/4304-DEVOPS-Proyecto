# Blacklist Microservice — Entrega 1

Microservicio REST para gestión de listas negras de emails, desarrollado con **Flask** y desplegable en **AWS Elastic Beanstalk**.

---

## Stack tecnológico

| Componente | Versión |
|---|---|
| Python | 3.8+ |
| Flask | 2.3 |
| Flask-SQLAlchemy | 3.1 |
| Flask-RESTful | 0.3 |
| Flask-Marshmallow | 0.15 |
| Flask-JWT-Extended | 4.5 |
| Werkzeug | 2.3 |
| PostgreSQL (AWS RDS) | 14+ |
| Gunicorn | 21.2 |

---

## Estructura del proyecto

```
blacklist-microservice/
├── app.py                  # Application factory
├── application.py          # WSGI entry point para Beanstalk
├── extensions.py           # SQLAlchemy + Marshmallow compartidos
├── models/
│   └── blacklist.py        # Modelo BlacklistEntry
├── schemas/
│   └── blacklist_schema.py # Validación y serialización
├── routes/
│   └── blacklist_routes.py # Endpoints POST y GET
├── tests/
│   └── test_blacklist.py   # 10 pruebas unitarias
├── generate_token.py       # Genera el Bearer token estático
├── requirements.txt
├── Procfile
└── .env.example
```

---

## Instalación local

```bash
# 1. Clonar y entrar al directorio
git clone <repo-url>
cd blacklist-microservice

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con sus credenciales de RDS

# 5. Ejecutar en modo desarrollo (usa SQLite por defecto)
python app.py
```

---

## Generar el Bearer Token

```bash
python generate_token.py
```

Copia el token impreso y úsalo en Postman como:

```
Authorization: Bearer <token>
```

---

## API Reference

### `POST /blacklists`
Agrega un email a la lista negra global.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Body:**
```json
{
  "email": "spam@example.com",
  "app_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "blocked_reason": "Reporte de spam reiterado"
}
```

**Respuesta 201:**
```json
{
  "msg": "Email 'spam@example.com' was successfully added to the blacklist.",
  "id": "a1b2c3d4-..."
}
```

**Respuesta 409** (email ya existe):
```json
{
  "msg": "The email 'spam@example.com' is already in the blacklist.",
  "id": "a1b2c3d4-..."
}
```

---

### `GET /blacklists/<email>`
Consulta si un email está en la lista negra.

**Headers:**
```
Authorization: Bearer <token>
```

**Respuesta 200 — en lista negra:**
```json
{
  "blacklisted": true,
  "email": "spam@example.com",
  "blocked_reason": "Reporte de spam reiterado",
  "created_at": "2024-01-15T10:30:00"
}
```

**Respuesta 200 — no está en lista negra:**
```json
{
  "blacklisted": false,
  "email": "clean@example.com",
  "blocked_reason": null
}
```

---

### `GET /health`
Health check para AWS Beanstalk.

**Respuesta 200:**
```json
{ "status": "healthy" }
```

---

## Ejecución de pruebas

```bash
python -m pytest tests/ -v
```

---

## Despliegue en AWS Elastic Beanstalk

### Prerequisitos
- AWS CLI configurado
- EB CLI instalado (`pip install awsebcli`)
- Instancia RDS PostgreSQL creada en AWS

### Pasos

```bash
# 1. Inicializar EB
eb init -p python-3.11 blacklist-service --region us-east-1

# 2. Crear entorno con variables de entorno
eb create blacklist-env \
  --envvars DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/db,\
JWT_SECRET_KEY=my-secret-key

# 3. Desplegar
eb deploy

# 4. Ver estado
eb status
eb health
```

### Variables de entorno en Beanstalk
Configure en **Configuration → Software → Environment properties**:

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | URL de conexión a RDS PostgreSQL |
| `JWT_SECRET_KEY` | Clave secreta para firmar los JWT |

---

## Estrategias de despliegue documentadas (Entrega)

| Estrategia | Instancias mínimas | Downtime |
|---|---|---|
| All-at-once | 1 | Sí |
| Rolling | 3+ | No |
| Rolling with additional batch | 3+ | No |
| Immutable | 3+ (duplica temporalmente) | No |
| Traffic splitting | 3+ | No |
