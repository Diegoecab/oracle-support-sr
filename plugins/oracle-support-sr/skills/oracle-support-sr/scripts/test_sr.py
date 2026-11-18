import contextlib
import datetime as dt
import io
from html.parser import HTMLParser
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch, MagicMock

import sr

TENANCY = 'ocid1.tenancy.oc1..testfixture'
REQUEST = {'compartmentId': TENANCY, 'problemType': 'TECH', 'userGroupId': 'fixture-group', 'ticket': {'severity': 'MEDIUM', 'title': 'Fixture case', 'description': 'A local test, never sent.'}}


class SafetyTests(unittest.TestCase):
    def draft(self, args):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(sr.main(args), 0)
        return json.loads(output.getvalue())

    def write_args(self, folder, operation='comment'):
        path = Path(folder) / ('request.json' if operation == 'create' else 'evidence.txt')
        path.write_text(json.dumps(REQUEST) if operation == 'create' else 'Verified fixture evidence', encoding='utf-8')
        args = ['--profile', 'fixture', '--backend', 'cli', '--evidence-dir', folder, operation, '--expected-tenancy', TENANCY]
        if operation == 'create':
            args += ['--request-file', str(path)]
        else:
            args += ['--key', 'fixture-key', '--file' if operation == 'attach' else '--text-file', str(path)]
        return args, path

    def test_manual_default_blocks_every_unapproved_write_before_credentials(self):
        for operation in ('create', 'comment', 'attach', 'close'):
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as folder:
                args, _ = self.write_args(folder, operation)
                with patch.object(sr, 'Support', side_effect=AssertionError('No credentials before approval')):
                    with self.assertRaisesRegex(ValueError, 'MANUAL requires user approval'):
                        sr.main(args + ['--execute'])
                self.assertFalse((Path(folder) / 'attempts').exists())

    def test_approval_is_bound_to_payload_target_profile_and_region(self):
        with tempfile.TemporaryDirectory() as folder:
            args, path = self.write_args(folder)
            approved = self.draft(args)['approval_digest']
            changed = []
            for flag, value in (('--key', 'different-sr'), ('--profile', 'other-profile')):
                new_args = list(args)
                new_args[new_args.index(flag) + 1] = value
                changed.append(new_args)
            changed.append(['--region', 'different-region'] + args)
            for new_args in changed:
                with patch.object(sr, 'Support', side_effect=AssertionError('Changed scope')):
                    with self.assertRaisesRegex(ValueError, 'changed approval'):
                        sr.main(new_args + ['--execute', '--approval-digest', approved])
            path.write_text('Changed outgoing note', encoding='utf-8')
            with patch.object(sr, 'Support', side_effect=AssertionError('Changed payload')):
                with self.assertRaisesRegex(ValueError, 'changed approval'):
                    sr.main(args + ['--execute', '--approval-digest', approved])

    def test_manual_exact_approval_allows_only_that_write(self):
        with tempfile.TemporaryDirectory() as folder:
            args, _ = self.write_args(folder)
            preview = self.draft(args)
            fake = MagicMock(tenancy=TENANCY, region='fixture-region')
            fake.oci = SimpleNamespace(__version__='fixture')
            fake.call.return_value = {'status': 200, 'data': {}}
            with patch.object(sr, 'Support', return_value=fake):
                result = self.draft(args + ['--execute', '--approval-digest', preview['approval_digest']])
            self.assertEqual(result['approval']['mode'], 'MANUAL')
            self.assertEqual(result['write_state'], 'success')
            self.assertEqual([call.args[0] for call in fake.call.call_args_list], ['get', 'comment'])

    def test_auto_without_execute_remains_an_offline_draft(self):
        with tempfile.TemporaryDirectory() as folder:
            args, _ = self.write_args(folder)
            with patch.object(sr, 'Support', side_effect=AssertionError('Still a draft')):
                result = self.draft(['--mode', 'AUTO'] + args)
            self.assertEqual(result['state'], 'draft_only')
            self.assertEqual(result['mode'], 'AUTO')

    def test_auto_executes_a_scoped_note_without_manual_digest(self):
        with tempfile.TemporaryDirectory() as folder:
            args, _ = self.write_args(folder)
            fake = MagicMock(tenancy=TENANCY, region='fixture-region')
            fake.oci = SimpleNamespace(__version__='fixture')
            fake.call.return_value = {'status': 200, 'data': {}}
            with patch.object(sr, 'Support', return_value=fake):
                result = self.draft(['--mode', 'AUTO'] + args + ['--execute'])
            self.assertEqual(result['approval']['policy'], 'SCOPED_AUTO')
            self.assertEqual([call.args[0] for call in fake.call.call_args_list], ['get', 'comment'])

    def test_attachment_upload_uses_the_approved_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            args, path = self.write_args(folder, 'attach')
            approved_bytes = path.read_bytes()
            preview = self.draft(args)
            fake = MagicMock(tenancy=TENANCY, region='fixture-region')
            fake.oci = SimpleNamespace(__version__='fixture')
            def call(operation, **kwargs):
                if operation == 'get':
                    path.write_text('Source file changed during preflight', encoding='utf-8')
                else:
                    self.assertEqual(operation, 'attach')
                    self.assertEqual(Path(kwargs['file']).read_bytes(), approved_bytes)
                return {'status': 200, 'data': {}}
            fake.call.side_effect = call
            with patch.object(sr, 'Support', return_value=fake):
                result = self.draft(args + ['--execute', '--approval-digest', preview['approval_digest']])
            self.assertEqual(result['write_state'], 'success')

    def test_changed_attachment_requires_new_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            args, path = self.write_args(folder, 'attach')
            preview = self.draft(args)
            path.write_text('Different evidence', encoding='utf-8')
            with patch.object(sr, 'Support', side_effect=AssertionError('Changed attachment')):
                with self.assertRaisesRegex(ValueError, 'changed approval'):
                    sr.main(args + ['--execute', '--approval-digest', preview['approval_digest']])

    def routing_fixture(self):
        request = dict(REQUEST, ticket=dict(REQUEST['ticket'], resourceList=[{'region': 'IAD', 'item': {'type': 'tech', 'category': {'categoryKey': 'category'}, 'subCategory': {'subCategoryKey': 'backup'}}}]))
        catalog = [{'service': {'group': 'Group'}, 'services': [{'service': {'service': 'Service'}, 'service_categories': [{'service_category': {'category': 'Category'}, 'sub_categories': [{'sub_category': {'backup': 'Backup and Restore'}}]}]}]}]
        route = dict(sr.flatten_taxonomy(catalog)[0], region_key='IAD')
        now = dt.datetime.now(dt.timezone.utc)
        registry = {'schema_version': 1, 'status': 'VERIFIED', 'tenancy_ocid': TENANCY, 'user_group_id': 'fixture-group', 'routes': [route], 'expected_portal': {'product': 'Expected product', 'category': 'Backup and Restore'}, 'verification': {'observed_portal': {'product': 'Expected product', 'category': 'Backup and Restore'}, 'source': 'Local test fixture, never a real approved route', 'observed_at_utc': (now-dt.timedelta(hours=1)).isoformat(), 'valid_until_utc': (now+dt.timedelta(hours=1)).isoformat()}}
        return request, registry, catalog

    def test_unverified_or_mismatched_portal_mapping_is_blocked(self):
        request, registry, catalog = self.routing_fixture()
        registry['status'] = 'UNVERIFIED'
        with self.assertRaisesRegex(ValueError, 'not VERIFIED'):
            sr.validate_routing(request, registry, catalog)
        registry['status'] = 'VERIFIED'
        registry['verification']['observed_portal']['category'] = 'Cluster Provision and Resize'
        with self.assertRaisesRegex(ValueError, 'portal product/category mismatch'):
            sr.validate_routing(request, registry, catalog)

    def test_current_catalog_and_registry_scope_are_required(self):
        request, registry, catalog = self.routing_fixture()
        self.assertEqual(sr.validate_routing(request, registry, catalog)['category'], 'Backup and Restore')
        catalog[0]['services'][0]['service_categories'][0]['sub_categories'][0]['sub_category'] = {'different': 'Other category'}
        with self.assertRaisesRegex(ValueError, 'live taxonomy'):
            sr.validate_routing(request, registry, catalog)
        registry['tenancy_ocid'] = 'ocid1.tenancy.oc1..other'
        with self.assertRaisesRegex(ValueError, 'tenancy/group'):
            sr.validate_routing(request, registry)

    def test_expired_route_or_changed_payload_is_blocked(self):
        request, registry, _ = self.routing_fixture()
        registry['verification']['valid_until_utc'] = (dt.datetime.now(dt.timezone.utc)-dt.timedelta(seconds=1)).isoformat()
        with self.assertRaisesRegex(ValueError, 'expired'):
            sr.validate_routing(request, registry)
        request, registry, _ = self.routing_fixture()
        request['ticket']['resourceList'][0]['item']['subCategory']['subCategoryKey'] = 'other'
        with self.assertRaisesRegex(ValueError, 'differs'):
            sr.validate_routing(request, registry)

    def test_missing_route_never_submits_a_technical_create(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'request.json'
            path.write_text(json.dumps(REQUEST))
            fake = MagicMock(tenancy=TENANCY)
            with patch.object(sr, 'Support', return_value=fake), self.assertRaisesRegex(ValueError, 'VERIFIED mapping'):
                sr.main(['--mode', 'AUTO', '--profile', 'fixture', '--evidence-dir', folder, 'create', '--request-file', str(path), '--expected-tenancy', TENANCY, '--execute'])
            fake.call.assert_not_called()
            self.assertFalse((Path(folder) / 'attempts').exists())

    def test_note_keeps_structure_and_treats_evidence_as_text(self):
        text = '## Findings\n\n- HTTP 404\n- Error: <script>unsafe</script> & retry\n\nRequest ID:\nfixture/id'
        rendered = sr.format_note(text)
        class Tags(HTMLParser):
            def __init__(self):
                super().__init__()
                self.tags = []
                self.words = []
            def handle_starttag(self, tag, attrs):
                self.tags.append(tag)
            def handle_data(self, data):
                self.words.append(data)
        parsed = Tags()
        parsed.feed(rendered)
        self.assertIn('strong', parsed.tags)
        self.assertEqual(parsed.tags.count('li'), 2)
        self.assertIn('br', parsed.tags)
        self.assertNotIn('script', parsed.tags)
        self.assertIn('<script>unsafe</script> & retry', ''.join(parsed.words))

    def test_note_default_is_applied_before_draft_and_before_credentials(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'note.txt'
            path.write_text('Summary\n\nEvidence\nRequest ID: fixture', encoding='utf-8')
            with patch.object(sr, 'Support', side_effect=AssertionError('Offline draft')), contextlib.redirect_stdout(io.StringIO()) as output:
                sr.main(['--profile', 'fixture', '--evidence-dir', folder, 'comment', '--key', 'fixture', '--text-file', str(path), '--expected-tenancy', TENANCY])
            comment = json.loads(output.getvalue())['payload']['ticket']['resource']['item']['comments']
            self.assertEqual(comment, sr.format_note(path.read_text(encoding='utf-8')))
            self.assertEqual(sr.format_note('one\n\ntwo', 'verbatim'), 'one\n\ntwo')

    def test_region_name_rejected_before_credentials_or_submission(self):
        with tempfile.TemporaryDirectory() as folder:
            request = dict(REQUEST, ticket=dict(REQUEST['ticket'], resourceList=[{'region': 'us-ashburn-1', 'item': {'type': 'tech'}}]))
            path = Path(folder) / 'request.json'
            path.write_text(json.dumps(request))
            with patch.object(sr, 'Support', side_effect=AssertionError('Invalid draft must stay local')):
                with self.assertRaisesRegex(ValueError, 'region key'):
                    sr.main(['--mode', 'AUTO', '--profile', 'fixture', '--evidence-dir', folder, 'create', '--request-file', str(path), '--expected-tenancy', TENANCY, '--execute'])
            self.assertFalse((Path(folder) / 'attempts').exists())

    def test_unicode_response_survives_legacy_windows_stdout(self):
        with tempfile.TemporaryDirectory() as folder:
            label='OpenSearch Γειά 東京'
            fake=MagicMock()
            fake.oci=SimpleNamespace(__version__='fixture')
            fake.region='us-ashburn-1'
            fake.call.return_value={'status':200,'data':[{'label':label}]}
            raw=io.BytesIO()
            console=io.TextIOWrapper(raw,encoding='cp1252',errors='strict')
            try:
                with patch.object(sr,'Support',return_value=fake),contextlib.redirect_stdout(console):
                    result=sr.main(['--profile','fixture','--evidence-dir',folder,'taxonomy'])
                console.flush()
                parsed=json.loads(raw.getvalue().decode('cp1252'))
                self.assertEqual(result,0)
                self.assertEqual(parsed['data'][0]['label'],label)
                saved=json.loads(next(Path(folder).glob('*-taxonomy.json')).read_text(encoding='utf-8'))
                self.assertEqual(saved['data'][0]['label'],label)
            finally:
                console.close()

    def test_draft_does_not_load_credentials_or_contact_service(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'request.json'
            path.write_text(json.dumps(REQUEST))
            with patch.object(sr, 'Support', side_effect=AssertionError('No service in draft mode')), contextlib.redirect_stdout(io.StringIO()) as output:
                result = sr.main(['--profile', 'fixture', '--evidence-dir', folder, 'create', '--request-file', str(path), '--expected-tenancy', TENANCY])
            self.assertEqual(result, 0)
            self.assertEqual(json.loads(output.getvalue())['state'], 'draft_only')
            self.assertFalse((Path(folder) / 'attempts').exists())

    def test_wrong_profile_tenancy_never_sends(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'request.json'
            path.write_text(json.dumps(REQUEST))
            fake = MagicMock(tenancy='ocid1.tenancy.oc1..other')
            with patch.object(sr, 'Support', return_value=fake):
                with self.assertRaisesRegex(ValueError, 'Profile tenancy'):
                    sr.main(['--mode', 'AUTO', '--profile', 'fixture', '--evidence-dir', folder, 'create', '--request-file', str(path), '--expected-tenancy', TENANCY, '--execute'])
            fake.call.assert_not_called()

    def test_pending_attempt_blocks_a_blind_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            sr.begin_attempt(folder, 'create', REQUEST)
            with self.assertRaisesRegex(RuntimeError, 'reconcile'):
                sr.begin_attempt(folder, 'create', REQUEST)

    def test_success_receipt_is_reused(self):
        with tempfile.TemporaryDirectory() as folder:
            path, record, send = sr.begin_attempt(folder, 'create', REQUEST)
            self.assertTrue(send)
            sr.finish_attempt(path, record, {'status': 200, 'data': {'key': 'fixture-key'}})
            _, previous, send = sr.begin_attempt(folder, 'create', REQUEST)
            self.assertFalse(send)
            self.assertEqual(previous['result']['data']['key'], 'fixture-key')

    def test_timeout_is_uncertain(self):
        with tempfile.TemporaryDirectory() as folder:
            path, record, _ = sr.begin_attempt(folder, 'create', REQUEST)
            final = sr.finish_attempt(path, record, {'error_type': 'TimeoutExpired'})
            self.assertEqual(final['state'], 'uncertain')
            with self.assertRaises(RuntimeError):
                sr.begin_attempt(folder, 'create', REQUEST)

    def test_create_without_returned_key_is_uncertain(self):
        with tempfile.TemporaryDirectory() as folder:
            path, record, _ = sr.begin_attempt(folder, 'create', REQUEST)
            self.assertEqual(sr.finish_attempt(path, record, {'status': 200, 'data': None})['state'], 'uncertain')

    def test_throttle_is_uncertain_and_bad_request_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path, record, _ = sr.begin_attempt(folder, 'create', REQUEST)
            self.assertEqual(sr.finish_attempt(path, record, {'status': 429})['state'], 'uncertain')
        with tempfile.TemporaryDirectory() as folder:
            path, record, _ = sr.begin_attempt(folder, 'create', REQUEST)
            self.assertEqual(sr.finish_attempt(path, record, {'status': 400})['state'], 'rejected')

    def test_compartment_cannot_be_child_compartment(self):
        with self.assertRaisesRegex(ValueError, 'tenancy OCID'):
            sr.validate_request(dict(REQUEST, compartmentId='ocid1.compartment.oc1..fixture'))

    def test_oversized_description_stays_local(self):
        request = dict(REQUEST, ticket=dict(REQUEST['ticket'], description='x'*1501))
        with self.assertRaisesRegex(ValueError, '1500'):
            sr.validate_request(request)

    def test_sdk_contract_preserves_note_and_problem_type(self):
        try:
            import oci
        except ImportError:
            self.skipTest('Official SDK not installed')
        payload = {'problemType': 'TECH', 'ticket': {'resource': {'item': {'type': 'activity', 'activityType': 'NOTES', 'comments': 'Fixture evidence'}}}}
        model = sr.model_from_wire(oci, 'UpdateIncident', payload)
        wire = oci.util.to_dict(model)
        self.assertEqual(wire['problem_type'], 'TECH')
        self.assertEqual(wire['ticket']['resource']['item']['comments'], 'Fixture evidence')
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            sr.model_from_wire(oci, 'CreateIncident', dict(REQUEST, inventedField='ignored?'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
