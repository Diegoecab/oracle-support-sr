# Datadog critical alert to an OCI technical SR

Status: proposed architecture, not deployed. The interactive skill and its local helper do not install a background agent or turn Datadog alerts into SRs by themselves. Reuse the Python API workflow in an independently deployed handler; an LLM may summarize approved evidence but is not required to make the API call.

## Evidence and official examples

- [Datadog Workflow Automation blog](https://www.datadoghq.com/blog/automate-end-to-end-processes-with-datadog-workflows/), published 2022-10-19, updated 2023-06-05: event-driven workflows with optional human input.
- [Datadog getting-started guide](https://docs.datadoghq.com/getting_started/workflow_automation/): monitor alert creates a Jira issue, then notifies Slack with the issue link. This is a useful pattern to adapt; it is not an Oracle SR integration tutorial.
- [HTTP workflow actions](https://docs.datadoghq.com/actions/workflows/actions/): call a custom endpoint and branch on results.
- [Webhooks integration](https://docs.datadoghq.com/integrations/webhooks/): alert POST, custom JSON and headers, cycle/monitor identifiers, retries and a 15-second individual-request timeout.
- [Oracle API Gateway authorizer functions](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/adding_authn_authz_request_policies-multi-argument.htm) and [Functions invocation modes](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsinvokingfunctions.htm): authenticated ingress and asynchronous detached processing.

The reviewed Oracle blog [The Power of Oracle Cloud Support](https://blogs.oracle.com/cloud-infrastructure/the-power-of-oracle-cloud-support), July 13, 2021, describes Support Center and contextual information collection. It is not a CreateIncident API tutorial. No public Oracle blog specifically demonstrating Datadog-to-OCI-SR or the complete technical SR API lifecycle was verified in this research. Use the official Support Management API/SDK guides for that contract.

## Recommended flow, with no dedicated VM

```text
Critical Datadog monitor
  -> Datadog Workflow Automation / HTTP action
  -> OCI API Gateway + authorizer
  -> receiver Function: validate, authorize scope, persist event
  -> worker Function (detached invocation): enrich, deduplicate, create/get SR
  -> durable result: SR key, link, request IDs and evidence pointers
  -> workflow reads status and pages the on-call team with the SR link
```

Use a durable event/operation registry, for example Object Storage records with conditional create/ETag updates. The receiver calls the worker using the supported `fn_invoke_type='detached'`; a 202 acknowledges processing, not SR creation. A configured scheduled reconciliation Function handles stuck records and uncertain outcomes. Object Storage does not automatically invoke this worker in this design. No VM or persistent polling process is required.

For the first pilot, a synchronous Function may return the SR key directly to the Workflow HTTP action if the configured time budgets permit. The detached design separates acknowledgement from work and tolerates enrichment/cold-start/API latency. A plain Datadog webhook must acknowledge within its documented timeout; do not hold it open expecting a completed SR in every run.

## Have the SR ready when the pager arrives

Two explicit policies are possible:

- SR first: the workflow waits for CREATED plus a successful GetIncident, then triggers the on-call notification containing the SR number, link, symptoms and diagnostics. Set a bounded creation wait agreed with operations. On timeout/error, page anyway with SR_PENDING or SR_CREATION_FAILED and the automation correlation ID; enrich the incident later. There is no guarantee that an external Support API will always finish before the page.
- Immediate page: page and create the SR in parallel; update the incident when the key becomes available. Prefer this when any delay to a critical page is unacceptable. This mode does not promise a ticket already exists in the first page.

Do not leave the original monitor paging in parallel and also add an unconditional second workflow page without defining deduplication/escalation ownership. Retain a tested fallback path. Workflow Automation availability and commercial entitlement must be confirmed for the customer's Datadog site.

## Required intake and routing

Maintain an approved monitor-to-service mapping: Datadog organization/site and monitor ID, OCI tenancy and region, support user group, product/category/subcategory, resource OCID or a reliable inventory reference, owning team/runbook and a severity rule justified by business impact. Validate the mapping against real portal routing before unattended creation. The observed OpenSearch fine-category mismatch is still a release limitation.

Collect alert cycle/start time, group/scope, state/priority, monitor URL/query, service/environment, a bounded recent log window, related metrics, last known resource lifecycle, request IDs and diagnostic errors. Keep evidence source/time. Read-only failures become explicit missing evidence; never interpret a 404 as deletion. A monitor priority such as P1 is not automatically Oracle HIGHEST. Critical outage/contact commitments must come from an approved operational policy or a responsible person.

If essential impact or routing data is absent, persist AWAITING_CONTEXT and page the on-call team with a draft. Do not invent impact, OCIDs or internal taxonomy fields to force automatic creation. A recovered monitor may append a recovery note to the same SR under policy; it must not automatically close a production SR just because one metric recovered.

## Delivery and duplicate prevention

- Authenticate the Datadog-to-Gateway call using approved headers and an authorizer; Datadog's generic webhook does not automatically produce OCI API request signatures. Validate body size, expected sender scope and allowed monitor/resource mappings. Do not put keys in URLs or payload logs.
- For generic webhooks, a deduplication key can combine the trusted Datadog organization, `$ALERT_ID`, `$ALERT_CYCLE_KEY` and the alert group/scope. A renotification in the same cycle updates the same operation; a new incident cycle can create a new SR. Define grouping explicitly to avoid one SR for every host in the same outage.
- Persist an operation intent before CreateIncident and atomically claim it. On a timeout, mark UNCERTAIN and reconcile List/Get using a correlation marker in the submitted description before any retry. `opc-request-id` is correlation, not an idempotency key. The helper's local attempt files are insufficient across stateless Function instances; implement the shared registry before production.
- Use resource principals for scoped access to the registry/Vault and detached Function invocation as appropriate. For Support Management, start with a dedicated, provisioned support user and signing key in Vault; resource-principal creation of SRs has not been validated here. Validate the support account/group with that exact runtime principal before enabling writes.
- Share only relevant, redacted diagnostics with Oracle. Store oversized logs as approved evidence and use PutAttachment when authorized, or attach a filtered summary. The initial SR description remains limited to the current contract; keep detailed evidence in notes/attachments.
- Record operation latency, duplicate suppression, missing mappings, authorization failures, creation failures, reconciliation age and successful final GET. Alert on the automation itself. Test cold starts, 429/5xx, timeouts after acceptance, renotify, recovery, malformed bodies and invalid OCIDs before enabling critical monitors.

## Proposed acceptance test

Use a selected nonproduction monitor with a genuine controlled test case and explicit create/update/close authorization. Confirm one new SR per intended cycle, correct portal product and category, resource/evidence completeness, a verified SR link in the on-call event, and a page on creation failure. Measure alert-to-SR and alert-to-page P50/P95, plus on-call manual time. Do not claim this integration is live based only on the interactive 32-second API demo.
