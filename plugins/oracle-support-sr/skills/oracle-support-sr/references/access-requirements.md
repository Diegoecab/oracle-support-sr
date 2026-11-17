# Minimum access for SR operations and evidence collection

Checked 2026-11-17. These are separate authorization layers; ticket access does not grant access to databases, application logs or Datadog. Use a dedicated operator group scoped to the task. The administrator account used during the pilot is not the recommended client permission set.

## Runtime and authentication

- Pilot runtime baseline: Python 3.11 and official OCI SDK `oci>=2.177.0,<3`; local compatibility tests include 2.177.0. The optional CLI backend additionally needs OCI CLI. Both backends use the Python SDK to load profile/support context.
- Codex or Claude Code with local command execution, filesystem evidence access and HTTPS access to the required OCI endpoints. GitHub access is needed to obtain this private distribution, not for each SR operation.
- A named OCI configuration profile and registered API signing key belonging to the actual support user; configure the tenancy home region. Never distribute credentials with the plugin. Initial account/key setup is separate from recurring operation time.
- A paid support-eligible tenancy, provisioned My Oracle Cloud Support identity, and appropriate support-user-group visibility and create/update privileges. See [support account setup](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/usingsupport.htm) and [creation requirements](https://docs.oracle.com/en-us/iaas/Content/GSG/support/create-incident.htm).
- Check [known issues](https://docs.oracle.com/en-us/iaas/Content/GSG/support/known-issues.htm): Oracle documents that Support CLI commands are not supported in Cloud Shell, and SDK/CLI/API rejections can require subscription to Phoenix plus the actual home-region parameter. These are environment prerequisites/troubleshooting, not instructions to subscribe or change a tenancy automatically.

## Support authorization

The [IAM reference](https://docs.oracle.com/en-us/iaas/Content/GSG/support/policy-reference.htm) maps read operations to `TICKET_READ` and creation/update to `TICKET_MANAGE`. The [security guide](https://docs.oracle.com/en-us/iaas/Content/Security/Reference/support-management.htm) provides these policies:

```text
Allow group SR-Readers to read tickets in tenancy
Allow group SR-Operators to manage tickets in tenancy
```

Use the actual domain-qualified group when applicable. The manage policy already includes read. `inspect tickets` grants no ticket API operations in the published table.

| Task | API / helper | Minimum published IAM level | Additional support prerequisite |
| --- | --- | --- | --- |
| List/get, taxonomy, validate identity | ListIncidents, GetIncident, ListIncidentResourceTypes, ValidateUser | read tickets | Support identity and visibility in the selected support group. |
| Create | CreateIncident / create | manage tickets | CUA-assigned create privilege in a support group; select its validated userGroupId. |
| Add a note / close selected SR | UpdateIncident / comment, close | manage tickets | Update privilege and visibility in that SR's group; explicit authorized action. |
| Attach evidence | PutAttachment / attach | Start from the operator policy and support update privilege; validate with the delegated account | PutAttachment is absent from the current IAM operation table, so its exact granular permission mapping is not established there. Validate upload separately; an admin-account success is not proof of minimum privilege. |
| Delete SR | Not exposed by the reviewed public client | No deletion operation identified | Closing preserves case history and is the supported operation used here. |

Support group membership and IAM group membership are different. Being an IAM administrator does not provision a support account or its group privileges. Read/write receipts and local storage must be accessible only to the intended operators.

## Evidence permissions, only when needed

| Evidence | Scoped permission or access | Boundary |
| --- | --- | --- |
| ADB lifecycle, OCID, compartment and GET/list results | inspect autonomous-databases in the affected compartment | [ADB policy reference](https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/autonomous-database-iam-policies.html) includes Get/List under inspect. This does not supply SQL or OS log access. |
| OpenSearch cluster, backup, work-request metadata | inspect opensearch-clusters; inspect opensearch-cluster-backups and opensearch-work-requests when needed | [OpenSearch permissions](https://docs.oracle.com/en-us/iaas/Content/search-opensearch/Concepts/ocisearchpermissions.htm). The published table still names some operations Elasticsearch; verify the installed/current operation mapping. Cluster data-plane credentials/network access are separate. |
| Compartment discovery | inspect compartments in tenancy, if discovery is required | If identifiers are already supplied, avoid broader inventory just for convenience. |
| OCI log contents | read log-content in the log compartment, with log-group restrictions where applicable | [Logging IAM](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/loggingpolicyreference.htm). Log metadata access does not by itself authorize content. |
| OCI metrics | read metrics in the affected compartment | [Monitoring policies](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/monitoringpolicyreference.htm). |
| Object Storage diagnostic files | read objects in the diagnostic compartment, restricted to the intended bucket/prefix | Existing evidence only. Creating buckets or changing logging is not required to manage SRs. |
| Usage/cost evidence | read usage-report in tenancy | [Cost Analysis / Usage API requirements](https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/costanalysisoverview.htm). This is separate from invoice/payment administration. |
| Datadog logs and monitors | Read access to only relevant endpoints/data, using an approved service identity | [Logs Search](https://docs.datadoghq.com/api/latest/logs/search-logs-get/) requires logs_read_data; applicable index/query restrictions also apply. Configure monitor/metric/workflow permissions only for endpoints actually used. |
| Database internals, application or OS logs | Read-only SQL/database role, OS account or approved log-export source, plus connectivity, only if that diagnostic needs it | OCI control-plane inspect and support privileges do not imply these grants. Prefer existing exported diagnostics and redact unrelated sensitive content. |
| IAM troubleshooting | Read the relevant memberships/groups/policies only if the incident requires it | Not a prerequisite for ordinary SR management; do not grant manage all-resources just to collect evidence. |

Use an approved intake checklist for the service. Relevant resource OCID, region, compartment, UTC window, request IDs, observed status, business impact, diagnostics and routing must accompany the SR. The helper does not implement universal collection of every service's logs; the agent needs the corresponding authorized tools and access. No dedicated VM is required for interactive use.
