# ADB: evidencia adicional mediante MCP

Como complemento, una ADB Serverless puede aportar diagnósticos a través de su MCP nativo administrado. El asistente usa las herramientas autorizadas que la base expone y prepara los resultados relevantes para agregarlos al SR. Su configuración es un tema aparte y no es requisito para gestionar SRs por API.

| Alternativa | Uso para el SR | Referencia oficial |
| --- | --- | --- |
| MCP nativo de ADB Serverless | Invocar herramientas Select AI Agent ya habilitadas para la identidad del cliente, guardar la evidencia y cargarla como nota/adjunto si corresponde. | [Use MCP Server](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/use-mcp-server.html), [prerrequisitos](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/prerequisites.html). |
| SQLcl MCP | Usar una conexión guardada y consultas de diagnóstico aprobadas, cuando esa alternativa ya esté configurada. | [SQLcl MCP oficial](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/25.4/sqcug/using-oracle-sqlcl-mcp-server.html), [blog oficial de Oracle](https://blogs.oracle.com/ai-and-datascience/ai-driven-sql-made-simple-with-oracle-sqlcl-mcp-server). |

El MCP nativo tiene un endpoint por base y expone las herramientas permitidas; no implica acceso SQL irrestricto. SQLcl es una alternativa, no un requisito del MCP nativo. En ambos casos se necesita conectividad e identidad con acceso a la información requerida. Los permisos para manejar tickets no conceden permisos sobre datos de la base.

La skill de SRs puede reutilizar esa evidencia ya obtenida, revisarla y adjuntarla mediante Support Management. No habilita MCPs ni cambia grants para abrir un ticket. Si la base no es accesible, se documenta esa limitación y se utiliza la evidencia disponible del control plane y de los logs.
