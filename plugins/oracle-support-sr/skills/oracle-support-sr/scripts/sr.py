#!/usr/bin/env python3
"""Portable OCI Support helper. MANUAL is default; writes require explicit execution."""
import argparse
import datetime as dt
import hashlib
from html import escape
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from presentation import render_markdown

ROUTING_TEST_NOTICE = 'Customer-authorized API routing validation; no production incident or infrastructure action is requested.'
# Conservative drafting budget, not a documented universal Oracle maximum.
# Reject locally before approval or credentials; never silently truncate text.
TITLE_MAX_LENGTH = 80
WRITE_REVIEW_RULES = {'create': None, 'test-create': None, 'comment': None, 'attach': None, 'close': 'CASE_CLOSURE'}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def literal_report(record):
    """Select original field values for display, without translation or fallback.

    Keep provenance separate: a draft, write response and retrieved case are
    different sources. This view never certifies persistence or routing.
    """
    cached = record.get('reused_receipt') is True
    source = record.get('result', {}) if cached else record
    draft = source.get('state') == 'draft_only'
    data = source.get('payload' if draft else 'data')
    data = data if isinstance(data, dict) else {}
    execution_keys = ('operation', 'profile', 'backend', 'state', 'mode',
                      'requested_mode', 'mandatory_review_reason',
                      'approval_required', 'status', 'execution_mode',
                      'requested_execution_mode', 'at_utc', 'write_state',
                      'error_type', 'message')
    execution = {k: source[k] for k in execution_keys if k in source}
    execution['source'] = ('CACHED_RECEIPT' if cached else 'DRAFT_PAYLOAD' if draft
                           else 'GET_RESPONSE' if source.get('operation') == 'get'
                           else 'API_RESPONSE')
    if draft and source.get('key') is not None:
        execution['target_key'] = source['key']
    elif source.get('target_key') is not None:
        execution['target_key'] = source['target_key']
    fields = {k: data[k] for k in ('id', 'key', 'problemType', 'problem_type', 'problem-type') if k in data}
    ticket = data.get('ticket')
    if isinstance(ticket, dict):
        # Preserve field names/values, excluding the entire correspondence
        # history from the compact view. The original response remains intact.
        fields['ticket'] = dict(ticket) if draft else {
            k: v for k, v in ticket.items()
            if k not in ('resourceList', 'resource_list', 'resource-list')
        }
        if not draft:
            for name in ('resourceList', 'resource_list', 'resource-list'):
                resources = ticket.get(name)
                if isinstance(resources, list):
                    structured = [r for r in resources if isinstance(r, dict)
                                  and isinstance(r.get('item'), dict)
                                  and r['item'].get('type') != 'activity']
                    if structured:
                        fields['ticket'][name] = structured
    report = {'execution': execution, 'sr_fields': fields}
    if draft and source.get('operation') == 'attach':
        report['outgoing_attachment'] = data
    if isinstance(source.get('routing'), dict):
        report['classification_evidence'] = source['routing']
    return report


def save_report_artifacts(record, evidence_dir, backend, operation, stamp=None):
    """Save readable and complete JSON views; does not change request data."""
    folder = Path(evidence_dir)
    folder.mkdir(parents=True, exist_ok=True)
    stamp = stamp or dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    raw = folder / f'{stamp}-{backend}-{operation}.json'
    readable = folder / f'{stamp}-{backend}-{operation}-report.md'
    record['user_report'] = literal_report(record)
    record['report_files'] = {'readable_markdown': str(readable), 'raw_json': str(raw)}
    record['user_report_markdown'] = render_markdown(record['user_report'], raw)
    readable.write_text(record['user_report_markdown'], encoding='utf-8')
    raw.write_text(json.dumps(record, indent=2, ensure_ascii=False, default=str), encoding='utf-8')


def emit_result(record, output_format='json', stream=None):
    stream = stream or sys.stdout
    if output_format == 'readable' and record.get('user_report_markdown'):
        if callable(getattr(stream, 'reconfigure', None)):
            stream.reconfigure(encoding='utf-8')
        text = record['user_report_markdown']
        stream.write(text if text.endswith('\n') else text + '\n')
    else:
        print(json.dumps(record, indent=2, ensure_ascii=True, default=str), file=stream)


def approval_preview(args, payload):
    """Bind confirmation to the action, account selectors and exact outgoing data.

    This detects a changed draft. The calling assistant must obtain real user
    approval; knowing this digest alone does not prove human consent.
    """
    if args.operation not in WRITE_REVIEW_RULES:
        raise ValueError('Write operation has no reviewed risk policy; no write permitted')
    scope = {
        'operation': args.operation, 'key': getattr(args, 'key', None),
        'expected_tenancy': args.expected_tenancy, 'profile': args.profile,
        'config_file': str(Path(args.config_file).expanduser().resolve()),
        'region': args.region, 'domain_id': args.domain_id,
        'backend': args.backend, 'problem_type': args.problem_type,
        'legacy_csi': args.legacy_csi, 'payload': payload,
    }
    review_reason = WRITE_REVIEW_RULES[args.operation]
    if getattr(args, 'routing_file', None):
        scope['routing_sha256'] = hashlib.sha256(Path(args.routing_file).read_bytes()).hexdigest()
    if getattr(args, 'test_plan_file', None):
        scope['test_plan_sha256'] = hashlib.sha256(Path(args.test_plan_file).read_bytes()).hexdigest()
    digest = hashlib.sha256(canonical(scope).encode('utf-8')).hexdigest()
    effective_mode = 'MANUAL' if review_reason else args.mode
    return {'state': 'draft_only', 'mode': effective_mode,
            'requested_mode': args.mode, 'mandatory_review_reason': review_reason,
            'approval_required': effective_mode == 'MANUAL',
            'approval_digest': digest, **scope}


