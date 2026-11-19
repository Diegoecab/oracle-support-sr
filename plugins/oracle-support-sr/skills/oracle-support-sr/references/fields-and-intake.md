# SR fields, severity, and evidence intake

Checked 2026-11-17 against official OCI model sources and AWS Botocore contracts. Keep backend requirements, client requirements, and useful diagnostic evidence distinct. Current [CreateIncident](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/cims/models/oci.cims.models.CreateIncident.html), [CreateTicketDetails](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/cims/models/oci.cims.models.CreateTicketDetails.html), and [CLI create](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/support/incident/create.html) are authoritative for names and values.

## OCI severity values

| API / CLI value | Technical SR severity | Console impact label | Selection basis |
| --- | --- | --- | --- |
| `HIGHEST` | 1 | Critical issue / critical outage | Mission-critical production unavailable or severely stopped; 24x7 contact commitment required. |
| `HIGH` | 2 | Significant impairment | Significant service impairment with important operational impact. |
| `MEDIUM` | 3 | Technical issue | Limited operational impairment or a technical investigation, with work able to continue. |
| `LOW` | 4 | General guidance | Information, usage, enhancement, or documentation guidance. |

`ticket.severity` is an enum string, not an integer. Use the enum in API requests and show both enum and human severity in reports. The ordinal alignment follows OCI Support's critical/significant/technical/guidance ordering; do not apply it to unrelated Oracle products' priority fields or infer a response SLA from the label. Sources: [OCI create guide](https://docs.oracle.com/en-us/iaas/Content/GSG/support/create-incident.htm) and [OCI support severity definitions](https://docs.oracle.com/en-us/iaas/Content/dedicated/dedicated-region/customer-support.htm#Support_Severity_Levels). The latter has Dedicated Region response objectives; do not transplant those response times to another support plan.

Select severity from current impact, scope, production status, workaround, urgency, and contact availability. Do not infer a production outage merely from HTTP 404, ongoing cost, an old incident, or a requested credit. Severity escalation is a separate requested mutation; documenting the field does not authorize changing an existing SR.

## OCI creation field dictionary

Wire JSON uses camelCase; SDK attributes use snake_case. The CLI create command flattens title, description, and severity instead of accepting the full nested ticket structure.

| Wire path | Requirement | Source / validation |
| --- | --- | --- |
| `compartmentId` | Required | Tenancy OCID from the selected profile, despite the field name. Never substitute the affected resource's compartment. |
| `problemType` | Required | `TECH` or `ACCOUNT` for helper creation; distinguish a technical investigation from a billing request. Other API enum values do not imply helper support. |
| `ticket` | Required object | Contains the required title, description, and severity. |
| `ticket.title` | Required text | Concise symptom and affected service; draft from evidence within the helper's conservative 80-character budget. This is a local preventive limit, not a documented universal Oracle maximum. Validate before approval; do not silently truncate. |
| `ticket.description` | Required text | Evidence, business impact, resource/region/time, diagnostics, request IDs, and requested outcome. Helper caps the initial description at 1500 characters; use notes/attachments for the rest. That helper cap is not a claim about every Oracle portal. |
| `ticket.severity` | Required enum | `LOW`, `MEDIUM`, `HIGH`, `HIGHEST`; use the mapping above. |
| `userGroupId` | Optional in current API; required explicitly by this helper for TECH | Discover using `ValidateUser`; current service may select an eligible group if omitted. Explicit selection prevents unintended visibility. |
| `contacts[]` and nested contact fields | Deprecated creation input, retained in some client models | Oracle's Support Management deprecation notice says this CreateIncident input has no functional effect for public API usage; removal is scheduled for May 20, 2027. Do not promise additional recipients or notification targets from populating it. Manage intended contacts through a currently supported interface. |
| `ticket.resourceList[]` | Optional in model; useful for routing | SDK `CreateResourceDetails`; current model exposes `item` and `region`. Not all fields are exposed by flattened CLI create. |
| `ticket.resourceList[].region` | Optional | Resolve the affected region's key using Identity ListRegions, for example `IAD`. A live request using `us-ashburn-1` was rejected with HTTP 400; the otherwise identical body using `IAD` succeeded. Keep the full region name for the SDK client endpoint. |
| `ticket.resourceList[].item` | Optional object | Current CreateItemDetails has `type`, `category`, `subCategory`, `issueType`, and `name`; inspect live TAXONOMY and typed nested models before populating. |
| `ticket.contextualData` | Optional | Structured contextual payload; use a known documented schema rather than inventing a universal payload. |
| `referrer` | Optional | Origin/reference context, often a URL. Not a notification callback. |
| CSI | Legacy client compatibility | Removed from newer creation models; use only a verified CSI if an old client requires it. Never substitute a user-group ID. |

Operation context is separate from the body: profile/config, acting user `ocid`, support home region, and `domainid` where required. Authentication is supplied by the signer, not a password in the SR. Returned `key`, lifecycle state/details, and created/updated timestamps are response fields, not required creation input. Attachments use the supported upload workflow; do not invent a top-level `attachments` field.

### Product and Category shown in the portal

Query live `ListIncidentResourceTypes` with `problemType=TAXONOMY` before constructing classification. Preserve the returned service-group -> service -> service-category -> subcategory hierarchy, IDs, and labels. Portal product labels can differ from API service labels; report that difference rather than asserting an exact mapping from similar text.

The typed creation body permits `ticket.resourceList[].item.category.categoryKey` and optional `subCategory.subCategoryKey`/`issueType.issueTypeKey`, with item type `tech`. Prefer the documented `CreateTechSupportItemDetails` model. `CreateCategoryDetails.categoryKey` identifies the service category. Select subcategory only when known; do not fabricate Connectivity or Performance merely to complete a screenshot. Resolve current SDK model fields before using another level of the hierarchy.

A live SDK creation test on November 17, 2026 supplied the live OpenSearch category key and Backup and Restore subcategory key. The backend accepted the body and echoed both keys. The authenticated case showed the exact product **OCI Search Service with OpenSearch**, but its Details category was **Cluster Provision and Resize**, not the requested Backup and Restore. Thus exact product selection was observed, while finer category selection did not match. Do not publish the tested subcategory payload as a verified routing recipe. The taxonomy parent schema matched Cluster Provision and Resize; this is a correlation, not proof of the fallback algorithm. Public models do not establish how the returned taxonomy schema maps to a create input. Do not invent `issueTypeKey` or contextualData values to compensate. Seek supported clarification, preferably within the already authorized case rather than creating extra duplicates.

The current My Oracle Support UI can label a finer classification as Category, while the OCI taxonomy exposes separate service/category/subcategory levels. Compare labels and provenance explicitly; do not treat the similarly named levels as interchangeable. When inspecting reassignment, distinguish a Knowledge Assistant handoff to an engineer from a confirmed transfer between product queues. A current product label or a creation email is not a complete assignment audit.

See [Support Management service changes](https://docs.oracle.com/en-us/iaas/Content/servicechanges.htm) for deprecated CreateIncident contacts and the current 1500-character initial-description limit. Presence in an older SDK model does not establish current service behavior.

There is no documented top-level `product` field in the reviewed CreateIncident model. Do not use `item.name` to claim setting Product: it is documented as the item's display name. The dedicated flattened CLI create command does not expose the full `resourceList`; use the SDK or a separately identified raw REST request for structured classification.

Keep validation levels explicit: a successful taxonomy read establishes the available catalog; a typed model check establishes local payload compatibility; neither proves the backend will reproduce an exact portal Product label. Validate actual routing when an authorized real creation requires it, using a supported read or portal view. If GetIncident omits classification, do not report it as verified. Do not create a duplicate test SR or change an unrelated existing SR just to test classification.

If the user literally wants to upload a screenshot, use PutAttachment with the actual authorized file. Attaching an image does not by itself populate Product or Category.

### Minimal complete routing packet for resource cases

Keep user input simple: affected resource (OCID, link, or identifiable name), symptom, and known impact. Resolve account/context, metadata, taxonomy IDs, and support authorization through read-only sources when possible; ask only for missing facts that change the case. A name is not a verified OCID, and HTTP 404 leaves resource metadata unresolved rather than proving deletion.

- Put the affected **resource OCID** explicitly in `ticket.description` and diagnostic notes/attachments. The reviewed CreateIncident/CreateResourceDetails model has no dedicated affected-resource-OCID property. Preserve a sidecar case/evidence record and use only a documented contextualData schema if one is available; do not claim an arbitrary payload establishes structured resource association.
- CIMS `compartmentId` means the **tenancy OCID**. The affected resource's actual compartment OCID is separate evidence. Operation `ocid` means the acting **user OCID**, not the resource. Capture nondefault identity `domainid` only where applicable.
- Resolve the full visible service-group/service/category/subcategory tree and retain its labels and IDs with the taxonomy timestamp. Use the supported `categoryKey`, `subCategoryKey`, and, when applicable, `issueTypeKey` fields. Do not populate invented serviceId/productId/queueId keys. Do not infer that a returned `schema` identifier alone is a valid contextualData schema contract.
- `userGroupId` establishes customer-side visibility and create/update privileges. Product/category classification supplies routing context for Oracle Support. A genuine CSI, when a legacy client requires it, is an entitlement identifier; it is not a service-category ID.
- Include the affected region, relevant UTC times, exact error, and original service `opc-request-id`. Distinguish those request IDs from the support API request ID and retain both for correlation. Put the service and routing labels in the description even when structured classification is supplied.
- Verify what was actually submitted and what Oracle returns. If the response omits classification, retain that verification gap; an assigned engineer or product label in an activity does not prove our creation payload set structured routing.

Do not require opaque IDs from the customer or another confirmation when the intended action and populated scope are already authorized. If taxonomy selection is ambiguous, ask a focused business/service question. If no suitable mapping can be verified, disclose the missing routing and prepare a reviewable draft rather than silently choosing unrelated values.

## Intake workflow for either provider

For OpenSearch, also read [service-data-collection.md](service-data-collection.md). Its SRDC and observed questionnaire cover resource identifiers, components, and diagnostics beyond the formal CreateIncident required parameters. Portal-only structured fields do not become public API parameters merely because the portal displays them.

1. Reuse already authorized account, issue, evidence, and operation. Identify the affected service/resource and UTC incident window from available context and read-only sources.
2. Build an intake record with each value's provenance: profile/API-derived, observed in diagnostics, stated by the user, or proposed classification. Mark unresolved facts as unknown.
3. Query taxonomy and authorization. Ask only for material missing business facts: current production impact, affected users, workaround, required date, and contact availability. Technical evidence cannot establish these by itself.
4. Draft the payload, show meaningful classification/severity and missing items, validate locally, then submit within the user's existing authorization. Preserve receipts and reconcile ambiguous writes.
5. Read the returned case and verify title, severity, routing, contacts, and attachment/note availability. A local valid JSON is not proof of support-side acceptance.

## Business impact intake on our side

Business-impact collection applies when preparing a new SR or assessing a requested severity change. Reading and monitoring an existing SR do not require an interactive questionnaire. Surface any Support request for business impact without fabricating an answer or changing severity.

For initial intake, combine the current conversation with maintained customer/application context. Stable context includes environment, application owner, business criticality, preferred language, and contact. Incident-specific facts include current production effect, affected business process/users, workaround, deadline, and current contact availability. Criticality alone does not prove an outage. Revalidate stale context and record source/time. A missing answer is unknown, not no impact; do not silently default to MEDIUM.

For a cost/access issue, resource, region, observed errors, request IDs, usage interval, and measured usage cost can already come from evidence. The remaining question may simply be whether a production process is affected in addition to the cost. A future cost projection is an estimate, not an observed loss.

| Intake option | Approach | Suitable use |
| --- | --- | --- |
| Skill conversation | Reuse known facts, ask only missing impact in the current conversation, draft severity with justification. | Initial pilot; no new OCI interaction service. |
| Customer/application profile and rules | Reuse stable context and an explicit policy for authorized actions; refresh current incident facts. | Consistent intake with fewer repeated questions. |
| Authenticated web form | Prefill evidence, collect missing business facts, persist the draft, submit to a serverless handler. | Multiple client users; requires frontend, authentication, and inbound API components. |
| Interactive chat or existing ITSM | Ask an owner and receive an authenticated chat action or incident update through a separate inbound integration. | Clients already operating a bot or incident workflow. Notifications delivery alone does not collect replies. |

Recommended flow: profile/evidence -> conversation only for missing impact -> draft with severity and justification -> submit within existing authorization -> verify. Do not ask for approval again when action and scope are already authorized. If essential facts are missing, keep the draft and ask for those facts. A preauthorized automation policy permits only its defined actions when required facts are present.

An explicit user-selected severity and already sufficient authorized scope can be reused without a fresh questionnaire. Do not require every possible intake field merely to submit a valid case; ask when the answer would materially change classification or a required action. Record unknown impact honestly rather than inventing a justification.

For future unattended creation, persist an `AWAITING_IMPACT` draft and return when human input is needed. A later authenticated response loads that draft and resumes validation. Do not hold a Function invocation open waiting for a person. Use draft revisions, event IDs, and write reconciliation to prevent duplicate submission. These pending states, policy evaluation, profile loading, and inbound handlers are design extensions, not features implemented by `sr.py`.

Keep the monitor independent: detect and notify automatically. A severity-review suggestion includes evidence; actual reclassification requires the requested action, current impact facts, and a supported update path. The current helper does not implement severity changes.

## How AWS gathers creation fields

The reviewed [AWS Support MCP](https://github.com/awslabs/mcp/tree/7b09fa86e895068b7ed990503224cdfe1421e481/src/aws-support-mcp-server) exposes tool schemas and API calls. Its `create_support_case` requires `subject`, `communication_body`, `service_code`, `category_code`, and `severity_code`. It supplies defaults for language and issue type and optional CC addresses and an attachment-set ID. The underlying [CreateCase SDK contract](https://docs.aws.amazon.com/boto3/latest/reference/services/support/client/create_case.html) formally requires only `subject` and `communicationBody`; service-side rules and support-plan authorization still apply.

An agent can obtain service/category options with `describe_services`, valid severities with `describe_severity_levels`, and language/hours options with `describe_supported_languages` and `describe_create_case_options`. These catalogs do not collect the incident's business impact or logs. The MCP itself does not scan CloudWatch or resources to fill every required field: that needs the agent's authorized context/tools and user answers. The separate `support-cases` skill reviewed earlier focuses on reading historical cases, not a complete creation intake wizard.

| AWS create field | Acquisition |
| --- | --- |
| Account | Selected credentials / role; caller context, not a required accountId body field. |
| `subject`, `communicationBody` | Agent drafts from observed symptoms and impact; include region, resource ARN/ID, UTC times, errors, diagnostics, and request IDs in body/evidence. |
| `serviceCode`, `categoryCode` | Discover current catalog; match symptoms and service. Do not guess opaque identifiers. |
| `severityCode` | `low`, `normal`, `high`, `urgent`, `critical`; choose by impact and check plan availability. No universal positional mapping to OCI severity. |
| `language`, `issueType` | User preference and current supported options. Current API issueType uses `technical` or `customer-service`. The reviewed MCP's actual IssueType enum accepts `technical`, `account-and-billing`, `service-limit` and rejects `customer-service`. This is a static contract mismatch affecting nontechnical creation, not just a docstring discrepancy. Technical default agrees. Fix/validate that adapter or use the current direct SDK contract for nontechnical cases. |
| `ccEmailAddresses` | Intended verified recipients; API maximum 10. |
| `attachmentSetId` | Upload evidence through AddAttachmentsToSet first; the reviewed MCP supports this path. |

The current AWS API additionally has `dryRun` and `uploadIds`; those were absent from the reviewed MCP create signature. API `dryRun=true` validates without creating and signals success via `DryRunOperationException`. Do not claim our OCI local draft validator is equivalent to a server-side dry run, and do not run AWS validation without the intended AWS account. No AWS account/API test was performed in this review.
