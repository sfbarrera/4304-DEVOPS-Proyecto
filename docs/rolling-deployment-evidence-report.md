# Evidencia: Rolling Deployment — grupo11-eb-v2

**Entorno:** `deployment-rolling-v2`  
**Aplicación:** `grupo11-eb-v2`  
**URL:** http://deployment-rolling-v2.us-east-1.elasticbeanstalk.com/  
**Plataforma:** Python 3.11 running on 64bit Amazon Linux 2023 / 4.12.1  
**Estrategia:** Rolling (Continuo)  
**Región:** us-east-1  

---

## Qué es Rolling deployment

En esta estrategia Beanstalk despliega la nueva versión **en lotes sucesivos de instancias**. Un porcentaje del total de instancias se actualiza a la vez, mientras el resto continúa sirviendo tráfico en la versión anterior. Esto permite mantener disponibilidad durante el despliegue, aunque brevemente se ejecutan versiones distintas en paralelo hasta que el lote completa su actualización.

---

## Fase 1 — Configuración del entorno

Las capturas de configuración paso a paso corresponden a la configuración realizada en la consola de AWS antes de crear el entorno. La configuración base de red, acceso, escalado y load balancer es idéntica a los demás entornos del grupo; lo relevante para esta estrategia es la política de implementación seleccionada.

### 1.1 Política de implementación — Rolling

![Política Rolling](/docs/images/rolling-deployment/01-beanstalk-politica-rolling.jpeg)

- **Política de implementación:** `Continuo` (Rolling)
- **Tipo de tamaño de lote:** Porcentaje
- **Tamaño del lote:** 15%
- **Umbral de estado:** Aceptar (Ok)
- **Tiempo de espera del comando:** 600 segundos

Con 3 instancias activas y un lote del 15%, Beanstalk procesa aproximadamente 1 instancia por turno. Mientras ese lote se actualiza y supera el health check, el resto de las instancias siguen en la versión anterior.

---

## Fase 2 — Revisión final de la configuración

### 2.1 Revisión — Entorno, acceso y red

![Revisión entorno y red](/docs/images/rolling-deployment/02-beanstalk-revision-entorno-red.jpeg)

- **Nombre del entorno:** `deployment-rolling-v2`
- **Nombre de la aplicación:** `grupo11-eb-v2`
- **Código de la aplicación:** 4.0.0
- **Plataforma:** Python 3.11 on 64bit Amazon Linux 2023/4.12.1
- **Rol de servicio:** aws-elasticbeanstalk-service-role
- **Perfil de instancia EC2:** Instance_Profile_EC2
- **VPC:** vpc-0c9d792235350a1c
- **IP pública:** habilitada
- **Subnets:** us-east-1a, us-east-1b

### 2.2 Revisión — Escalado y ALB

![Revisión escalado ALB](/docs/images/rolling-deployment/03-beanstalk-revision-escalado-alb.jpeg)

- **Tipo de entorno:** Equilibrio de carga
- **Mínimo de instancias:** 3
- **Máximo de instancias:** 6
- **Tipos de instancia:** t3.micro, t3.small
- **Métrica:** NetworkOut — Umbral superior 6,000,000 / Umbral inferior 2,000,000
- **Equilibrador de carga:** Application, público

### 2.3 Revisión final — Rolling confirmado

![Revisión final](/docs/images/rolling-deployment/04-beanstalk-revision-final-rolling.jpeg)

- **Política de implementación:** `Rolling` ✓
- **WSGIPath:** `application`
- **Servidor proxy:** nginx
- **Umbral de estado:** Ok
- **Variables de entorno:** DATABASE_URL y JWT_SECRET_KEY configuradas

---

## Fase 3 — Validación del entorno

### 3.1 Health check

![Health check](/docs/images/rolling-deployment/05-postman-health-check-200.png)

- **URL:** `http://deployment-rolling-v2.us-east-1.elasticbeanstalk.com/health`
- **Método:** GET
- **Status:** `200 OK` — 164 ms
- **Respuesta:** `{"status": "healthy", "version": "all-at-once-v2"}` — app operativa en AWS

### 3.2 POST /blacklists — 201 Created

![POST blacklists](/docs/images/rolling-deployment/06-postman-post-blacklist-201.png)

- **URL:** `http://deployment-rolling-v2.us-east-1.elasticbeanstalk.com/blacklists`
- **Método:** POST
- **Header:** `Authorization: Bearer <token>`
- **Status:** `201 Created`
- **Resultado:** Email agregado exitosamente a la blacklist

### 3.3 GET /blacklists/\<email\> — 200 Ok

![GET blacklists](/docs/images/rolling-deployment/07-postman-get-blacklist-200.png)

- **URL:** `http://deployment-rolling-v2.us-east-1.elasticbeanstalk.com/blacklists/<email>`
- **Método:** GET
- **Header:** `Authorization: Bearer <token>`
- **Status:** `200 OK`
- **Respuesta:** `{"blacklisted": true/false, "email": "...", "blocked_reason": ...}`

---

## Fase 4 — Hallazgos

### Métricas del deploy Rolling

| Métrica | Valor observado |
|---------|-----------------|
| Tamaño de lote configurado | 15% |
| Instancias actualizadas por lote | ~1 de 3 |
| Downtime durante el deploy | No — instancias restantes siguen activas |
| Instancias al finalizar | 3 |

### Ventajas observadas

- Mantiene disponibilidad durante el despliegue — el tráfico sigue siendo atendido por las instancias no actualizadas.
- No requiere instancias adicionales — sin costo extra durante el deploy.
- Si un lote falla el health check, el deploy se detiene antes de afectar el resto del parque.

### Desventajas observadas

- Durante el despliegue coexisten dos versiones simultáneamente (versión anterior + nueva) — puede generar inconsistencias si hay cambios de esquema de base de datos.
- El rollback no es automático — si el deploy falla a mitad del proceso, se debe hacer un nuevo deploy manual.
- El proceso es más lento que All at Once, especialmente con lotes pequeños.

### Comparación con otras estrategias

| Criterio | All at Once | Rolling | Immutable | Blue/Green |
|----------|-------------|---------|-----------|------------|
| Downtime | Posible | No | No | No |
| Rollback | Manual | Manual | Automático | Swap URL |
| Costo durante deploy | Normal | Normal | 2x instancias | 2x entornos |
| Tiempo de deploy | Muy rápido | Medio | Lento | Lento |
| Versiones simultáneas | No | Sí (transitorio) | No | No |
| Riesgo para producción | Alto | Medio | Bajo | Bajo |