class ApprovalRequired(ValueError):
    def __init__(self, message, preview, evidence_dir=None, output_format='json'):
        super().__init__(message)
        self.output_format = output_format
        if evidence_dir is not None:
            save_report_artifacts(preview, evidence_dir, preview['backend'], preview['operation'])
        self.user_report = literal_report(preview)
        self.user_report_markdown = preview.get('user_report_markdown') or render_markdown(self.user_report)
        self.report_files = preview.get('report_files')


def format_note(text, mode='readable'):
    """Preserve structure in MOS, which renders note content as HTML."""
    if mode == 'verbatim':
        return text
    if mode != 'readable':
        raise ValueError('Unsupported note text format')
    lines = text.replace('\r\n', '\n').replace('\r', '\n').strip().split('\n')
    blocks, paragraph, bullets = [], [], []

    def flush():
        if paragraph:
            blocks.append('<p>' + '<br>'.join(escape(line, quote=False) for line in paragraph) + '</p>')
            paragraph.clear()
        if bullets:
            blocks.append('<ul>' + ''.join('<li>' + escape(line, quote=False) + '</li>' for line in bullets) + '</ul>')
            bullets.clear()

    for line in lines:
        line = line.strip()
        if not line:
            flush()
        elif re.match(r'^#{1,3}\s+\S', line):
            flush()
            blocks.append('<p><strong>' + escape(re.sub(r'^#{1,3}\s+', '', line), quote=False) + '</strong></p>')
        elif re.match(r'^[-*]\s+\S', line):
            if paragraph:
                flush()
            bullets.append(line[2:].strip())
        else:
            if bullets:
                flush()
            paragraph.append(line)
    flush()
    return '\n'.join(blocks)


def validate_request(data):
    if not isinstance(data, dict):
        raise ValueError('Request must be a JSON object')
    if not str(data.get('compartmentId', '')).startswith('ocid1.tenancy.'):
        raise ValueError('compartmentId must be a tenancy OCID')
    if data.get('problemType') not in ('TECH', 'ACCOUNT'):
        raise ValueError('This helper creates TECH or ACCOUNT cases only')
    if data['problemType'] == 'TECH' and not data.get('userGroupId'):
        raise ValueError('TECH requires an explicitly validated userGroupId in this helper')
    ticket = data.get('ticket', {})
    if not isinstance(ticket, dict):
        raise ValueError('ticket must be a JSON object')
    if ticket.get('severity') not in ('LOW', 'MEDIUM', 'HIGH', 'HIGHEST'):
        raise ValueError('Invalid severity')
    for field in ('title', 'description'):
        if not isinstance(ticket.get(field), str) or not ticket[field].strip():
            raise ValueError(f'ticket.{field} must be nonempty text')
    if len(ticket['title']) > TITLE_MAX_LENGTH:
        raise ValueError(f'Title exceeds the helper conservative {TITLE_MAX_LENGTH}-character drafting budget; shorten it without changing meaning before approval or submission (Oracle maximum is not established here)')
    if len(ticket['description']) > 1500:
        raise ValueError('Initial description exceeds 1500 characters; use a note/attachment')
    for resource in ticket.get('resourceList') or []:
        region = resource.get('region') if isinstance(resource, dict) else None
        if isinstance(region, str) and '-' in region:
            raise ValueError('resourceList.region expects an OCI region key (for example IAD), not a region name; resolve it with Identity ListRegions')
    return data


def flatten_taxonomy(groups):
    """Keep hierarchy and schema metadata, without inventing wire selectors."""
    rows = []
    def field(value, name):
        camel = re.sub(r'_([a-z])', lambda match: match[1].upper(), name)
        for key in (name, name.replace('_', '-'), camel):
            if key in value:
                return value[key]
        return None
    for group in groups or []:
        for group_key, group_label in (group.get('service') or {}).items():
            for service in group.get('services') or []:
                for service_key, service_label in (service.get('service') or {}).items():
                    for category in field(service, 'service_categories') or []:
                        for category_key, category_label in (field(category, 'service_category') or {}).items():
                            children = field(category, 'sub_categories') or [{}]
                            for child in children:
                                for sub_key, sub_label in (field(child, 'sub_category') or {None: None}).items():
                                    rows.append({'service_group_key': group_key, 'service_group_label': group_label, 'service_key': service_key, 'service_label': service_label, 'category_key': category_key, 'category_label': category_label, 'subcategory_key': sub_key, 'subcategory_label': sub_label, 'service_schema': service.get('schema'), 'category_schema': category.get('schema'), 'subcategory_schema': child.get('schema'), 'category_has_subcategory': field(category, 'has_sub_category')})
    return rows


