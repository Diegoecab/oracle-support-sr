# Actualizaciones legibles en el SR

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

La skill muestra primero una ficha legible: enlace y número del SR, título exacto, tipo, severidad y estado, seguidos de la descripción completa en párrafos y listas. Conserva el idioma y las palabras originales; no traduce, resume ni corta el contenido. Los saltos de línea se ven como saltos, en lugar de secuencias escapadas dentro de un JSON. Si la descripción contiene JSON, lo indenta sin cambiar sus tokens, claves duplicadas o precisión numérica. No alcanza con mostrar el número del SR o un HTTP 200.

Los metadatos van en un detalle técnico expandible. Se ofrecen un archivo Markdown legible y el output completo en JSON como evidencia, sin volcarlo por defecto en pantalla ni devolver fragmentos incompletos. El formato legible es una presentación del mismo contenido; el raw conserva el origen exacto, incluido HTML. Las etiquetas HTML conocidas se muestran como texto estructurado inerte, sin ejecutar contenido. Un JSON del helper no equivale necesariamente al cuerpo REST original; REST_JSON identifica la lectura realizada con --raw-response.

Para las respuestas al usuario, el asistente pasa --output-format readable antes de la operación. El CLI del helper conserva JSON por defecto para no romper integraciones existentes; --output-format json lo selecciona expresamente. En ambos casos queda guardada la evidencia JSON completa.

La estructura interna separa execution de sr_fields y declara la fuente: DRAFT_PAYLOAD para el borrador, API_RESPONSE para la respuesta de una llamada, GET_RESPONSE para el caso recuperado o CACHED_RECEIPT para un recibo anterior. También se aplica a borradores y envíos bloqueados. Un borrador no tiene número de SR creado ni estado persistido; no se inventan ni se completan con otros datos. Después de escribir se muestra la lectura posterior, manteniendo los campos ausentes como ausentes. El cambio enviado y la clasificación solicitada se identifican por separado de lo realmente recuperado. El enlace al caso utiliza el parámetro SR; kmContentId corresponde a contenido de Knowledge.

Para formatear una evidencia existente sin consultar ni modificar OCI:

```text
python scripts/presentation.py --input resultado.json --output reporte.md
```

| Operación | Datos que incluye la respuesta |
| --- | --- |
| Creación | SR y enlace, título, descripción, tipo, severidad, estado, recurso/región pertinentes y clasificación solicitada frente a la realmente comprobada. |
| Actualización | Identidad y descripción literal del caso, texto exacto de la nota publicada o campos modificados, valores literales anteriores/nuevos cuando estén disponibles y estado posterior. Agregar correspondencia no equivale a modificar otros campos. |
| Adjunto | Identidad y descripción del caso, nombres de archivos, restricción de acceso y estado de procesamiento devuelto. |
| Cierre | Identidad y descripción del caso, motivo o nota de cierre y estado obtenido al verificar. Pedir el cierre no prueba que ya esté CLOSED; no elimina el historial. |

Después de cada escritura se consulta el SR para comprobar el resultado. La respuesta indica cuándo se verificó, qué quedó confirmado, qué sigue pendiente y la próxima acción. Si la lectura falla, distingue el envío aceptado de la verificación pendiente antes de reintentar. Para varias operaciones solicitadas, muestra el resultado de cada paso.

Los datos fundamentales ausentes no se inventan. La clasificación enviada no se presenta como clasificación persistida sin evidencia independiente. Request IDs, versiones y archivos de evidencia quedan como detalle técnico cuando aportan valor, sin volcar logs sensibles en la conversación.

Referencias: [agregar comentarios](https://docs.oracle.com/en-us/iaas/Content/GSG/support/update-incident-add-comment.htm) y [modelo UpdateActivityItemDetails](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/cims/models/oci.cims.models.UpdateActivityItemDetails.html).
