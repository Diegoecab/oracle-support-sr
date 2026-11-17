# Oracle Support SR para Codex y Claude Code

Plugin privado de piloto. Un único código de skill y helper Python, con manifiestos para ambos agentes. Creación, consulta, notas con formato, adjuntos y cierre de SRs de OCI mediante el SDK/CLI oficial. Es una herramienta propia, sin aval oficial de Oracle. No incluye credenciales, datos de clientes ni un servicio de monitoreo desplegado.

## Instalar

Requisitos previos: acceso de lectura a este repositorio privado, Git autenticado, el cliente CLI elegido en PATH, Python 3.11 y SDK `oci>=2.177.0,<3` en el Python que usará el helper. Para instalar dependencias dentro del entorno Python aprobado:

```text
python -m pip install -r plugins/oracle-support-sr/skills/oracle-support-sr/requirements.txt
```

Después de descargar/descomprimir el repositorio, la instalación en ambos agentes se ejecuta con una línea:

```text
python install.py --agent both
```

También acepta `--agent codex`, `--agent claude` y `--dry-run`. Usa los instaladores nativos y no modifica credenciales ni permisos OCI. La primera autenticación, la asignación de privilegios y la instalación de dependencias son pasos previos; no se resuelven con una única orden de plugin.

Alternativa nativa Codex:

```text
codex plugin marketplace add Diegoecab/oracle-support-sr
codex plugin add oracle-support-sr@diego-oci-support
```

Alternativa nativa Claude Code:

```text
claude plugin marketplace add Diegoecab/oracle-support-sr
claude plugin install oracle-support-sr@diego-oci-support --scope user
```

Abrí una sesión nueva después de instalar. En Codex, invocá la skill desde el plugin instalado o pedí usar oracle-support-sr. En Claude, el nombre de la skill instalada como plugin es `/oracle-support-sr:oracle-support-sr`; una copia standalone utiliza `/oracle-support-sr`. No hace falta un MCP para este piloto. El SDK debe estar en el Python que ejecute el helper: si usás un entorno virtual, iniciá el CLI desde ese entorno o indicá al asistente la ruta del intérprete aprobado.

## Primera prueba, sin escrituras

```text
Usá oracle-support-sr con el perfil MI_PERFIL para validar acceso y listar
mis SRs visibles. Mostrá tenancy, región, estado y evidencia. No crees un SR todavía.
```

Para el ciclo completo, elegí un caso real de consulta o una validación controlada que no duplique un incidente existente. Indicá producto, síntoma, recurso cuando corresponda e impacto. Autorizá explícitamente la creación y el cierre de ese SR de prueba; verificá producto/categoría en el portal y la consulta posterior. No cierres un incidente de producción para probar el plugin.

## Alcance validado y tiempos

El piloto ejecutó creación, consulta, nota, lectura de novedades, cierre y GET final en 32,062 s de ejecución automática sobre un SR de consulta. No incluye investigación ni todo el razonamiento del asistente. La referencia comercial de 5 minutos frente a 30 en consola expresa hasta un 83 % de ahorro estimado, incluyendo preparación y primera actualización; todavía no es un benchmark completo comparable. El formulario de consola también puede precargar información: medir ese flujo real antes de validar el ahorro del cliente.

Se confirmó el producto OpenSearch, pero una subcategoría solicitada no coincidió con el portal. El mapeo fino sigue pendiente de Oracle; es un requisito a resolver antes de prometer enrutamiento automático completo o habilitar creación desatendida. Los casos de consulta no prueban la recolección automática de logs de un incidente real.

## Documentación y requisitos

- [Manual del cliente, HTML sin datos del piloto](docs/manual-cliente.html)
- [Acceso mínimo: SRs y evidencia](docs/requisitos.md)
- [Diseño Datadog -> OCI Functions -> SR -> pager](docs/datadog.md)
- [Formato de nuestros updates](docs/formato-updates.md)
- [Fuentes oficiales y blogs](docs/fuentes.md)

Gestionar tickets requiere permisos IAM de tickets más los privilegios del grupo de soporte. Obtener OCIDs, logs, métricas y costos requiere permisos de lectura adicionales, limitados a cada fuente. No se requiere una VM dedicada. La integración Datadog y el monitoreo automático son una propuesta, no componentes desplegados por este plugin.

## Operación y mantenimiento

El helper conserva borradores, respuestas y recibos de escritura en el evidence-dir elegido. Las escrituras necesitan `--execute` y coincidencia de tenancy. No reintenta automáticamente escrituras inciertas: conciliar antes de repetir. Los recibos locales no sustituyen un registro compartido en Functions. Cerrar no elimina el SR; no se identificó una operación pública de borrado.

Las notas nuevas preservan estructura mediante HTML escapado; se verificó su renderizado en My Oracle Support. El API no reescribe comentarios anteriores. Las claves y la configuración OCI permanecen fuera del repositorio. SDK/CLI y comportamiento del portal pueden evolucionar; revisar referencias y validar en el entorno del cliente.
