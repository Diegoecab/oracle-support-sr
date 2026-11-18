# Service-specific data collection: OpenSearch

For a customer using Datadog, read [opensearch-datadog.md](opensearch-datadog.md) for the documented Prometheus/OpenMetrics path and the proposed integration with SR evidence. Check the actual managed version, private connectivity, read-only monitoring access, full node coverage and metric cardinality before claiming the data is available. Do not enable plugins, change cluster settings, deploy collectors or create monitors as a side effect of collecting an SR draft.

Consult service-specific SRDC guidance when preparing an actual issue. The formal CreateIncident contract, the portal's conditional questionnaire, and the evidence Support needs are different layers; a successful API creation does not prove the diagnostic intake is complete.

## Verified Oracle guidance

The authenticated Oracle Support article [SRDC - OCI OpenSearch Information Required to Troubleshoot Issues](https://support.oracle.com/support/?kmContentId=2864665), displayed as **SRDC1037**, was inspected on November 17, 2026. Its last-updated date was April 23, 2025. The customer-facing action plan asks for the resource identifier, component, and subcomponent, plus error logs and screenshots when relevant. Recheck the current article for a new investigation. Do not export internal-only sections of an article into a customer case or reusable skill.

The observed conversational creation flow selected **OCI Search Service with OpenSearch**, **General Guidance**, **Backup and Restore**, and request type **Have an issue**. After these selections it displayed an additional questionnaire. This is one observed branch, not an exhaustive schema for every OpenSearch issue. The browser was used only to read the user's draft; no new SR was submitted through that form.

| Diagnostic information | Acquisition / applicability |
| --- | --- |
| Product, category and issue type | User's intended service and symptom, current taxonomy, and impact. Preserve the exact selected labels; verify the resulting case. |
| Region and availability domain | Resolve from the affected resource when available. A regional planning question may have no applicable AD. The portal's free-text region question is distinct from the Support API resourceList.region key. |
| Tenancy OCID | Selected OCI profile, verified against the authorized account. |
| Resource / cluster OCID and resource URL | Read-only resource lookup or a verified user-provided OCID/console link. Do not infer an OCID from a display name. |
| Compartment OCID | Resource metadata; keep separate from CIMS compartmentId, which is the tenancy OCID. If unresolved, say so. |
| Instance, volume and backup OCIDs | Collect only for the resources relevant to the issue. The observed form explicitly marked these questions as applicable only in some cases. |
| Component and subcomponent | Identify the failing component from the actual symptoms, diagnostics, and current service guidance. The SRDC does not establish a one-to-one mapping to categoryKey/subCategoryKey. Do not invent opaque component values. |
| Errors, logs and screenshots | UTC time, exact error, reproduction, service request IDs, relevant redacted diagnostics. Upload only the authorized files. |
| System lifecycle and business impact | Reuse current known context; ask for missing incident facts that affect severity or triage. A value displayed in an unsubmitted draft is not verified production impact. |

The observed questionnaire allowed N/A for some inapplicable OCID questions and validated tenancy/resource identifiers. Use N/A only where the actual form allows it and the identifier does not apply; never submit dummy OCIDs or reuse example values from a draft. The screenshot or accessibility observation does not establish that every displayed field is mandatory.

## Simple intake for the skill

Start with resource or console link, symptom, and impact. Resolve the tenancy, region, compartment, relevant identifiers, and supported routing metadata automatically through authorized reads. Consult the current SRDC, then ask only for missing component/impact/evidence facts that affect the investigation. For a general planning question without an affected cluster, state that scope explicitly rather than inventing a resource.

Retain a service-specific evidence packet and include the important values in the description, diagnostic note, or attachment. The reviewed CreateIncident model has no dedicated affected-resource-OCID field. Do not claim this text fills the portal's structured Resource OCID field. Structured questionnaire/contextualData submission requires a verified public schema contract; do not invent fields or replay a private portal creation endpoint as the supported public API.

For the observed OpenSearch product/category mismatch and region-key behavior, see [fields-and-intake.md](fields-and-intake.md). The SRDC improves diagnostic completeness but does not resolve the public API subcategory mapping by itself.
