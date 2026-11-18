# Oracle Support SR para Codex y Claude Code

Plugin de piloto con código público. Un único código de skill y helper Python, con manifiestos para ambos agentes. Creación, consulta, notas con formato, adjuntos y cierre de SRs de OCI mediante el SDK/CLI oficial. Es una herramienta propia, sin aval oficial de Oracle. No incluye credenciales, datos de clientes ni un servicio de monitoreo desplegado.

## Instalar

Requisitos previos: Git y acceso HTTPS a GitHub, el cliente CLI elegido en PATH, Python 3.11 y SDK `oci>=2.177.0,<3` en el Python que usará el helper. El repositorio se puede descargar sin invitación. El plugin se instala con los comandos nativos de cada cliente.

Si el marketplace ya está registrado, instalar es una orden por agente.

Codex:

```text
codex plugin add oracle-support-sr@diego-oci-support
```

Claude Code:

```text
claude plugin install oracle-support-sr@diego-oci-support --scope user
```

La primera vez se registra el catálogo, una sola vez en cada cliente. Para Codex:

```text
codex plugin marketplace add Diegoecab/oracle-support-sr
```

Para Claude:

```text
claude plugin marketplace add Diegoecab/oracle-support-sr
```

En Claude Code 2.1.292 o posterior, el comando de shell también permite registrar e instalar juntos: `claude plugin install oracle-support-sr --marketplace Diegoecab/oracle-support-sr --scope user`. En una sesión, la documentación ofrece `/plugin install oracle-support-sr --marketplace Diegoecab/oracle-support-sr` desde 2.1.275. Estas variantes requieren esas versiones; los comandos separados de arriba fueron los comprobados en el piloto. [Documentación oficial de instalación](https://code.claude.com/docs/en/discover-plugins).

Instalar el plugin no configura la identidad OCI ni otorga permisos. El SDK puede instalarse dentro del entorno Python aprobado con `python -m pip install "oci>=2.177.0,<3"`. No hace falta descargar el repositorio ni ejecutar un instalador Python para registrar el plugin.

Abrí una sesión nueva después de instalar. En Codex, invocá la skill desde el plugin instalado o pedí usar oracle-support-sr. En Claude, el nombre de la skill instalada como plugin es `/oracle-support-sr:oracle-support-sr`; una copia standalone utiliza `/oracle-support-sr`. No hace falta un MCP para este piloto. El SDK debe estar en el Python que ejecute el helper: si usás un entorno virtual, iniciá el CLI desde ese entorno o indicá al asistente la ruta del intérprete aprobado.

## Primera prueba, sin escrituras

```text
Usá oracle-support-sr con el perfil MI_PERFIL para validar acceso y listar
mis SRs visibles. Mostrá tenancy, región, estado y evidencia. No crees un SR todavía.
```

Para operar, usá pedidos naturales: "Abrí un SR por este error", "Qué novedades hay?", "Agregá este diagnóstico" o "Cerralo; ya quedó resuelto". La skill reutiliza perfil y recurso del contexto y pregunta por lo relevante que falte. Crear un caso requiere un mapeo de producto/categoría verificado; si falta, conserva el borrador. No se necesita dictar IDs opacos ni una secuencia completa de comandos.

## Modos y aprobación

MANUAL es el modo predeterminado: las consultas y los borradores pueden avanzar, pero antes de cada escritura muestra la acción, cuenta/SR, texto y adjuntos y espera el OK al contenido concreto. Si cambian, se revisa la nueva versión. Una aprobación de ese mismo borrador se reutiliza.

AUTO se elige expresamente para un trabajo definido, por ejemplo: "Usá AUTO para responder este SR con estas comprobaciones y adjuntar el diagnóstico". Ejecuta las acciones autorizadas y vuelve a MANUAL al terminar. Cerrar un SR y crear con una selección de primer uso siempre requieren aprobación manual del borrador exacto, incluso en AUTO. Cada sesión nueva comienza en MANUAL. Estos modos no modifican los permisos propios de Codex/Claude ni conceden operaciones sobre infraestructura.

En ambos modos, los datos fundamentales faltantes se preguntan. No se inventan identificadores, resultados, impacto de negocio, entorno, clasificación ni compromisos de atención. Los detalles de presentación pueden resolverse con una opción razonable. [Detalle de modos e información requerida](docs/modos.md).

## Alcance validado y tiempos

El escenario considera un solo SR con cinco interacciones en total, incluyendo apertura y seguimientos: leer novedades, reunir logs o información adicional, responder y verificar. Con una media supuesta de 30 minutos por interacción en consola y 5 con la skill, el total es de 2 h 30 min frente a 25 min: 2 h 5 min de ahorro estimado, un 83 %. El tiempo de CLI/SDK manual se estima en 15 minutos por interacción, 1 h 15 min para ese mismo caso.

Estas medias todavía no se midieron en un SR completo con cinco interacciones. La referencia de 5 minutos proviene de un tramo de apertura de 3 min 43 s redondeado; aplicarla al seguimiento es un supuesto. Se cuenta tiempo activo, sin esperas de Oracle, configuración inicial ni investigación compleja. Se asumen perfil, clasificación y fuentes accesibles ya configurados. La consola puede conservar sesión y precargar información.

El piloto previo al guard de clasificación de 0.3.0 ejecutó seis operaciones automáticas en 32,062 s sobre un SR de consulta. Es tiempo de ejecución de comandos y no mide las cinco interacciones del escenario.

Para un producto nuevo no hace falta un SR previo: desde 0.7.0 se puede preparar una selección CATALOG_ONLY desde el catálogo vigente, mostrar el destino esperado y pedir aprobación manual, incluso en AUTO. Una ruta VERIFIED reutiliza evidencia ya comprobada; ambas se contrastan con la taxonomía en vivo. Una discrepancia conocida sigue bloqueada para incidentes reales, como en el ejemplo OpenSearch/Backup and Restore. Los schemas se conservan y comparan, pero no se convierten en selectores del API sin un contrato comprobado. La API sí modela respuestas con categoría/subcategoría; en los SRs revisados GetIncident no pobló esos campos y ListIncidents devolvió incidentResourceType vacío. Esa es una observación de esas respuestas, no una afirmación de imposibilidad general. La clasificación persistida y la asignación interna de ingenieros se comprueban por separado. No se distribuyen rutas de clientes preaprobadas.

## Documentación y requisitos

- [Manual del cliente, HTML sin datos del piloto](docs/manual-cliente.html)
- [Recorrido por consola y con pedidos naturales](docs/recorrido.md)
- [Modos MANUAL y AUTO](docs/modos.md)
- [Producto, subproducto y registro de mapeos verificados](docs/clasificacion.md)
- [ADB: MCP nativo y SQLcl como fuentes opcionales de evidencia](docs/adb-mcp.md)
- [Acceso mínimo: SRs y evidencia](docs/requisitos.md)
- [Diseño Datadog -> OCI Functions -> SR -> pager](docs/datadog.md)
- [Métricas de OCI OpenSearch: Prometheus -> Datadog](docs/opensearch-datadog.md)
- [Formato de nuestros updates](docs/formato-updates.md)
- [Fuentes oficiales y blogs](docs/fuentes.md)

Gestionar tickets requiere permisos IAM de tickets más los privilegios del grupo de soporte. Obtener OCIDs, logs, métricas y costos requiere permisos de lectura adicionales, limitados a cada fuente. No se requiere una VM dedicada. La integración Datadog y el monitoreo automático son una propuesta, no componentes desplegados por este plugin.

## Operación y mantenimiento

El helper conserva respuestas y recibos de escritura en el evidence-dir elegido. Las escrituras necesitan `--execute` y coincidencia de tenancy. MANUAL requiere además el `--approval-digest` del borrador aprobado; el asistente lo pasa solo después del OK real. El digest detecta cambios y no demuestra por sí solo consentimiento humano. AUTO se pasa explícitamente como `--mode AUTO`. No reintenta automáticamente escrituras inciertas: conciliar antes de repetir. Los recibos locales no sustituyen un registro compartido en Functions. Cerrar no elimina el SR; no se identificó una operación pública de borrado.

Las notas nuevas preservan estructura mediante HTML escapado; se verificó su renderizado en My Oracle Support. El API no reescribe comentarios anteriores. Las claves y la configuración OCI permanecen fuera del repositorio. SDK/CLI y comportamiento del portal pueden evolucionar; revisar referencias y validar en el entorno del cliente.
