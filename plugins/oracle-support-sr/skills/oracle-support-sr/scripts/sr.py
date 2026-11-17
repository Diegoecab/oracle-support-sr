#!/usr/bin/env python3
"""Portable OCI Support helper. Writes require --execute and a tenancy check."""
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


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


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
    if len(ticket['description']) > 1500:
        raise ValueError('Initial description exceeds 1500 characters; use a note/attachment')
    for resource in ticket.get('resourceList') or []:
        region = resource.get('region') if isinstance(resource, dict) else None
        if isinstance(region, str) and '-' in region:
            raise ValueError('resourceList.region expects an OCI region key (for example IAD), not a region name; resolve it with Identity ListRegions')
    return data


def begin_attempt(directory, operation, payload):
    """An exclusive local receipt blocks duplicate or uncertain write retries."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(canonical({'operation': operation, 'payload': payload}).encode()).hexdigest()
    path = directory / (digest + '.json')
    record = {'operation': operation, 'payload_sha256': digest, 'state': 'pending', 'at_utc': dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        with path.open('x', encoding='utf-8') as output:
            json.dump(record, output, indent=2)
    except FileExistsError:
        previous = json.loads(path.read_text(encoding='utf-8'))
        if previous['state'] == 'success':
            return path, previous, False
        raise RuntimeError(f'Existing {previous["state"]} attempt at {path}; reconcile with Oracle before retrying')
    return path, record, True


def finish_attempt(path, record, result):
    status = result.get('status')
    if isinstance(status, int) and 200 <= status < 300:
        data = result.get('data')
        if record['operation'] != 'create' or (isinstance(data, dict) and data.get('key')):
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
        self.client = oci.cims.IncidentClient(cfg, timeout=(15, 60), retry_strategy=oci.retry.NoneRetryStrategy())
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
    result.add_argument('--cli', default='oci', help='CLI executable path')
    result.add_argument('--legacy-csi', help='Genuine verified CSI for a legacy CLI only')
    result.add_argument('--problem-type', choices=('TECH', 'ACCOUNT'), default='TECH')
    result.add_argument('--evidence-dir', required=True)
    subs = result.add_subparsers(dest='operation', required=True)
    for name in ('preflight', 'list', 'taxonomy', 'get', 'create', 'comment', 'close', 'attach'):
        sub = subs.add_parser(name)
        if name in ('get', 'comment', 'close', 'attach'):
            sub.add_argument('--key', required=True)
        if name in ('comment', 'close'):
            sub.add_argument('--text-file', required=True)
            sub.add_argument('--text-format', choices=('readable', 'verbatim'), default='readable', help='Default: escaped paragraphs, headings and lists for MOS; verbatim preserves the exact supplied body')
        if name == 'attach':
            sub.add_argument('--file', required=True)
        if name == 'create':
            sub.add_argument('--request-file', required=True)
        if name in ('create', 'comment', 'close', 'attach'):
            sub.add_argument('--execute', action='store_true')
            sub.add_argument('--expected-tenancy', required=True)
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    mutation = args.operation in ('create', 'comment', 'close', 'attach')
    payload = None
    if args.operation == 'create':
        payload = validate_request(json.loads(Path(args.request_file).read_text(encoding='utf-8-sig')))
        if payload['compartmentId'] != args.expected_tenancy:
            raise ValueError('Draft tenancy differs from expected tenancy')
    elif args.operation in ('comment', 'close'):
        text = Path(args.text_file).read_text(encoding='utf-8-sig')
        if not text.strip():
            raise ValueError('Empty update')
        text = format_note(text, args.text_format)
        payload = {'ticket': {'resource': {'item': {'type': 'activity', 'activityType': 'CLOSE' if args.operation == 'close' else 'NOTES', 'comments': text}}}}
    elif args.operation == 'attach':
        content = Path(args.file).read_bytes()
        if not content:
            raise ValueError('Empty attachment')
        payload = {'filename': Path(args.file).name, 'sha256': hashlib.sha256(content).hexdigest(), 'size': len(content)}
    if mutation and not args.execute:
        print(json.dumps({'state': 'draft_only', 'operation': args.operation, 'key': getattr(args, 'key', None), 'expected_tenancy': args.expected_tenancy, 'payload': payload}, indent=2, ensure_ascii=True))
        return 0
    service = Support(args)
    if mutation and service.tenancy != args.expected_tenancy:
        raise ValueError('Profile tenancy differs from expected tenancy; no write sent')
    if mutation and args.backend == 'sdk':
        # Reject unsupported contracts before reserving a write receipt.
        if args.operation == 'attach' and not hasattr(service.client, 'put_attachment'):
            raise ValueError('Installed SDK has no PutAttachment; upgrade the official oci package')
        if args.operation == 'create':
            model_from_wire(service.oci, 'CreateIncident', payload)
        if args.operation in ('comment', 'close'):
            model_from_wire(service.oci, 'UpdateIncident', dict(payload, problemType=args.problem_type))
    if mutation and args.operation != 'create':
        before = service.call('get', key=args.key)
        if before.get('status') != 200:
            raise ValueError('Cannot verify target SR before write: ' + canonical(before))
    if mutation and args.operation == 'create':
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
    evidence = Path(args.evidence_dir)
    evidence.mkdir(parents=True, exist_ok=True)
    attempt = None
    if mutation:
        scope = {'tenancy': service.tenancy, 'region': service.region, 'key': getattr(args, 'key', None), 'payload': payload}
        path, record, send = begin_attempt(evidence / 'attempts', args.operation, scope)
        if not send:
            print(json.dumps(dict(record, reused_receipt=True), indent=2))
            return 0
        attempt = path, record
    start = time.monotonic()
    try:
        result = service.call(args.operation, payload=payload, key=getattr(args, 'key', None), file=getattr(args, 'file', None))
    except Exception as exc:
        result = {'error_type': type(exc).__name__, 'message': str(exc)}
    result.update(operation=args.operation, backend=args.backend, sdk_version=service.oci.__version__, profile=args.profile, region=service.region, at_utc=dt.datetime.now(dt.timezone.utc).isoformat(), elapsed_seconds=round(time.monotonic()-start, 3))
    if attempt:
        receipt = finish_attempt(*attempt, result)
        result['receipt'] = str(attempt[0])
        result['write_state'] = receipt['state']
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    (evidence / f'{stamp}-{args.backend}-{args.operation}.json').write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    # Keep stdout valid JSON on Windows legacy console encodings as well as UTF-8.
    # The evidence file above retains the original Unicode text in UTF-8.
    print(json.dumps(result, indent=2, ensure_ascii=True, default=str))
    return 0 if isinstance(result.get('status'), int) and 200 <= result['status'] < 300 and result.get('write_state', 'success') == 'success' else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, OSError) as exc:
        print(json.dumps({'error_type': type(exc).__name__, 'message': str(exc)}), file=sys.stderr)
        sys.exit(2)
