# ADB: evidencia adicional mediante MCP

Como complemento, una ADB Serverless puede aportar diagnósticos a través de su MCP nativo administrado. El asistente usa las herramientas autorizadas que la base expone y prepara los resultados relevantes para agregarlos al SR. Su configuración es un tema aparte y no es requisito para gestionar SRs por API.

| Alternativa | Uso para el SR | Referencia oficial |
| --- | --- | --- |
| MCP nativo de ADB Serverless | Invocar herramientas Select AI Agent ya habilitadas para la identidad del cliente, guardar la evidencia y cargarla como nota/adjunto si corresponde. | [Use MCP Server](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/use-mcp-server.html), [prerrequisitos](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/prerequisites.html). |
| SQLcl MCP | Usar una conexión guardada y consultas de diagnóstico aprobadas, cuando esa alternativa ya esté configurada. | [SQLcl MCP oficial](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/25.4/sqcug/using-oracle-sqlcl-mcp-server.html), [blog oficial de Oracle](https://blogs.oracle.com/ai-and-datascience/ai-driven-sql-made-simple-with-oracle-sqlcl-mcp-server). |

El MCP nativo tiene un endpoint por base y expone las herramientas permitidas; no implica acceso SQL irrestricto. SQLcl es una alternativa, no un requisito del MCP nativo. En ambos casos se necesita conectividad e identidad con acceso a la información requerida. Los permisos para manejar tickets no conceden permisos sobre datos de la base.

La skill de SRs puede reutilizar esa evidencia ya obtenida, revisarla y adjuntarla mediante Support Management. No habilita MCPs ni cambia grants para abrir un ticket. Si la base no es accesible, se documenta esa limitación y se utiliza la evidencia disponible del control plane y de los logs.

## Logs y reportes AWR: alcance verificado

Oracle documenta la exposición de herramientas Select AI Agent a través del MCP nativo. Una herramienta SQL/PLSQL autorizada puede recuperar la información a la que tenga acceso su identidad; el endpoint MCP por sí solo no convierte todos los diagnósticos en herramientas listas para usar.

| Evidencia | Qué se puede afirmar |
| --- | --- |
| Datos de errores del cliente | ADB Serverless permite consultar V$CLIENT_ERRORS. Esa lectura puede exponerse mediante una herramienta de diagnóstico configurada y autorizada. No implica acceso a todos los logs internos del servicio. |
| Reportes AWR | La generación y descarga desde Performance Hub están documentadas. Obtener el archivo mediante MCP requiere preparar una herramienta específica y validar el mecanismo soportado, permisos, intervalo/snapshots y manejo del resultado. Es una integración propuesta: no se encontró una herramienta AWR predefinida en la documentación del MCP nativo consultada ni se probó ese flujo en el piloto. |

Para ADB Serverless, Oracle indica que V$DIAG_ALERT_EXT no está disponible para datos del alert log y recomienda V$CLIENT_ERRORS. No trasladar instrucciones de ADB Dedicated a Serverless sin comprobar su compatibilidad.

Referencias oficiales:

- [MCP nativo y herramientas personalizadas](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/use-mcp-server.html).
- [Query for Client Errors](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/autonomous-query-alert-log.html).
- [Cambio documentado sobre V$DIAG_ALERT_EXT](https://docs.oracle.com/en-us/iaas/releasenotes/autonomous-database-serverless/2025-07-query-for-client-errors.htm).
- [AWR en Performance Hub](https://docs.oracle.com/en-us/iaas/performance-hub/doc/download-awr-report.html).
- [Blog oficial de observabilidad de ADB Serverless](https://blogs.oracle.com/autonomous-ai-database/autonomous-database-serverless-observability-for-adbs).