def validate_routing(request, registry, catalog=None, now=None):
    """Validate selected TECH catalog routes. This cannot guarantee a backend queue."""
    status = registry.get('status')
    if registry.get('schema_version') != 1 or status not in ('VERIFIED', 'CATALOG_ONLY'):
        raise ValueError('Routing is not VERIFIED or an explicit CATALOG_ONLY first-use selection; keep a draft')
    if registry.get('known_mismatch') is True:
        raise ValueError('Known routing mismatch remains unresolved; no production SR created')
    if status == 'CATALOG_ONLY':
        previous = (registry.get('verification') or {}).get('observed_portal') or {}
        expected_previous = registry.get('expected_portal') or {}
        if previous and expected_previous and any(previous.get(k) != expected_previous.get(k) for k in ('product', 'category')):
            raise ValueError('Known routing mismatch cannot be relabeled as a first-use route')
    if registry.get('tenancy_ocid') != request['compartmentId'] or registry.get('user_group_id') != request.get('userGroupId'):
        raise ValueError('Routing registry tenancy/group does not match the request')
    now = now or dt.datetime.now(dt.timezone.utc)
    verification = (registry.get('verification') if status == 'VERIFIED' else registry.get('catalog_evidence')) or {}
    try:
        observed_at = dt.datetime.fromisoformat(verification['observed_at_utc' if status == 'VERIFIED' else 'captured_at_utc'].replace('Z', '+00:00'))
        valid_until = dt.datetime.fromisoformat(verification['valid_until_utc'].replace('Z', '+00:00'))
        valid = observed_at.tzinfo is not None and valid_until.tzinfo is not None and observed_at <= now < valid_until
        if status == 'CATALOG_ONLY':
            valid = valid and valid_until - observed_at <= dt.timedelta(hours=24) and verification.get('source') == 'ListIncidentResourceTypes/TAXONOMY'
    except (KeyError, ValueError, TypeError):
        valid = False
    if not valid:
        raise ValueError('Routing evidence is expired, future-dated or missing a timezone')
    expected = registry.get('expected_portal') or {}
    observed = verification.get('observed_portal') or {}
    if status == 'VERIFIED' and (not all(isinstance(expected.get(k), str) and expected[k].strip() and expected[k] == observed.get(k) for k in ('product', 'category')) or not verification.get('source')):
        raise ValueError('Routing portal product/category mismatch or missing verification source')
    if status == 'CATALOG_ONLY' and request['ticket'].get('contextualData') is not None:
        raise ValueError('First-use routing cannot invent a contextualData contract')
    resources = request['ticket'].get('resourceList') or []
    routes = registry.get('routes') or []
    if not resources or len(resources) != len(routes):
        raise ValueError('Every technical create resource requires a classified verified route')
    rows = flatten_taxonomy(catalog) if catalog is not None else None
    for resource, route in zip(resources, routes):
        item = resource.get('item') or {}
        actual = {'region_key': resource.get('region'), 'category_key': (item.get('category') or {}).get('categoryKey'), 'subcategory_key': (item.get('subCategory') or {}).get('subCategoryKey'), 'issue_type_key': (item.get('issueType') or {}).get('issueTypeKey')}
        if item.get('type') != 'tech' or not actual['region_key'] or not actual['category_key'] or any(actual[k] != route.get(k) for k in actual):
            raise ValueError('Request routing differs from the verified recipe')
        if actual['issue_type_key']:
            raise ValueError('This guard cannot validate issueTypeKey against the reviewed catalog; keep a draft')
        if str(route.get('category_has_subcategory', '')).strip().lower() == 'true' and not actual['subcategory_key']:
            raise ValueError('Selected category requires a subcategory; no SR created')
        if rows is not None:
            keys = ('service_group_key', 'service_group_label', 'service_key', 'service_label', 'category_key', 'category_label', 'subcategory_key', 'subcategory_label')
            matches = [row for row in rows if all(route.get(k) == row[k] for k in keys)]
            if not matches:
                raise ValueError('Verified route no longer matches the live taxonomy hierarchy/labels')
            metadata = ('service_schema', 'category_schema', 'subcategory_schema', 'category_has_subcategory')
            variants = {tuple(row[k] for k in metadata) for row in matches}
            if len(variants) != 1:
                raise ValueError('Ambiguous schema metadata for the selected live taxonomy route; no SR created')
            if not all(route.get(k) == matches[0][k] for k in metadata):
                raise ValueError('Verified route schema metadata is missing or changed; reverify the routing recipe')
    return expected


