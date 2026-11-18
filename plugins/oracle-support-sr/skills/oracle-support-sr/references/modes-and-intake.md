# Modos de ejecución y datos fundamentales

## MANUAL, predeterminado

La skill puede consultar, recolectar evidencia mediante lecturas autorizadas y preparar un borrador. Para crear un SR, publicar una nota, subir un adjunto o cerrar, muestra primero la acción concreta, la cuenta/SR, el contenido y los archivos; luego espera el OK del usuario. La aprobación de un borrador exacto no se vuelve a pedir. Una aprobación puede abarcar varias acciones si todas se mostraron con su contenido y destino.

Ejemplo: “Prepará la respuesta y mostrámela antes de enviarla”. El usuario revisa el texto y responde “OK, publicá esa nota y ese adjunto”. Cambiar los datos importantes después de ese OK requiere volver a revisarlos. Si una novedad cambia el sentido de una respuesta preparada, detener el envío y actualizar el borrador.

El helper usa `--mode MANUAL` por defecto. Sin `--execute`, devuelve el borrador y su `approval_digest`. La ejecución requiere `--approval-digest` con ese valor exacto. El digest vincula operación, SR, selectores de cuenta/región, payload y, cuando corresponde, bytes del adjunto y receta de clasificación. Detecta cambios del borrador; por sí solo no demuestra que una persona aprobó. El asistente debe obtener el OK real antes de pasarlo. La identidad efectiva y la tenancy se verifican con los controles existentes.

## AUTO, elegido expresamente

Ejemplo: “Usá AUTO para responder este SR con los resultados de estas lecturas y adjuntar el diagnóstico”. La skill puede publicar las acciones autorizadas sin pedir confirmación por cada envío. Mantiene el alcance elegido y vuelve a MANUAL al terminar ese trabajo. AUTO no habilita por sí solo cerrar casos, publicar otros archivos, hacer cambios de infraestructura ni operar sobre cuentas diferentes.

En el helper se selecciona antes de la operación: `--mode AUTO`. Las escrituras siguen requiriendo `--execute`, tenancy coincidente, clasificación verificada cuando corresponde y conciliación antes de reintentar un resultado incierto. AUTO sin `--execute` sigue generando solamente un borrador. Los permisos de Codex/Claude y del sistema operativo se aplican independientemente; este modo no modifica esa configuración.

## Qué se pregunta y qué se puede asumir

| Dato | Tratamiento si falta o es contradictorio |
| --- | --- |
| Perfil/tenancy, SR destino, recurso afectado y región aplicable | Resolver mediante contexto o lectura autorizada. Si hay ambigüedad, preguntar antes de escribir. |
| Producto, categoría/subcategoría y claves de enrutamiento | Consultar catálogo y receta verificada. Una coincidencia de nombre no prueba la cola. Mantener borrador si falta validación. |
| Producción o prueba, alcance del impacto, indisponibilidad, pérdida de datos, urgencia y compromisos de atención | Preguntar lo necesario para la acción. No inferirlos del nombre del recurso, una alerta o la severidad deseada. |
| Resultado de una prueba, logs, OCIDs, estado de un recurso, identidad de navegador versus API | Informar únicamente lo observado o confirmado, con fuente y fecha. No inventar resultados ni equiparar identidades. |
| Intención de cierre, cambios de severidad o destinatarios | Obtener una instrucción explícita para esa acción. AUTO genérico no la concede. |
| Títulos de secciones, orden de los hallazgos, nombre descriptivo del archivo y formato | Se puede elegir una opción razonable sin interrumpir el flujo. Explicitar el supuesto si ayuda a entender el resultado. |

Preguntar solamente por los datos fundamentales para la acción actual. Una nota de diagnóstico puede informar una comparación de consola todavía pendiente sin inventar su resultado; la falta de ese dato no obliga a retener los hechos independientes ya comprobados. Si el dato desconocido determina cuenta, destino, impacto o contenido de la escritura, detener esa escritura y preguntar. En ambos modos, una respuesta desconocida se conserva como desconocida.

## Uso interno

```text
python scripts/sr.py --profile MI_PERFIL --evidence-dir ./evidencia comment --key SR_KEY --text-file respuesta.txt --expected-tenancy TENANCY_OCID
```

Tras el OK real al borrador mostrado:

```text
python scripts/sr.py --profile MI_PERFIL --evidence-dir ./evidencia comment --key SR_KEY --text-file respuesta.txt --expected-tenancy TENANCY_OCID --approval-digest DIGEST_DEL_BORRADOR_APROBADO --execute
```

Para un flujo AUTO autorizado:

```text
python scripts/sr.py --profile MI_PERFIL --mode AUTO --evidence-dir ./evidencia comment --key SR_KEY --text-file respuesta.txt --expected-tenancy TENANCY_OCID --execute
```

El usuario opera con lenguaje natural; el asistente administra los parámetros internos. Nunca cambiar al API/CLI directo para omitir una aprobación o validación bloqueada.
