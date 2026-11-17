# Evidence and API history

For billing/lifecycle investigations retain resource OCID, service, region, original usage interval, currency, SKU, and observed cost. Use half-open UTC intervals and distinguish usage cost from an invoiced amount or a promised credit. Confirm pagination. A zero/empty response is not proof of termination. Never infer deletion from a console error or ongoing cost from an old email alone.

Collect the resource GET's `opc-request-id`, UTC time, and full service error code. These are useful to Support even when the resource cannot be opened. Do not repeat a DELETE just to reproduce an access error. For a stopped database, ask Support to distinguish storage retained by design, backup retention, missing privileges, unsuccessful termination, and orphaned artifacts. State hypotheses as hypotheses.

## Timeline: distinguish three milestones

- **2020-04-28:** Oracle announced the Support Management REST service. This establishes the general API, not a precise technical-SR launch date. API version `20181231` is a contract version, not proof of a December 2018 public launch. [Oracle release note](https://docs.oracle.com/en-us/iaas/releasenotes/changes/b658c0ef-daa7-462b-b792-06607dc60110/index.htm)
- **2023-09-05:** Official Python SDK **2.112.0** explicitly added creation of `TECH`, `LIMIT`, and `ACCOUNT` support requests. This is direct published evidence that technical SR creation was supported by that date. CLI **3.33.0** on the same date changed the endpoint and moved incident commands to their current parent group. Avoid claiming the exact backend GA date without a release announcement specifically stating it. [SDK changelog](https://github.com/oracle/oci-python-sdk/blob/master/CHANGELOG.rst), [CLI changelog](https://github.com/oracle/oci-cli/blob/master/CHANGELOG.rst)
- **2024-11-19:** SDK/CLI/API migration support for My Oracle Cloud Support and user-group-based access was announced. This is a migration milestone, not the original TECH creation launch. [Oracle release note](https://docs.oracle.com/en-us/iaas/releasenotes/support/sdk-cli-api-my-oracle-cloud-support-migration.htm)
- **2025-08-19:** CLI/API support for technical SR file attachments. [Oracle release note](https://docs.oracle.com/en-us/iaas/releasenotes/support/attach-cli-api.htm)
- **2026-06-02:** Python SDK **2.177.0** removed CSI parameters from support models. Check newer contracts before using old examples. [SDK changelog](https://github.com/oracle/oci-python-sdk/blob/master/CHANGELOG.rst)

History checked on 2026-11-16; recheck current docs when revising the integration.