def validate_test_plan(request, plan, catalog=None, now=None):
    """A separately authorized LOW test can establish evidence for a new route.

    A candidate is never represented as a verified production recipe. This
    path accepts catalog keys only; it cannot infer a schema-to-wire mapping.
    """
    validate_request(request)
    if plan.get('schema_version') != 1 or plan.get('purpose') != 'ROUTING_VALIDATION' or plan.get('status') != 'CANDIDATE' or plan.get('production_use') is not False or type(plan.get('max_creations')) is not int or plan['max_creations'] != 1:
        raise ValueError('A routing test requires an explicit single-case CANDIDATE plan for nonproduction validation')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{7,79}', str(plan.get('test_id', ''))):
        raise ValueError('Routing test requires a stable test_id')
    if plan.get('tenancy_ocid') != request['compartmentId'] or plan.get('user_group_id') != request.get('userGroupId'):
        raise ValueError('Routing test tenancy/group does not match the request')
    now = now or dt.datetime.now(dt.timezone.utc)
    try:
        created = dt.datetime.fromisoformat(plan['created_at_utc'].replace('Z', '+00:00'))
        expires = dt.datetime.fromisoformat(plan['expires_at_utc'].replace('Z', '+00:00'))
        valid = created.tzinfo is not None and expires.tzinfo is not None and created <= now < expires and expires - created <= dt.timedelta(hours=24)
    except (KeyError, TypeError, ValueError):
        valid = False
    if not valid:
        raise ValueError('Routing test plan must be current and expire within 24 hours')
    ticket = request['ticket']
    if request['problemType'] != 'TECH' or ticket['severity'] != 'LOW' or not ticket['title'].startswith('[ROUTING TEST] ') or ROUTING_TEST_NOTICE not in ticket['description']:
        raise ValueError('Routing test requires TECH, LOW, a [ROUTING TEST] title and the explicit validation notice')
    if set(request) - {'compartmentId', 'problemType', 'userGroupId', 'ticket'} or set(ticket) - {'severity', 'title', 'description', 'resourceList'}:
        raise ValueError('Routing test cannot add contextualData, contacts or other unreviewed fields')
    resources, routes = ticket.get('resourceList') or [], plan.get('routes') or []
    if len(resources) != 1 or len(routes) != 1:
        raise ValueError('Routing test supports exactly one resource/route')
    resource, route = resources[0], routes[0]
    item = resource.get('item') or {}
    if set(resource) - {'region', 'item'} or set(item) - {'type', 'category', 'subCategory'}:
        raise ValueError('Routing test only supports catalog category/subcategory keys; no guessed issueTypeKey')
    if set(item.get('category') or {}) != {'categoryKey'} or (item.get('subCategory') is not None and set(item['subCategory']) != {'subCategoryKey'}):
        raise ValueError('Routing test contains unsupported category fields')
    actual = {'region_key': resource.get('region'), 'category_key': (item.get('category') or {}).get('categoryKey'), 'subcategory_key': (item.get('subCategory') or {}).get('subCategoryKey')}
    if item.get('type') != 'tech' or not actual['region_key'] or not actual['category_key'] or any(actual[k] != route.get(k) for k in actual):
        raise ValueError('Routing test request differs from its candidate route')
    if str(route.get('category_has_subcategory', '')).strip().lower() == 'true' and not actual['subcategory_key']:
        raise ValueError('Routing test category requires a subcategory')
    expected = plan.get('expected_portal') or {}
    if not all(isinstance(expected.get(k), str) and expected[k].strip() for k in ('product', 'category')) or expected['category'] != (route.get('subcategory_label') or route.get('category_label')):
        raise ValueError('Routing test requires an explicit expected product/category matching the selected catalog label')
    if catalog is not None:
        keys = ('service_group_key', 'service_group_label', 'service_key', 'service_label', 'category_key', 'category_label', 'subcategory_key', 'subcategory_label')
        metadata = ('service_schema', 'category_schema', 'subcategory_schema', 'category_has_subcategory')
        matches = [row for row in flatten_taxonomy(catalog) if all(route.get(k) == row[k] for k in keys)]
        if not matches or len({tuple(row[k] for k in metadata) for row in matches}) != 1 or any(route.get(k) != matches[0][k] for k in metadata):
            raise ValueError('Routing test candidate no longer matches the complete live taxonomy route/schemas')
    return expected


