# Evidencia: All at Once Deployment — grupo11-eb-v2

**Entorno:** `deployment-allatonce-v2`  
**Aplicación:** `grupo11-eb-v2`  
**URL:** http://deployment-allatonce.us-east-1.elasticbeanstalk.com/  
**Plataforma:** Python 3.11 running on 64bit Amazon Linux 2023 / 4.12.1  
**Estrategia:** All at Once (Todo a la vez)  
**Región:** us-east-1  

---

## Qué es All at Once deployment

En esta estrategia Beanstalk despliega la nueva versión **en todas las instancias al mismo tiempo**. Es la estrategia más rápida pero implica que durante el proceso de actualización el servicio puede no estar disponible, ya que todas las instancias se actualizan simultáneamente sin mantener instancias en la versión anterior.

---

## Fase 1 — Configuración del entorno

### 1.1 Configuración general del entorno
![Configuración del entorno](/docs/images/all-at-once-deployment/01-beanstalk-configuracion-entorno.jpeg)

- **Nombre del entorno:** `deployment-allatonce-v2`
- **Nombre de la aplicación:** `grupo11-eb-v2`
- **Plataforma:** Python 3.11 running on 64bit Amazon Linux 2023
- **Versión de la plataforma:** 4.12.1 (Recommended)
- **Código de la aplicación:** Versión existente 4.0.0
- **Preset:** Alta disponibilidad (High availability)

### 1.2 Configuración del acceso al servicio
![Acceso al servicio](/docs/images/all-at-once-deployment/02-beanstalk-acceso-servicio-roles.jpeg)

- **Rol de servicio:** `aws-elasticbeanstalk-service-role`
- **Perfil de instancia EC2:** `Instance_Profile_EC2`

### 1.3 Configuración de red y subnets
![Configuración de red](/docs/images/all-at-once-deployment/03-beanstalk-configuracion-red-subnets.jpeg)

- **VPC:** `vpc-0c9d792235350a1c` (grupo11-aws-vpc)
- **Subnets seleccionadas:**
  - `us-east-1a` — subnet-0e95a90f6d1db97b0 (público)
  - `us-east-1b` — subnet-0efaab20187bd49cb (público)

### 1.4 Escalado — CloudWatch e IMDSv2
![Escalado CloudWatch](/docs/images/all-at-once-deployment/04-beanstalk-escalado-cloudwatch-imds.jpeg)

- **IMDSv1:** Deshabilitado (solo IMDSv2)
- **Intervalo de monitoreo CloudWatch:** 5 minutos
- **Grupos de seguridad EC2:** configurados por defecto

### 1.5 Capacidad — Auto Scaling 3 a 6 instancias
![Auto Scaling](/docs/images/all-at-once-deployment/05-beanstalk-autoscaling-3-6-instancias.jpeg)

- **Tipo de entorno:** Equilibrio de carga (Load balanced)
- **Número mínimo de instancias:** `3`
- **Número máximo de instancias:** `6`
- **Composición de la flota:** Instancias bajo demanda
- **Tipos de instancia:** t3.micro, t3.small
- **Arquitectura:** x86_64
- **Métrica de escalado:** NetworkOut
- **Umbral superior:** 6,000,000 bytes
- **Umbral inferior:** 2,000,000 bytes
- **Tipo de equilibrador de carga:** Application

### 1.6 Configuración del Load Balancer
![Load Balancer](/docs/images/all-at-once-deployment/06-beanstalk-load-balancer-configuracion.jpeg)

- **Visibilidad:** Público
- **Subnets del ALB:** us-east-1a y us-east-1b
- **Tipo de equilibrador de carga:** Application (dedicado)
- **Agente de escucha:** Puerto 80, HTTP

### 1.7 Proceso default — Health check configurado
![Proceso health check](/docs/images/all-at-once-deployment/07-beanstalk-proceso-healthcheck-ruta.jpeg)

- **Nombre:** `default`
- **Puerto:** `80`
- **Protocolo:** HTTP
- **Ruta de comprobación de estado:** `/health`
- **Código HTTP esperado:** `200`
- **Tiempo de espera:** 5 segundos
- **Intervalo:** 15 segundos
- **Umbral de mal estado:** 5 solicitudes
- **Umbral de buen estado:** 3 solicitudes

### 1.8 Agentes de escucha y procesos — resumen
![Agentes y procesos](/docs/images/all-at-once-deployment/08-beanstalk-agentes-escucha-procesos.jpeg)

- **Agente de escucha:** Puerto 80, HTTP, proceso `default` habilitado
- **Proceso default:** Puerto 80, HTTP, código 200, ruta `/health`, persistencia deshabilitada

### 1.9 Monitoreo y actualizaciones administradas
![Monitoreo](/docs/images/all-at-once-deployment/09-beanstalk-monitoreo-actualizaciones.jpeg)

- **Sistema de monitoreo:** Mejorado
- **Métricas CloudWatch instancia:** ApplicationLatencyP50, P75, P85, P90, P95, Requests2xx, Requests3xx, Requests4xx, Requests5xx, CPUSystem
- **Métricas CloudWatch entorno:** ApplicationLatencyP50, P75, P85, P90, P95, Requests2xx, Requests4xx, Requests5xx, InstancesOk
- **Actualizaciones administradas:** Activadas — Sábados a las 00:31 UTC, nivel Minor y parche

