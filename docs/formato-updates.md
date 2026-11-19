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

La skill muestra un bloque JSON con los campos literales: número del SR, título y descripción completa, además de los datos devueltos del caso. Conserva el idioma, texto, nombres de campos, enums y saltos de línea originales; no los traduce ni resume. Una explicación breve puede acompañar al bloque, sin reemplazarlo. No alcanza con mostrar el número del SR o un HTTP 200.

La estructura separa execution de sr_fields y declara la fuente: DRAFT_PAYLOAD para el borrador, API_RESPONSE para la respuesta de una llamada, GET_RESPONSE para el caso recuperado o CACHED_RECEIPT para un recibo anterior. También se aplica a borradores y envíos bloqueados. Un borrador no tiene número de SR creado ni estado persistido; no se inventan ni se completan con otros datos. Después de escribir se muestra la lectura posterior, manteniendo los campos ausentes como ausentes. El cambio enviado y la clasificación solicitada se identifican por separado de lo realmente recuperado.

| Operación | Datos que incluye la respuesta |
| --- | --- |
| Creación | SR y enlace, título, descripción, tipo, severidad, estado, recurso/región pertinentes y clasificación solicitada frente a la realmente comprobada. |
| Actualización | Identidad y descripción literal del caso, texto exacto de la nota publicada o campos modificados, valores literales anteriores/nuevos cuando estén disponibles y estado posterior. Agregar correspondencia no equivale a modificar otros campos. |
| Adjunto | Identidad y descripción del caso, nombres de archivos, restricción de acceso y estado de procesamiento devuelto. |
| Cierre | Identidad y descripción del caso, motivo o nota de cierre y estado obtenido al verificar. Pedir el cierre no prueba que ya esté CLOSED; no elimina el historial. |

Después de cada escritura se consulta el SR para comprobar el resultado. La respuesta indica cuándo se verificó, qué quedó confirmado, qué sigue pendiente y la próxima acción. Si la lectura falla, distingue el envío aceptado de la verificación pendiente antes de reintentar. Para varias operaciones solicitadas, muestra el resultado de cada paso.

Los datos fundamentales ausentes no se inventan. La clasificación enviada no se presenta como clasificación persistida sin evidencia independiente. Request IDs, versiones y archivos de evidencia quedan como detalle técnico cuando aportan valor, sin volcar logs sensibles en la conversación.

Referencias: [agregar comentarios](https://docs.oracle.com/en-us/iaas/Content/GSG/support/update-incident-add-comment.htm) y [modelo UpdateActivityItemDetails](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/cims/models/oci.cims.models.UpdateActivityItemDetails.html).
