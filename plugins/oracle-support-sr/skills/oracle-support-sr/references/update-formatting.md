# Readable SR correspondence

Author every new title, description, impact narrative, note and attachment description in English, regardless of conversation language. Preserve identifiers, resource names, exact catalog labels and original diagnostics. Check language before sending; the helper does not translate or reliably detect language. Existing retrieved fields remain literal, even when historical text is not English.

Write in the customer's own voice, addressing Oracle Support directly. Use "we/our" or "I/my", not "the customer requests/reports" or "on behalf of the customer" when referring to the requester. This does not prohibit a factual business-impact statement about the customer's own end users, such as "Our customers cannot complete checkout". Keep chat sessions, AI/assistant identity, approval procedures, local cleanup and other internal coordination out of the SR. Preserve original diagnostic excerpts and attribute Oracle's findings accurately; first-person voice is not permission to invent observations, signatures, commitments or a resolution.

For example, a diagnostic note can say: "We have attached the AWR report for the affected period. We are still experiencing slow response times. Please review the report and advise on the next steps." Use each sentence only when supported by the actual evidence.

For a user-authorized closure where a new SR is planned and resolution is not confirmed: "Please close this service request. We will continue the investigation in a new SR." Do not mention a new chat session or claim that the issue was resolved. For a confirmed resolution: "We have verified that the issue is resolved. Please close this service request." These are drafting examples, not authorization to close a case; mandatory exact-draft approval still applies.

After each operation, show the full case card on screen, not only evidence links: exact title and full description, type/severity/impact, status, resource context, requested classification with its catalog keys, returned classification separately, attachment state and the exact outgoing update. Label absent verification NOT_VERIFIED beside product/category. A create echo or catalog match does not prove the persisted portal category or Oracle internal queue.


The observed My Oracle Support portal interpreted correspondence as HTML and collapsed bare newlines. `comment` and `close` now use `--text-format readable` by default. For longer diagnostic updates, write source text with blank paragraphs, optional `##` section titles and `- ` bullets. Short replies and closing requests can remain one or two natural sentences. The helper emits escaped `<p>`, `<br>`, `<strong>`, `<ul>` and `<li>` elements. It treats log content and embedded HTML as text, never as markup to execute. It does not implement general Markdown, tables or arbitrary rich HTML.

Suggested note:

```text
Hi Support,

## Summary
- We are experiencing [observed symptom and confirmed impact].
- Since our previous update, we have [verified action or result].

## Evidence
Operation: GetResource
UTC: actual test time
Result: actual status and code
Request ID: exact correlation ID

## Requested action
Please investigate [specific open question] and advise on the supported next steps.
```

Preview without credentials or a network request:

```text
python scripts/run_sr.py --profile PROFILE --evidence-dir ./evidence comment --key SR_KEY --text-file update.txt --expected-tenancy TENANCY_OCID
```

The draft JSON contains the actual HTML that would be sent. After the already-authorized submission, re-read the case and verify the expected note and its CUSTOMER author. HTML may be normalized by the portal, so compare visible text if the serialized strings differ. API retrieval proves acceptance and storage; claim visual rendering only after inspecting the portal. `--text-format verbatim` preserves the exact input for an explicitly chosen existing contract; it bypasses the escaping formatter.

For a closing note, the observed API added its own close-reason prefix before the submitted HTML while preserving the complete approved body. Do not retry a successful close because the entire activity string differs from the submitted string. Confirm the approved content within the CUSTOMER activity and check the final lifecycle state with GetIncident. Record the prefix or normalization separately; a stored note alone does not establish CLOSED.

Use the [supported comment workflow](https://docs.oracle.com/en-us/iaas/Content/GSG/support/update-incident-add-comment.htm) and [UpdateActivityItemDetails model](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/cims/models/oci.cims.models.UpdateActivityItemDetails.html). The limited HTML convention is based on the observed portal, not a separately documented rich-text schema. No public edit/delete-correspondence operation was found in the reviewed client. If a previous note needs a readable replacement, append a clearly labeled summary only when requested; preserve the original audit trail.
