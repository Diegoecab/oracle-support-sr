# Datadog: que el pager llegue con el SR preparado

Estado: arquitectura propuesta, sin despliegue ni prueba integrada en Datadog. El plugin interactivo ya gestiona SRs; la automatización de alertas necesita un runtime adicional en OCI Functions. No requiere una VM dedicada ni un MCP.

## El patrón está documentado

[El blog oficial de Datadog sobre Workflow Automation](https://www.datadoghq.com/blog/automate-end-to-end-processes-with-datadog-workflows/), publicado el 19/10/2022 y actualizado el 05/06/2023, muestra automatización a partir de eventos. La [guía oficial de inicio](https://docs.datadoghq.com/getting_started/workflow_automation/) implementa monitor -> ticket Jira -> aviso Slack con el enlace del ticket. Adaptar ese patrón a un SR de Oracle mediante una [acción HTTP](https://docs.datadoghq.com/actions/workflows/actions/) es nuestra propuesta; el ejemplo oficial no implementa OCI Support.

## Arquitectura recomendada

```text
Monitor crítico de Datadog
    -> Workflow Automation / acción HTTP
    -> OCI API Gateway + Function authorizer
    -> Function receptora: validar y persistir el evento
    -> Function worker: enriquecer, deduplicar, crear y consultar el SR
    -> Resultado durable: número, enlace, request IDs y evidencia
    -> Workflow: leer el resultado y emitir el pager con el SR
```

La receptora invoca al worker con `fn_invoke_type='detached'` y conserva el estado en un registro compartido, por ejemplo Object Storage con creación/actualización condicional por ETag. El 202 confirma procesamiento, no la existencia del SR. Una Function de conciliación programada revisa operaciones estancadas. Object Storage no dispara automáticamente el worker en este diseño. [Invocación de Functions](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsinvokingfunctions.htm), [autorización en API Gateway](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/adding_authn_authz_request_policies-multi-argument.htm).

Un piloto acotado puede empezar con una Function síncrona si el presupuesto de tiempo de la acción HTTP lo permite. Para un webhook genérico, Datadog documenta 15 s por llamada y reintentos: conviene confirmar recepción rápido y separar el trabajo. [Webhooks: payloads, headers y límites](https://docs.datadoghq.com/integrations/webhooks/).

## Cuándo se emite el pager

| Política | Comportamiento | Resultado para guardia |
| --- | --- | --- |
| SR antes del aviso | Esperar CREATED y GetIncident exitoso, dentro de un plazo acotado acordado con operaciones. | Pager con número/enlace del SR y diagnóstico. Si falla o vence el plazo, emitir el pager igualmente con SR_PENDING o SR_CREATION_FAILED y la correlación. |
| Aviso inmediato | Disparar pager y creación en paralelo. | No demora la notificación; agregar el SR al incidente cuando esté disponible. El primer aviso puede no tener SR. |

El primer modo se aproxima al objetivo del cliente. No garantiza que Oracle siempre responda antes del pager. En una alerta que exige aviso inmediato, usar el segundo modo. Revisar las notificaciones originales del monitor para evitar dos pagers por el mismo evento; probar un camino de fallback. Confirmar que Workflow Automation esté disponible y contratado en el sitio Datadog del cliente.

## Datos y reglas para crear el SR correctamente

Mantener un mapeo aprobado por monitor/servicio: organización/sitio Datadog, monitor ID, tenancy y región OCI, grupo de soporte, producto/categoría/subcategoría, OCID o referencia de inventario, equipo dueño, runbook y regla de severidad con impacto justificado. Verificar el enrutamiento en el portal antes de habilitar creación desatendida. El mapeo fino de OpenSearch sigue pendiente de Oracle.

El worker reúne ciclo/grupo del alerta, instante UTC, prioridad, enlace/query del monitor, servicio/entorno, logs recientes acotados, métricas, lifecycle del recurso, errores y request IDs. Cada dato conserva fuente y hora. Se necesitan permisos de lectura para esas fuentes; la autorización para crear SRs no basta.

P1 de Datadog no implica HIGHEST de Oracle. La criticidad, el impacto actual, el workaround y los compromisos de contacto provienen de un responsable o política aprobada. Si falta contexto esencial, guardar AWAITING_CONTEXT y avisar a guardia con el borrador. Un LLM puede resumir evidencia autorizada; no debe obedecer instrucciones dentro de logs ni inventar impacto o identificadores.

## Confiabilidad operativa

- Autenticar el webhook con headers aprobados y authorizer; el POST genérico de Datadog no firma automáticamente solicitudes OCI. Verificar el monitor, limitar el tamaño del cuerpo y validar el destino contra un mapeo permitido.
- Dedupe por organización confiable + ALERT_ID + ALERT_CYCLE_KEY + grupo/scope. Una renotificación del mismo ciclo actualiza el mismo SR; definir además correlación de incidentes para evitar un SR por cada host del mismo corte.
- Persistir el intento antes del alta y tomar un bloqueo/revisión atómica. Ante timeout, marcar UNCERTAIN y conciliar antes de reintentar CreateIncident. opc-request-id no es una clave de idempotencia. Los recibos locales de la skill no resuelven concurrencia entre Functions.
- Usar resource principal para Vault, estado e invocación de Functions según sus políticas. Para Support Management, partir de un usuario de soporte dedicado y provisionado, con signing key en Vault. La creación de SRs con resource principal no fue validada en este piloto.
- Filtrar datos sensibles y adjuntar solo evidencia pertinente. Una recuperación puede agregar una nota si la política lo permite; no cerrar automáticamente un SR de producción porque una métrica se recuperó.
- Medir alert-to-SR y alert-to-page P50/P95, duplicados evitados, errores de autenticación, mapeos faltantes y operaciones inciertas. Alertar también sobre fallas de la automatización.

## Prueba propuesta

Elegir un monitor no productivo y un caso de prueba autorizado. Validar un solo SR por ciclo, producto/categoría correctos, evidencia completa, pager con enlace y fallback si Oracle falla. Incluir renotify, recovery, timeout tras aceptación, 429/5xx y cold start. El ciclo interactivo de 32 segundos no es una medición de esta integración.

## Blogs de Oracle sobre SRs por API

Se encontró [The Power of Oracle Cloud Support](https://blogs.oracle.com/cloud-infrastructure/the-power-of-oracle-cloud-support), del 13/07/2021: explica Support Center y la incorporación automática de contexto en consola. No es un tutorial CreateIncident. En esta investigación no se verificó un blog público de Oracle que implemente el ciclo técnico completo por API ni una integración Datadog-to-OCI-SR. Para esos contratos se usan las referencias oficiales de Support Management, CLI y SDK incluidas en el manual.