def begin_attempt(directory, operation, payload, identity=None):
    """An exclusive local receipt blocks duplicate or uncertain write retries."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(canonical({'operation': operation, 'payload': payload}).encode()).hexdigest()
    identity_digest = hashlib.sha256(canonical(identity).encode()).hexdigest() if identity is not None else digest
    path = directory / (identity_digest + '.json')
    record = {'operation': operation, 'payload_sha256': digest, 'state': 'pending', 'at_utc': dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        with path.open('x', encoding='utf-8') as output:
            json.dump(record, output, indent=2)
    except FileExistsError:
        previous = json.loads(path.read_text(encoding='utf-8'))
        if previous['payload_sha256'] != digest:
            raise RuntimeError('This test_id already reserved a different request; reconcile the existing SR instead of creating another')
        if previous['state'] == 'success':
            return path, previous, False
        raise RuntimeError(f'Existing {previous["state"]} attempt at {path}; reconcile with Oracle before retrying')
    return path, record, True


def finish_attempt(path, record, result):
    status = result.get('status')
    if isinstance(status, int) and 200 <= status < 300:
        data = result.get('data')
        if record['operation'] not in ('create', 'test-create') or (isinstance(data, dict) and data.get('key')):
            record['state'] = 'success'
        else:
            record['state'] = 'uncertain'
    elif isinstance(status, int) and 400 <= status < 500 and status not in (408, 429):
        record['state'] = 'rejected'
    else:
        record['state'] = 'uncertain'
    record['result'] = result
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(record, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    temp.replace(path)
    return record


def model_from_wire(oci, model_name, data):
    model_class = getattr(oci.cims.models, model_name)
    sample = model_class()
    reverse = {wire: attr for attr, wire in sample.attribute_map.items()}
    unknown = set(data) - set(reverse)
    if unknown:
        raise ValueError(f'Unsupported {model_name} fields: {sorted(unknown)}')
    values = {}
    for wire, value in data.items():
        attr = reverse[wire]
        kind = sample.swagger_types[attr]
        if value is not None and kind.startswith('list['):
            inner = kind[5:-1]
            value = [model_from_wire(oci, inner, item) if hasattr(oci.cims.models, inner) else item for item in value]
        elif value is not None and hasattr(oci.cims.models, kind):
            value = model_from_wire(oci, kind, value)
        values[attr] = value
    return model_class(**values)


class Support:
    def __init__(self, args):
        import oci
        self.oci, self.args = oci, args
        self.config = oci.config.from_file(file_location=args.config_file, profile_name=args.profile)
        self.tenancy = self.config['tenancy']
        self.region = args.region or self.config['region']
        cfg = dict(self.config, region=self.region)
        self.client = oci.cims.IncidentClient(cfg, timeout=(15, 60), retry_strategy=oci.retry.NoneRetryStrategy(), skip_deserialization=getattr(args, 'raw_response', False))
        self.identity = oci.identity.IdentityClient(cfg, timeout=(15, 45), retry_strategy=oci.retry.NoneRetryStrategy())
        self.common = {'ocid': self.config['user'], 'homeregion': self.region}
        if args.domain_id:
            self.common['domainid'] = args.domain_id

    def sdk(self, method, **kwargs):
        try:
            response = getattr(self.client, method)(**kwargs)
            return {'status': response.status, 'data': self.oci.util.to_dict(response.data), 'request_id': response.headers.get('opc-request-id'), 'next_page': response.headers.get('opc-next-page')}
        except self.oci.exceptions.ServiceError as exc:
            return {'status': exc.status, 'code': exc.code, 'message': exc.message, 'request_id': exc.request_id}
        except Exception as exc:
            return {'error_type': type(exc).__name__, 'message': str(exc)}

    def cli(self, command, params, mutation=False):
        executable = self.args.cli
        base = [executable, '--profile', self.args.profile, '--config-file', str(Path(self.args.config_file).expanduser()), '--region', self.region, '--connection-timeout', '15', '--read-timeout', '60', '--max-retries', '0']
        help_result = subprocess.run(base + command + ['--help'], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
        if help_result.returncode:
            raise RuntimeError(help_result.stderr or help_result.stdout)
        if mutation and command[-1] == 'create' and '--csi' in help_result.stdout and '[required]' in help_result.stdout.split('--csi', 1)[1].split('--severity', 1)[0]:
            if self.args.legacy_csi is None:
                raise ValueError('Installed CLI requires CSI. Upgrade or pass a verified --legacy-csi; never substitute a group ID')
        actual = dict(params)
        if self.args.legacy_csi is not None:
            if '--csi' not in help_result.stdout:
                raise ValueError('Installed CLI removed --csi; omit --legacy-csi')
            actual['csi'] = self.args.legacy_csi
        with tempfile.TemporaryDirectory(prefix='oracle-sr-') as work:
            path = Path(work) / 'input.json'
            path.write_text(json.dumps(actual, ensure_ascii=False), encoding='utf-8')
            args = base + command + ['--from-json', 'file://' + str(path)]
            if mutation and command[-1] == 'update':
                args.append('--force')
            try:
                proc = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=100)
            except subprocess.TimeoutExpired:
                return {'error_type': 'TimeoutExpired', 'message': 'CLI timed out; reconcile writes before retrying'}
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            parsed = {}
        if proc.returncode == 0:
            result = {'status': 200, 'data': parsed.get('data'), 'cli_exit_code': 0}
        else:
            # OCI CLI usually emits ServiceError JSON after a textual prefix.
            error = {}
            for stream in (proc.stderr, proc.stdout):
                begin = stream.find('{')
                if begin >= 0:
                    try:
                        error = json.loads(stream[begin:])
                        break
                    except json.JSONDecodeError:
                        pass
            result = {'status': error.get('status'), 'code': error.get('code'), 'message': error.get('message') or proc.stderr or proc.stdout, 'request_id': error.get('opc-request-id'), 'cli_exit_code': proc.returncode}
        # CLI exit 0 confirms command success; HTTP status is not exposed here.
        result['status_source'] = 'normalized_from_cli_exit' if proc.returncode == 0 else 'service_error_or_unknown'
        return result

    def call(self, operation, payload=None, key=None, file=None):
        if self.args.backend == 'sdk':
            common = dict(self.common)
            if operation == 'preflight':
                return self.sdk('validate_user', problem_type=self.args.problem_type, **common)
            if operation == 'taxonomy':
                return self.sdk('list_incident_resource_types', problem_type='TAXONOMY', compartment_id=self.tenancy, **common)
            if operation == 'list':
                items, pages, page = [], [], None
                while True:
                    kwargs = dict(compartment_id=self.tenancy, problem_type=self.args.problem_type, **common)
                    if page:
                        kwargs['page'] = page
                    result = self.sdk('list_incidents', **kwargs)
                    pages.append({k: v for k, v in result.items() if k != 'data'})
                    if result.get('status') != 200:
                        return dict(result, completed_pages=pages, partial_data=items)
                    items.extend(result['data'])
                    page = result.get('next_page')
                    if not page:
                        return {'status': 200, 'data': items, 'pages': pages, 'complete': True}
            if operation == 'get':
                return self.sdk('get_incident', incident_key=key, compartment_id=self.tenancy, problemtype=self.args.problem_type, **common)
            if operation == 'create':
                return self.sdk('create_incident', create_incident_details=model_from_wire(self.oci, 'CreateIncident', payload), **common)
            if operation in ('comment', 'close'):
                body = dict(payload, problemType=self.args.problem_type)
                return self.sdk('update_incident', incident_key=key, update_incident_details=model_from_wire(self.oci, 'UpdateIncident', body), compartment_id=self.tenancy, **common)
            if operation == 'attach':
                with Path(file).open('rb') as content:
                    return self.sdk('put_attachment', put_attachment_details=content, incident_key=key, compartment_id=self.tenancy, attachment_name=Path(file).name, problemtype=self.args.problem_type, is_restricted_flag=True, **common)
        common = {'ocid': self.config['user'], 'homeregion': self.region}
        if self.args.domain_id:
            common['domainid'] = self.args.domain_id
        if operation == 'preflight':
            return self.cli(['support', 'validation-response', 'validate-user'], dict(common, problemType=self.args.problem_type))
        if operation in ('list', 'taxonomy', 'get'):
            command = ['support', 'incident-resource-type' if operation == 'taxonomy' else 'incident', 'list' if operation != 'get' else 'get']
            params = dict(common, compartmentId=self.tenancy)
            params['problemType' if operation != 'get' else 'problemtype'] = 'TAXONOMY' if operation == 'taxonomy' else self.args.problem_type
            if operation == 'list':
                params['all'] = True
            if key:
                params['incidentKey'] = key
            return self.cli(command, params)
        if operation == 'create':
            extra = set(payload['ticket']) - {'title', 'severity', 'description'}
            top_extra = set(payload) - {'compartmentId', 'problemType', 'userGroupId', 'contacts', 'referrer', 'ticket'}
            if extra or top_extra:
                raise ValueError(f'Flattened CLI cannot preserve these fields: {sorted(extra | top_extra)}. Use SDK')
            params = {k: v for k, v in payload.items() if k != 'ticket'}
            params.update(payload['ticket'])
            params.update(common)
            return self.cli(['support', 'incident', 'create'], params, mutation=True)
        if operation in ('comment', 'close'):
            item = payload['ticket']['resource']['item']
            params = dict(common, compartmentId=self.tenancy, incidentKey=key, problemType=self.args.problem_type, activityType=item['activityType'], type='activity', comments=item['comments'])
            return self.cli(['support', 'incident', 'update'], params, mutation=True)
        if operation == 'attach':
            return self.cli(['support', 'incident', 'put-attachment'], dict(common, compartmentId=self.tenancy, incidentKey=key, problemtype=self.args.problem_type, file=str(Path(file).resolve()), isRestrictedFlag=True), mutation=True)
        raise ValueError('Unsupported operation')


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument('--profile', required=True)
    result.add_argument('--config-file', default='~/.oci/config')
    result.add_argument('--region', help='Support home region; defaults to profile region')
    result.add_argument('--domain-id')
    result.add_argument('--backend', choices=('cli', 'sdk'), default='sdk')
    result.add_argument('--output-format', choices=('json', 'readable'), default='json', help='Readable case card or compatible JSON stdout; complete JSON evidence is retained')
    result.add_argument('--raw-response', action='store_true', help='SDK reads only: preserve REST JSON field names and unmodeled response fields')
    result.add_argument('--cli', default='oci', help='CLI executable path')
    result.add_argument('--legacy-csi', help='Genuine verified CSI for a legacy CLI only')
    result.add_argument('--problem-type', choices=('TECH', 'ACCOUNT'), default='TECH')
    result.add_argument('--mode', type=str.upper, choices=('MANUAL', 'AUTO'), default='MANUAL', help='MANUAL requires approval of the exact draft; AUTO is only for an explicitly authorized workflow')
    result.add_argument('--evidence-dir', required=True)
    subs = result.add_subparsers(dest='operation', required=True)
    for name in ('preflight', 'list', 'taxonomy', 'get', 'create', 'test-create', 'comment', 'close', 'attach'):
        sub = subs.add_parser(name)
        if name in ('get', 'comment', 'close', 'attach'):
            sub.add_argument('--key', required=True)
        if name in ('comment', 'close'):
            sub.add_argument('--text-file', required=True)
            sub.add_argument('--text-format', choices=('readable', 'verbatim'), default='readable', help='Default: escaped paragraphs, headings and lists for MOS; verbatim preserves the exact supplied body')
        if name == 'attach':
            sub.add_argument('--file', required=True)
        if name in ('create', 'test-create'):
            sub.add_argument('--request-file', required=True)
        if name == 'create':
            sub.add_argument('--routing-file', help='VERIFIED route or explicit CATALOG_ONLY selection; both honor the chosen mode and must match fresh taxonomy')
        if name == 'test-create':
            sub.add_argument('--test-plan-file', required=True, help='Explicitly authorized, single-case LOW routing-validation plan; never a verified production route')
        if name == 'taxonomy':
            sub.add_argument('--catalog-file', help='Also save a flattened hierarchy for the agent; a catalog is not routing verification')
        if name in ('create', 'test-create', 'comment', 'close', 'attach'):
            sub.add_argument('--execute', action='store_true')
            sub.add_argument('--approval-digest', help='Digest of the exact draft approved by the user in MANUAL mode; supplied by the assistant after approval')
            sub.add_argument('--expected-tenancy', required=True)
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    creates = args.operation in ('create', 'test-create')
    mutation = creates or args.operation in ('comment', 'close', 'attach')
    if args.raw_response and (mutation or args.backend != 'sdk'):
        raise ValueError('--raw-response supports read-only SDK operations; no write sent')
    payload = None
    attachment_content = None
    test_plan = None
    if creates:
        payload = validate_request(json.loads(Path(args.request_file).read_text(encoding='utf-8-sig')))
        if payload['compartmentId'] != args.expected_tenancy:
            raise ValueError('Draft tenancy differs from expected tenancy')
        if args.operation == 'test-create':
            if args.backend != 'sdk':
                raise ValueError('Routing tests require SDK to preserve structured classification')
            test_plan = json.loads(Path(args.test_plan_file).read_text(encoding='utf-8-sig'))
            validate_test_plan(payload, test_plan)
    elif args.operation in ('comment', 'close'):
        text = Path(args.text_file).read_text(encoding='utf-8-sig')
        if not text.strip():
            raise ValueError('Empty update')
        text = format_note(text, args.text_format)
        payload = {'ticket': {'resource': {'item': {'type': 'activity', 'activityType': 'CLOSE' if args.operation == 'close' else 'NOTES', 'comments': text}}}}
    elif args.operation == 'attach':
        attachment_content = Path(args.file).read_bytes()
        if not attachment_content:
            raise ValueError('Empty attachment')
        payload = {'filename': Path(args.file).name, 'sha256': hashlib.sha256(attachment_content).hexdigest(), 'size': len(attachment_content)}
    preview = approval_preview(args, payload) if mutation else None
    if mutation:
        if not args.execute:
            save_report_artifacts(preview, args.evidence_dir, args.backend, args.operation)
            emit_result(preview, args.output_format)
            return 0
        if preview['approval_required'] and args.approval_digest != preview['approval_digest']:
            reason = preview.get('mandatory_review_reason') or 'DEFAULT_MANUAL'
            raise ApprovalRequired('MANUAL requires user approval of this exact draft and its --approval-digest (' + reason + '); missing or changed approval, no write sent', preview, args.evidence_dir, args.output_format)
    service = Support(args)
    if mutation and service.tenancy != args.expected_tenancy:
        raise ValueError('Profile tenancy differs from expected tenancy; no write sent')
    routing = None
    if mutation and args.operation == 'create' and payload['problemType'] == 'TECH':
        if not args.routing_file:
            raise ValueError('TECH creation requires --routing-file with a VERIFIED mapping or explicit CATALOG_ONLY first-use selection; draft retained, no SR created')
        routing = json.loads(Path(args.routing_file).read_text(encoding='utf-8-sig'))
        validate_routing(payload, routing)
    if mutation and args.backend == 'sdk':
        # Reject unsupported contracts before reserving a write receipt.
        if args.operation == 'attach' and not hasattr(service.client, 'put_attachment'):
            raise ValueError('Installed SDK has no PutAttachment; upgrade the official oci package')
        if creates:
            model_from_wire(service.oci, 'CreateIncident', payload)
        if args.operation in ('comment', 'close'):
            model_from_wire(service.oci, 'UpdateIncident', dict(payload, problemType=args.problem_type))
    if mutation and not creates:
        before = service.call('get', key=args.key)
        if before.get('status') != 200:
            raise ValueError('Cannot verify target SR before write: ' + canonical(before))
    if mutation and creates:
        validation = service.call('preflight')
        data = validation.get('data') or {}
        valid = data.get('is_valid_user', data.get('is-valid-user'))
        groups = data.get('write_permitted_user_group_infos', data.get('write-permitted-user-group-infos', [])) or []
        group_ids = {g.get('user_group_id', g.get('user-group-id')) for g in groups}
        if validation.get('status') != 200 or valid is not True:
            raise ValueError('Support user validation failed; no create sent')
        if payload['problemType'] != args.problem_type:
            raise ValueError('Request problemType differs from --problem-type')
        if args.problem_type == 'TECH' and payload['userGroupId'] not in group_ids:
            raise ValueError('Requested group does not grant create permission')
        if routing:
            catalog = service.call('taxonomy')
            if catalog.get('status') != 200 or catalog.get('next_page'):
                raise ValueError('Cannot validate a complete live taxonomy; no SR created')
            validate_routing(payload, routing, catalog['data'])
        if test_plan:
            catalog = service.call('taxonomy')
            if catalog.get('status') != 200 or catalog.get('next_page'):
                raise ValueError('Cannot verify the complete live taxonomy for this routing test; no SR created')
            validate_test_plan(payload, test_plan, catalog['data'])
    evidence = Path(args.evidence_dir)
    evidence.mkdir(parents=True, exist_ok=True)
    attempt = None
    if mutation:
        scope = {'tenancy': service.tenancy, 'region': service.region, 'key': getattr(args, 'key', None), 'payload': payload}
        test_identity = {'operation': 'test-create', 'tenancy': service.tenancy, 'test_id': test_plan['test_id']} if test_plan else None
        path, record, send = begin_attempt(evidence / 'attempts', args.operation, scope, identity=test_identity)
        if not send:
            reused = dict(record, reused_receipt=True)
            save_report_artifacts(reused, evidence, args.backend, args.operation)
            emit_result(reused, args.output_format)
            return 0
        attempt = path, record
    start = time.monotonic()
    try:
        if args.operation == 'attach':
            # Upload the same immutable bytes that were hashed and approved.
            with tempfile.TemporaryDirectory(prefix='oracle-sr-attachment-') as folder:
                snapshot = Path(folder) / payload['filename']
                snapshot.write_bytes(attachment_content)
                result = service.call(args.operation, payload=payload, key=args.key, file=str(snapshot))
        else:
            result = service.call('create' if test_plan else args.operation, payload=payload, key=getattr(args, 'key', None), file=getattr(args, 'file', None))
    except Exception as exc:
        result = {'error_type': type(exc).__name__, 'message': str(exc)}
    effective_mode = preview['mode'] if mutation else args.mode
    result.update(operation=args.operation, backend=args.backend, data_format='REST_JSON' if args.raw_response else ('SDK_MODEL' if args.backend == 'sdk' else 'CLI_JSON'), sdk_version=service.oci.__version__, profile=args.profile, region=service.region, execution_mode=effective_mode, requested_execution_mode=args.mode, at_utc=dt.datetime.now(dt.timezone.utc).isoformat(), elapsed_seconds=round(time.monotonic()-start, 3))
    if mutation:
        result['approval'] = {'mode': effective_mode, 'draft_sha256': preview['approval_digest'], 'policy': 'EXACT_DRAFT_CONFIRMATION' if effective_mode == 'MANUAL' else 'SCOPED_AUTO', 'mandatory_review_reason': preview.get('mandatory_review_reason')}
    if args.operation == 'taxonomy' and args.catalog_file and result.get('status') == 200:
        catalog_path = Path(args.catalog_file)
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_path.write_text(json.dumps({'catalog_schema_version': 2, 'tenancy_ocid': service.tenancy, 'captured_at_utc': result['at_utc'], 'routing_verified': False, 'routes': flatten_taxonomy(result['data'])}, indent=2, ensure_ascii=False), encoding='utf-8')
        result['catalog_file'] = str(catalog_path)
    if routing:
        result['routing'] = {'recipe': 'VERIFIED_AND_MATCHED_LIVE_CATALOG' if routing['status'] == 'VERIFIED' else 'FIRST_USE_MATCHED_LIVE_CATALOG', 'expected_portal': routing.get('expected_portal'), 'requested_selection': [{k: route.get(k) for k in ('service_group_label', 'service_label', 'category_label', 'subcategory_label')} for route in routing['routes']], 'persisted_classification': 'NOT_VERIFIED', 'current_case_assignment': 'NOT_VERIFIED'}
    if test_plan:
        result['routing'] = {'recipe': 'CANDIDATE_CONTROLLED_TEST', 'test_id': test_plan['test_id'], 'live_catalog_match': True, 'expected_portal': test_plan['expected_portal'], 'persisted_classification': 'NOT_VERIFIED', 'current_case_assignment': 'NOT_VERIFIED', 'production_recipe_created': False}
    if attempt:
        receipt = finish_attempt(*attempt, result)
        result['receipt'] = str(attempt[0])
        result['write_state'] = receipt['state']
    if mutation or args.operation == 'get':
        if getattr(args, 'key', None) is not None:
            result['target_key'] = args.key
        save_report_artifacts(result, evidence, args.backend, args.operation)
    else:
        stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        (evidence / f'{stamp}-{args.backend}-{args.operation}.json').write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    # JSON mode is ASCII-safe for legacy pipes; readable mode selects UTF-8.
    # The evidence file always retains the original Unicode text in UTF-8.
    emit_result(result, args.output_format)
    return 0 if isinstance(result.get('status'), int) and 200 <= result['status'] < 300 and result.get('write_state', 'success') == 'success' else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, OSError) as exc:
        error = {'error_type': type(exc).__name__, 'message': str(exc)}
        if isinstance(exc, ApprovalRequired):
            error['user_report'] = exc.user_report
            error['user_report_markdown'] = exc.user_report_markdown
            error['report_files'] = exc.report_files
        emit_result(error, exc.output_format if isinstance(exc, ApprovalRequired) else 'json', sys.stderr)
        sys.exit(2)