### 1.10 Política de implementación — All at Once
![Política All at Once](/docs/images/all-at-once-deployment/10-beanstalk-politica-all-at-once.jpeg)

- **Política de implementación:** `Todo a la vez` (All at Once)
- **Tipo de tamaño de lote:** Porcentaje
- **Umbral de estado:** Aceptar (Ok)
- **Tiempo de espera del comando:** 600 segundos

### 1.11 Software de plataforma y variables de entorno
![Software y variables](/docs/images/all-at-once-deployment/11-beanstalk-software-variables-entorno.jpeg)

- **Servidor proxy:** Nginx
- **Variables de entorno configuradas:**
  - `DATABASE_URL`: postgresql://... (omitido por seguridad)
  - `JWT_SECRET_KEY`: (omitido por seguridad)

---

## Fase 2 — Revisión final de la configuración

### 2.1 Revisión — Entorno, acceso y red
![Revisión entorno y red](/docs/images/all-at-once-deployment/12-beanstalk-revision-entorno-red.jpeg)

- **Nombre del entorno:** `deployment-allatonce-v2`
- **Nombre de la aplicación:** `grupo11-eb-v2`
- **Código de la aplicación:** 4.0.0
- **Plataforma:** Python 3.11 on 64bit Amazon Linux 2023/4.12.1
- **Rol de servicio:** aws-elasticbeanstalk-service-role
- **Perfil de instancia EC2:** Instance_Profile_EC2
- **VPC:** vpc-0c9d792235350a1c
- **Subnets:** subnet-0e95a90f6d1db97b0, subnet-0efaab20187bd49cb

### 2.2 Revisión — Escalado y ALB
![Revisión escalado ALB](/docs/images/all-at-once-deployment/13-beanstalk-revision-escalado-alb.jpeg)

- **Tipo de entorno:** Equilibrio de carga
- **Mínimo de instancias:** 3
- **Máximo de instancias:** 6
- **Tipos de instancia:** t3.micro, t3.small
- **Métrica:** NetworkOut — Umbral superior 6,000,000 / Umbral inferior 2,000,000
- **Equilibrador de carga:** Application, público, dedicado

### 2.3 Revisión final — All at Once confirmado
![Revisión final](/docs/images/all-at-once-deployment/14-beanstalk-revision-final-all-at-once.jpeg)

- **Política de implementación:** `AllAtOnce` ✓
- **WSGIPath:** `application`
- **Servidor proxy:** nginx
- **Umbral de estado:** Ok
- **Variables de entorno:** DATABASE_URL y JWT_SECRET_KEY configuradas

---

## Fase 3 — Validación del entorno

### 3.1 Health check
![Health check](/docs/images/all-at-once-deployment/15-postman-health-check-200.png)

- **URL:** `http://deployment-allatonce.us-east-1.elasticbeanstalk.com/health`
- **Método:** GET
- **Status:** `200 OK` — 163 ms
- **Respuesta:** `{"status": "healthy"}` — app operativa en AWS

### 3.2 POST /blacklists — 201 Created
![POST blacklists](/docs/images/all-at-once-deployment/16-postman-post-blacklist-201.png)

- **URL:** `http://deployment-allatonce.us-east-1.elasticbeanstalk.com/blacklists`
- **Método:** POST
- **Header:** `Authorization: Bearer <token>`
- **Status:** `201 Created`
- **Resultado:** Email agregado exitosamente a la blacklist

### 3.3 GET /blacklists/\<email\> — 200 Ok
![GET blacklists](/docs/images/all-at-once-deployment/17-postman-get-blacklist-200.png)

- **URL:** `http://deployment-allatonce.us-east-1.elasticbeanstalk.com/blacklists/spam2@example.co`
- **Método:** GET
- **Header:** `Authorization: Bearer <token>`
- **Status:** `200 OK` — 81 ms
- **Respuesta:** `{"blacklisted": false, "email": "spam2@example.co", "blocked_reason": null}` — email no encontrado en la blacklist

---

## Fase 3 — Hallazgos

### Métricas del deploy All at Once

| Métrica | Valor observado |
|---------|-----------------|
| Tiempo total del deploy | ___ minutos |
| Instancias actualizadas simultáneamente | 3 (todas a la vez) |
| Downtime durante el deploy | Posible — todas las instancias se actualizan al mismo tiempo |
| Instancias al finalizar | 3 |

### Ventajas observadas

- Es la estrategia más rápida — todas las instancias se actualizan en un solo paso.
- No requiere instancias adicionales durante el deploy — sin costo extra.
- Configuración simple, ideal para entornos de desarrollo o pruebas.

### Desventajas observadas

- Durante el deploy todas las instancias están en actualización simultánea — posible downtime.
- No hay rollback automático — si el deploy falla se debe hacer un nuevo deploy manual.
- No recomendada para producción en servicios que requieren alta disponibilidad.

### Comparación con otras estrategias

| Criterio | All at Once | Rolling | Immutable | Blue/Green |
|----------|-------------|---------|-----------|------------|
| Downtime | Posible | No | No | No |
| Rollback | Manual | Manual | Automático | Swap URL |
| Costo durante deploy | Normal | Normal | 2x instancias | 2x entornos |
| Tiempo de deploy | Muy rápido | Medio | Lento | Lento |
| Riesgo para producción | Alto | Medio | Bajo | Bajo |
