# El recorrido por consola y con la skill

## Pasos por consola

Estos son, a grandes rasgos, los pasos para abrir y mantener un SR desde OCI/My Oracle Support: autenticarse, seleccionar el producto, reunir el contexto del recurso, completar el formulario, enviar y volver al caso para consultar o agregar evidencia. Parte de la información puede venir precargada si se inicia desde la página del recurso.

<details>
<summary>01 · Completar el diálogo de creación</summary>

Elegir producto, tipo de problema, categoría/subcategoría e impacto; completar título y descripción. Las opciones dependen de la selección anterior. Product/Category del portal no se deben equiparar por nombre con campos arbitrarios del API.

</details>

<details>
<summary>02 · Reunir identificadores y contexto</summary>

Obtener recurso/OCID, tenancy, compartment, región y ventana del problema cuando correspondan. Revisar qué datos ya se precargaron y completar los faltantes.

</details>

<details>
<summary>03 · Recopilar la evidencia del servicio</summary>

Consultar la guía de diagnóstico, reunir request IDs, errores, logs y métricas relevantes y filtrar lo que se compartirá. Para OpenSearch, revisar SRDC1037. Como opción adicional, ADB-S puede aportar información mediante su MCP nativo o SQLcl MCP, si ya existe acceso autorizado.

</details>

<details>
<summary>04 · Crear y comprobar el SR</summary>

Enviar el formulario, conservar el número y revisar producto, categoría, severidad y evidencia persistidos. La selección esperada debe contrastarse con el caso creado.

</details>

<details>
<summary>05 · Consultar, actualizar y cerrar</summary>

Entrar al SR para leer respuestas, agregar diagnósticos y archivos y, cuando corresponda, solicitar el cierre. No se borra el historial.

</details>

## Pasos con la skill

El usuario expresa el problema y su impacto en lenguaje natural. El perfil, recurso y SR ya seleccionados se reutilizan. La skill reúne el contexto accesible y pregunta únicamente por datos relevantes que falten; no requiere dictar IDs de taxonomía, JSON ni una secuencia de comandos de prueba.

El modo predeterminado es MANUAL: prepara la escritura, muestra el contenido y espera el OK antes de enviarlo. AUTO se elige expresamente para un trabajo definido. En ambos modos, si falta un dato fundamental, lo pregunta; no lo inventa. Ver [modos y aprobación](modos.md).

### Crear

```text
Abrí un SR por el error de restore de este cluster de OpenSearch.
```

La skill identifica el recurso, recupera diagnósticos disponibles, propone severidad según el impacto conocido y consulta el catálogo. Para un producto nuevo puede usar una selección CATALOG_ONLY: muestra el producto/categoría elegidos desde el catálogo actual y respeta el modo MANUAL o AUTO expresamente elegido. No exige otro OK solo por primer uso, un SR previo ni una prueba ficticia. La clasificación persistida se comprueba después, cuando la respuesta del servicio o el portal la expone. Si falta un dato importante o hay ambigüedad, pregunta. Una ruta que ya mostró una clasificación incorrecta permanece bloqueada para incidentes reales hasta resolver esa discrepancia; ese es el estado del ejemplo OpenSearch/Backup and Restore.

Para validar una ruta nueva, el usuario puede solicitar expresamente un SR de prueba LOW. La skill usa un flujo separado con un plan de un único caso, muestra el alta y el cierre previsto y espera el OK en MANUAL. Comprueba las claves contra el catálogo actual, pero mantiene la clasificación persistida como pendiente hasta contar con evidencia. Si se elige una prueba solo por API y GetIncident no expone Product/Category, informa esa limitación. La prueba no habilita automáticamente el mapeo para incidentes reales. Ver [clasificación y prueba controlada](clasificacion.md).

### Consultar novedades

```text
Qué novedades hay en el SR?
```

Recupera la actividad y resume cambios, pedidos de Oracle y acciones pendientes. Distingue una respuesta de soporte de una nota del cliente o un mensaje automático.

### Actualizar o adjuntar evidencia

```text
Agregá este diagnóstico al SR y adjuntá el detalle si hace falta.
```

Prepara una nota legible con títulos y listas, muestra los adjuntos y espera el OK en MANUAL. Después publica lo aprobado y verifica la lectura posterior. En AUTO ejecuta lo autorizado sin esa confirmación por envío. La recolección mediante un MCP de ADB es una opción adicional y se configura aparte.

### Cerrar

```text
Cerralo; ya quedó resuelto.
```

Selecciona el SR del contexto y prepara el motivo de cierre. Siempre muestra ese borrador y espera la aprobación manual, incluso en AUTO; un OK exacto ya dado no se vuelve a pedir. Después solicita el cierre y consulta otra vez para confirmar CLOSED. La verificación es parte del trabajo del asistente y no requiere que el usuario pida cada GET interno.

## Qué verá la persona

Número y estado del SR, producto/categoría esperados y su nivel de comprobación, resumen de la acción, evidencia y próximos pasos. Los comandos y JSON quedan disponibles como detalle técnico. El ciclo de crear, consultar y cerrar se usa para validar el piloto; no es una instrucción que el usuario deba repetir completa en una situación real.
