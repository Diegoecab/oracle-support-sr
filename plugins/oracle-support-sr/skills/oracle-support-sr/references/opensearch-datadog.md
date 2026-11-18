# Métricas de OCI OpenSearch en Datadog

Revisión documental: 18/11/2026. La conexión es viable por el formato de métricas que ambos productos admiten. La configuración propuesta requiere una prueba en el cluster y la organización Datadog del cliente; no fue desplegada durante esta investigación.

## Qué está documentado

Oracle incluye el plugin Prometheus en su [matriz de plugins soportados para OCI Search with OpenSearch](https://docs.oracle.com/en-us/iaas/Content/search-opensearch/Concepts/supportedplugins.htm). La fila consultada marca soporte para 2.11.0, 2.15.0, 2.18.0, 2.19.1 y 3.2.0; no para 1.2.4 ni 2.3.0. Esa tabla no enumera todas las versiones más nuevas del servicio: para otra versión hay que confirmar la compatibilidad exacta y el plugin presente en el cluster.

Datadog documenta la lectura de endpoints Prometheus mediante [OpenMetrics](https://docs.datadoghq.com/integrations/openmetrics/) en su Agent. Se puede reutilizar un Agent existente con acceso al cluster. No hace falta sumar un servidor Prometheus ni instalar el Agent en los nodos administrados por Oracle.

## Cómo se conecta

```text
Datadog Agent existente, en un host o contenedor con acceso a la VCN
    -> GET HTTPS al endpoint privado del exporter de OpenSearch
    <- muestras de métricas en formato Prometheus
    -> envío de métricas por HTTPS a Datadog

Datadog Monitor
    -> alerta y contexto del cluster
    -> flujo de creación del SR y pager, si se implementa esa automatización
```

El Agent inicia la recolección; el plugin expone las métricas. Si ya hay Prometheus, ambos colectores pueden leer el exporter, evitando reenviar dos veces las mismas series a Datadog. El exporter no envía directamente datos a Datadog SaaS. Esta propuesta usa el check OpenMetrics del Agent y no depende de configurar remote_write.

Oracle documenta [endpoints privados y conectividad al cluster](https://docs.oracle.com/en-us/iaas/Content/search-opensearch/Tasks/ingestingociopensearchdata.htm). El Agent necesita ruta, DNS y acceso al puerto del endpoint; habitualmente es HTTPS en 9200. Puede aprovechar infraestructura existente en OCI o conectividad privada ya disponible. Tener Datadog contratado no demuestra que un Agent actual pueda llegar a esa VCN.

El proyecto del [exporter de OpenSearch](https://github.com/opensearch-project/opensearch-prometheus-exporter) describe la ruta `/_prometheus/metrics`. Hay que comprobarla en la versión administrada del cliente antes de darla por operativa. En un servicio administrado se verifica el plugin provisto por Oracle; no se propone instalar ZIPs comunitarios por SSH en sus nodos.

## Configuración de referencia

Plantilla para `conf.d/openmetrics.d/conf.yaml`, basada en la [guía de recolección de Datadog](https://docs.datadoghq.com/integrations/guide/prometheus-host-collection/) y el [ejemplo oficial de configuración](https://github.com/DataDog/integrations-core/blob/master/openmetrics/datadog_checks/openmetrics/data/conf.yaml.example). Usar una versión mantenida del Agent 7 compatible con el modo actual de OpenMetrics. Los valores entre `<...>` deben completarse con datos comprobados; los nombres de métricas se obtienen del scrape real.

```yaml
init_config:
instances:
  - openmetrics_endpoint: "https://<FQDN_PRIVADO_CLUSTER>:9200/_prometheus/metrics"
    namespace: oci_opensearch_exporter
    auth_type: basic
    username: ENC[opensearch_metrics_user]
    password: ENC[opensearch_metrics_password]
    tls_verify: true
    min_collection_interval: 60
    metrics:
      - "<NOMBRE_EXACTO_DE_METRICA_OBSERVADA>"
    tags:
      - "service:oci-opensearch"
      - "env:<ENTORNO_CONFIRMADO>"
      - "oci_region:<REGION_CONFIRMADA>"
      - "cluster_ocid:<OCID_CONFIRMADO>"
```

Los handles `ENC[...]` requieren configurar el [backend de secretos del Agent](https://docs.datadoghq.com/agent/configuration/secrets-management/). La identidad de monitoreo debe tener permisos de lectura suficientes para el exporter. El acceso IAM de OCI a metadatos o SRs es independiente de la autenticación y roles del cluster. Si corresponde una CA privada, configurar `tls_ca_cert` con la cadena confiable; conservar la validación TLS. El intervalo de 60 segundos es un punto de partida propuesto que se ajusta según carga y detección requerida.

## Comprobar que cubra todos los nodos

El exporter upstream usa por defecto estadísticas del nodo que atiende la petición. También documenta `prometheus.nodes.filter` con `_all` para ampliar la cobertura. Esas capacidades deben confirmarse en la versión provista por OCI; no se asume que todos los ajustes upstream estén permitidos en el servicio administrado.

Consultar un único endpoint balanceado no demuestra cobertura de todos los nodos. Antes de alertar, contrastar los identificadores de nodos de las muestras con los del cluster. En Datadog, conservar las etiquetas de cluster y nodo; el host del Agent recolector no representa por sí solo al nodo OpenSearch. El equipo debe acordar una agregación soportada por Oracle o endpoints de recolección que cubran los nodos necesarios. Si varios Agents recogen el mismo cluster completo, definir un colector propietario o una distribución que evite duplicados.

## Alertas, costos y evidencia para el SR

Empezar con una selección acotada: estado del cluster y shards, heap/GC, uso de disco, rechazos de búsquedas o indexación y colas, según lo que exponga esa versión. La ausencia de muestras necesita su propio tratamiento; no equivale a un cluster sano. El exporter aporta métricas, no el paquete completo de logs ni el historial del incidente.

Datadog clasifica lo recogido por OpenMetrics como custom metrics. El costo depende de las series y sus combinaciones de etiquetas, además del contrato aplicable. Las métricas por índice pueden elevar la cardinalidad: seleccionar familias y dimensiones necesarias, medir volumen y revisar duplicación. Reutilizar un Agent evita una VM dedicada, pero no implica costo incremental cero.

OCI también publica [métricas nativas del cluster](https://docs.oracle.com/en-us/iaas/Content/search-opensearch/ociopensearchmetrics.htm), con namespace `oci_opensearch`. Son una fuente complementaria para contrastar cobertura. La [lista consultada de namespaces de la integración OCI de Datadog](https://docs.datadoghq.com/integrations/oracle-cloud-infrastructure/) no enumera ese namespace: no se afirma aquí que el conector lo ingiera sin configuración o soporte adicional. La integración Datadog Amazon OpenSearch corresponde a AWS y no sustituye esta validación para OCI.

Para unirlo al flujo de SRs, conservar OCID/compartment/región confirmados, ventana UTC, consulta y enlace de la alerta, valores/umbrales observados, nodos afectados y diagnósticos relevantes. El monitor puede disparar el [diseño Datadog -> OCI Functions -> SR -> pager](datadog-automation.md). La clasificación de soporte y el impacto de negocio requieren un mapeo aprobado; una alerta no habilita inventar severidad, impacto ni campos faltantes. MANUAL sigue siendo el valor predeterminado de la skill. Un worker desatendido necesita AUTO expresamente autorizado y una ruta de fallback cuando falten datos fundamentales.

## Prueba propuesta con el cliente

- Confirmar versión del cluster, plugin, endpoint y un Agent existente con conectividad.
- Usar una identidad de monitoreo con el acceso necesario y obtener una muestra de solo lectura.
- Elegir las métricas efectivamente presentes, revisar etiquetas y comprobar cobertura de nodos.
- Habilitar el check en el entorno autorizado; verificar `openmetrics` en el estado del Agent y las series recibidas en Datadog.
- Probar un monitor controlado y revisar latencia de detección, datos ausentes, cardinalidad y duplicados.
- Preparar un borrador de SR con esa evidencia; validar separadamente el flujo de creación y el pager sin provocar una falla productiva.
