# ADB: obtener un AWR por API y adjuntarlo a un SR

El ejemplo separa dos tareas: obtener el reporte mediante una API de la base y usar oracle-support-sr para adjuntarlo y actualizar el caso. La recolección de AWR queda fuera de la skill y no requiere MCP.

Se ejecutó con ADB Serverless Always Free 19c mediante ORDS REST-Enabled SQL, sin habilitar Database Management. La generación y descarga del HTML completo tardó aproximadamente 6 segundos; ese tiempo no incluye aprovisionamiento, configuración de diagnósticos, captura de snapshots ni trabajo del asistente. La disponibilidad y los privilegios deben comprobarse para cada base.

## Requisitos

- Base accesible por HTTPS, URL ORDS obtenida de la API de ADB y una identidad de base autorizada para las consultas y DBMS_WORKLOAD_REPOSITORY. En el laboratorio se usó ADMIN de una base nueva; para uso operativo, definir los privilegios de diagnóstico necesarios.
- Dos snapshots propios de la PDB, de la misma instancia y sin reinicio entre ellos, que cubran el período relevante.
- OCI CLI para las operaciones del control plane y curl para las llamadas HTTPS. En Windows, usar curl.exe.
- Identidad de soporte y permisos para actualizar el SR y adjuntar archivos, según los [requisitos de la guía ADB](adb.md).

Las credenciales de la base y las de OCI son independientes. No poner contraseñas en argumentos, historial, archivos compartidos ni en el SR. Los comandos curl con --user ADMIN solicitan la contraseña de forma interactiva; conservan la validación TLS y no siguen redirecciones.

## 1. Crear una base de laboratorio, si hace falta

Este paso es independiente de la gestión del SR. Usar un compartment de pruebas autorizado, la región home y un cupo Always Free disponible. No convertir automáticamente a una opción paga si la creación falla.

Preparar adb-create.private.json fuera del repositorio y de carpetas compartidas, con una contraseña generada y almacenada de forma segura. Los marcadores se reemplazan por valores comprobados:

```json
{
  "compartmentId": "<COMPARTMENT_OCID>",
  "dbName": "SRAWRDEMO",
  "displayName": "sr-awr-api-demo",
  "dbWorkload": "OLTP",
  "dbVersion": "19c",
  "adminPassword": "<CONTRASENA_GENERADA_SEGURA>",
  "isFreeTier": true,
  "cpuCoreCount": 1,
  "dataStorageSizeInGbs": 20,
  "isAutoScalingEnabled": false,
  "isAutoScalingForStorageEnabled": false,
  "isMtlsConnectionRequired": true,
  "licenseModel": "LICENSE_INCLUDED"
}
```

```text
oci db autonomous-database create --profile MI_PERFIL --region MI_HOME_REGION --from-json file://adb-create.private.json
```

Conservar el OCID devuelto y comprobar lifecycle-state=AVAILABLE e is-free-tier=true. La creación requiere permisos de aprovisionamiento adicionales a los de soporte. La modalidad Developer de Serverless tiene facturación horaria; no equivale a Always Free.

## 2. Obtener el endpoint y elegir los snapshots

```text
oci db autonomous-database get --profile MI_PERFIL --autonomous-database-id ADB_OCID --query 'data."connection-urls"."ords-url"' --raw-output
```

Usar la URL devuelta y completar el endpoint de la identidad habilitada para REST-Enabled SQL: https://HOST/ords/admin/_/sql para ADMIN. No construir el hostname a partir del nombre visible de la base.

Guardar como snapshots.sql:

```sql
select name, dbid, con_id
from v$pdbs
where con_id=to_number(sys_context('USERENV','CON_ID'));

select dbid, snap_id, instance_number, startup_time,
       begin_interval_time, end_interval_time
from awr_pdb_snapshot
where dbid=(select dbid from v$pdbs
            where con_id=to_number(sys_context('USERENV','CON_ID')))
order by snap_id, instance_number;
```

```text
curl.exe --fail-with-body --silent --show-error --max-time 180 --user ADMIN --header "Content-Type: application/sql" --data-binary "@snapshots.sql" "https://HOST/ords/admin/_/sql" --output snapshots.json
```

Comprobar tanto HTTP como el result de cada sentencia: HTTP 200 puede incluir un error SQL. Elegir DBID, instancia y snapshots de la PDB actual. Descartar datos heredados de una plantilla o del root. El intervalo del informe va desde end_interval_time del snapshot inicial hasta end_interval_time del final.

En una base nueva puede no haber snapshots. La captura manual y los ajustes de AWR son cambios de diagnóstico separados, que se ejecutan solo en el laboratorio autorizado. El procedimiento con CREATE_SNAPSHOT(flush_level=>'LITE', dbid=>DBID_DE_LA_PDB) funcionó en el piloto. Si la programación local está deshabilitada, revisar MODIFY_SNAPSHOT_SETTINGS con el DBA. Ante un timeout, comprobar las vistas de snapshots y sesiones antes de repetir la captura.

