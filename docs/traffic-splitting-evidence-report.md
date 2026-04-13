# Evidencia: Traffic Splitting Deployment — grupo11-eb-v2

**Entorno:** `deployment-trafficsplitting-v2`  
**Aplicación:** `grupo11-eb-v2`  
**URL:** http://deployment-trafficsplitting-v2.us-east-1.elasticbeanstalk.com/  
**Plataforma:** Python 3.11 running on 64bit Amazon Linux 2023 / 4.12.1  
**Estrategia:** Traffic Splitting (División del tráfico)  
**Región:** us-east-1  

---

## Qué es Traffic Splitting deployment

En esta estrategia Beanstalk despliega la nueva versión en un **conjunto de instancias temporales nuevas** y redirige un porcentaje configurable del tráfico de entrada hacia ellas durante un periodo de evaluación. Si las instancias nuevas superan los health checks durante ese tiempo, el despliegue completa y el tráfico restante se transfiere. Si fallan, el tráfico vuelve completamente a las instancias originales de forma automática. Es la estrategia con mayor control de riesgo en producción.

---

## Fase 1 — Configuración del entorno

### 1.1 Configuración general del entorno

![Configuración del entorno](/docs/images/traffic-splitting-deployment/01-beanstalk-configuracion-entorno.jpeg)

- **Nombre del entorno:** `deployment-trafficsplitting-v2`
- **Nombre de la aplicación:** `grupo11-eb-v2`
- **Dominio:** `deployment-trafficsplitting-v2.us-east-1.elasticbeanstalk.com`
- **Plataforma:** Python 3.11 running on 64bit Amazon Linux 2023
- **Versión de la plataforma:** 4.12.1 (Recommended)
- **Código de la aplicación:** Versión existente 4.0.0
- **Preset:** Alta disponibilidad (con instancias de spot y bajo demanda)

### 1.2 Política de implementación — Traffic Splitting

![Política Traffic Splitting](/docs/images/traffic-splitting-deployment/02-beanstalk-politica-traffic-splitting.jpeg)

- **Política de implementación:** `División del tráfico` (Traffic Splitting)
- **Tipo de tamaño de lote:** Porcentaje
- **Tamaño del lote de implementación:** 30%
- **División del tráfico:** 15% — porcentaje del tráfico enrutado a la nueva versión
- **Tiempo de evaluación de división del tráfico:** 5 minutos
- **Actualizaciones de configuración continua:** Deshabilitado
- **Ignorar comprobación de estado:** Falso
- **Umbral de estado:** Aceptar (Ok)
- **Tiempo de espera del comando:** 600 segundos

Durante el despliegue, el 15% del tráfico se redirige a las nuevas instancias durante 5 minutos. Si pasan los health checks, el deploy completa transfiriendo el 100% del tráfico.

---

## Fase 2 — Revisión final de la configuración

### 2.1 Revisión — Entorno, acceso y red

![Revisión entorno y red](/docs/images/traffic-splitting-deployment/03-beanstalk-revision-entorno-red.jpeg)

- **Nombre del entorno:** `deployment-trafficsplitting-v2`
- **Nombre de la aplicación:** `grupo11-eb-v2`
- **Código de la aplicación:** 4.0.0
- **Plataforma:** Python 3.11 on 64bit Amazon Linux 2023/4.12.1
- **Rol de servicio:** aws-elasticbeanstalk-service-role
- **Perfil de instancia EC2:** Instance_Profile_EC2
- **VPC:** vpc-0c9d792235350a1c
- **IP pública:** habilitada
- **Subnets:** subnet-0e95a90fd61db97b0, subnet-0efaab20187bd49cb

### 2.2 Revisión — Escalado y ALB

![Revisión escalado ALB](/docs/images/traffic-splitting-deployment/04-beanstalk-revision-escalado-alb.jpeg)

- **Tipo de entorno:** Equilibrio de carga
- **Mínimo de instancias:** 3
- **Máximo de instancias:** 6
- **Tipos de instancia:** t3.micro, t3.small
- **Métrica:** NetworkOut — Umbral superior 6,000,000 / Umbral inferior 2,000,000
- **Equilibrador de carga:** Application, público, dedicado
- **Subnets del ALB:** subnet-0e95a90fd61db97b0, subnet-0efaab20187bd49cb

