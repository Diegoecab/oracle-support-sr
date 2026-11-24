# Readable SR correspondence

The observed My Oracle Support portal interpreted correspondence as HTML and collapsed bare newlines. `comment` and `close` now use `--text-format readable` by default. Write the source note as text with blank paragraphs, `##` section titles and `- ` bullets. The helper emits escaped `<p>`, `<br>`, `<strong>`, `<ul>` and `<li>` elements. It treats log content and embedded HTML as text, never as markup to execute. It does not implement general Markdown, tables or arbitrary rich HTML.

Suggested note:

```text
Hi Support,

## Summary
- Current symptom and impact.
- What changed since the previous update.

## Evidence
Operation: GetResource
UTC: actual test time
Result: actual status and code
Request ID: exact correlation ID

## Requested action
Specific investigation or supported remediation requested from Oracle.
```

Preview without credentials or a network request:

```text
python scripts/run_sr.py --profile PROFILE --evidence-dir ./evidence comment --key SR_KEY --text-file update.txt --expected-tenancy TENANCY_OCID
```

The draft JSON contains the actual HTML that would be sent. After the already-authorized submission, re-read the case and verify the expected note and its CUSTOMER author. HTML may be normalized by the portal, so compare visible text if the serialized strings differ. API retrieval proves acceptance and storage; claim visual rendering only after inspecting the portal. `--text-format verbatim` preserves the exact input for an explicitly chosen existing contract; it bypasses the escaping formatter.

For a closing note, the observed API added its own close-reason prefix before the submitted HTML while preserving the complete approved body. Do not retry a successful close because the entire activity string differs from the submitted string. Confirm the approved content within the CUSTOMER activity and check the final lifecycle state with GetIncident. Record the prefix or normalization separately; a stored note alone does not establish CLOSED.

Use the [supported comment workflow](https://docs.oracle.com/en-us/iaas/Content/GSG/support/update-incident-add-comment.htm) and [UpdateActivityItemDetails model](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/cims/models/oci.cims.models.UpdateActivityItemDetails.html). The limited HTML convention is based on the observed portal, not a separately documented rich-text schema. No public edit/delete-correspondence operation was found in the reviewed client. If a previous note needs a readable replacement, append a clearly labeled summary only when requested; preserve the original audit trail.