## 3. Generar y descargar el AWR completo

Guardar como awr.sql y reemplazar los cuatro marcadores por los valores recuperados. Esta consulta reúne las líneas en un único CLOB para evitar perder páginas o truncar el reporte mediante el formato de texto de SQLcl:

```sql
select xmlagg(xmlelement(e, output||chr(10)) order by line_number)
  .extract('//text()').getclobval() as report_html_xml
from (
  select rownum as line_number, output
  from table(dbms_workload_repository.awr_report_html(
    l_dbid => <DBID_DE_LA_PDB>,
    l_inst_num => <INSTANCE_NUMBER>,
    l_bid => <BEGIN_SNAPSHOT>,
    l_eid => <END_SNAPSHOT>,
    l_options => 0))
);
```

```text
curl.exe --fail-with-body --silent --show-error --max-time 180 --user ADMIN --header "Content-Type: application/sql" --data-binary "@awr.sql" "https://HOST/ords/admin/_/sql" --output awr-response.json
```

Guardar como extract_awr.py y ejecutar python extract_awr.py:

```python
from html import unescape
import hashlib
import json
from pathlib import Path

data = json.loads(Path("awr-response.json").read_text(encoding="utf-8"))
assert data["items"] and all(x.get("result") == 0 for x in data["items"])
result = data["items"][0]["resultSet"]
assert result["hasMore"] is False and len(result["items"]) == 1
html = unescape(result["items"][0]["report_html_xml"])
assert "<html" in html.lower() and "</html>" in html.lower()
target = Path("awr.html")
with target.open("x", encoding="utf-8", newline="") as output:
    output.write(html)
print(target.name, target.stat().st_size, hashlib.sha256(target.read_bytes()).hexdigest())
```

La decodificación retira una sola capa de escape XML; el archivo conserva el HTML del reporte. Revisar PDB, DBID, ventana, contenido y tamaño antes de compartirlo. AWR puede incluir metadatos, SQL y literales sensibles. No adjuntar una respuesta parcial, un mensaje de error ni un informe de otra base.

## 4. Adjuntarlo y actualizar el SR con la skill

Con el SR y el perfil ya identificados en la conversación:

```text
Adjuntá awr.html al SR que acabamos de abrir y actualizalo con el método de recolección, la ventana del reporte y el resultado.
```

Internamente, la operación de adjunto usa el helper de la skill:

```text
python scripts/sr.py --profile MI_PERFIL --evidence-dir ./sr-evidence --output-format readable attach --key SR_KEY --file awr.html --expected-tenancy TENANCY_OCID
```

En MANUAL, el asistente presenta el caso, el archivo y su hash. Después del OK ejecuta ese mismo borrador con --approval-digest y --execute. AUTO debe elegirse expresamente para un alcance definido. El adjunto es restringido por defecto.

La nota identifica el archivo, la PDB, los snapshots, la ventana UTC y el método de obtención. Después de enviar, la skill consulta el SR: un upload aceptado puede figurar PROCESSING antes de pasar a RECEIVED. La nota y el estado del archivo se verifican por separado; RECEIVED no implica que un ingeniero ya lo haya analizado.

## Otra opción: API de Database Management

Si Diagnostics & Management ya está habilitado con conexión, credenciales y permisos adecuados, GetAwrDbReport permite obtener el contenido del informe directamente mediante OCI CLI/SDK. La habilitación de funciones avanzadas tiene costo adicional. Esta alternativa se verificó en documentación; el ejemplo ejecutado usó REST-Enabled SQL.

```text
oci database-management managed-database get-awr-db-report --managed-database-id MANAGED_DATABASE_OCID --awr-db-id AWR_DB_ID --begin-sn-id-greater-than-or-equal-to BEGIN_SNAPSHOT --end-sn-id-less-than-or-equal-to END_SNAPSHOT --report-type AWR --report-format HTML --query data.content --raw-output > awr.html
```

OCI Monitoring permite recuperar series de métricas para complementar la evidencia; no genera el informe AWR.

## Referencias oficiales

- [REST APIs de Autonomous Database Serverless](https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/rest-apis.html).
- [ORDS: REST-Enabled SQL, autenticación y formato de resultados](https://docs.oracle.com/en/database/oracle/oracle-rest-data-services/26.2/orddg/rest-enabled-sql-service.html).
- [DBMS_WORKLOAD_REPOSITORY: AWR_REPORT_HTML, snapshots y ajustes](https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_WORKLOAD_REPOSITORY.html).
- [Always Free: límites y condiciones](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/autonomous-always-free.html).
- [Developer: facturación horaria hasta la terminación](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/autonomous-database-for-developers-billing.html).
- [AWR por la API/CLI de Database Management](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/database-management/managed-database/get-awr-db-report.html).
- [Database Management para ADB](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/mdw-oci-database-management.html).
- [Carga de adjuntos al SR](https://docs.oracle.com/en-us/iaas/Content/GSG/support/update-incident-add-attachment.htm).