### 2.3 Revisión final — Traffic Splitting confirmado

![Revisión final](/docs/images/traffic-splitting-deployment/05-beanstalk-revision-final-traffic-splitting.jpeg)

- **Política de implementación:** `TrafficSplitting` ✓
- **División del tráfico:** 15%
- **Tiempo de evaluación:** 5 minutos
- **WSGIPath:** `application`
- **Servidor proxy:** nginx
- **NumProcesses:** 1 / **NumThreads:** 15
- **Umbral de estado:** Ok
- **Actualizaciones administradas:** Habilitadas — nivel minor
- **Variables de entorno:** DATABASE_URL y JWT_SECRET_KEY configuradas

---

## Fase 3 — Validación del entorno

### 3.1 Health check

![Health check](/docs/images/traffic-splitting-deployment/06-postman-health-check-200.png)

- **URL:** `http://deployment-trafficsplitting-v2.us-east-1.elasticbeanstalk.com/health`
- **Método:** GET
- **Status:** `200 OK` — 243 ms
- **Respuesta:** `{"status": "healthy", "version": "all-at-once-v2"}` — app operativa en AWS

### 3.2 POST /blacklists — 201 Created

![POST blacklists](/docs/images/traffic-splitting-deployment/07-postman-post-blacklist-201.png)

- **URL:** `http://deployment-trafficsplitting-v2.us-east-1.elasticbeanstalk.com/blacklists`
- **Método:** POST
- **Header:** `Authorization: Bearer <token>`
- **Status:** `201 Created` — 69 ms
- **Resultado:** Email agregado exitosamente a la blacklist

### 3.3 GET /blacklists/\<email\> — 200 Ok

![GET blacklists](/docs/images/traffic-splitting-deployment/08-postman-get-blacklist-200.png)

- **URL:** `http://deployment-trafficsplitting-v2.us-east-1.elasticbeanstalk.com/blacklists/spam4@example.co`
- **Método:** GET
- **Header:** `Authorization: Bearer <token>`
- **Status:** `200 OK` — 82 ms
- **Respuesta:** `{"blacklisted": false, "email": "spam4@example.co", "blocked_reason": null, "version": "all-at-once-v2"}` — app operativa en AWS

---

## Fase 4 — Hallazgos

### Métricas del deploy Traffic Splitting

| Métrica | Valor observado |
|---------|-----------------|
| División del tráfico configurada | 15% hacia nuevas instancias |
| Tiempo de evaluación | 5 minutos |
| Tamaño del lote | 30% |
| Downtime durante el deploy | No — tráfico principal continúa en instancias originales |
| Rollback si falla | Automático — el tráfico vuelve al 100% original |

### Ventajas observadas

- Permite validar la nueva versión con tráfico real antes de completar el despliegue.
- Si las nuevas instancias fallan durante la evaluación, el rollback es automático sin intervención manual.
- Menor riesgo que Rolling — solo un porcentaje pequeño de usuarios experimenta la nueva versión durante la evaluación.
- No hay downtime — el tráfico principal se mantiene en las instancias originales durante todo el proceso.

### Desventajas observadas

- Requiere instancias adicionales durante el periodo de evaluación — mayor costo temporal.
- Más complejo de configurar y monitorear que All at Once o Rolling.
- Durante la evaluación coexisten dos versiones activas, lo que puede generar inconsistencias si hay cambios de esquema de base de datos.

### Comparación con otras estrategias

| Criterio | All at Once | Rolling | Immutable | Traffic Splitting |
|----------|-------------|---------|-----------|-------------------|
| Downtime | Posible | No | No | No |
| Rollback | Manual | Manual | Automático | Automático |
| Costo durante deploy | Normal | Normal | 2x instancias | 2x instancias (parcial) |
| Tiempo de deploy | Muy rápido | Medio | Lento | Lento |
| Versiones simultáneas | No | Sí (transitorio) | No | Sí (controlado) |
| Validación con tráfico real | No | No | No | Sí |
| Riesgo para producción | Alto | Medio | Bajo | Muy bajo |
