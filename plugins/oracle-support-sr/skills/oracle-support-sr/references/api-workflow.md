# API workflow and client differences

Since 0.4.0, MANUAL is the default execution mode. The helper emits an `approval_digest` with the offline draft and requires the same `--approval-digest` plus `--execute` after actual user approval. Explicitly authorized AUTO uses global `--mode AUTO` and still requires `--execute`. All command examples below are subject to that mode policy; direct SDK/CLI calls must not bypass it. Read [modes-and-intake.md](modes-and-intake.md). Essential missing facts are resolved from authorized evidence or asked, in both modes; they are never invented.

Authoritative references, checked 2026-11-16:

- [Create a support request](https://docs.oracle.com/en-us/iaas/Content/GSG/support/create-incident.htm)
- [Validate a user](https://docs.oracle.com/en-us/iaas/Content/GSG/support/validate-user.htm)
- [Python IncidentClient](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/cims/client/oci.cims.IncidentClient.html)
- [CLI create](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/support/incident/create.html)
- [List product taxonomy](https://docs.oracle.com/en-us/iaas/Content/GSG/support/list-incident-resource-types-taxonomy.htm)
- [Attach a file](https://docs.oracle.com/en-us/iaas/Content/GSG/support/update-incident-add-attachment.htm)

## Authentication and versions

Use the user's local OCI config and signing key through `oci.config.from_file(profile_name=...)` or `oci --profile ...`. Do not copy keys into a skill or report. `ocid` in support operation parameters is the acting **user** OCID, distinct from tenancy/resource OCIDs. Use the tenancy's home region for support. When the identity belongs to a nondefault identity domain, discover and pass the correct `domainid`; do not invent a domain ID or use a bearer-token workaround.

Record `oci --version` and `oci.__version__`. The 2026 SDK removed `csi` from CreateIncident and other support models; the CLI removed `--csi`. Older installed versions can still mark CSI required even though current service documentation says it is optional. Prefer upgrading in an isolated environment. If using an older CLI, supply a genuine CSI only when verified; do not use a group ID as CSI. The helper accepts `--legacy-csi` for this purpose. It refuses a legacy CLI write without it when that CLI requires CSI. SDK models that retain the old field can omit it if the actual service supports omission. Verify the live result.

The general guide may lag the command reference or retain a `--csi` example. Check the installed help and current official client contract instead of copying obsolete flags.

## Canonical create JSON

Read [fields-and-intake.md](fields-and-intake.md) when explaining required/optional fields, `MEDIUM` versus numeric severity, or how an agent gathers creation data. It separates service contracts, this helper's stricter checks, and diagnostic evidence.

```json
{
  "compartmentId": "ocid1.tenancy...",
  "problemType": "TECH",
  "userGroupId": "VALIDATED_SUPPORT_GROUP_ID",
  "ticket": {
    "severity": "MEDIUM",
    "title": "Brief symptom and affected service",
    "description": "Current evidence, impact, UTC timestamp, request IDs, and desired resolution."
  }
}
```

Keep the initial description at or below 1500 characters for current service compatibility; put extended diagnostics in a follow-up note or attachment. `TECH` is a technical investigation; `ACCOUNT` is billing. A case involving an inaccessible resource and ongoing charges can start as TECH to investigate lifecycle/access, with financial remediation referred to billing as appropriate. Do not claim automatic credits.

Since plugin 0.3.0, executing a TECH create also requires a customer-local VERIFIED `--routing-file` and a successful match against fresh taxonomy. See [routing-validation.md](routing-validation.md). This is a helper safeguard, not a newly invented Oracle API field. Drafts still work without it. Do not bypass a blocked route using a raw CLI/SDK call. A previous successful unclassified pilot is historical evidence, not authorization to create production cases with unknown routing.

The helper SDK backend maps this JSON to typed models. Optional nested `resourceList` uses `CreateResourceDetails` and `CreateItemDetails`; discover all category keys from live TAXONOMY responses. Its `region` body field accepted the region key `IAD`, while `us-ashburn-1` caused HTTP 400 in the live test. Resolve keys using Identity ListRegions. Structured classification still needs case-side verification: the tested OpenSearch product was correct but the requested Backup and Restore subcategory did not match the portal category. See fields-and-intake.md before relying on this path. CLI `oci support incident create` flattens title/severity/description and does **not** expose the full ticket's resourceList/contextualData. The helper refuses silently dropping those SDK-only fields. Use SDK for structured classification, or explicitly choose `oci raw-request` with the current documented REST contract and a canonical JSON body. Identify this as a raw CLI REST test, not the flattened create command.

For CLI use `--from-json file://...` with the CLI's own flat schema. Do not pass the SDK's nested ticket JSON to that flag. `--generate-full-command-json-input` creates a local skeleton; it does not test live SR creation.

## Follow-up and closure

The wire shape for a note is:

```json
{
  "ticket": {
    "resource": {
      "item": {
        "type": "activity",
        "activityType": "NOTES",
        "comments": "Evidence and request IDs"
      }
    }
  }
}
```

Use helper `comment --key KEY --text-file note.txt`, then `--execute` when authorized. CLI equivalent is `oci support incident update --incident-key KEY --compartment-id TENANCY --problem-type TECH --type activity --activity-type NOTES --comments TEXT --force` plus profile/user/home-region flags. `--force` only suppresses CLI interaction; it does not supply user authorization.

The current general comment guide shows `activityType UPDATE`, while the helper's installed/tested SDK contract and successful live notes use `NOTES`. Preserve the verified typed contract instead of copying an incompatible enum blindly. Comments and closing notes default to structured, escaped HTML for portal readability; see [update-formatting.md](update-formatting.md).

Use `close` only when the user explicitly requests closure, with a closing note and `--execute`. Closure uses activity type `CLOSE`, not infrastructure deletion. No SR deletion operation was found in the reviewed public client. The helper does not change severity or add contacts: for those, inspect current supported operations and preserve scope rather than inventing fields. The [Support Management deprecation notice](https://docs.oracle.com/en-us/iaas/Content/servicechanges.htm) says CreateIncident `contacts` has no functional value for public API usage and is scheduled for removal on May 20, 2027. Do not infer that a retained model field adds recipients; use a supported contact-management interface.

Attachments: helper `attach --key KEY --file evidence.txt --execute` sends that exact file with `PutAttachment`. The helper defaults to a restricted attachment. Inspect content first; never upload a config, PEM/private key, unredacted HAR, or unrelated mailbox export. The Console's creation-time attachment limit is not proof of the separate API's size limit. Check the current attachment documentation/service response. Deleting attachments requires My Oracle Cloud Support according to current documentation; do not assume an API deletion method exists.

## Failure interpretation

- 400: record validation error; correct the draft rather than retrying unchanged.
- 401: verify profile, key registration, clock, and signing configuration without printing secrets.
- 403/support-invalid user: verify support registration and support-group privileges; IAM admin access alone is insufficient.
- 404: check SR key, tenancy, group visibility, region, and acting identity. Resource GET 404 may mean missing privilege or absence.
- 429/5xx/timeout on a write: mark outcome uncertain; use reads to reconcile before any resubmission.
- Missing SDK/CLI: prepare the concrete draft and provide the missing dependency; do not call the live path tested.

Read operations may be retried with normal bounded backoff when appropriate. A pending local write receipt must be reconciled by inspecting the service, then archived/annotated deliberately before retrying; never delete it automatically.
