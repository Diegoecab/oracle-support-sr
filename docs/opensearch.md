# Gestión de SRs de OCI OpenSearch con CLI, SDK y skill

Versión 0.9.16. Revisión: 20/11/2026.

## Gestión de SRs mediante API, CLI y SDK

Los Service Requests (SRs) de **OCI Search Service with OpenSearch** pueden gestionarse mediante la **Support Management API de OCI**, tanto por REST como desde OCI CLI y los SDK oficiales. Estas interfaces permiten crear y consultar casos, publicar actualizaciones, subir archivos y solicitar el cierre.

Pongo a disposición [oracle-support-sr](https://github.com/Diegoecab/oracle-support-sr), una skill compatible con **Codex y Claude Code** que puede ayudar a simplificar la apertura y el seguimiento de SRs. Permite trabajar con pedidos en lenguaje natural, reutilizar el contexto disponible y consultar el resultado de cada operación.

Esta guía reúne instalación, permisos, campos y ejemplos para que el equipo pruebe el flujo con casos autorizados y evalúe su adopción. También detalla los modos de aprobación y las limitaciones identificadas para este servicio.



### Tres ejemplos: del pedido al resultado

Ejemplos ilustrativos con datos ficticios; no son salidas de operaciones ejecutadas. El recurso y el perfil ya están identificados. La actualización y el cierre usan el mismo SR creado en el primer ejemplo. Las salidas muestran el resultado posterior a las aprobaciones y a la verificación por API.

#### Crear el SR

```prompt
Creá un SR por la latencia de búsqueda de este cluster. Es un entorno de pruebas, sin impacto productivo.
```

**Salida ilustrativa del asistente**

```text
SR: SR_DEL_EJEMPLO
Título: OpenSearch: search latency in a non-production cluster
Tipo: TECH
Severidad: LOW
Estado: ACTIVE / PENDING_WITH_ORACLE

Descripción del SR
Search latency increased in a non-production cluster during the incident window. No production impact is reported.

We will provide the relevant cluster logs. Please investigate and advise on the next diagnostic steps.

Resultado: SR creado y consultado para comprobar su contenido.
```

#### Actualizar el SR y adjuntar evidencia

```prompt
Adjuntá cluster-logs.txt al SR y publicá una actualización con el contexto de los logs.
```

**Salida ilustrativa del asistente**

```text
SR: SR_DEL_EJEMPLO
Título: OpenSearch: search latency in a non-production cluster
Tipo: TECH
Severidad: LOW
Estado: ACTIVE / PENDING_WITH_ORACLE

Descripción del SR
Search latency increased in a non-production cluster during the incident window. No production impact is reported.

We will provide the relevant cluster logs. Please investigate and advise on the next diagnostic steps.

Origen del archivo: Logs del cluster disponibles en el contexto autorizado.

Adjunto: cluster-logs.txt
Tamaño: 48 KiB
Acceso: restringido
Estado del adjunto: RECEIVED

Nota publicada
We have attached cluster-logs.txt with the log entries collected for the incident window. Please correlate this evidence with the reported search latency and advise on the next diagnostic steps.

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
Título: OpenSearch: search latency in a non-production cluster
Tipo: TECH
Severidad: LOW
Estado: CLOSED

Descripción del SR
Search latency increased in a non-production cluster during the incident window. No production impact is reported.

We will provide the relevant cluster logs. Please investigate and advise on the next diagnostic steps.

Motivo publicado
We have verified that the issue is resolved in our non-production environment. Please close this service request.

Verificación: cierre confirmado al consultar el SR; el historial se conserva.
```

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

## Qué cubre esta guía

Guía para crear, consultar, actualizar, adjuntar evidencia y cerrar SRs de OCI Search Service with OpenSearch con OCI CLI, SDK Python y la skill oracle-support-sr. La recolección usa solo lecturas autorizadas del servicio; gestionar el SR no implica operar ni modificar el cluster.

## Pasos por consola

Estos son, a grandes rasgos, los pasos para crear y mantener el SR desde la consola. Cada seguimiento puede requerir volver a autenticarse y reunir nueva evidencia.

<details>
<summary>01 · Autenticarse y seleccionar el producto</summary>

Entrar a OCI/My Oracle Cloud Support y elegir el producto, tipo de problema e impacto. Revisar el contexto que el portal ya haya precargado.

</details>

<details>
<summary>02 · Reunir identificadores y contexto</summary>

Localizar el cluster afectado, su OCID, región, compartment y ventana del problema. Confirmar que la cuenta y el recurso corresponden al incidente.

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

El usuario expresa el problema en lenguaje natural; el asistente reutiliza perfil y cluster del contexto y pregunta por los datos relevantes que falten.

```prompt
Usá oracle-support-sr con MI_PERFIL para validar acceso y listar mis SRs.
```

```prompt
Prepará un SR por el error de restore de este cluster de OpenSearch.
```

```prompt
Qué novedades hay? Reuní lo que pide Oracle y prepará la respuesta.
```

En MANUAL se muestra la escritura concreta antes del envío. El asistente resuelve OCIDs y claves desde lecturas y catálogo; no obliga al usuario a dictar JSON o IDs opacos. Si faltan impacto, entorno o una selección inequívoca, pregunta.

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


Para diagnósticos, agregar solo las lecturas necesarias y acotarlas al compartment del cluster:

```text
Allow group SR-Evidence to inspect opensearch-clusters in compartment CLUSTER_COMPARTMENT
Allow group SR-Evidence to inspect opensearch-cluster-backups in compartment CLUSTER_COMPARTMENT
Allow group SR-Evidence to inspect opensearch-work-requests in compartment CLUSTER_COMPARTMENT
```

La referencia IAM de Oracle asigna Get/List a permisos INSPECT; algunas filas conservan nombres de API Elasticsearch. Confirmar la operación vigente al implementar la política. Las dos últimas líneas se necesitan si se consultan backups y work requests. No otorgan acceso a documentos o índices del cluster.

La lectura del endpoint privado del cluster requiere conectividad, TLS y una identidad con roles de solo lectura apropiados para las APIs que se utilizarán. IAM del control plane y autenticación del cluster son capas distintas. Si hacen falta métricas, logs OCI o archivos existentes, agregar respectivamente read metrics, read log-content o read objects en el alcance pertinente. No habilitar logs, exportadores ni cambiar ajustes como efecto secundario de abrir un SR.

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


Aplicar la guía [SRDC1037: información requerida para investigar OCI OpenSearch](https://support.oracle.com/support/?kmContentId=2864665), que requiere acceso a Oracle Support, y la documentación actual del componente.

- Cluster OCID, nombre, versión, región, compartment y enlaces pertinentes.
- Componente/subcomponente y síntoma concretos; no equivalen automáticamente a categoryKey/subCategoryKey.
- UTC, error, reproducción y request ID de la operación que falló.
- Estado del cluster y de work requests; para backup/restore, identificar backup, origen, destino y operación involucrada cuando aplique.
- Salud, shards, presión de recursos y logs relevantes, si ya existe acceso autorizado a esa evidencia.
- Impacto, alcance y entorno confirmados por el responsable.

No inventar un cluster ni OCIDs para una consulta de planificación. No incluir documentos indexados o consultas con datos de negocio si no son necesarios y están autorizados para el caso.

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

## MCP como fuente opcional de evidencia

Oracle publica el [OCI OpenSearch MCP Server](https://github.com/oracle/mcp/tree/main/src/oci-opensearch-mcp-server), basado en las APIs del control plane. El [blog oficial del 6 de noviembre de 2026](https://blogs.oracle.com/cloud-infrastructure/managing-oci-opensearch-with-mcp-server) lo presenta como implementación de referencia para exploración, prototipos y aprendizaje, no para producción. Su existencia no implica una recomendación de despliegue productivo.

| Lectura del MCP | Evidencia que puede aportar |
| --- | --- |
| list_opensearch_clusters / get_opensearch_cluster | Descubrimiento y configuración del cluster. |
| list_work_requests / get_work_request | Estado y correlación de operaciones asíncronas. |
| list_opensearch_cluster_shapes | Contexto de shapes disponibles cuando sea pertinente. |

Es un servidor externo que usa un perfil OCI; no es un endpoint MCP nativo habilitado dentro del cluster ni un servidor de consultas de índices. Es una herramienta independiente: la skill administra SRs y no incluye código, instalación ni configuración de ese MCP. Su instalación y compatibilidad no se probaron en este piloto. Consultar los requisitos actualizados en el repositorio oficial.

El paquete también expone creación, borrado, actualización, resize y backup. Para reunir evidencia, limitar IAM y herramientas al subconjunto de lectura. Los permisos y aprobaciones del MCP se configuran aparte: los guardrails de la skill de SRs no gobiernan por sí solos otro servidor. No activar ni ejecutar mutaciones para preparar un ticket.

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

- [IAM de Search with OpenSearch](https://docs.oracle.com/en-us/iaas/Content/search-opensearch/Concepts/ocisearchpermissions.htm)
- [SDK del servicio OpenSearch](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/opensearch.html)
- [Métricas OCI del servicio](https://docs.oracle.com/en-us/iaas/Content/search-opensearch/ociopensearchmetrics.htm)
- [SRDC1037, acceso autenticado](https://support.oracle.com/support/?kmContentId=2864665)
- [MCP de OCI OpenSearch: README](https://github.com/oracle/mcp/tree/main/src/oci-opensearch-mcp-server)
- [MCP: requisitos de la versión de referencia](https://github.com/oracle/mcp/blob/main/src/oci-opensearch-mcp-server/pyproject.toml)
- [Blog oficial del MCP](https://blogs.oracle.com/cloud-infrastructure/managing-oci-opensearch-with-mcp-server)
