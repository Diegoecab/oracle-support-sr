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

## El mapeo que necesita la skill

Usar dos registros distintos:

- Catálogo disponible: obtenerlo de la API con el perfil del cliente. Guardar nombres, claves, jerarquía y fecha. Sirve para descubrir opciones, no para certificar el destino.
- Recetas verificadas del cliente: relacionar las claves exactas del payload con Product/Category realmente observados en un SR creado por ese contrato, tenancy/grupo, fuente de evidencia, fecha y vencimiento. Solo el estado VERIFIED habilita creación técnica. Las recetas no van embebidas con datos de una cuenta en el plugin distribuido.

La persona describe servicio/recurso, síntoma e impacto. El LLM obtiene los IDs desde el catálogo y busca una receta válida; no le pide que memorice claves. Los aliases humanos ayudan a buscar pero no habilitan un mapeo por similitud de texto. Si la selección es ambigua o el mapeo es desconocido, preparar el borrador y explicar el dato pendiente.

## Qué aplica la versión 0.3.0

El helper requiere --routing-file para ejecutar create de tipo TECH. Comprueba coincidencia de tenancy/grupo, región y claves del request, igualdad de producto/categoría esperados y observados en la evidencia, vigencia de esa evidencia y pertenencia de la ruta a la taxonomía consultada en vivo. Un cambio de etiquetas o de jerarquía detiene el alta. No hay receta técnica preaprobada incluida en el paquete.

El archivo es una configuración local mantenida por el cliente, no un nuevo campo del API. La skill lo resuelve desde el contexto/configuración autorizada y lo pasa al helper. El usuario no tiene que escribirlo en cada pedido. No marcar VERIFIED automáticamente, falsificar una comprobación, ignorar un vencimiento ni cambiar a raw API/CLI para sortear el control.

La inicialización de recetas requiere evidencia externa comprobable del mismo contrato o una validación controlada aparte, autorizada para ese propósito. El helper entregado no incluye una opción para omitir el control en producción. Una selección correcta en un SR creado por consola no prueba por sí sola el payload equivalente de API.

El catálogo puede exportarse en formato simple para la skill:

```text
python scripts/sr.py --profile MI_PERFIL --evidence-dir ./evidencia taxonomy --catalog-file ./configuracion/catalogo-productos.json
```

Un archivo de receta tiene schema_version=1, status=VERIFIED, tenancy_ocid, user_group_id, routes y expected_portal. Cada ruta conserva region_key, las claves y etiquetas de la jerarquía exportada y, cuando no aplica, subcategory_key/subcategory_label nulos. verification contiene source, observed_at_utc, valid_until_utc y observed_portal.product/category iguales a expected_portal. Las fechas requieren zona horaria. La evidencia debe existir y referirse al contrato usado; esta estructura no otorga validez a una declaración sin evidencia.

El modelo público admite issueTypeKey, pero el guard actual no lo considera verificado con la taxonomía revisada y bloquea una creación que lo incluya. Esta limitación se documenta para no simular cobertura de un nivel que aún no se ha comprobado.

Después de crear con una receta válida, el resultado diferencia receta comprobada de asignación del nuevo SR. Revisar Product/Category persistidos cuando exista una lectura soportada; si requiere portal, mantener la comprobación pendiente hasta verla. No crear duplicados, cambiar otra clasificación o cerrar un SR para ocultar una discrepancia. Este control reduce el riesgo conocido; no promete una cola interna inmutable ni elimina la necesidad de verificar cambios de comportamiento de Oracle.
