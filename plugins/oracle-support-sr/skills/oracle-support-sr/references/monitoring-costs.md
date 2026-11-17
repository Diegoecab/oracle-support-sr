# Costing the OCI monitor

Reference rates checked 2026-11-17 in [Oracle's public USD price catalog](https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/) (catalog updated 2026-11-02). Recheck current rates and the tenancy's remaining allowances before presenting a binding estimate. Model execution duration, retention, recipients, metrics, and image storage explicitly; no live Function runtime benchmark exists yet.

## Units and baseline

- One Function checks one watched SR every 5 minutes, 30-day month: 8,640 invocations. Twelve staggered hourly schedules invoke the same Function, not twelve resident compute instances. A single hourly schedule gives 720 invocations.
- Illustrative sizing: 0.5 GB memory, 10 billed seconds per execution, no provisioned concurrency. That is 43,200 GB-seconds/month. Duration includes network waits and initialization insofar as billed; replace with measured values.
- Illustrative monthly ancillary use: 1 GB persistent state/evidence, 1 GB retained container images, 0.1 GB logs, six Object Storage operations per SR check, 100 notification events sent to one email and one HTTPS destination, 10 custom metric points per check and the same number retrieved. Include retries and a retention lifecycle when validating actual consumption.
- Keep account allowances shared, not per SR, Function, application, or schedule. Model both remaining allowance and fully consumed allowance scenarios. Count notification deliveries per recipient, not just change events.

## Current rates and SKUs

| Component | Public USD rate after free band | Monthly free band / condition |
| --- | --- | --- |
| Functions invocation B90618 | 0.20 / million | 2 million invocations |
| Functions execution B90617 | 0.1417 / 10,000 GB-seconds | 400,000 GB-seconds |
| Object Storage B91628 | 0.0255 / GB-month | First 10 GB in catalog |
| Object operations B91627 | 0.0034 / 10,000 requests | First 50,000 requests |
| Container Registry | Storage at Object Storage standard rate | No separate registry-service fee; include image bytes and pull/build activity. |
| Logging B92593 | 0.05 / GB-month | First 10 GB |
| Notifications email B90941 | 0.02 / 1,000 deliveries | First 1,000 |
| Notifications HTTPS B90940 | 0.60 / million deliveries | First 1 million |
| Monitoring ingestion B90925 | 0.0025 / million points | First 500 million |
| Monitoring retrieval B90926 | 0.0015 / million points | First 1 billion |
| Vault secrets + software-protected key in standard vault | No priced secret SKU; software keys free | Stay within available secret quotas; avoid confusing standard vault with dedicated Virtual Private Vault. |
| Resource Scheduler | Modeled 0 | No separate scheduler SKU was found in public price catalog/list; this is a pricing assumption, not an explicit contractual no-fee guarantee. |

Source details: [Functions](https://www.oracle.com/cloud/cloud-native/functions/), [Notifications FAQ](https://www.oracle.com/cloud/cloud-native/notifications/faq/), [Registry](https://www.oracle.com/cloud/cloud-native/container-registry/), [Vault allowances](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm).

For networking use the same region, OCI service access where supported and appropriate outbound connectivity. Do not assume CIMS is reachable through a service gateway until tested. VCN has no service fee and same-region public OCI service access has no transfer fee according to the [VCN FAQ](https://www.oracle.com/cloud/networking/virtual-cloud-network/faq/). No dedicated network appliance, API Gateway, load balancer, NAT hourly fee, or provisioned concurrency is included in this minimal model; gateway no-fee treatment follows absence of a priced gateway SKU and requires confirmation for the deployed topology. External egress, cross-region data, and added appliances must be costed if used.

## Formulas and alternatives

`checks = days * 24 * 60 / interval_minutes`; `GB_seconds = checks * billed_seconds * memory_GB`. For a priced band use the amount above the remaining monthly allowance, respecting the SKU's metric unit. No rounding to whole 10,000-request or million-invocation blocks is assumed in the arithmetic; invoice rounding/contract minimums may differ.

For the illustrative baseline, variable-band allowances available yield approximately zero variable cost; Object operations marginally exceed 50,000 with six operations/check. Container-image allowance eligibility can vary, so retain a small image-storage allowance. With all priced variable bands consumed, expected modeled services total well below USD 1/month at the stated 10-second runtime. This is a scenario, not an invoice quote or measured bill.

Cron itself has no license charge. On an already operating runner the incremental scheduling infrastructure may be near zero, though capacity and maintenance still matter. For a new dedicated OCI A1 VM, a reference 1 OCPU + 6 GB RAM costs `(0.01 + 6*0.0015)*720 = 13.68 USD/month` before free compute allowance; add 50 GB balanced boot volume `(0.0255 + 10*0.0017)*50 = 2.125`, total 15.805. A1 capacity/quotas and Always Free availability are not guaranteed. If cron invokes the Function, add its cost; if the VM runs the poller directly, avoid counting Function execution again.

The estimate covers incremental OCI infrastructure, not implementation labor, ongoing administration, taxes, negotiated contract changes, Slack/PagerDuty licenses, LLM summarization, or AWS paid support plans. Deterministic change detection requires no LLM. Clearly disclose these scope boundaries when asked for total cost.
