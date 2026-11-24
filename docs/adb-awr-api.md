# ADB: obtener el AWR por Database Management y adjuntarlo al SR

El asistente obtiene el reporte con la **API de Database Management** y usa **oracle-support-sr** para adjuntarlo, publicar la actualización y comprobar su recepción. El usuario describe lo que necesita; el asistente consulta los identificadores, resuelve los snapshots y guarda el archivo. No hace falta entrar a la consola, preparar archivos SQL ni copiar valores técnicos entre comandos.

La recolección se orquesta con las herramientas CLI/SDK del asistente, fuera de la skill de SRs. Instalar el plugin no despliega un recolector ni habilita Database Management. Esta vía se verificó con una ADB de laboratorio. El 24/11/2026 se observó el flujo de apertura, AWR, adjunto, nota y verificación en 4 min 13 s; [ver el ejemplo y sus límites](adb.md#ejemplo-observado). Los 30–40 minutos de la alternativa manual son una estimación del usuario.

## Qué pide el usuario

Con la base y el SR identificados en la conversación:

```prompt
Obtené el AWR de esta ADB para el período del incidente y adjuntalo al SR.
```

El asistente reutiliza el perfil OCI, la región, la base, el SR y la ventana temporal del contexto. Si falta un dato fundamental o hay varias bases o casos posibles, pregunta solo por esa información. No inventa el período del incidente ni pide al usuario que busque OCIDs, DBIDs o números de snapshots que pueda recuperar por API.

## Alternativa mediante conexión a la base

El AWR también puede generarse con **DBMS_WORKLOAD_REPOSITORY.AWR_REPORT_HTML**, ejecutando una consulta mediante una conexión SQL autorizada a la ADB. **Esta alternativa no requiere habilitar OCI Database Management avanzado y evita el cargo de ese servicio.** Continúan aplicando el consumo normal de la base, la conectividad y los derechos de uso de diagnóstico correspondientes a la modalidad contratada. No se debe extrapolar esta condición a una Enterprise Edition instalada en IaaS u on-premises sin verificar su licencia de Diagnostics Pack.

El asistente puede resolver los identificadores y snapshots retenidos, ejecutar la función para la ventana acordada, guardar las filas del resultado como un único HTML y comprobar base, intervalo y contenido. Después usa oracle-support-sr para adjuntar el archivo, publicar la nota y verificar RECEIVED. El usuario no necesita preparar archivos SQL ni copiar parámetros. Se requieren una conexión de base de datos existente y autorizada y privilegios de lectura y ejecución adecuados; un perfil IAM de OCI por sí solo no concede acceso SQL. No se crean snapshots ni se cambian permisos como parte de la recolección.

La recolección SQL se configura fuera de la skill. El tiempo de 4 min 13 s documentado en el ejemplo corresponde al recorrido por Database Management y no constituye una medición de esta alternativa.

Referencia oficial: [DBMS_WORKLOAD_REPOSITORY: funciones AWR_REPORT_HTML y AWR_REPORT_TEXT](https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_WORKLOAD_REPOSITORY.html). Para los derechos de uso en servicios PaaS bajo BYOL Enterprise Edition, consultar la [FAQ oficial de BYOL](https://www.oracle.com/cloud/bring-your-own-license/faq/).

## Preparación del entorno para Database Management

Antes de usar este flujo, la ADB debe tener **Diagnostics & Management habilitado**, conectividad y una credencial de diagnóstico válida. Oracle exige una credencial ADMIN para las funciones avanzadas de Performance Hub que lo requieren. Las funciones avanzadas tienen costo adicional; su habilitación es una tarea de configuración separada y autorizada, no una acción implícita al solicitar un AWR.

Se necesitan:

- Perfil OCI o principal de ejecución autorizado en la región de la base, y CLI o SDK Python disponibles para el asistente.
- Permisos de descubrimiento y lectura de la base administrada y sus datos AWR. GetAwrDbReport requiere DBMGMT_MANAGED_DB_READ; usar el alcance mínimo definido en la [referencia de IAM](https://docs.oracle.com/en-us/iaas/database-management/doc/policy-details-database-management.html).
- Conexión y credencial de Database Management configuradas, con los permisos separados sobre named credentials o secretos que correspondan. Las credenciales permanecen en su almacenamiento autorizado, fuera de la conversación y del SR.
- Snapshots retenidos de la base y el contenedor correctos que permitan generar el reporte para la ventana relevante.
- Identidad de soporte y permisos para actualizar el SR y cargar adjuntos, según los [requisitos de la guía ADB](adb.md).

El asistente comprueba los requisitos por las interfaces disponibles. Si falta configuración o acceso, informa el impedimento y detiene la recolección. No crea una base, habilita servicios, cambia permisos, genera snapshots ni pasa a otra interfaz de recolección automáticamente.

## Qué ejecuta el asistente

| Etapa | Operaciones por API | Resultado |
| --- | --- | --- |
| Identificar la base | ListManagedDatabases y GetManagedDatabase | Base administrada correspondiente al recurso y la región solicitados. Una coincidencia de nombre por sí sola no prueba la identidad. |
| Resolver la ventana | ListAwrDbs, SummarizeAwrDbSnapshotRanges y ListAwrDbSnapshots | Identidad AWR, contenedor e instancias pertinentes, con snapshots continuos y su cobertura temporal. |
| Obtener el reporte | GetAwrDbReport con reportType=AWR y reportFormat=HTML | Contenido HTML para la selección verificada. |
| Preparar la evidencia | Guardado y validación local del contenido devuelto | Archivo HTML completo, base y ventana identificadas, tamaño y SHA-256. |
| Entregarla al SR | oracle-support-sr: attach, comment y get | Adjunto restringido, nota con contexto y comprobación posterior del estado. |

El asistente recorre las páginas de resultados y resuelve los parámetros con los datos devueltos. Conserva la ventana solicitada y la efectiva. Si los snapshots no alcanzan, la selección es ambigua o el reporte no permite comprobar la base y el intervalo, informa la limitación antes de subirlo. Una respuesta vacía o un error no se adjuntan como reporte.

La nota identifica el archivo, el recurso, las ventanas UTC solicitada y efectiva, los snapshots e instancias utilizados y el método de obtención. Antes del upload se revisa el contenido: AWR puede incluir SQL y datos sensibles. Si hace falta retirar contenido, se conserva el original local y se identifica la copia que se compartirá.

## Aprobación y resultado

La recolección y la preparación no requieren que el usuario arme archivos o ejecute comandos. En **MANUAL**, la skill presenta el archivo y la nota antes de publicarlos; en **AUTO**, realiza las operaciones incluidas en el alcance autorizado. Se conservan los modos de aprobación de la skill.

Después del upload, el asistente consulta el SR. Un envío aceptado puede quedar en PROCESSING antes de pasar a RECEIVED. Comprueba el archivo y la nota por separado, y devuelve el enlace del caso, la actualización literal publicada, el nombre y tamaño del adjunto y el estado verificado. Si la recepción sigue pendiente, lo indica sin volver a subirlo a ciegas.

## Beneficio y tiempos

Este flujo reduce la navegación, búsqueda de snapshots, descarga y carga manual del archivo. El usuario hace el pedido y recibe el resultado del recorrido.

El ahorro adicional se mide por separado del 83 % estimativo de la guía: tiempo activo de la persona y tiempo transcurrido hasta confirmar RECEIVED. El ejemplo del 24/11/2026 registró 4 min 13 s para el flujo completo con Database Management, con el entorno previamente configurado. Los tiempos de generación obtenidos mediante conexión SQL no se atribuyen a esta API. El ciclo completo con AWR puede superar los cinco minutos por gestión del escenario de referencia.

OCI Monitoring puede complementar el caso con métricas, pero no genera AWR. El MCP nativo de ADB puede aportar otros diagnósticos mediante herramientas autorizadas; no es un requisito de este flujo.

## Referencias oficiales

- [GetAwrDbReport por OCI CLI: filtros, formato y parámetros](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/database-management/managed-database/get-awr-db-report.html).
- [SDK Python: operaciones de Database Management](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/database_management/client/oci.database_management.DbManagementClient.html).
- [Modelo AwrDbReport: contenido y formato](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/database_management/models/oci.database_management.models.AwrDbReport.html).
- [Habilitación y conexión de Diagnostics & Management para ADB](https://docs.oracle.com/en-us/iaas/database-management/doc/enable-database-management-autonomous-databases.html).
- [Matriz de funciones y credenciales requeridas](https://docs.oracle.com/en-us/iaas/database-management/doc/database-management-feature-support-matrix.html).
- [Permisos de Database Management](https://docs.oracle.com/en-us/iaas/database-management/doc/policy-details-database-management.html).
- [Carga de adjuntos al SR](https://docs.oracle.com/en-us/iaas/Content/GSG/support/update-incident-add-attachment.htm).
