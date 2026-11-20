# Gestión de SRs de ADB Serverless con CLI, SDK y skill

Versión 0.9.5. Revisión: 20/11/2026.

## Gestión de SRs mediante API, CLI y SDK

Los Service Requests (SRs) de **Autonomous Database Serverless** pueden gestionarse mediante la **Support Management API de OCI**, tanto por REST como desde OCI CLI y los SDK oficiales. Estas interfaces permiten crear y consultar casos, publicar actualizaciones, subir archivos y solicitar el cierre.

Para reducir las tareas repetitivas de apertura y seguimiento, desarrollamos [oracle-support-sr](https://github.com/Diegoecab/oracle-support-sr), una skill compatible con **Codex y Claude Code**. El piloto demuestra cómo gestionar un SR con pedidos en lenguaje natural, reutilizar el contexto disponible y mantener una salida legible con evidencia de cada operación.

Esta guía reúne instalación, permisos, campos y ejemplos para que el equipo pruebe el flujo con casos autorizados y evalúe su adopción. También detalla los modos de aprobación y las limitaciones identificadas para este servicio.

**Un plus en ADB: del AWR al SR con menos pasos.** Si el equipo todavía obtiene los reportes desde el portal y los adjunta a mano, automatizar ese recorrido puede reducir trabajo adicional en los seguimientos. El [ejemplo con comandos](https://github.com/Diegoecab/oracle-support-sr/blob/main/docs/adb-awr-api.md) obtiene el AWR mediante [REST-Enabled SQL](https://docs.oracle.com/en/database/oracle/oracle-rest-data-services/26.2/orddg/rest-enabled-sql-service.html) y usa la skill para subirlo y actualizar el caso. La [API de Database Management](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/database_management/client/oci.database_management.DbManagementClient.html#get_awr_db_report) es otra alternativa, con sus requisitos. El [MCP nativo de ADB](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/use-mcp-server.html) también puede aportar diagnósticos mediante herramientas configuradas y autorizadas. La recolección se configura por separado de la skill. El [beneficio adicional del AWR](#plus-awr) se evalúa aparte del escenario estimativo del 83 %.

**Documentación oficial de Oracle**

- [Gestión de SRs: creación mediante consola, CLI y API](https://docs.oracle.com/en-us/iaas/Content/GSG/support/create-incident.htm).
- [Referencia de las API REST de OCI](https://docs.oracle.com/en-us/iaas/api/).
- [OCI CLI: Support Management](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/support.html).
- [SDK Python: IncidentClient de Support Management](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/cims/client/oci.cims.IncidentClient.html).

## Tiempo estimado para un SR

1 apertura + 4 seguimientos = 5 gestiones del mismo SR. Cada gestión incluye revisar la novedad, reunir la información, enviarla y verificar el resultado.

| Forma de trabajo | Minutos por gestión (supuesto) | Cálculo | Total para el SR |
| --- | ---: | --- | --- |
| Consola / portal | 30 min | 5 × 30 min | 2 h 30 min (150 min) |
| CLI / SDK manual | 15 min | 5 × 15 min | 1 h 15 min (75 min) |
| Skill en Codex / Claude | 5 min | 5 × 5 min | 25 min |

Ahorro estimado frente a la consola: 150 − 25 = 125 minutos (2 h 5 min), aproximadamente un 83 %. Frente al CLI / SDK manual: 50 minutos. Son supuestos para comparar formas de trabajar; falta medir cinco gestiones comparables de un SR completo. Se cuenta tiempo activo y se excluyen esperas de Oracle, configuración inicial e investigación compleja.

<a id="plus-awr"></a>

## Un plus en ADB: automatizar el AWR y adjuntarlo al SR

Si el equipo todavía genera y descarga los AWR desde el portal y después los carga a mano en Oracle Support, hay otra oportunidad de reducir el tiempo dedicado al SR.

| Trabajo del seguimiento | Qué puede automatizar el flujo |
| --- | --- |
| Preparar el diagnóstico | Recuperar el contexto disponible y consultar los snapshots de la PDB para la ventana solicitada. Preguntar por los datos fundamentales que falten. |
| Generar y obtener el reporte | Ejecutar la API autorizada, guardar el HTML completo y comprobar base, intervalo y contenido. |
| Entregar la evidencia | Usar oracle-support-sr para adjuntar el archivo, publicar la actualización y consultar el estado del envío. |

El beneficio está en reducir pasos manuales y reutilizar el contexto entre la base y el SR. Si el equipo ya automatiza la obtención del AWR, puede aprovechar ese proceso y sumar la carga y el seguimiento del caso con la skill. La recolección de AWR permanece fuera de oracle-support-sr.

El ciclo AWR completo puede superar los cinco minutos por gestión usados en el ejemplo. El ahorro potencial adicional se evalúa por separado del 83 %; todavía no tiene un porcentaje medido.

<details>
<summary>Mediciones del piloto y cómo calcular el ahorro</summary>

En el piloto, un reporte de unos 311 KB tardó aproximadamente 6 segundos en generarse y descargarse; la llamada de upload al SR tardó aproximadamente 5 segundos. Son mediciones parciales de ese archivo, no el tiempo total de una actualización con AWR. Excluyen la preparación, la configuración, la captura de snapshots, la revisión y la espera de procesamiento del adjunto.

El acceso, la selección de snapshots, la generación, la revisión del archivo, el upload y su procesamiento tienen tiempos propios. El ahorro potencial adicional puede ser mayor para un equipo que hoy hace estos pasos manualmente. Para cuantificarlo, comparar el mismo seguimiento con y sin automatización: registrar por separado el tiempo activo de la persona y el tiempo transcurrido hasta confirmar el adjunto recibido. El escenario del 83 % conserva sus supuestos.

</details>

[Ver el ejemplo y los comandos de recolección y adjunto](https://github.com/Diegoecab/oracle-support-sr/blob/main/docs/adb-awr-api.md).

## Qué cubre esta guía

Guía para crear, consultar, actualizar, adjuntar evidencia y cerrar SRs de Autonomous Database Serverless con OCI CLI, SDK Python y la skill oracle-support-sr. Los diagnósticos del control plane y el acceso SQL son permisos y fuentes diferentes; esta guía no autoriza cambios en la base.

## Pasos por consola

Estos son, a grandes rasgos, los pasos para crear y mantener el SR desde la consola. Cada seguimiento puede requerir volver a autenticarse y reunir nueva evidencia.

<details>
<summary>01 · Autenticarse y seleccionar el producto</summary>

Entrar a OCI/My Oracle Cloud Support y elegir el producto, tipo de problema e impacto. Revisar el contexto que el portal ya haya precargado.

</details>

<details>
<summary>02 · Reunir identificadores y contexto</summary>

Localizar la base afectada, su OCID, región, compartment y ventana del problema. Confirmar que la cuenta y el recurso corresponden al incidente.

</details>

<details>
<summary>03 · Obtener diagnósticos</summary>

Consultar la guía del servicio, reunir errores, request IDs, logs o métricas relevantes y revisar el contenido que se compartirá.

</details>

<details>
<summary>04 · Completar y enviar</summary>

Completar título, descripción, clasificación e impacto; adjuntar lo necesario. Después comprobar el caso creado y su clasificación persistida.

</details>

<details>
<summary>05 · Volver al caso para los seguimientos</summary>

Leer novedades, obtener la información adicional solicitada, publicar la respuesta y comprobarla. Cerrar cuando el responsable lo autorice.

</details>

## Pasos con la skill

El usuario describe el problema y su impacto. El asistente reutiliza la base y el perfil del contexto, reúne la información accesible y pregunta solo por datos fundamentales que falten.

```text
Usá oracle-support-sr con MI_PERFIL para validar acceso y listar mis SRs.
```

```text
No puedo conectarme a esta ADB. Reuní el contexto y prepará un SR.
```

```text
Revisá el pedido de Oracle y prepará la respuesta con los diagnósticos disponibles.
```

La recolección puede usar API de infraestructura o consultas aprobadas cuando ya existe acceso a la base. El asistente no cambia grants, ACLs, credenciales, lifecycle ni políticas para abrir el caso.

## Instalación

El mismo plugin funciona en Codex y Claude Code. El catálogo de instalación se llama oci-support-tools. Es un proyecto de piloto independiente, sin aval oficial de Oracle. Con el marketplace registrado, instalar requiere una orden por agente.

Codex:

```text
codex plugin add oracle-support-sr@oci-support-tools
```

Claude Code:

```text
claude plugin install oracle-support-sr@oci-support-tools --scope user
```

<details>
<summary>Registrar el marketplace la primera vez</summary>

Codex:

```text
codex plugin marketplace add Diegoecab/oracle-support-sr
```

Claude Code:

```text
claude plugin marketplace add Diegoecab/oracle-support-sr
```

Se necesitan Git y acceso HTTPS al repositorio público. Después de instalar, abrir una sesión nueva. Instalar el plugin no configura OCI ni concede permisos.

</details>

En Codex, pedir usar oracle-support-sr. En Claude, la skill del plugin se invoca como `/oracle-support-sr:oracle-support-sr`. El asistente debe usar el intérprete Python que tenga el SDK instalado.

```text
python -m pip install "oci>=2.177.0,<3"
```

La base propuesta para el piloto es Python 3.11 o posterior. Se verificó el helper con SDK 2.177.0 y CLI 3.82.0; revisar compatibilidad al actualizar. El backend CLI requiere además OCI CLI en PATH. No se necesita una VM dedicada ni un MCP para gestionar SRs.

## Requisitos y permisos mínimos

Los permisos para administrar el SR y para leer el recurso afectado son independientes. Usar una identidad de alcance limitado, no administrar toda la tenancy para abrir un ticket.

| Necesidad | Requisito |
| --- | --- |
| Autenticación OCI | Perfil con tenancy, usuario, región home y método de autenticación válido. API signing key y tokens tienen gestión y vigencia propias; respetar la política de rotación del cliente. |
| Identidad de soporte | Tenancy elegible para soporte técnico, usuario registrado en My Oracle Cloud Support y acceso al grupo del caso. |
| Consultar SRs y catálogo | read tickets / TICKET_READ y visibilidad del grupo de soporte. |
| Crear, actualizar y cerrar | manage tickets / TICKET_MANAGE y privilegios create/update del grupo de soporte, según la operación. |
| Adjuntar | Validar PutAttachment con la identidad del cliente y sus privilegios de actualización. La tabla IAM publicada no identifica su permiso granular por separado. |
| Conectividad | HTTPS a los endpoints OCI de soporte y a las fuentes de evidencia utilizadas. Para un dominio de identidad no predeterminado, informar el domainid real cuando corresponda. |

```text
Allow group SR-Readers to read tickets in tenancy
Allow group SR-Operators to manage tickets in tenancy
```

El grupo IAM y el grupo de soporte son entidades distintas. `userGroupId` se obtiene mediante ValidateUser; no es un CSI. Si el cliente usa grupos con dominio, adaptar la sintaxis a su dominio de identidad.

Oracle documenta restricciones de Support CLI en Cloud Shell y requisitos de suscripción a Phoenix/home region para algunas llamadas. Revisar los [problemas conocidos](https://docs.oracle.com/en-us/iaas/Content/GSG/support/known-issues.htm) antes del piloto; la instalación no cambia suscripciones ni políticas.


Para leer metadatos y backups, cuando correspondan:

```text
Allow group SR-Evidence to inspect autonomous-databases in compartment DB_COMPARTMENT
Allow group SR-Evidence to inspect autonomous-backups in compartment DB_COMPARTMENT
```

La tabla oficial incluye GetAutonomousDatabase y ListAutonomousDatabases bajo INSPECT. La segunda línea cubre metadatos Get/List de backups y se agrega solo si se necesitan. Estas políticas no conceden acceso SQL.

La generación de performance data o wallets tiene permisos adicionales; no forma parte del acceso mínimo general para un SR. No generar ni adjuntar wallets como diagnóstico. Para SQL, usar una conexión existente y privilegios específicos sobre las vistas necesarias, sin conceder privilegios globales por defecto. Si hacen falta métricas, logs OCI o archivos existentes, agregar read metrics, read log-content o read objects en el alcance pertinente. Para una investigación de cargos, el acceso de lectura a uso/costos es independiente de administrar facturas.

## Campos del SR y evidencia requerida

El usuario aporta el recurso o enlace, síntoma e impacto. El asistente obtiene los identificadores desde el contexto y lecturas autorizadas. Si falta un dato que cambia el destino, la prioridad o el diagnóstico, lo pregunta.

| Campo o dato | Cómo se completa |
| --- | --- |
| compartmentId del API de soporte | OCID de la tenancy; no el compartment del recurso afectado. |
| problemType | TECH para investigación técnica; ACCOUNT corresponde a una consulta de facturación. |
| userGroupId | Grupo con permisos de creación devuelto por ValidateUser y seleccionado para el caso. |
| title / description | Síntoma y pedido concretos. Antes de aprobar/enviar, el helper aplica un presupuesto preventivo local de 80 caracteres al título (no es el máximo contractual de Oracle) y limita la descripción inicial a 1500. Las notas y adjuntos amplían el detalle. |
| severity | LOW, MEDIUM, HIGH o HIGHEST según impacto confirmado. |
| Recurso / OCID | Incluirlo explícitamente en descripción y evidencia. El modelo revisado no tiene un campo dedicado para el OCID afectado en CreateResourceDetails. |
| Región | Endpoint de soporte en la home region; para resourceList.region resolver la clave regional, por ejemplo IAD, con ListRegions. |
| Categoría y subcategoría | Resolver las claves desde TAXONOMY y mantener la jerarquía completa. No inventar issueTypeKey ni contextualData. |
| Evidencia | Ventana UTC, error exacto, pasos de reproducción, request IDs y resultados de las lecturas pertinentes. |
| Compromisos de atención | Los confirma el responsable. Una alerta o un error no prueban una indisponibilidad productiva. |

| Valor de severity | Referencia operativa |
| --- | --- |
| LOW | Orientación general; nivel 4. |
| MEDIUM | Incidente técnico con afectación limitada; nivel 3. |
| HIGH | Afectación significativa; nivel 2. |
| HIGHEST | Impacto crítico; nivel 1 y compromiso de contacto 24x7 requerido por Oracle. |

El enum no es un número ni implica por sí solo un SLA. No se inventan impacto, entorno o disponibilidad de contacto. Los campos contacts de creación están deprecados y no deben usarse para prometer nuevos destinatarios de notificaciones.


La evidencia depende del síntoma; no todos los casos necesitan SQL ni logs de aplicación.

- Database OCID, región, compartment, workload/tipo y modelo de servicio confirmados.
- UTC, error exacto, pasos de reproducción y request IDs del control plane o identificadores de ejecución disponibles.
- Estado observado, conexión utilizada y método de autenticación, sin contraseñas, tokens ni wallets.
- Para rendimiento: ventana, métricas y consultas/planes pertinentes, revisando datos y literales antes de compartirlos.
- Para backup/restore o disponibilidad: operación, backup y eventos relevantes, sin ejecutar un restore como diagnóstico.
- Impacto, entorno y alcance confirmados por el responsable.

Registrar la fuente y fecha de cada diagnóstico. Si una lectura o conexión no está disponible, indicar la limitación y utilizar la evidencia accesible.

## Altas, consultas, modificaciones, adjuntos y cierre

En este documento, la baja de un SR significa solicitar su cierre y conservar el historial.

| Acción | API / SDK | OCI CLI |
| --- | --- | --- |
| Validar acceso | ValidateUser / validate_user | support validation-response validate-user |
| Ver productos y categorías | ListIncidentResourceTypes / list_incident_resource_types, TAXONOMY | support incident-resource-type list |
| Crear | CreateIncident / create_incident | raw-request con POST y JSON completo |
| Listar / consultar | ListIncidents / list_incidents; GetIncident / get_incident | support incident list / get |
| Agregar una actualización | UpdateIncident / update_incident, NOTES | support incident update |
| Adjuntar | PutAttachment / put_attachment | support incident put-attachment |
| Cerrar | UpdateIncident / update_incident, CLOSE | support incident update |

El comando simplificado `oci support incident create` no expone la clasificación completa de resourceList. Para un alta clasificada, la skill usa el SDK. CLI raw-request puede enviar el mismo JSON, manteniendo las mismas revisiones; no se utiliza para eludir una validación bloqueada.

<details>
<summary>Ejemplos CLI y SDK para el equipo técnico</summary>

Las mayúsculas representan valores que el asistente resuelve y comprueba. Los ejemplos de escritura requieren revisión y autorización; no son una orden para ejecutarlos sobre un caso real.

Consulta CLI:

```text
oci --profile MI_PERFIL support incident get --incident-key SR_KEY --compartment-id TENANCY_OCID --problemtype TECH --ocid USER_OCID --homeregion HOME_REGION
```

Actualización CLI sobre el SR aprobado:

```text
oci --profile MI_PERFIL support incident update --incident-key SR_KEY --compartment-id TENANCY_OCID --problem-type TECH --type activity --activity-type NOTES --comments "Texto aprobado" --ocid USER_OCID --homeregion HOME_REGION --force
```

Para el cierre se usa CLOSE como activity-type y el motivo aprobado. `--force` suprime la pregunta interactiva del CLI; no concede aprobación del usuario. Los archivos se cargan mediante put-attachment con su nombre y contenido revisados.

Alta por CLI REST, con JSON y headers previamente preparados:

```text
oci --profile MI_PERFIL raw-request --http-method POST --target-uri "https://incidentmanagement.HOME_REGION.oci.oraclecloud.com/20181231/v2/incidents" --request-headers file://headers.json --request-body file://solicitud.json
```

headers.json contiene el usuario actuante en ocid, homeregion y domainid cuando aplique. solicitud.json contiene compartmentId de tenancy, problemType, userGroupId y ticket; dentro de ticket.resourceList[].item se usan type=tech, category.categoryKey y subCategory.subCategoryKey de la selección validada. Las credenciales de firma permanecen en la configuración OCI.

Consulta equivalente con SDK Python:

```python
import oci

cfg = oci.config.from_file(profile_name="MI_PERFIL")
client = oci.cims.IncidentClient(
    cfg, retry_strategy=oci.retry.NoneRetryStrategy()
)
context = {"ocid": cfg["user"], "homeregion": cfg["region"]}
# Agregar domainid real si la identidad pertenece a un dominio no predeterminado.
response = client.get_incident(
    incident_key="SR_KEY", compartment_id=cfg["tenancy"],
    problemtype="TECH", **context
)
print(oci.util.to_dict(response.data))
```

El mismo cliente expone create_incident, update_incident y put_attachment. El helper del plugin convierte el JSON canónico en los modelos oficiales y registra resultados y request IDs. No agrega un SDK alternativo.

</details>

La skill verifica una escritura con una lectura posterior. Un HTTP 200 confirma aceptación, no que el equipo interno ni la clasificación sean los esperados. Si el resultado es incierto, consulta antes de reintentar para evitar duplicados. Las notas se agregan al historial; no editan correspondencia anterior.

## Métricas y reportes AWR mediante API

Hay dos interfaces complementarias para preparar evidencia de rendimiento:

| Evidencia | Interfaz soportada | Resultado |
| --- | --- | --- |
| Series de métricas | OCI Monitoring: SummarizeMetricsData | Datos agregados para la ventana y dimensiones consultadas. Se guardan para el SR si son relevantes. |
| Reporte AWR mediante SQL/PLSQL | ORDS REST-Enabled SQL y DBMS_WORKLOAD_REPOSITORY.AWR_REPORT_HTML | HTML completo para los snapshots de la PDB seleccionados; usa una identidad de base con permisos. |
| Reporte AWR mediante OCI | Database Management: GetAwrDbReport, disponible por REST, CLI y SDK | Contenido del informe en HTML o texto, con Diagnostics & Management y sus requisitos. |

El [ejemplo completo: obtener el AWR y adjuntarlo a un SR](https://github.com/Diegoecab/oracle-support-sr/blob/main/docs/adb-awr-api.md) documenta los comandos de creación de una ADB Free, consultas de snapshots, descarga por REST-Enabled SQL y carga con la skill. La vía REST-Enabled SQL se ejecutó con Always Free 19c sin habilitar Database Management; los comandos de recolección permanecen fuera de la skill.

OCI Monitoring no genera el informe AWR. Para la alternativa de Database Management, el flujo documentado es:

1. Usar una ADB con Diagnostics & Management habilitado, conexión y credencial de diagnóstico configuradas. Oracle documenta soporte para ADB Serverless; las funciones avanzadas tienen costo adicional. La habilitación es una tarea separada del SR.

2. Resolver el Managed Database mediante ListManagedDatabases, el identificador interno AWR mediante ListAwrDbs y los snapshots disponibles mediante ListAwrDbSnapshots. Elegir la ventana del incidente; no inventar estos identificadores.

3. Ejecutar GetAwrDbReport con reportType=AWR y reportFormat=HTML, y guardar el campo content como un archivo .html.

4. Revisar el archivo, retirar información que no corresponda compartir y pedir a la skill que lo adjunte al SR seleccionado, según el modo de aprobación.

Ejemplo CLI; reemplazar los marcadores por valores comprobados y usar el perfil y la región configurados para esa base:

```text
oci database-management managed-database get-awr-db-report --managed-database-id <MANAGED_DATABASE_OCID> --awr-db-id <AWR_DB_ID> --begin-sn-id-greater-than-or-equal-to <BEGIN_SNAPSHOT> --end-sn-id-less-than-or-equal-to <END_SNAPSHOT> --report-type AWR --report-format HTML --query data.content --raw-output > awr.html
```

La llamada equivalente en Python es DbManagementClient.get_awr_db_report(...); el archivo se obtiene de response.data.content. Estas operaciones pertenecen a Database Management, fuera del helper de SRs. También sigue disponible la descarga desde Performance Hub.

## Permisos y límites

GetAwrDbReport requiere DBMGMT_MANAGED_DB_READ, incluido en read dbmgmt-managed-databases en el compartment pertinente. La credencial de base y el acceso a secretos o named credentials se autorizan por separado. Para las funciones avanzadas que lo requieren, Oracle exige una credencial ADMIN; consultar la matriz oficial, sin ampliar permisos automáticamente. Oracle documenta un límite de 4 MB para los AWR generados por AWR Explorer en bases Cloud y Autonomous. La disponibilidad se comprueba con la configuración y versión de la base.

Referencias: [AWR por CLI](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/database-management/managed-database/get-awr-db-report.html), [SDK Python](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/database_management/client/oci.database_management.DbManagementClient.html#get_awr_db_report), [habilitación para ADB](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/mdw-oci-database-management.html), [matriz de soporte](https://docs.oracle.com/en-us/iaas/database-management/doc/database-management-feature-support-matrix.html), [conexión y credenciales](https://docs.oracle.com/en-us/iaas/database-management/doc/enable-database-management-autonomous-databases.html), [IAM de Database Management](https://docs.oracle.com/en-us/iaas/database-management/doc/policy-details-database-management.html), [límites de AWR Explorer](https://docs.oracle.com/en-us/iaas/database-management/doc/use-awr-explorer-analyze-database-performance.html) y [API de métricas](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/monitoring/client/oci.monitoring.MonitoringClient.html#summarize_metrics_data).

El mecanismo está documentado por Oracle; su ejecución con una base del cliente debe validarse antes de automatizarlo. No se habilitan servicios ni se generan reportes al instalar la skill.

## MCP como fuente opcional de evidencia

Autonomous Database Serverless dispone de un [MCP nativo administrado](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/use-mcp-server.html). Puede aportar resultados de herramientas Select AI Agent ya habilitadas y autorizadas para la identidad de la base. No se limita a SQLcl ni implica acceso SQL irrestricto.

| Alternativa | Alcance para reunir evidencia |
| --- | --- |
| MCP nativo de la base | Endpoint por base; herramientas autorizadas expuestas mediante Select AI Agent. Revisar los prerrequisitos y permisos de cada herramienta. |
| SQLcl MCP | Otra alternativa para una conexión guardada y consultas de diagnóstico aprobadas. Se configura y autentica por separado. |

| Evidencia | Alcance documentado y preparación necesaria |
| --- | --- |
| Errores y datos de logs accesibles al cliente | Oracle documenta la consulta de V$CLIENT_ERRORS. Para invocarla por MCP debe existir una herramienta autorizada con acceso a esa vista. Esto no equivale a descargar todos los logs internos de Oracle. |
| Reportes AWR | Se pueden generar con DBMS_WORKLOAD_REPOSITORY mediante REST-Enabled SQL, obtener por GetAwrDbReport de Database Management o descargar desde Performance Hub. No se encontró una herramienta AWR preconfigurada en el MCP nativo consultado; exponer el flujo por MCP requiere una herramienta autorizada. Las APIs directas no requieren MCP. |

Las fuentes son [Use MCP Server](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/use-mcp-server.html), [Query for Client Errors](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/autonomous-query-alert-log.html) y [AWR en Performance Hub](https://docs.oracle.com/en-us/iaas/performance-hub/doc/download-awr-report.html). Para ADB Serverless, la [nota de Oracle](https://docs.oracle.com/en-us/iaas/releasenotes/autonomous-database-serverless/2025-07-query-for-client-errors.htm) indica que V$DIAG_ALERT_EXT no está disponible para datos del alert log y remite a V$CLIENT_ERRORS.

Usar únicamente herramientas de diagnóstico autorizadas y conexiones ya disponibles. Activar el MCP, crear herramientas, cambiar grants o habilitar servicios son tareas separadas; la instalación de la skill no las ejecuta. Configurar permisos y aprobaciones del cliente MCP aparte de los del plugin de SRs.

Revisar y filtrar los resultados antes de una nota o adjunto: SQL, literales y datos pueden contener información de negocio. No adjuntar credenciales ni wallets. Si la base es inaccesible, el MCP no elimina ese bloqueo; reunir evidencia del control plane y de las fuentes que sí estén disponibles. La conexión mediante estos MCPs no se probó durante el piloto de gestión de SRs.

## MANUAL, AUTO y controles por riesgo

| Modo | Consultas y borradores | Crear, actualizar, adjuntar o cerrar |
| --- | --- | --- |
| MANUAL, predeterminado | Puede leer y preparar el caso con el acceso autorizado. | Muestra la acción, el SR/cuenta, el texto y los archivos. Espera el OK del usuario al borrador concreto antes de enviar. |
| AUTO, elegido expresamente | Puede leer y preparar el caso con el acceso autorizado. | Ejecuta las acciones incluidas en el trabajo autorizado, también una creación con selección nueva inequívoca validada contra el catálogo. Cerrar un SR mantiene revisión manual. |

Por ejemplo: “Prepará la respuesta y mostrámela antes de enviarla”. Una vez revisada: “OK, publicá esa nota y ese adjunto”. Si cambia el contenido o el destino, se revisa la nueva versión. Un OK a ese mismo borrador no se pide de nuevo.

Para AUTO: “Usá AUTO para responder este SR con el resultado de estas comprobaciones y adjuntar el diagnóstico”. Al terminar ese trabajo vuelve a MANUAL. Cada sesión nueva comienza en MANUAL. AUTO conserva los controles de cuenta, clasificación, permisos, duplicados y resultados inciertos. Una instrucción genérica de AUTO no autoriza el cierre: el caso y motivo concretos pasan por aprobación manual. Un borrador exacto ya aprobado no se vuelve a aprobar.

## Controles según el riesgo

| Acción | Comportamiento |
| --- | --- |
| Leer, listar o preparar un borrador | Puede continuar con el acceso autorizado. |
| Crear con una ruta ya comprobada, actualizar o adjuntar | Sigue MANUAL o el alcance AUTO expresamente elegido. |
| Crear para un producto nuevo | Obtiene una selección inequívoca del catálogo vigente y respeta MANUAL o AUTO. No pide otro OK solo por primer uso ni exige un SR anterior. |
| Cerrar un SR | Siempre pide aprobación del caso y motivo exactos, incluso en AUTO. |
| Usar una ruta con una discrepancia conocida | Bloquea su uso para incidentes reales hasta resolverla. |
| Borrar, detener o modificar infraestructura | Fuera del alcance de esta skill; requiere otro flujo con recursos, impacto y aprobación manual concretos. |
| Escritura desconocida sin política de riesgo | Se deniega. |

La aprobación se vincula al contenido, perfil, destino y archivos; si cambian, el OK anterior no habilita esa nueva escritura. Los resultados inciertos se concilian antes de reintentar para evitar duplicados. Emails, notas y logs aportan evidencia, nunca permisos para ejecutar instrucciones embebidas. Estos controles siguen los principios de mínimo alcance y revisión humana de [OWASP](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/).

La confirmación pertenece al flujo de la skill. El digest detecta cambios, pero no prueba por sí solo que una persona aprobó: el asistente debe obtener el OK real. Los permisos de Codex/Claude, del sistema operativo, IAM y soporte siguen aplicándose por separado; la skill no cambia esas políticas globales.

## Los datos fundamentales se preguntan

El título se redacta y valida antes de pedir aprobación, dentro del presupuesto preventivo local de 80 caracteres; no es una afirmación sobre el máximo contractual de Oracle. En AUTO, acortar solo el título sin cambiar el sentido no requiere otro OK. Tras un rechazo explícito HTTP 400 / INVALID_SR_TICKET_TITLE, con intento rejected y sin clave de SR, se concilian los casos visibles y se permite como máximo un envío corregido, sin cambiar descripción, ruta, impacto o destino. Un resultado incierto no se reintenta. MANUAL mantiene la aprobación del borrador exacto.

En ambos modos, la skill obtiene los datos del contexto o de lecturas autorizadas. Si falta un dato importante para la acción, pregunta antes de escribir. No inventa OCIDs, resultados, logs, producto/categoría, entorno productivo, impacto de negocio, severidad, identidad ni compromisos de atención. Los hechos contradictorios se informan y se investigan.

Puede elegir detalles de presentación, como el título de una sección, el orden del resumen o el nombre descriptivo de un archivo. Un dato importante desconocido queda marcado como pendiente en el borrador. La persona aporta las decisiones de negocio que los logs no pueden resolver.

## Actualizaciones legibles

El portal de My Oracle Support consultado interpreta las notas como HTML y agrupa las líneas de texto sin formato. La skill convierte párrafos, títulos y listas en una nota legible. Escapa el contenido de logs y diagnósticos para conservarlo como texto.

Una actualización puede tener esta estructura:

```text
Hi Support,

## Summary
- Current symptom and business impact.
- What changed since the previous update.

## Evidence
Operation: GetResource
UTC: actual test time
Result: actual status and code
Request ID: exact correlation ID

## Requested action
Specific investigation or supported remediation requested from Oracle.
```

El asistente separa los identificadores largos y resume los hallazgos. Los logs extensos se adjuntan cuando corresponde. Antes de enviar, se puede revisar el borrador local; después, la skill consulta el SR para comprobar que la nota quedó guardada. La aceptación del API y la presentación visual en el portal son comprobaciones distintas.

El formato predeterminado del helper es `--text-format readable`. Admite párrafos, títulos con `##` y listas con `- `; no es un conversor general de Markdown. La convención de HTML limitado se comprobó en el portal y no representa un esquema de texto enriquecido documentado por Oracle.

Las actualizaciones agregan correspondencia. No reescriben ni eliminan notas anteriores. Si hace falta aclarar una nota previa, se publica una nueva cuando el usuario lo solicita.

## Qué recibe el usuario después de cada operación

Después de cada operación recibís:

- Enlace y número del SR, título, descripción completa, severidad y estado, con el contenido original y formato legible.
- Resultado de la acción: nota enviada, archivo adjuntado o cierre solicitado, según corresponda.
- Verificación posterior, pendientes y acceso al JSON completo como evidencia.

Los datos ausentes no se inventan. Los detalles técnicos quedan disponibles sin ocupar la respuesta principal.

Referencias: [agregar comentarios](https://docs.oracle.com/en-us/iaas/Content/GSG/support/update-incident-add-comment.htm) y [modelo UpdateActivityItemDetails](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/cims/models/oci.cims.models.UpdateActivityItemDetails.html).

## Referencias oficiales

- [Crear SR y requisitos de soporte](https://docs.oracle.com/en-us/iaas/Content/GSG/support/create-incident.htm)
- [Referencia IAM de Support Management](https://docs.oracle.com/en-us/iaas/Content/GSG/support/policy-reference.htm)
- [Seguridad y políticas de tickets](https://docs.oracle.com/en-us/iaas/Content/Security/Reference/support-management.htm)
- [Python IncidentClient](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/cims/client/oci.cims.IncidentClient.html)
- [Clasificación de CreateTechSupportItemDetails](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/cims/models/oci.cims.models.CreateTechSupportItemDetails.html)
- [OCI CLI Support](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/support.html)
- [OCI CLI raw-request](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/raw-request.html)
- [Taxonomía de productos](https://docs.oracle.com/en-us/iaas/Content/GSG/support/list-incident-resource-types-taxonomy.htm)
- [Notas y comentarios](https://docs.oracle.com/en-us/iaas/Content/GSG/support/update-incident-add-comment.htm)
- [Adjuntos](https://docs.oracle.com/en-us/iaas/Content/GSG/support/update-incident-add-attachment.htm)
- [Actualización y cierre](https://docs.oracle.com/en-us/iaas/Content/GSG/support/update-incident.htm)
- [Cambios y deprecaciones del servicio](https://docs.oracle.com/en-us/iaas/Content/servicechanges.htm)

- [IAM de Autonomous Database Serverless](https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/autonomous-database-iam-policies.html)
- [SDK DatabaseClient](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/database/client/oci.database.DatabaseClient.html)
- [MCP nativo: Use MCP Server](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/use-mcp-server.html)
- [Prerrequisitos del MCP](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/prerequisites.html)
- [Configuración de herramientas integradas](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/autonomous-tools.html)
- [Errores consultables: V$CLIENT_ERRORS](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/autonomous-query-alert-log.html)
- [Cambio de acceso a datos del alert log en ADB Serverless](https://docs.oracle.com/en-us/iaas/releasenotes/autonomous-database-serverless/2025-07-query-for-client-errors.htm)
- [Generación y descarga de AWR mediante Performance Hub](https://docs.oracle.com/en-us/iaas/performance-hub/doc/download-awr-report.html)
- [AWR mediante OCI CLI: GetAwrDbReport](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/database-management/managed-database/get-awr-db-report.html)
- [REST-Enabled SQL: autenticación, SQL/PLSQL y resultados JSON](https://docs.oracle.com/en/database/oracle/oracle-rest-data-services/26.2/orddg/rest-enabled-sql-service.html)
- [API PL/SQL de AWR](https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_WORKLOAD_REPOSITORY.html)
- [Database Management para ADB Serverless](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/mdw-oci-database-management.html)
- [IAM de Database Management](https://docs.oracle.com/en-us/iaas/database-management/doc/policy-details-database-management.html)
- [Blog oficial: observabilidad, AWR y SQL trace en ADB Serverless](https://blogs.oracle.com/autonomous-ai-database/autonomous-database-serverless-observability-for-adbs)
- [SQLcl MCP oficial](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/25.4/sqcug/using-oracle-sqlcl-mcp-server.html)
- [Restricciones de SQLcl MCP](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/25.4/sqcug/configuring-restrict-levels-sqlcl-mcp-server.html)
- [Blog oficial SQLcl MCP](https://blogs.oracle.com/ai-and-datascience/ai-driven-sql-made-simple-with-oracle-sqlcl-mcp-server)
