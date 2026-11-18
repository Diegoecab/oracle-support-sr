# El recorrido por consola y con la skill

## Primero: cómo se haría desde la consola

Estos son, a grandes rasgos, los pasos para abrir y mantener un SR desde OCI/My Oracle Support: autenticarse, seleccionar el producto, reunir el contexto del recurso, completar el formulario, enviar y volver al caso para consultar o agregar evidencia. Parte de la información puede venir precargada si se inicia desde la página del recurso.

### 01 · Completar el diálogo de creación

Elegir producto, tipo de problema, categoría/subcategoría e impacto; completar título y descripción. Las opciones dependen de la selección anterior. Product/Category del portal no se deben equiparar por nombre con campos arbitrarios del API.

### 02 · Reunir identificadores y contexto

Obtener recurso/OCID, tenancy, compartment, región y ventana del problema cuando correspondan. Revisar qué datos ya se precargaron y completar los faltantes.

### 03 · Recopilar la evidencia del servicio

Consultar la guía de diagnóstico, reunir request IDs, errores, logs y métricas relevantes y filtrar lo que se compartirá. Para OpenSearch, revisar SRDC1037. Como opción adicional, ADB-S puede aportar información mediante su MCP nativo o SQLcl MCP, si ya existe acceso autorizado.

### 04 · Crear y comprobar el SR

Enviar el formulario, conservar el número y revisar producto, categoría, severidad y evidencia persistidos. La selección esperada debe contrastarse con el caso creado.

### 05 · Consultar, actualizar y cerrar

Entrar al SR para leer respuestas, agregar diagnósticos y archivos y, cuando corresponda, solicitar el cierre. No se borra el historial.

## Después: cómo se hace con la skill

El usuario expresa el problema y su impacto en lenguaje natural. El perfil, recurso y SR ya seleccionados se reutilizan. La skill reúne el contexto accesible y pregunta únicamente por datos relevantes que falten; no requiere dictar IDs de taxonomía, JSON ni una secuencia de comandos de prueba.

### Crear

```text
Abrí un SR por el error de restore de este cluster de OpenSearch.
```

La skill identifica el recurso, recupera diagnósticos disponibles, propone severidad según el impacto conocido y consulta el catálogo. Usa una receta de clasificación verificada. Si esa receta no está habilitada, deja un borrador y explica qué validación falta; no crea el caso en una clasificación aproximada. El ejemplo OpenSearch/Backup and Restore permanece en ese estado pendiente.

### Consultar novedades

```text
Qué novedades hay en el SR?
```

Recupera la actividad y resume cambios, pedidos de Oracle y acciones pendientes. Distingue una respuesta de soporte de una nota del cliente o un mensaje automático.

### Actualizar o adjuntar evidencia

```text
Agregá este diagnóstico al SR y adjuntá el detalle si hace falta.
```

Prepara una nota legible con títulos y listas, publica lo autorizado y verifica la lectura posterior. Los archivos se revisan antes de cargarlos. La recolección mediante un MCP de ADB es una opción adicional y se configura aparte.

### Cerrar

```text
Cerralo; ya quedó resuelto.
```

Selecciona el SR del contexto, registra el motivo y consulta otra vez para confirmar CLOSED. La verificación es parte del trabajo del asistente y no requiere que el usuario pida cada GET interno.

## Qué verá la persona

Número y estado del SR, producto/categoría esperados y su nivel de comprobación, resumen de la acción, evidencia y próximos pasos. Los comandos y JSON quedan disponibles como detalle técnico. El ciclo de crear, consultar y cerrar se usa para validar el piloto; no es una instrucción que el usuario deba repetir completa en una situación real.
