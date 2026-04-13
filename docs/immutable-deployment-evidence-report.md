# Evidencia: Immutable Deployment — grupo11-eb-v2

**Entorno:** `deployment-inmutable-v2`  
**Aplicación:** `grupo11-eb-v2`  
**URL:** http://deployment-inmutable-v2.us-east-1.elasticbeanstalk.com/  
**Plataforma:** Python 3.11 running on 64bit Amazon Linux 2023 / 4.12.1  
**Estrategia:** Immutable  
**Región:** us-east-1  

---

## Fase 1 — Configuración del entorno

### 1.1 Configuración general del entorno
![Configuración del entorno](/docs/images/immutable-deployment/01-beanstalk-configuracion-entorno.jpeg)

- **Nombre del entorno:** `deployment-inmutable-v2`
- **Nombre de la aplicación:** `grupo11-eb-v2`
- **Plataforma:** Python 3.11 running on 64bit Amazon Linux 2023
- **Versión de la plataforma:** 4.12.1 (Recommended)
- **Preset:** Alta disponibilidad (High availability)

### 1.2 Configuración de red
![Configuración de redes](/docs/images/immutable-deployment/02-beanstalk-configuracion-red.jpeg)

- **VPC:** `vpc-0c9d792235350a1c` (grupo11-aws-vpc)
- **Dirección IP pública:** Activada
- **Subnets seleccionadas:**
  - `us-east-1a` — subnet-0e95a90f6d1db97b0 (público)
  - `us-east-1b` — subnet-0efaab20187bd49cb (público)

### 1.3 Escalado y tráfico de instancias
![Escalado y tráfico](/docs/images/immutable-deployment/05-beanstalk-autoscaling-3-6-instancias.jpeg)

- **Tipo de entorno:** Equilibrio de carga (Load balanced)
- **Número mínimo de instancias:** `3`
- **Número máximo de instancias:** `6`
- **Tipos de instancia:** t3.micro, t3.small
- **Tipo de equilibrador de carga:** Application (ALB)
- **Visibilidad del ALB:** Public
- **Métrica de escalado:** NetworkOut
- **Umbral superior:** 6,000,000 bytes
- **Umbral inferior:** 2,000,000 bytes

### 1.4 Política de implementación — Immutable
![Política Immutable](/docs/images/immutable-deployment/03-beanstalk-politica-immutable.jpeg)

- **Política de implementación:** `Immutable`
- **Umbral de estado:** Aceptar (Ok)
- **Tiempo de espera del comando:** 600 segundos

### 1.5 Variables de entorno y configuración final
![Variables y configuración](/docs/images/immutable-deployment/06-beanstalk-variables-entorno-wsgipath.jpeg)

- **Política de implementación:** Immutable ✓
- **WSGIPath:** `application`
- **Servidor proxy:** nginx
- **Variables de entorno configuradas:**
  - `DATABASE_URL`: postgresql://... (omitido por seguridad)
  - `JWT_SECRET_KEY`: (omitido por seguridad)

### 1.6 Revisión final antes de crear
![Revisión](/docs/images/immutable-deployment/04-beanstalk-revision-final.jpeg)

- **Nombre del entorno:** `deployment-inmutable-v2`
- **Nombre de la aplicación:** `grupo11-eb-v2`
- **Código de la aplicación:** 4.0.0
- **Plataforma:** Python 3.11 on 64bit Amazon Linux 2023/4.12.1
- **Rol de servicio:** aws-elasticbeanstalk-service-role
- **Perfil de instancia EC2:** Instance_Profile_EC2

---

## Fase 2 — Validación del entorno

### 2.1 Health check
![Health check](/docs/images/immutable-deployment/07-postman-health-check-200.png)

- **URL:** `http://deployment-inmutable-v2.us-east-1.elasticbeanstalk.com/health`
- **Método:** GET
- **Status:** `200 OK` — 318 ms
- **Respuesta:** `{"status": "healthy"}` — app operativa en AWS

### 2.2 POST /blacklists — 201 Created
![POST blacklists](/docs/images/immutable-deployment/08-postman-post-blacklist-201.png)

- **URL:** `http://deployment-inmutable-v2.us-east-1.elasticbeanstalk.com/blacklists`
- **Método:** POST
- **Header:** `Authorization: Bearer <token>`
- **Status:** `201 Created`
- **Resultado:** Email agregado exitosamente a la blacklist

### 2.3 GET /blacklists/\<email\> — 200 Ok
![GET blacklists](/docs/images/immutable-deployment/09-postman-get-blacklist-200.png)

- **URL:** `http://deployment-inmutable-v2.us-east-1.elasticbeanstalk.com/blacklists/<email>`
- **Método:** GET
- **Header:** `Authorization: Bearer <token>`
- **Status:** `200 Ok`
- **Resultado:** Email encontrado en la blacklist con `"blacklisted": true`

---

## Fase 3 — Hallazgos

### Ventajas observadas del Immutable deployment

- Las instancias existentes no se modifican en ningún momento del deploy — si el nuevo
  código falla al arrancar, el entorno activo no se ve afectado.
- El tráfico migra únicamente cuando las nuevas instancias pasan el health check,
  garantizando downtime cero.
- Rollback automático disponible si las nuevas instancias no pasan el health check.

### Desventajas observadas

- Durante la transición el número de instancias se duplica (3 → 6) — mayor costo EC2
  durante el período de deploy.
- El tiempo de deploy es mayor que estrategias como Rolling o All at once por el ciclo
  completo de lanzamiento de instancias nuevas.

### Comparación con otras estrategias

| Criterio | Immutable | Rolling | Blue/Green | All at once |
|----------|-----------|---------|------------|-------------|
| Downtime | Cero | Cero | Cero | Sí |
| Rollback | Automático | Manual | Swap URL | Redeploy |
| Costo durante deploy | 2x instancias | Normal | 2x entornos | Normal |
| Tiempo de deploy | ~8-10 min | Medio | ~8-10 min | Rápido |
| Riesgo para producción | Bajo | Medio | Bajo | Alto |
