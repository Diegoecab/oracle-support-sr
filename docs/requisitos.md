# Requisitos mínimos: SRs y recolección de evidencia

Revisión: 17/11/2026. Los permisos para gestionar un SR y los permisos para leer el recurso afectado son independientes. No se requiere una VM dedicada ni permisos de administrador de toda la tenancy.

## Entorno y autenticación

- Python 3.11 y SDK oficial OCI `oci>=2.177.0,<3` en el intérprete que use el helper. Las pruebas locales pasaron con 2.177.0; el ciclo original en vivo se ejecutó con 2.152.0. El backend CLI es opcional y necesita además OCI CLI.
- Codex o Claude Code con ejecución local de comandos, almacenamiento de evidencia y conectividad HTTPS hacia los endpoints OCI utilizados. Para instalar el plugin, Git y acceso HTTPS al repositorio público en GitHub.
- Perfil OCI con tenancy, usuario, región y API signing key registrada. Configurar la home region real; resolver la clave regional para el cuerpo de creación cuando corresponda. Las credenciales se administran localmente y no están incluidas en el plugin.
- Tenancy de pago elegible para soporte, identidad provisionada en My Oracle Cloud Support y privilegios en el grupo de soporte del caso. [Configuración de soporte](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/usingsupport.htm), [requisitos de creación](https://docs.oracle.com/en-us/iaas/Content/GSG/support/create-incident.htm).
- Revisar las restricciones documentadas: Support CLI no está soportado en Cloud Shell; algunas llamadas SDK/CLI/API requieren que la tenancy esté suscrita a Phoenix y que se informe correctamente la home region. [Problemas conocidos](https://docs.oracle.com/en-us/iaas/Content/GSG/support/known-issues.htm). La instalación no cambia suscripciones ni políticas automáticamente.

## Altas, consultas, modificaciones y cierre

| Operación | API / helper | IAM publicado | Privilegio adicional en soporte |
| --- | --- | --- | --- |
| Consultar, listar, taxonomía y validar usuario | GetIncident, ListIncidents, ListIncidentResourceTypes, ValidateUser | read tickets / TICKET_READ | Usuario de soporte y visibilidad en el grupo correspondiente. |
| Crear | CreateIncident / create | manage tickets / TICKET_MANAGE | Privilegio create asignado por el CUA en un grupo de soporte; seleccionar su userGroupId validado. |
| Agregar notas y cerrar un SR seleccionado | UpdateIncident / comment, close | manage tickets / TICKET_MANAGE | Privilegio de edición y visibilidad en el grupo del SR, además de la acción autorizada. |
| Adjuntar evidencia | PutAttachment / attach | Validar con la identidad delegada que tenga manage tickets | La tabla IAM actual omite PutAttachment: no establece su permiso granular exacto. Requiere validación operativa independiente con el usuario del cliente y privilegios de actualización. |
| Borrar un SR | No identificado en el cliente público revisado | Sin operación de borrado identificada | El cierre conserva el historial y es la operación soportada que probamos. |

Los ejemplos oficiales son:

```text
Allow group SR-Readers to read tickets in tenancy
Allow group SR-Operators to manage tickets in tenancy
```

`manage` ya incluye lectura. Calificar el grupo con el dominio de identidad cuando aplique. `inspect tickets` no habilita operaciones en la tabla publicada. El grupo IAM y el grupo de My Oracle Cloud Support son entidades distintas; el acceso efectivo necesita ambas capas. [Referencia IAM](https://docs.oracle.com/en-us/iaas/Content/GSG/support/policy-reference.htm), [seguridad de Support Management](https://docs.oracle.com/en-us/iaas/Content/Security/Reference/support-management.htm), [privilegios para comentarios](https://docs.oracle.com/en-us/iaas/Content/GSG/support/update-incident-add-comment.htm).

## Permisos para obtener lo que luego se sube al SR

Agregar únicamente las lecturas que requiera el incidente y limitarlas al compartment, log group, bucket o servicio pertinente.

| Información | Acceso necesario | Alcance y referencia |
| --- | --- | --- |
| OCID, estado y metadata de ADB | inspect autonomous-databases | Get/List están cubiertos; no equivale a acceso SQL ni a logs internos. [ADB IAM](https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/autonomous-database-iam-policies.html). |
| Metadata de OpenSearch | inspect opensearch-clusters | Agregar inspect opensearch-cluster-backups y opensearch-work-requests si se usan esos diagnósticos. La referencia conserva algunos nombres Elasticsearch; comprobar la operación vigente. [OpenSearch IAM](https://docs.oracle.com/en-us/iaas/Content/search-opensearch/Concepts/ocisearchpermissions.htm). |
| Descubrir compartments | inspect compartments in tenancy, cuando sea necesario | Puede omitirse si los identificadores ya están disponibles. |
| Contenido de logs OCI | read log-content | Restringir al compartment/log group. Leer la configuración del log no habilita su contenido. [Logging IAM](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/loggingpolicyreference.htm). |
| Métricas OCI | read metrics en el compartment afectado | [Monitoring IAM](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/monitoringpolicyreference.htm). |
| Archivos de diagnóstico existentes | read objects limitado al bucket/prefix autorizado | No requiere crear buckets ni habilitar nuevos logs para operar un SR. |
| Uso y costos | read usage-report in tenancy | Independiente de administración de facturas y pagos. [Usage API / Cost Analysis](https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/costanalysisoverview.htm). |
| Logs en Datadog | API/application key u OAuth aprobado, con acceso de lectura al subconjunto requerido | Logs Search requiere logs_read_data y respeta restricciones de índices/consulta. Monitor y métricas requieren los permisos de sus endpoints. [Logs API](https://docs.datadoghq.com/api/latest/logs/search-logs-get/), [RBAC](https://docs.datadoghq.com/logs/guide/logs-rbac-permissions/). |
| Diagnósticos SQL, aplicación o sistema operativo | Cuenta/rol de lectura y conectividad específicos, solo si se requieren | No están implícitos en inspect de OCI ni en los permisos de soporte. Preferir evidencia exportada y filtrada. |
| Investigar IAM | Lectura de memberships/grupos/políticas pertinentes, solo si el problema lo requiere | No es requisito general del plugin y no justifica manage all-resources. |

La skill guía al LLM para obtener contexto mediante herramientas y lecturas autorizadas. El helper no incorpora un recolector universal de logs. El impacto de negocio y los compromisos de contacto los aporta el responsable o una política previamente aprobada; no se deducen de un 404 ni de una prioridad de monitor.

Como fuente opcional de evidencia, ADB Serverless dispone de MCP nativo; SQLcl MCP es otra alternativa. Se configuran aparte y requieren identidad, conectividad y permisos para las herramientas o consultas aprobadas. Los privilegios de tickets no los conceden.

Para ejecutar un alta TECH, la versión 0.3.0 exige además una receta local de producto/categoría verificada y vigente, que coincida con el catálogo actual. Si no existe o no coincide, conserva el borrador y bloquea el envío. Es un control de la skill, no un parámetro adicional del API de Oracle.

## Campos que no deben faltar en el caso

Recurso/OCID cuando aplique, región, compartment conocido, síntoma, ventana UTC, request IDs, resultados observados, impacto, diagnóstico relevante y pedido concreto a Oracle. Seleccionar producto/categoría desde la taxonomía vigente y comprobar el enrutamiento persistido. Para OpenSearch, [SRDC1037](https://support.oracle.com/support/?kmContentId=2864665) agrega componente/subcomponente y evidencia condicional; requiere acceso autenticado.

La descripción inicial se limita al contrato actual; el helper aplica 1500 caracteres. Las notas y adjuntos conservan el detalle ampliado. MEDIUM es el enum de severidad 3; LOW corresponde a orientación general. Elegir la severidad por impacto documentado. No se promete un SLA por el nombre del enum.
