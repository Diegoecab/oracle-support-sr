# Producto, subproducto y control de enrutamiento

## Qué permite la API y qué está comprobado

La API permite enviar clasificación estructurada durante CreateIncident. El [modelo oficial CreateTechSupportItemDetails](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/cims/models/oci.cims.models.CreateTechSupportItemDetails.html) expone category, sub_category e issue_type. En JSON de red se usan category.categoryKey, subCategory.subCategoryKey e issueType.issueTypeKey, dentro de ticket.resourceList[].item, con type=tech. No hay campos superiores llamados product y subproduct en el contrato revisado, ni un parámetro público para fijar una cola interna de ingenieros.

El catálogo oficial se obtiene mediante [ListIncidentResourceTypes con problemType=TAXONOMY](https://docs.oracle.com/en-us/iaas/Content/GSG/support/list-incident-resource-types-taxonomy.htm). Mantiene la jerarquía service group -> service -> service category -> subcategory. Los nombres Product/Category del portal no representan necesariamente los mismos niveles con los mismos nombres.

```json
{
  "region": "IAD",
  "item": {
    "type": "tech",
    "category": {"categoryKey": "CATEGORY_KEY_FROM_LIVE_TAXONOMY"},
    "subCategory": {"subCategoryKey": "SUBCATEGORY_KEY_FROM_LIVE_TAXONOMY"}
  }
}
```

El ejemplo muestra la forma del contrato, no una receta lista para ejecutar. La clave de región se resuelve con Identity ListRegions. El SDK usa el nombre habitual de región para su endpoint. El comando CLI create aplanado no expone todo resourceList; usar SDK para esta clasificación.

| Nivel de comprobación | OpenSearch / Backup and Restore |
| --- | --- |
| Opción devuelta por el catálogo | Sí, con categoría y subcategoría identificadas. |
| Payload aceptado por CreateIncident | Sí; la respuesta repitió las claves enviadas. |
| Producto mostrado en el portal | Coincidió con OCI Search Service with OpenSearch. |
| Clasificación fina mostrada | No coincidió: se observó Cluster Provision and Resize. |
| Receta habilitada para creación técnica en la skill | No. Permanece sin verificar y se bloquea. |

No convertir el HTTP 200 ni las claves repetidas en una afirmación de que la cola es correcta. GetIncident devolvió actividades, sin el detalle persistido de clasificación necesario para comprobarla. Oracle todavía debe aclarar el mapeo fino; no inventar contextualData ni issueTypeKey para compensarlo. Una asignación interna tampoco es un atributo inmutable que este API garantice.

Como ejemplo de descubrimiento, la consulta del 17/11/2026 devolvió para OpenSearch: Backup and Restore, Connectivity, Import and Export, Performance y Cluster Provision and Resize. Ese listado ilustra el catálogo disponible en esa consulta, no cinco recetas verificadas. La skill vuelve a consultar el catálogo en el entorno del cliente.

## Schemas y selección de subcategoría

La taxonomía contiene más información que las claves y etiquetas. Los modelos oficiales [Services](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/cims/models/oci.cims.models.Services.html), [SubCategories](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/cims/models/oci.cims.models.SubCategories.html) y [SubComponents](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/cims/models/oci.cims.models.SubComponents.html) incluyen `schema` en distintos niveles y el indicador `hasSubCategory` donde corresponde.

En la rama OpenSearch consultada el 18/11/2026, el schema de la categoría padre coincide con el schema de Cluster Provision and Resize; Backup and Restore tiene otro schema. El primer valor coincide con la clasificación alternativa observada en el portal. Es una correlación concreta para investigar con Oracle, no una causa probada ni evidencia de que deba enviarse ese valor en otro campo.

La exportación anterior omitía esos metadatos. Desde 0.5.0 se conservan `service_schema`, `category_schema`, `subcategory_schema` y `category_has_subcategory`. La comparación con una receta verificada también los revisa: un cambio de schema puede detener una creación aunque las claves y etiquetas sigan iguales. Si el catálogo tiene variantes contradictorias para la misma ruta, no se elige la primera. Si exige subcategoría, no se acepta su omisión.

Estos valores se mantienen como evidencia del catálogo. No se traducen automáticamente a `issueTypeKey`, `contextualData.schemaName` ni a campos nuevos del request. El [modelo ContextualData](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/cims/models/oci.cims.models.ContextualData.html) define un contenedor, pero no establece por sí solo el contrato de ese payload para la ruta elegida. Hay que obtener y verificar el uso soportado antes de completar esos campos.

El [MCP oficial de Oracle, código de conversión revisado](https://github.com/oracle/mcp/blob/cdea374d50c230c221fe4ea306fcd953b3977ef9/src/oci-support-mcp-server/oracle/oci_support_mcp_server/models.py) pasa los campos al SDK sin aportar una traducción adicional de esos schemas. Cambiar a ese MCP no demuestra resolver el mapeo. También se inspeccionó el JSON original del GetIncident público: la respuesta del caso revisado no incluía una clasificación persistida estructurada ni historial interno de asignaciones. Esa ausencia no era únicamente un descarte del modelo del SDK.

## El mapeo que necesita la skill

Usar dos registros distintos:

- Catálogo disponible: obtenerlo de la API con el perfil del cliente. Guardar nombres, claves, jerarquía y fecha. Sirve para descubrir opciones, no para certificar el destino.
- Recetas verificadas del cliente: relacionar las claves exactas del payload con Product/Category realmente observados en un SR creado por ese contrato, tenancy/grupo, fuente de evidencia, fecha y vencimiento. Solo el estado VERIFIED habilita creación técnica. Las recetas no van embebidas con datos de una cuenta en el plugin distribuido.

La persona describe servicio/recurso, síntoma e impacto. El LLM obtiene los IDs desde el catálogo y busca una receta válida; no le pide que memorice claves. Los aliases humanos ayudan a buscar pero no habilitan un mapeo por similitud de texto. Si la selección es ambigua o el mapeo es desconocido, preparar el borrador y explicar el dato pendiente.

## Qué aplica el control actual

Desde 0.3.0, el helper requiere --routing-file para ejecutar create de tipo TECH. Comprueba coincidencia de tenancy/grupo, región y claves del request, igualdad de producto/categoría esperados y observados en la evidencia, vigencia de esa evidencia y pertenencia de la ruta a la taxonomía consultada en vivo. Un cambio de etiquetas o de jerarquía detiene el alta. Desde 0.5.0 compara además los schemas y la obligatoriedad de la subcategoría. No hay receta técnica preaprobada incluida en el paquete.

El archivo es una configuración local mantenida por el cliente, no un nuevo campo del API. La skill lo resuelve desde el contexto/configuración autorizada y lo pasa al helper. El usuario no tiene que escribirlo en cada pedido. No marcar VERIFIED automáticamente, falsificar una comprobación, ignorar un vencimiento ni cambiar a raw API/CLI para sortear el control.

La inicialización de recetas requiere evidencia externa comprobable del mismo contrato o una validación controlada autorizada para ese propósito. Una selección correcta en un SR creado por consola no prueba por sí sola el payload equivalente de API.

## Prueba controlada de una ruta nueva

Desde 0.6.0, `test-create` cubre esa validación inicial sin declarar una receta como VERIFIED. Solo se utiliza cuando el usuario solicita expresamente una prueba. `create` conserva el control de recetas verificadas para el uso habitual.

```text
python scripts/sr.py --profile MI_PERFIL --backend sdk --evidence-dir ./evidencia test-create --request-file prueba.json --test-plan-file plan-prueba.json --expected-tenancy TENANCY_OCID
```

El primer comando genera un borrador MANUAL, sin red ni credenciales. El envío usa su digest aprobado y `--execute`, como las otras escrituras. El plan debe declarar `schema_version=1`, `purpose=ROUTING_VALIDATION`, `status=CANDIDATE`, `production_use=false`, `max_creations=1`, un `test_id` estable, `tenancy_ocid`, `user_group_id`, `created_at_utc`, `expires_at_utc`, `expected_portal` y una sola entrada `routes` con la ruta completa y sus schemas. Su vigencia máxima es de 24 horas. El request debe ser TECH/LOW, tener título con prefijo `[ROUTING TEST] ` y contener este aviso literal en la descripción:

```text
Customer-authorized API routing validation; no production incident or infrastructure action is requested.
```

El flujo admite únicamente las claves de categoría/subcategoría del catálogo, sin contextualData ni issueTypeKey especulativos. Valida usuario/grupo y consulta la taxonomía en vivo antes del envío. Un cambio en la ruta o sus schemas detiene la prueba. Los metadatos schema siguen siendo evidencia: este flujo no convierte ninguno en un selector nuevo ni corrige por sí mismo el backend.

El recibo local se vincula a tenancy/test_id: repetir la misma solicitud exitosa devuelve su recibo; reutilizar ese ID con otro payload se bloquea. Esta protección comparte los límites del registro local; varios equipos deben compartir el registro para coordinarse. Un resultado incierto requiere conciliación antes de cualquier otro intento. No iniciar una serie de pruebas con IDs distintos para eludir esa conciliación.

El resultado mantiene `persisted_classification=NOT_VERIFIED` y no crea una receta de producción. Después se consulta el SR devuelto y se verifica el título/contenido. Si GetIncident solo devuelve actividades, la comprobación de Product/Category requiere otra lectura soportada o el portal. Si el usuario elige continuar solo por API, se informa esa parte pendiente. Un cierre autorizado corresponde únicamente al nuevo SR de prueba, conserva la limitación/discrepancia en su nota y se verifica con un GetIncident posterior. No cerrar el caso que investiga el mapeo ni otro SR existente.

El catálogo puede exportarse en formato simple para la skill:

```text
python scripts/sr.py --profile MI_PERFIL --evidence-dir ./evidencia taxonomy --catalog-file ./configuracion/catalogo-productos.json
```

El catálogo enriquecido usa `catalog_schema_version=2`. Un archivo de receta conserva schema_version=1, status=VERIFIED, tenancy_ocid, user_group_id, routes y expected_portal. Cada ruta conserva region_key, las claves y etiquetas de la jerarquía exportada, los cuatro metadatos nuevos y, cuando no aplica, subcategory_key/subcategory_label nulos. verification contiene source, observed_at_utc, valid_until_utc y observed_portal.product/category iguales a expected_portal. Las fechas requieren zona horaria. La evidencia debe existir y referirse al contrato usado; esta estructura no otorga validez a una declaración sin evidencia.

Una receta anterior sin esos metadatos debe revisarse si el catálogo actual los publica. No completar su prueba histórica con valores actuales y marcarla verificada automáticamente. Si la clasificación aún no fue comprobada, conservar el borrador y obtener primero el contrato soportado de Oracle. Una consulta a ListIncidentResourceTypes con TECH devolvió INVALID_FORMAT en el entorno revisado; para esta jerarquía se utiliza el valor documentado TAXONOMY, sin inventar otros tipos para buscar issue types.

El modelo público admite issueTypeKey, pero el guard actual no lo considera verificado con la taxonomía revisada y bloquea una creación que lo incluya. Esta limitación se documenta para no simular cobertura de un nivel que aún no se ha comprobado.

Después de crear con una receta válida, el resultado diferencia receta comprobada de asignación del nuevo SR. Revisar Product/Category persistidos cuando exista una lectura soportada; si requiere portal, mantener la comprobación pendiente hasta verla. No crear duplicados, cambiar otra clasificación o cerrar un SR para ocultar una discrepancia. Este control reduce el riesgo conocido; no promete una cola interna inmutable ni elimina la necesidad de verificar cambios de comportamiento de Oracle.

La garantía verificable se centra en la clasificación solicitada y comprobada. La asignación interna y los traslados entre equipos los coordina Oracle; no se encontró un selector público de cola. Para cerrar el mapeo pendiente, solicitar el payload mínimo soportado, el significado de cada nivel y schema y la forma de comprobar el producto/categoría resultante. Luego validar ese contrato en una prueba autorizada antes de habilitar una receta.
