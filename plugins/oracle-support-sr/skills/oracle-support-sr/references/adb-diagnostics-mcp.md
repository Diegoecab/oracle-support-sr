# ADB: MCP nativo y SQLcl como fuentes opcionales de diagnóstico

Este es un complemento de recolección de evidencia, separado de la gestión del SR. Además de las lecturas del control plane, ADB Serverless ofrece un MCP nativo administrado por base. SQLcl MCP es otra alternativa; no es la única.

## MCP nativo de Autonomous Database Serverless

El servidor MCP de ADB-S expone herramientas Select AI Agent autorizadas mediante un endpoint remoto por base. El cliente descubre e invoca las herramientas disponibles para su identidad; no asumir que cualquier consulta SQL está expuesta. Para un SR puede ejecutar una herramienta de diagnóstico ya aprobada, guardar el resultado filtrado con fuente/hora y agregarlo como nota o adjunto mediante Support Management.

La habilitación y la preparación de herramientas se configuran aparte; instalar esta skill no las habilita. Confirmar las versiones soportadas, identidad/token, permisos de las herramientas y conectividad del endpoint público/privado según las políticas del cliente. No habilitar servicios, crear herramientas o cambiar grants como efecto implícito de abrir un SR.

Documentación oficial del MCP nativo: [Use MCP Server](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/use-mcp-server.html), [prerrequisitos](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/prerequisites.html) y [herramientas integradas de ADB](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/autonomous-tools.html). La [nota del 10/11/2026](https://docs.oracle.com/en-us/iaas/releasenotes/autonomous-database-serverless/2026-11-support-mcp-server.htm) documenta la administración de MCP/A2A desde Tools; esa fecha no se presenta como el primer lanzamiento de MCP.

## Alternativa: SQLcl MCP

Si el cliente ya utiliza SQLcl MCP y una conexión SQL aprobada, puede recuperar diagnósticos con consultas autorizadas. No requiere desplegar el MCP nativo para usar esta alternativa.

Referencias oficiales:

- [Using the Oracle SQLcl MCP Server, SQLcl 25.4](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/25.4/sqcug/using-oracle-sqlcl-mcp-server.html).
- [Herramientas del SQLcl MCP Server](https://docs.oracle.com/en/database/oracle/sql-developer-vscode/25.2/sqdnx/sqlcl-mcp-server-tools.html): listar conexiones guardadas, conectar, ejecutar SQL y desconectar.
- [Preparación del entorno](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/25.4/sqcug/preparing-your-environment.html).
- [Restrict levels de SQLcl MCP](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/25.4/sqcug/configuring-restrict-levels-sqlcl-mcp-server.html).
- [Conexión de herramientas Oracle a ADB por TLS o mTLS](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/connect-tools.html).
- [Blog oficial: AI Driven SQL Made Simple with Oracle SQLcl MCP Server](https://blogs.oracle.com/ai-and-datascience/ai-driven-sql-made-simple-with-oracle-sqlcl-mcp-server), 03/03/2026.

## Recorrido para un SR

1. Identificar la conexión guardada correspondiente a la base afectada. Si hay varias candidatas y el contexto no resuelve cuál es, preguntar cuál usar. No conectarse por aproximación a otra base.
2. Conectar con el usuario SQL aprobado y reunir solo diagnósticos pertinentes: contexto de base/sesión, errores, estado de objetos del esquema o vistas de diagnóstico expresamente autorizadas. Elegir las consultas según el síntoma y la guía de recolección del servicio.
3. Guardar los resultados en un archivo local filtrado, con consulta, UTC, base/contenedor, resultado o error y fuente MCP. Un intento de conexión fallido también puede documentarse como evidencia; no habilita consultas que no se ejecutaron.
4. Preparar la nota y, si hace falta, adjuntar ese archivo con PutAttachment mediante la skill de SRs, dentro de la acción autorizada. Volver a consultar el SR para verificar la nota/archivo. No subir wallet, passwords, signing keys, tokens ni resultados de negocio ajenos al problema.

Pedido natural de ejemplo:

```text
Usá la conexión guardada de esta ADB para reunir el diagnóstico del error
y agregá al SR la información relevante. Adjuntá el detalle si hace falta.
```

Ambas alternativas obtienen evidencia de la base. La creación, actualización y carga de archivos del SR siguen usando Support Management CLI/SDK. No confundir estos MCPs de base con un MCP de soporte ni asumir que vienen configurados por instalar este plugin.

## Acceso mínimo y alcance

Se requiere SQLcl con soporte MCP, su entorno de ejecución compatible, un cliente MCP configurado, conectividad al endpoint ADB y una conexión SQL guardada con autenticación TLS/mTLS apropiada. El usuario de base necesita CREATE SESSION y únicamente los SELECT sobre objetos/vistas aprobados que requiera ese diagnóstico. Los permisos IAM inspect autonomous-databases y manage tickets no conceden permisos SQL.

Oracle recomienda mínimo privilegio, datos saneados o una réplica/subconjunto de lectura y auditoría de la actividad del LLM. Mantener el restrict level más limitado compatible con la tarea; en SQLcl 25.4 el default documentado es 4. Este nivel restringe comandos del cliente y no sustituye los grants de base ni garantiza por sí solo SQL de lectura. La configuración de auditoría necesaria se prepara con el DBA; no conceder CREATE TABLE ni otros privilegios amplios al asistente para resolverla automáticamente.

Este flujo se limita a recolección para soporte: no crear datos de ejemplo, sembrar tablas, ejecutar DDL/DML ni alterar la infraestructura como parte del diagnóstico. Si la base está detenida, inaccesible o faltan permisos, registrar esa limitación y recurrir al control plane y a evidencia existente. El plugin no conecta automáticamente una base ni convierte un acceso fallido en diagnóstico interno.
