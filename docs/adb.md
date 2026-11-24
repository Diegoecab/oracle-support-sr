# Gestión de SRs de ADB Serverless con CLI, SDK y skill

Versión 0.9.17. Revisión: 20/11/2026.

## Gestión de SRs mediante API, CLI y SDK

Los Service Requests (SRs) de **Autonomous Database Serverless** pueden gestionarse mediante la **Support Management API de OCI**, tanto por REST como desde OCI CLI y los SDK oficiales. Estas interfaces permiten crear y consultar casos, publicar actualizaciones, subir archivos y solicitar el cierre.

Pongo a disposición [oracle-support-sr](https://github.com/Diegoecab/oracle-support-sr), una skill compatible con **Codex y Claude Code** que puede ayudar a simplificar la apertura y el seguimiento de SRs. Permite trabajar con pedidos en lenguaje natural, reutilizar el contexto disponible y consultar el resultado de cada operación.

Esta guía reúne instalación, permisos, campos y ejemplos para que el equipo pruebe el flujo con casos autorizados y evalúe su adopción. También detalla los modos de aprobación y las limitaciones identificadas para este servicio.

**Un plus en ADB: del AWR al SR con menos pasos.** El asistente obtiene el reporte mediante la [API de Database Management](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/database_management/client/oci.database_management.DbManagementClient.html#get_awr_db_report) y usa la skill para adjuntarlo y actualizar el caso. Resuelve por API los identificadores y snapshots, guarda el HTML y comprueba la recepción; el usuario no prepara archivos SQL ni copia parámetros. El [flujo de recolección y adjunto](https://github.com/Diegoecab/oracle-support-sr/blob/main/docs/adb-awr-api.md) requiere Diagnostics & Management configurado y permanece fuera de la skill de SRs. El [MCP nativo de ADB](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/use-mcp-server.html) puede aportar otros diagnósticos mediante herramientas autorizadas. El [beneficio adicional del AWR](#plus-awr) se evalúa aparte del escenario estimativo del 83 %. [Ver el ejemplo observado: 4 min 13 s](#ejemplo-observado).

### Tres ejemplos: del pedido al resultado

Ejemplos ilustrativos con datos ficticios; no son salidas de operaciones ejecutadas. El recurso y el perfil ya están identificados. La actualización y el cierre usan el mismo SR creado en el primer ejemplo. Las salidas muestran el resultado posterior a las aprobaciones y a la verificación por API.

#### Crear el SR

```prompt
Creá un SR por la lentitud de esta ADB. Es un entorno de pruebas, sin impacto productivo.
```

**Salida ilustrativa del asistente**

```text
SR: SR_DEL_EJEMPLO
Título: ADB Serverless: slow response times in non-production
Tipo: TECH
Severidad: LOW
Estado: ACTIVE / PENDING_WITH_ORACLE

Descripción del SR
Response times increased in a non-production Autonomous Database Serverless instance during the incident window. No production impact is reported.

We will provide an AWR report for the affected period. Please investigate and recommend the next diagnostic steps.

Resultado: SR creado y consultado para comprobar su contenido.
```

#### Actualizar el SR y adjuntar evidencia

```prompt
Obtené el AWR del período del incidente por Database Management, adjuntalo al SR y publicá la actualización.
```

Este ejemplo es ilustrativo. La vía de Database Management se probó en laboratorio; el ejemplo observado de esta guía muestra el flujo y sus límites. El reporte se obtiene por API antes del upload.

**Salida ilustrativa del asistente**

```text
SR: SR_DEL_EJEMPLO
Título: ADB Serverless: slow response times in non-production
Tipo: TECH
Severidad: LOW
Estado: ACTIVE / PENDING_WITH_ORACLE

Descripción del SR
Response times increased in a non-production Autonomous Database Serverless instance during the incident window. No production impact is reported.

We will provide an AWR report for the affected period. Please investigate and recommend the next diagnostic steps.

Obtención del AWR: Database Management · GetAwrDbReport · HTML
Ventana del reporte: 2026-01-15 10:00–11:00 UTC

Adjunto: awr.html
Tamaño: 256 KiB
Acceso: restringido
Estado del adjunto: RECEIVED

Nota publicada
We have attached awr.html, obtained through the Database Management GetAwrDbReport API for the affected database. The report covers 2026-01-15 10:00 to 11:00 UTC. Please review the AWR evidence and recommend the next diagnostic steps.

Verificación: nota y recepción del archivo confirmadas al consultar el SR.
```

#### Cerrar el SR

```prompt
Cerrá el SR; ya validamos que quedó resuelto.
```

Antes del cierre, el asistente muestra el motivo y pide el OK manual, incluso en AUTO. La salida representa el resultado posterior a esa aprobación.

**Salida ilustrativa del asistente**

```text
SR: SR_DEL_EJEMPLO
Título: ADB Serverless: slow response times in non-production
Tipo: TECH
Severidad: LOW
Estado: CLOSED

Descripción del SR
Response times increased in a non-production Autonomous Database Serverless instance during the incident window. No production impact is reported.

We will provide an AWR report for the affected period. Please investigate and recommend the next diagnostic steps.

Motivo publicado
We have verified that the issue is resolved in our non-production environment. Please close this service request.

Verificación: cierre confirmado al consultar el SR; el historial se conserva.
```

**Documentación oficial de Oracle**

- [Gestión de SRs: creación mediante consola, CLI y API](https://docs.oracle.com/en-us/iaas/Content/GSG/support/create-incident.htm).
- [Referencia de las API REST de OCI](https://docs.oracle.com/en-us/iaas/api/).
- [OCI CLI: Support Management](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/support.html).
- [SDK Python: IncidentClient de Support Management](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/cims/client/oci.cims.IncidentClient.html).

<a id="ejemplo-observado"></a>

## Un SR con AWR adjunto en 4 min 13 s

El 24/11/2026 se observó una ejecución de **4 min 13 s** para reunir el contexto de la base, obtener el AWR por **Database Management**, crear el SR, cargar el HTML como adjunto restringido, publicar la nota y consultar el caso hasta comprobar **RECEIVED**.

La duración corresponde al tiempo mostrado por el asistente en la captura compartida. Los recibos locales corroboran el alta, el upload, la actualización y la recepción del archivo. Para compartir este ejemplo se reemplazaron el nombre de la base, SR, OCIDs, DBID, nombre del archivo y claves del catálogo; se mantienen el flujo, la clasificación solicitada, los estados, la ventana y el tamaño del reporte.

| Mismo trabajo | Tiempo | Base de comparación |
| --- | --- | --- |
| Consola y carga manual | 30–40 min | Estimación del usuario; no se cronometró una ejecución manual equivalente. |
| Asistente con APIs y skill de SRs | 4 min 13 s | Duración observada de este ejemplo, con el entorno previamente configurado. |
| Ahorro estimado | 25 min 47 s–35 min 47 s | Aproximadamente **86–89 % menos tiempo** respecto de la estimación manual. |

La comparación incluye localizar los datos de la DB —OCID, compartment y región—, seleccionar la clasificación, preparar el texto en inglés, obtener y guardar el AWR, completar el SR, cargar el archivo, publicar la nota y revisar el resultado. Requiere autenticación vigente, SDK compatible y Diagnostics & Management configurado. Excluye esa preparación inicial y el tiempo posterior de respuesta de Oracle. Es una observación de laboratorio, no una garantía ni una medición general del servicio.

**Cobertura del AWR:** se pidieron las últimas dos horas; los snapshots 93–95 cubrieron 11:02:49–13:02:26, hora de Buenos Aires. La ventana solicitada terminaba a las 13:37:26. La diferencia de aproximadamente 35 minutos se informó; no se presenta el reporte como cobertura exacta de esa ventana.

**Clasificación:** se comprobó la selección contra el catálogo. La clasificación persistida y la asignación interna no fueron devueltas en la consulta del caso y continúan como **NOT_VERIFIED**. El estado RECEIVED corresponde al adjunto.

### Pedido del usuario, anonimizado

```prompt
Usá oracle-support-sr para crear un SR de severidad MEDIA para la DB DB_PRUEBA, por problemas generales de performance. Obtené el AWR de las últimas 2 horas, adjuntalo al SR y publicá la actualización.
```

### Transcripción anonimizada del resultado observado

```text
SR: SR_DEL_EJEMPLO
Title: DB_PRUEBA: general database performance problems
Type: TECH | Severity: MEDIUM | Status: ACTIVE / PENDING_WITH_ORACLE

Description saved (identifiers replaced for this document)
We are experiencing general performance problems on DB_PRUEBA and request MEDIUM severity. Please investigate the cause and recommend corrective actions. Detailed business impact and affected SQL statements have not yet been established.
Service: Autonomous Database Serverless, us-ashburn-1. Current state: AVAILABLE.
Resource: [RESOURCE_OCID]
Compartment: [COMPARTMENT_OCID]
Routing: Autonomous Database Serverless / Database Performance / Overall Database Performance issues and not specific to SQLs.
We collected an AWR through Database Management, DBID [DBID], snapshots 93-95, 2026-11-24T14:02:49+00:00 to 2026-11-24T16:02:26+00:00. These are the latest two complete intervals available. The rolling two-hour window cannot be covered exactly because the latest snapshot ends at 2026-11-24T16:02:26+00:00. We will attach the report and publish its diagnostic context.

Requested classification
Product / service: Autonomous Database Serverless
Category: Database Performance
Subcategory: Overall Database Performance issues and not specific to SQLs
Catalog keys: [KEYS_FROM_LIVE_CATALOG]
Persisted classification and internal assignment: NOT_VERIFIED
Structured impact: not returned; no value inferred

Attachment: DB_PRUEBA-AWR.html | 697,743 bytes | Restricted | RECEIVED
Update: published and verified by a subsequent case read
Content of the update: report, resource, actual snapshot window and coverage limitation

Requested AWR window: 2026-11-24 14:37:26–16:37:26 UTC
Actual AWR window: 2026-11-24 14:02:49–16:02:26 UTC
The latest available snapshot did not cover the final 35 minutes of the requested window. This limitation was disclosed in the SR.
```


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

Si el equipo todavía genera y descarga los AWR desde el portal y después los carga a mano en Oracle Support, puede automatizar ese recorrido con Database Management y la skill de SRs.

| Trabajo del seguimiento | Qué ejecuta el asistente |
| --- | --- |
| Preparar el diagnóstico | Identifica la base administrada y resuelve por API los datos AWR y los snapshots de la ventana solicitada. Pregunta solo por datos fundamentales que falten. |
| Obtener el reporte | Invoca GetAwrDbReport, guarda el HTML y comprueba base, intervalo y contenido. |
| Entregar la evidencia | Usa oracle-support-sr para adjuntar el archivo, publicar la actualización y verificar el resultado. |

El usuario hace el pedido en lenguaje natural. No prepara scripts, elige números de snapshots ni descarga archivos a mano. El flujo requiere Diagnostics & Management configurado; su habilitación y costo adicional se tratan por separado. La recolección permanece fuera de oracle-support-sr y respeta los modos MANUAL y AUTO para publicar en el SR.

El [ejemplo observado del 24/11/2026](#ejemplo-observado) completó apertura, AWR, adjunto, nota y verificación en 4 min 13 s. Frente a los 30–40 minutos manuales estimados por el usuario, representa un ahorro estimado de 86–89 %. Es una gestión de apertura; el calculador del 83 % modela por separado un SR con cinco interacciones.

<details>
<summary>Cómo medir el ahorro adicional</summary>

Comparar el mismo seguimiento con y sin automatización, registrando el tiempo activo de la persona y el tiempo transcurrido hasta confirmar RECEIVED. Incluir identificación de la base y ventana, recolección, validación, upload y procesamiento. El ejemplo observado usa GetAwrDbReport y excluye la configuración inicial. La alternativa manual es una estimación, no una ejecución comparativa cronometrada.

</details>

[Ver el flujo automatizado de recolección y adjunto](https://github.com/Diegoecab/oracle-support-sr/blob/main/docs/adb-awr-api.md).

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

```prompt
Usá oracle-support-sr con MI_PERFIL para validar acceso y listar mis SRs.
```

```prompt
No puedo conectarme a la ADB "VENTASTEST" del compartment "Aplicaciones-Pruebas". Reuní el contexto y prepará un SR.
```

Los nombres son ilustrativos. El asistente recupera los OCIDs con las lecturas autorizadas; si la selección es ambigua, pregunta por el dato que falte.

Por nombre de la base:

```prompt
Revisá el pedido de Oracle en el SR de la ADB "VENTASTEST" y prepará la respuesta con los diagnósticos disponibles.
```

Por los últimos dígitos del SR:

```prompt
Revisá el pedido de Oracle en el SR que termina en 1234 y prepará la respuesta con los diagnósticos disponibles.
```

El asistente busca entre los SRs visibles, comprueba la coincidencia y muestra el número completo y el título del caso identificado. Si hay varios SRs para esa base o el sufijo no identifica un único caso, pregunta cuál usar. A la API se envía la clave completa, nunca solo el sufijo.

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

En Codex, pedir usar oracle-support-sr. En Claude, la skill del plugin se invoca como `/oracle-support-sr:oracle-support-sr`. La skill usa un entorno aislado con SDK 2.177.0, compartido por ambos agentes y con soporte de adjuntos comprobado antes de iniciar el flujo. La primera preparación necesita venv/pip e Internet; no modifica el Python global ni OCI CLI.

```text
python scripts/run_sr.py --check-runtime
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

El AWR se obtiene mediante la API de Database Management. El asistente orquesta las llamadas OCI con CLI/SDK y entrega el archivo a oracle-support-sr para actualizar el caso. La recolección es independiente del helper de SRs.

Con la base, el SR y el período del incidente ya identificados:

```prompt
Obtené el AWR de esta ADB para el período del incidente y adjuntalo al SR.
```

| Etapa | Operaciones que ejecuta el asistente |
| --- | --- |
| Identificar el recurso | ListManagedDatabases y GetManagedDatabase, comprobando la correspondencia con la ADB y su región. |
| Resolver la ventana | ListAwrDbs, SummarizeAwrDbSnapshotRanges y ListAwrDbSnapshots para seleccionar la base, el contenedor y los snapshots pertinentes. |
| Obtener y validar el archivo | GetAwrDbReport con reportType=AWR y reportFormat=HTML; guarda content y comprueba base, ventana y contenido. |
| Actualizar el caso | La skill adjunta el archivo como restringido, publica la nota y consulta el SR para comprobar ambos resultados. |

El asistente consulta todas las páginas necesarias, conserva la ventana solicitada y efectiva y resuelve los valores técnicos con las respuestas. Si falta un dato fundamental, el recurso es ambiguo o no hay snapshots suficientes, informa la limitación antes de publicar. El usuario no necesita buscar DBIDs ni preparar archivos SQL. En MANUAL se conserva la aprobación antes del envío; en AUTO se ejecuta el alcance autorizado.

El [flujo completo de recolección y adjunto](https://github.com/Diegoecab/oracle-support-sr/blob/main/docs/adb-awr-api.md) describe los requisitos y la verificación. OCI Monitoring permite complementar el SR con métricas, pero no genera AWR.

## Requisitos de la recolección

Diagnostics & Management debe estar habilitado con conexión y credencial de diagnóstico válidas. Las funciones avanzadas tienen costo adicional; habilitarlas no forma parte de una actualización del SR. GetAwrDbReport requiere DBMGMT_MANAGED_DB_READ, con acceso separado a las credenciales o secretos que correspondan y los permisos de descubrimiento necesarios. Oracle exige ADMIN para las funciones avanzadas que lo requieren. No se crean bases, generan snapshots, cambian permisos ni habilitan servicios automáticamente.

Referencias: [GetAwrDbReport por CLI](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/database-management/managed-database/get-awr-db-report.html), [SDK Python](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/database_management/client/oci.database_management.DbManagementClient.html), [configuración de Database Management para ADB](https://docs.oracle.com/en-us/iaas/database-management/doc/enable-database-management-autonomous-databases.html), [matriz de soporte](https://docs.oracle.com/en-us/iaas/database-management/doc/database-management-feature-support-matrix.html) e [IAM](https://docs.oracle.com/en-us/iaas/database-management/doc/policy-details-database-management.html).

Validación pendiente: la API está documentada por Oracle, pero este recorrido aún no se ejecutó con una ADB. La instalación de la skill no despliega un recolector ni habilita servicios.

## MCP como fuente opcional de evidencia

Autonomous Database Serverless dispone de un [MCP nativo administrado](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/use-mcp-server.html). Puede aportar resultados de herramientas Select AI Agent ya habilitadas y autorizadas para la identidad de la base. No se limita a SQLcl ni implica acceso SQL irrestricto.

| Alternativa | Alcance para reunir evidencia |
| --- | --- |
| MCP nativo de la base | Endpoint por base; herramientas autorizadas expuestas mediante Select AI Agent. Revisar los prerrequisitos y permisos de cada herramienta. |
| SQLcl MCP | Otra alternativa para una conexión guardada y consultas de diagnóstico aprobadas. Se configura y autentica por separado. |

| Evidencia | Alcance documentado y preparación necesaria |
| --- | --- |
| Errores y datos de logs accesibles al cliente | Oracle documenta la consulta de V$CLIENT_ERRORS. Para invocarla por MCP debe existir una herramienta autorizada con acceso a esa vista. Esto no equivale a descargar todos los logs internos de Oracle. |
| Reportes AWR | El flujo de esta guía usa GetAwrDbReport de Database Management y no requiere MCP. No se encontró una herramienta AWR preconfigurada en el MCP nativo consultado. El MCP puede aportar otros diagnósticos mediante herramientas autorizadas; su configuración es independiente. |

Las fuentes son [Use MCP Server](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/use-mcp-server.html), [Query for Client Errors](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/autonomous-query-alert-log.html) y [GetAwrDbReport](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/database-management/managed-database/get-awr-db-report.html). Para ADB Serverless, la [nota de Oracle](https://docs.oracle.com/en-us/iaas/releasenotes/autonomous-database-serverless/2025-07-query-for-client-errors.htm) indica que V$DIAG_ALERT_EXT no está disponible para datos del alert log y remite a V$CLIENT_ERRORS.

Usar únicamente herramientas de diagnóstico autorizadas y conexiones ya disponibles. Activar el MCP, crear herramientas, cambiar grants o habilitar servicios son tareas separadas; la instalación de la skill no las ejecuta. Configurar permisos y aprobaciones del cliente MCP aparte de los del plugin de SRs.

Revisar y filtrar los resultados antes de una nota o adjunto: SQL, literales y datos pueden contener información de negocio. No adjuntar credenciales ni wallets. Si la base es inaccesible, el MCP no elimina ese bloqueo; reunir evidencia del control plane y de las fuentes que sí estén disponibles. La conexión mediante estos MCPs no se probó durante el piloto de gestión de SRs.

## MANUAL, AUTO y controles por riesgo

| Modo | Consultas y borradores | Crear, actualizar, adjuntar o cerrar |
| --- | --- | --- |
| MANUAL, a pedido del usuario | Puede leer y preparar el caso con el acceso autorizado. | Muestra la acción, el SR/cuenta, el texto y los archivos. Espera el OK del usuario al borrador concreto antes de enviar. |
| AUTO, predeterminado | Puede leer y preparar el caso con el acceso autorizado. | Ejecuta las acciones incluidas en el trabajo autorizado, también una creación con selección nueva inequívoca validada contra el catálogo. Cerrar un SR mantiene revisión manual. |

Por ejemplo: “Prepará la respuesta y mostrámela antes de enviarla”. Una vez revisada: “OK, publicá esa nota y ese adjunto”. Si cambia el contenido o el destino, se revisa la nueva versión. Un OK a ese mismo borrador no se pide de nuevo.

Para AUTO: “Usá AUTO para responder este SR con el resultado de estas comprobaciones y adjuntar el diagnóstico”. Cada tarea nueva comienza en AUTO, salvo una preferencia MANUAL vigente del usuario. AUTO conserva los controles de cuenta, clasificación, permisos, duplicados y resultados inciertos. Una instrucción genérica de AUTO no autoriza el cierre: el caso y motivo concretos pasan por aprobación manual. Un borrador exacto ya aprobado no se vuelve a aprobar.

## Controles según el riesgo

| Acción | Comportamiento |
| --- | --- |
| Leer, listar o preparar un borrador | Puede continuar con el acceso autorizado. |
| Crear con una ruta ya comprobada, actualizar o adjuntar | Sigue MANUAL o el alcance AUTO autorizado. |
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
- [AWR mediante OCI CLI: GetAwrDbReport](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/database-management/managed-database/get-awr-db-report.html)
- [Database Management para ADB Serverless](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/mdw-oci-database-management.html)
- [IAM de Database Management](https://docs.oracle.com/en-us/iaas/database-management/doc/policy-details-database-management.html)
- [Blog oficial: observabilidad, AWR y SQL trace en ADB Serverless](https://blogs.oracle.com/autonomous-ai-database/autonomous-database-serverless-observability-for-adbs)
- [SQLcl MCP oficial](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/25.4/sqcug/using-oracle-sqlcl-mcp-server.html)
- [Restricciones de SQLcl MCP](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/25.4/sqcug/configuring-restrict-levels-sqlcl-mcp-server.html)
- [Blog oficial SQLcl MCP](https://blogs.oracle.com/ai-and-datascience/ai-driven-sql-made-simple-with-oracle-sqlcl-mcp-server)
