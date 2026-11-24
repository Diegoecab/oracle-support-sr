import contextlib
import copy
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
import presentation

TENANCY = 'ocid1.tenancy.oc1..testfixture'
REQUEST = {'compartmentId': TENANCY, 'problemType': 'TECH', 'userGroupId': 'fixture-group', 'ticket': {'severity': 'MEDIUM', 'title': 'Fixture case', 'description': 'A local test, never sent.'}}


class SafetyTests(unittest.TestCase):
    def test_default_auto_still_requires_manual_approval_for_closure(self):
        with tempfile.TemporaryDirectory() as folder:
            args, _ = self.write_args(folder, 'close')
            preview = self.draft(args)
            self.assertEqual(preview['requested_mode'], 'AUTO')
            self.assertEqual(preview['mode'], 'MANUAL')
            self.assertEqual(preview['mandatory_review_reason'], 'CASE_CLOSURE')
            with patch.object(sr, 'Support', side_effect=AssertionError('Closure must wait')):
                with self.assertRaisesRegex(ValueError, 'CASE_CLOSURE'):
                    sr.main(args + ['--execute'])

    def test_raw_response_never_applies_to_writes_or_cli(self):
        for operation in ('comment', 'close', 'attach', 'create'):
            with tempfile.TemporaryDirectory() as folder:
                args,_=self.write_args(folder,operation)
                args[args.index('cli')]='sdk'
                with patch.object(sr,'Support',side_effect=AssertionError('Raw write must be blocked')):
                    with self.assertRaisesRegex(ValueError,'read-only SDK'):
                        sr.main(['--raw-response']+args)
        with self.assertRaisesRegex(ValueError,'read-only SDK'):
            sr.main(['--profile','fixture','--backend','cli','--raw-response','--evidence-dir','unused','get','--key','fixture'])

    def test_raw_read_preserves_unmodeled_fields_and_wire_names(self):
        with tempfile.TemporaryDirectory() as folder:
            response={'key':'fixture','serverOnlyField':'retained','ticket':{'resourceList':[{'item':{'type':'tech','category':{'categoryKey':'fixture-category'}}}]}}
            fake=MagicMock(region='fixture-region',oci=SimpleNamespace(__version__='fixture'))
            fake.call.return_value={'status':200,'data':response}
            with patch.object(sr,'Support',return_value=fake):
                output=self.draft(['--profile','fixture','--raw-response','--evidence-dir',folder,'get','--key','fixture'])
            self.assertEqual(output['data'],response)
            self.assertEqual(output['data_format'],'REST_JSON')

    def test_raw_read_uses_sdk_skip_deserialization(self):
        import oci
        args=sr.parser().parse_args(['--profile','fixture','--raw-response','--evidence-dir','unused','get','--key','fixture'])
        with patch.object(oci.config,'from_file',return_value={'tenancy':TENANCY,'user':'fixture-user','region':'fixture-region'}), patch.object(oci.cims,'IncidentClient') as constructor, patch.object(oci.identity,'IdentityClient'):
            sr.Support(args)
        self.assertTrue(constructor.call_args.kwargs['skip_deserialization'])

    def test_unclassified_write_operation_is_denied_before_drafting(self):
        with self.assertRaisesRegex(ValueError, 'no reviewed risk policy'):
            sr.approval_preview(SimpleNamespace(operation='delete-resource'), {})

    def first_use_fixture(self):
        request, registry, catalog = self.routing_schema_fixture()
        registry['status'] = 'CATALOG_ONLY'
        registry['catalog_evidence'] = {'source': 'ListIncidentResourceTypes/TAXONOMY',
            'captured_at_utc': registry['verification']['observed_at_utc'], 'valid_until_utc': registry['verification']['valid_until_utc']}
        registry.pop('verification')
        registry.pop('expected_portal')
        return request, registry, catalog

    def test_auto_close_requires_manual_review_before_credentials(self):
        with tempfile.TemporaryDirectory() as folder:
            args, _ = self.write_args(folder, 'close')
            preview = self.draft(['--mode', 'AUTO']+args)
            self.assertEqual(preview['mode'], 'MANUAL')
            self.assertEqual(preview['mandatory_review_reason'], 'CASE_CLOSURE')
            with patch.object(sr, 'Support', side_effect=AssertionError('No automatic closure')):
                with self.assertRaisesRegex(ValueError, 'CASE_CLOSURE'):
                    sr.main(['--mode', 'AUTO']+args+['--execute'])

    def test_auto_close_executes_only_the_exact_manually_approved_draft(self):
        with tempfile.TemporaryDirectory() as folder:
            args, _ = self.write_args(folder, 'close')
            preview = self.draft(['--mode', 'AUTO']+args)
            fake = MagicMock(tenancy=TENANCY, region='fixture-region', oci=SimpleNamespace(__version__='fixture'))
            fake.call.return_value = {'status': 200, 'data': {}}
            with patch.object(sr, 'Support', return_value=fake):
                result = self.draft(['--mode', 'AUTO']+args+['--execute', '--approval-digest', preview['approval_digest']])
            self.assertEqual(result['requested_execution_mode'], 'AUTO')
            self.assertEqual(result['execution_mode'], 'MANUAL')
            self.assertEqual(result['approval']['policy'], 'EXACT_DRAFT_CONFIRMATION')

    def test_new_product_can_use_catalog_without_a_previous_sr(self):
        request, registry, catalog = self.first_use_fixture()
        self.assertEqual(sr.validate_routing(request, registry, catalog), {})
        self.assertNotIn('verification', registry)
        self.assertNotIn('expected_portal', registry)

    def test_first_use_respects_auto_and_manual_selection(self):
        with tempfile.TemporaryDirectory() as folder:
            request, registry, _ = self.first_use_fixture()
            request_path, route_path = Path(folder)/'request.json', Path(folder)/'route.json'
            request_path.write_text(json.dumps(request), encoding='utf-8')
            route_path.write_text(json.dumps(registry), encoding='utf-8')
            args=['--mode','AUTO','--profile','fixture','--evidence-dir',folder,'create','--request-file',str(request_path),'--routing-file',str(route_path),'--expected-tenancy',TENANCY]
            preview=self.draft(args)
            self.assertIsNone(preview['mandatory_review_reason'])
            self.assertEqual(preview['mode'], 'AUTO')
            self.assertFalse(preview['approval_required'])
            manual=self.draft(['--mode','MANUAL']+args[2:])
            self.assertEqual(manual['mode'], 'MANUAL')
            self.assertTrue(manual['approval_required'])

    def test_first_use_auto_executes_with_live_validation_and_pending_classification(self):
        import oci
        with tempfile.TemporaryDirectory() as folder:
            request, registry, catalog = self.first_use_fixture()
            request_path, route_path = Path(folder)/'request.json', Path(folder)/'route.json'
            request_path.write_text(json.dumps(request), encoding='utf-8')
            route_path.write_text(json.dumps(registry), encoding='utf-8')
            args=['--mode','AUTO','--profile','fixture','--evidence-dir',folder,'create','--request-file',str(request_path),'--routing-file',str(route_path),'--expected-tenancy',TENANCY]
            preview=self.draft(args)
            fake=MagicMock(tenancy=TENANCY,region='fixture-region',oci=oci)
            fake.call.side_effect=[{'status':200,'data':{'is_valid_user':True,'write_permitted_user_group_infos':[{'user_group_id':request['userGroupId']}]}},{'status':200,'data':catalog},{'status':200,'data':{'key':'fixture-new-product'}}]
            with patch.object(sr,'Support',return_value=fake):
                result=self.draft(args+['--execute'])
            self.assertEqual([call.args[0] for call in fake.call.call_args_list],['preflight','taxonomy','create'])
            self.assertEqual(result['execution_mode'],'AUTO')
            self.assertEqual(result['approval']['policy'],'SCOPED_AUTO')
            self.assertEqual(result['routing']['recipe'],'FIRST_USE_MATCHED_LIVE_CATALOG')
            self.assertIsNone(result['routing']['expected_portal'])
            self.assertEqual(result['routing']['persisted_classification'],'NOT_VERIFIED')

    def test_known_mismatch_cannot_be_disguised_as_a_new_product(self):
        request, registry, catalog=self.first_use_fixture()
        registry['known_mismatch']=True
        with self.assertRaisesRegex(ValueError,'Known routing mismatch'):
            sr.validate_routing(request,registry,catalog)
        registry.pop('known_mismatch')
        registry['expected_portal']={'product':'Expected product','category':'Backup and Restore'}
        registry['verification']={'observed_portal':{'product':'Expected product','category':'Other category'}}
        with self.assertRaisesRegex(ValueError,'cannot be relabeled'):
            sr.validate_routing(request,registry,catalog)

    def test_first_use_still_rejects_stale_catalog_evidence_and_schema_drift(self):
        request,registry,catalog=self.first_use_fixture()
        registry['catalog_evidence']['valid_until_utc']=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=2)).isoformat()
        with self.assertRaisesRegex(ValueError,'expired'):
            sr.validate_routing(request,registry,catalog)
        request,registry,catalog=self.first_use_fixture()
        catalog[0]['services'][0]['schema']='changed'
        with self.assertRaisesRegex(ValueError,'schema metadata'):
            sr.validate_routing(request,registry,catalog)

    def test_first_use_auto_blocks_known_mismatch_before_any_api_call(self):
        import oci
        with tempfile.TemporaryDirectory() as folder:
            request, registry, _ = self.first_use_fixture()
            registry['known_mismatch'] = True
            request_path, route_path = Path(folder)/'request.json', Path(folder)/'route.json'
            request_path.write_text(json.dumps(request), encoding='utf-8')
            route_path.write_text(json.dumps(registry), encoding='utf-8')
            fake = MagicMock(tenancy=TENANCY, region='fixture-region', oci=oci)
            with patch.object(sr, 'Support', return_value=fake):
                with self.assertRaisesRegex(ValueError, 'Known routing mismatch'):
                    sr.main(['--mode','AUTO','--profile','fixture','--evidence-dir',folder,
                             'create','--request-file',str(request_path),'--routing-file',str(route_path),
                             '--expected-tenancy',TENANCY,'--execute'])
            fake.call.assert_not_called()

    def test_first_use_auto_blocks_live_catalog_drift_before_create(self):
        import oci
        with tempfile.TemporaryDirectory() as folder:
            request, registry, catalog = self.first_use_fixture()
            request_path, route_path = Path(folder)/'request.json', Path(folder)/'route.json'
            request_path.write_text(json.dumps(request), encoding='utf-8')
            route_path.write_text(json.dumps(registry), encoding='utf-8')
            fake = MagicMock(tenancy=TENANCY, region='fixture-region', oci=oci)
            fake.call.side_effect = [
                {'status':200,'data':{'is_valid_user':True,'write_permitted_user_group_infos':[{'user_group_id':request['userGroupId']}]}},
                {'status':200,'data':[]}]
            with patch.object(sr, 'Support', return_value=fake):
                with self.assertRaisesRegex(ValueError, 'live taxonomy'):
                    sr.main(['--mode','AUTO','--profile','fixture','--evidence-dir',folder,
                             'create','--request-file',str(request_path),'--routing-file',str(route_path),
                             '--expected-tenancy',TENANCY,'--execute'])
            self.assertEqual([call.args[0] for call in fake.call.call_args_list], ['preflight','taxonomy'])

    def routing_test_fixture(self):
        request, _, catalog = self.routing_schema_fixture()
        request = copy.deepcopy(request)
        request['ticket'].update(severity='LOW', title='[ROUTING TEST] Fixture validation', description=sr.ROUTING_TEST_NOTICE)
        now = dt.datetime.now(dt.timezone.utc)
        plan = {'schema_version': 1, 'purpose': 'ROUTING_VALIDATION', 'status': 'CANDIDATE', 'production_use': False,
                'max_creations': 1, 'test_id': 'fixture-routing-001', 'created_at_utc': (now-dt.timedelta(minutes=1)).isoformat(),
                'expires_at_utc': (now+dt.timedelta(hours=1)).isoformat(), 'tenancy_ocid': TENANCY, 'user_group_id': 'fixture-group',
                'expected_portal': {'product': 'Expected product', 'category': 'Backup and Restore'},
                'routes': [dict(sr.flatten_taxonomy(catalog)[0], region_key='IAD')]}
        return request, plan, catalog

    def routing_test_args(self, folder):
        request, plan, catalog = self.routing_test_fixture()
        request_path, plan_path = Path(folder)/'request.json', Path(folder)/'test-plan.json'
        request_path.write_text(json.dumps(request), encoding='utf-8')
        plan_path.write_text(json.dumps(plan), encoding='utf-8')
        args = ['--profile', 'fixture', '--backend', 'sdk', '--evidence-dir', folder, 'test-create', '--request-file', str(request_path), '--test-plan-file', str(plan_path), '--expected-tenancy', TENANCY]
        return args, request, plan, catalog, plan_path

    def test_routing_test_is_an_offline_candidate_draft(self):
        with tempfile.TemporaryDirectory() as folder:
            args, request, _, _, _ = self.routing_test_args(folder)
            args = ['--mode', 'MANUAL'] + args
            with patch.object(sr, 'Support', side_effect=AssertionError('Offline test draft')):
                preview = self.draft(args)
            self.assertTrue(preview['approval_required'])
            self.assertEqual(preview['payload'], request)
            self.assertIn('test_plan_sha256', preview)
            self.assertFalse((Path(folder)/'attempts').exists())

    def test_routing_test_manual_approval_is_required_before_credentials(self):
        with tempfile.TemporaryDirectory() as folder:
            args, _, _, _, _ = self.routing_test_args(folder)
            args = ['--mode', 'MANUAL'] + args
            with patch.object(sr, 'Support', side_effect=AssertionError('Unapproved test write')):
                with self.assertRaisesRegex(ValueError, 'MANUAL requires user approval'):
                    sr.main(args+['--execute'])

    def test_changed_test_plan_invalidates_manual_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            args, _, plan, _, path = self.routing_test_args(folder)
            args = ['--mode', 'MANUAL'] + args
            preview = self.draft(args)
            plan['test_id'] = 'fixture-routing-002'
            path.write_text(json.dumps(plan), encoding='utf-8')
            with patch.object(sr, 'Support', side_effect=AssertionError('Changed test scope')):
                with self.assertRaisesRegex(ValueError, 'changed approval'):
                    sr.main(args+['--execute', '--approval-digest', preview['approval_digest']])

    def test_routing_test_rejects_urgency_and_missing_validation_notice(self):
        for change in ({'severity': 'MEDIUM'}, {'title': 'Production outage'}, {'description': 'Help with an outage'}):
            with self.subTest(change=change):
                request, plan, _ = self.routing_test_fixture()
                request['ticket'].update(change)
                with self.assertRaisesRegex(ValueError, 'requires TECH, LOW'):
                    sr.validate_test_plan(request, plan)

    def test_routing_test_rejects_guessed_schema_or_issue_type_fields(self):
        request, plan, _ = self.routing_test_fixture()
        request['ticket']['contextualData'] = {'schemaName': 'guessed'}
        with self.assertRaisesRegex(ValueError, 'unreviewed fields'):
            sr.validate_test_plan(request, plan)
        request, plan, _ = self.routing_test_fixture()
        request['ticket']['resourceList'][0]['item']['issueType'] = {'issueTypeKey': 'fixture-selected-leaf-schema'}
        with self.assertRaisesRegex(ValueError, 'guessed issueTypeKey'):
            sr.validate_test_plan(request, plan)

    def test_routing_test_rejects_stale_or_unbounded_plans(self):
        for change in ({'production_use': True}, {'status': 'VERIFIED'}, {'max_creations': 2}, {'max_creations': True}):
            request, plan, _ = self.routing_test_fixture()
            plan.update(change)
            with self.assertRaisesRegex(ValueError, 'single-case CANDIDATE'):
                sr.validate_test_plan(request, plan)
        for hours in (-1, 25):
            request, plan, _ = self.routing_test_fixture()
            plan['expires_at_utc'] = (dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=hours)).isoformat()
            with self.assertRaisesRegex(ValueError, 'expire within 24 hours'):
                sr.validate_test_plan(request, plan)

    def test_routing_test_still_requires_matching_scope_and_catalog(self):
        request, plan, catalog = self.routing_test_fixture()
        self.assertEqual(sr.validate_test_plan(request, plan, catalog)['category'], 'Backup and Restore')
        plan['tenancy_ocid'] = 'ocid1.tenancy.oc1..other'
        with self.assertRaisesRegex(ValueError, 'tenancy/group'):
            sr.validate_test_plan(request, plan, catalog)
        request, plan, catalog = self.routing_test_fixture()
        catalog[0]['services'][0]['service_categories'][0]['sub_categories'][0]['schema'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'complete live taxonomy'):
            sr.validate_test_plan(request, plan, catalog)

    def test_same_test_id_cannot_reserve_another_payload(self):
        with tempfile.TemporaryDirectory() as folder:
            identity = {'operation': 'test-create', 'tenancy': TENANCY, 'test_id': 'fixture-test'}
            path, record, _ = sr.begin_attempt(folder, 'test-create', {'body': 'first'}, identity=identity)
            sr.finish_attempt(path, record, {'status': 200, 'data': {'key': 'fixture-created'}})
            _, prior, send = sr.begin_attempt(folder, 'test-create', {'body': 'first'}, identity=identity)
            self.assertFalse(send)
            self.assertEqual(prior['result']['data']['key'], 'fixture-created')
            with self.assertRaisesRegex(RuntimeError, 'already reserved a different request'):
                sr.begin_attempt(folder, 'test-create', {'body': 'changed'}, identity=identity)

    def test_routing_test_without_returned_key_is_uncertain(self):
        with tempfile.TemporaryDirectory() as folder:
            path, record, _ = sr.begin_attempt(folder, 'test-create', REQUEST)
            self.assertEqual(sr.finish_attempt(path, record, {'status': 200, 'data': {}})['state'], 'uncertain')

    def test_routing_test_uses_live_preflight_catalog_and_create_without_promoting_candidate(self):
        import oci
        with tempfile.TemporaryDirectory() as folder:
            args, _, plan, catalog, _ = self.routing_test_args(folder)
            preview = self.draft(args)
            fake = MagicMock(tenancy=TENANCY, region='fixture-region', oci=oci)
            fake.call.side_effect = [
                {'status': 200, 'data': {'is_valid_user': True, 'write_permitted_user_group_infos': [{'user_group_id': plan['user_group_id']}]}},
                {'status': 200, 'data': catalog},
                {'status': 200, 'data': {'key': 'fixture-new-test'}}]
            with patch.object(sr, 'Support', return_value=fake):
                result = self.draft(args+['--execute', '--approval-digest', preview['approval_digest']])
            self.assertEqual([call.args[0] for call in fake.call.call_args_list], ['preflight', 'taxonomy', 'create'])
            self.assertEqual(result['routing']['persisted_classification'], 'NOT_VERIFIED')
            self.assertFalse(result['routing']['production_recipe_created'])
            self.assertEqual(result['write_state'], 'success')

    def test_routing_test_catalog_failure_never_reserves_or_creates(self):
        import oci
        with tempfile.TemporaryDirectory() as folder:
            args, _, plan, _, _ = self.routing_test_args(folder)
            fake = MagicMock(tenancy=TENANCY, region='fixture-region', oci=oci)
            fake.call.side_effect = [
                {'status': 200, 'data': {'is_valid_user': True, 'write_permitted_user_group_infos': [{'user_group_id': plan['user_group_id']}]}},
                {'status': 500, 'message': 'Fixture catalog unavailable'}]
            with patch.object(sr, 'Support', return_value=fake):
                with self.assertRaisesRegex(ValueError, 'complete live taxonomy'):
                    sr.main(['--mode', 'AUTO']+args+['--execute'])
            self.assertEqual([call.args[0] for call in fake.call.call_args_list], ['preflight', 'taxonomy'])
            self.assertFalse((Path(folder)/'attempts').exists())

    def routing_schema_fixture(self):
        request, registry, catalog = self.routing_fixture()
        service = catalog[0]['services'][0]
        category = service['service_categories'][0]
        service['schema'] = 'fixture-service-schema'
        category['schema'] = 'fixture-parent-default-schema'
        category['has_sub_category'] = 'true'
        category['sub_categories'][0]['schema'] = 'fixture-selected-leaf-schema'
        registry['routes'] = [dict(sr.flatten_taxonomy(catalog)[0], region_key='IAD')]
        return request, registry, catalog

    def test_schema_metadata_survives_sdk_cli_and_raw_json_names(self):
        _, registry, catalog = self.routing_schema_fixture()
        expected = dict(registry['routes'][0])
        expected.pop('region_key')
        def rename(value, style):
            if isinstance(value, list):
                return [rename(item, style) for item in value]
            if isinstance(value, dict):
                return {(key.replace('_', '-') if style == 'cli' else ''.join(part.title() if index else part for index, part in enumerate(key.split('_')))): rename(child, style) for key, child in value.items()}
            return value
        for style, value in [('sdk', catalog), ('cli', rename(catalog, 'cli')), ('raw', rename(catalog, 'raw'))]:
            with self.subTest(style=style):
                self.assertEqual(sr.flatten_taxonomy(value), [expected])
        self.assertEqual(expected['category_schema'], 'fixture-parent-default-schema')
        self.assertEqual(expected['subcategory_schema'], 'fixture-selected-leaf-schema')

    def test_schema_change_blocks_even_when_taxonomy_keys_and_labels_match(self):
        for level in ('service', 'category', 'subcategory'):
            with self.subTest(level=level):
                request, registry, catalog = self.routing_schema_fixture()
                self.assertEqual(sr.validate_routing(request, registry, catalog)['category'], 'Backup and Restore')
                service = catalog[0]['services'][0]
                category = service['service_categories'][0]
                target = {'service': service, 'category': category, 'subcategory': category['sub_categories'][0]}[level]
                target['schema'] = 'changed-fixture-schema'
                with self.assertRaisesRegex(ValueError, 'schema metadata is missing or changed'):
                    sr.validate_routing(request, registry, catalog)

    def test_older_recipe_without_available_schema_evidence_requires_reverification(self):
        request, registry, catalog = self.routing_schema_fixture()
        for key in ('service_schema', 'category_schema', 'subcategory_schema', 'category_has_subcategory'):
            registry['routes'][0].pop(key)
        with self.assertRaisesRegex(ValueError, 'reverify'):
            sr.validate_routing(request, registry, catalog)

    def test_required_subcategory_cannot_be_omitted(self):
        request, registry, _ = self.routing_schema_fixture()
        request['ticket']['resourceList'][0]['item'].pop('subCategory')
        registry['routes'][0]['subcategory_key'] = None
        with self.assertRaisesRegex(ValueError, 'requires a subcategory'):
            sr.validate_routing(request, registry)

    def test_conflicting_schema_rows_are_not_resolved_by_first_match(self):
        request, registry, catalog = self.routing_schema_fixture()
        duplicate = copy.deepcopy(catalog[0]['services'][0]['service_categories'][0])
        duplicate['sub_categories'][0]['schema'] = 'conflicting-fixture-schema'
        catalog[0]['services'][0]['service_categories'].append(duplicate)
        with self.assertRaisesRegex(ValueError, 'Ambiguous schema metadata'):
            sr.validate_routing(request, registry, catalog)

    def test_schema_metadata_does_not_invent_wire_fields_or_change_request(self):
        request, registry, catalog = self.routing_schema_fixture()
        original = copy.deepcopy(request)
        sr.validate_routing(request, registry, catalog)
        self.assertEqual(request, original)
        self.assertNotIn('issueType', request['ticket']['resourceList'][0]['item'])
        self.assertNotIn('contextualData', request['ticket'])

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

    def test_explicit_manual_blocks_every_unapproved_write_before_credentials(self):
        for operation in ('create', 'comment', 'attach', 'close'):
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as folder:
                args, _ = self.write_args(folder, operation)
                args = ['--mode', 'MANUAL'] + args
                with patch.object(sr, 'Support', side_effect=AssertionError('No credentials before approval')):
                    with self.assertRaisesRegex(ValueError, 'MANUAL requires user approval'):
                        sr.main(args + ['--execute'])
                self.assertFalse((Path(folder) / 'attempts').exists())

    def test_approval_is_bound_to_payload_target_profile_and_region(self):
        with tempfile.TemporaryDirectory() as folder:
            args, path = self.write_args(folder)
            args = ['--mode', 'MANUAL'] + args
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
            args = ['--mode', 'MANUAL'] + args
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

    def test_default_auto_executes_a_scoped_note_without_manual_digest(self):
        with tempfile.TemporaryDirectory() as folder:
            args, _ = self.write_args(folder)
            fake = MagicMock(tenancy=TENANCY, region='fixture-region')
            fake.oci = SimpleNamespace(__version__='fixture')
            fake.call.return_value = {'status': 200, 'data': {}}
            with patch.object(sr, 'Support', return_value=fake):
                result = self.draft(args + ['--execute'])
            self.assertEqual(result['execution_mode'], 'AUTO')
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
            args = ['--mode', 'MANUAL'] + args
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


class PresentationTests(unittest.TestCase):
    def test_readable_stdout_keeps_unicode_on_a_legacy_encoded_stream(self):
        buffer=io.BytesIO()
        stream=io.TextIOWrapper(buffer,encoding='ascii')
        sr.emit_result({'user_report_markdown':'Caf\u00e9\n'},'readable',stream)
        stream.flush()
        self.assertEqual(buffer.getvalue().decode('utf-8').splitlines(),['Caf\u00e9'])

    def test_readable_draft_stdout_has_a_full_json_evidence_file(self):
        with tempfile.TemporaryDirectory() as folder:
            request_path=Path(folder)/'request.json'
            request_path.write_text(json.dumps(REQUEST),encoding='utf-8')
            out=io.StringIO()
            with patch.object(sr,'Support',side_effect=AssertionError('No OCI access')),contextlib.redirect_stdout(out):
                sr.main(['--profile','FIXTURE','--output-format','readable','--evidence-dir',folder,
                         'create','--request-file',str(request_path),'--expected-tenancy',TENANCY])
            self.assertFalse(out.getvalue().lstrip().startswith('{'))
            self.assertIn('Fixture case',out.getvalue())
            raw=json.loads(next(Path(folder).glob('*-sdk-create.json')).read_text(encoding='utf-8'))
            self.assertEqual(raw['payload'],REQUEST)
            self.assertEqual(raw['user_report_markdown'],out.getvalue())

    def test_output_format_change_does_not_invalidate_exact_draft_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'request.json';path.write_text(json.dumps(REQUEST),encoding='utf-8')
            args=['--profile','FIXTURE','--evidence-dir',folder,'create','--request-file',str(path),'--expected-tenancy',TENANCY]
            with contextlib.redirect_stdout(io.StringIO()) as out:
                sr.main(args)
            digest=json.loads(out.getvalue())['approval_digest']
            with contextlib.redirect_stdout(io.StringIO()):
                sr.main(['--output-format','readable']+args)
            last=json.loads(sorted(Path(folder).glob('*-sdk-create.json'))[-1].read_text(encoding='utf-8'))
            self.assertEqual(last['approval_digest'],digest)

    def report(self, description):
        return sr.literal_report({'operation':'get','status':200,'data':{
            'key':'4-0000000000','problemType':'TECH','ticket':{
                'title':'Fixture case','severity':'LOW','lifecycle_state':'ACTIVE',
                'lifecycle_details':'PENDING_WITH_ORACLE','description':description}}})

    def test_readable_paragraphs_and_case_link_preserve_content(self):
        report = self.report('First paragraph.\n\nLOCAL standby, read only; no failover.')
        snapshot = copy.deepcopy(report)
        text = presentation.render_markdown(report)
        self.assertIn('https://support.oracle.com/support/?SR=4-0000000000',text)
        self.assertNotIn('kmContentId=',text)
        self.assertIn('> First paragraph.\n>\n> LOCAL standby, read only; no failover.',text)
        self.assertNotIn('```json',text)
        self.assertEqual(report,snapshot)

    def test_literal_backslash_n_is_not_decoded_as_a_line_break(self):
        text = presentation.render_markdown(self.report(r'Regex: \n is two characters.'))
        self.assertIn(r'\\n is two characters.',text)
        self.assertNotIn('> Regex: \n',text)

    def test_json_description_formatting_keeps_duplicate_keys_and_number_tokens(self):
        source='{"x":1.2300e+45,"x":-0.00,"nested":[{},"line\\ntext"]}'
        text = presentation.render_markdown(self.report(source))
        self.assertIn('```json\n{\n',text)
        self.assertEqual(text.count('"x"'),2)
        self.assertIn('1.2300e+45',text)
        self.assertIn('-0.00',text)
        self.assertIn('"line\\ntext"',text)
        self.assertIsNone(presentation._pretty_json('{"x":NaN}'))

    def test_html_correspondence_is_inert_with_structure_and_original_raw(self):
        original='<p>First &amp; second</p><ul><li>One</li><li>Two</li></ul><script>example()</script><p>![pixel](https://example.invalid/image)</p>'
        report=self.report(original)
        text=presentation.render_markdown(report)
        self.assertIn('First &amp; second',text)
        self.assertIn('> - One',text)
        self.assertNotIn('<script>',text)
        self.assertNotIn('![pixel]',text)
        self.assertEqual(report['sr_fields']['ticket']['description'],original)

    def test_artifacts_preserve_complete_data_and_link_the_raw_file(self):
        with tempfile.TemporaryDirectory(prefix='sr view ') as folder:
            record={'operation':'get','status':200,'data':{'key':'4-0000000000','ticket':{'description':'Exact\n\nEnglish text.'}}}
            original=copy.deepcopy(record['data'])
            sr.save_report_artifacts(record,folder,'sdk','get')
            raw=Path(record['report_files']['raw_json'])
            md=Path(record['report_files']['readable_markdown'])
            self.assertEqual(json.loads(raw.read_text(encoding='utf-8'))['data'],original)
            self.assertEqual(md.read_text(encoding='utf-8'),record['user_report_markdown'])
            self.assertIn('[Raw output (JSON)](<'+raw.resolve().as_posix()+'>)',md.read_text(encoding='utf-8'))

    def test_missing_fields_and_cached_receipts_do_not_look_like_fresh_creation(self):
        text=presentation.render_markdown(sr.literal_report({'operation':'create','status':200,'data':{}}))
        self.assertNotIn('Not created (draft)',text)
        self.assertIn('verification pending',text)
        cached=sr.literal_report({'reused_receipt':True,'result':{'operation':'create','data':{'key':'4-0000000000'}}})
        self.assertIn('not a new write or a fresh retrieval',presentation.render_markdown(cached))

    def test_existing_evidence_can_be_formatted_offline_without_source_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.json';target=Path(folder)/'view.md'
            source.write_text(json.dumps({'operation':'get','data':{'ticket':{'description':'Exact text.'}}}),encoding='utf-8')
            before=source.read_bytes()
            with patch.object(sr,'Support',side_effect=AssertionError('No OCI access')), patch.object(sr.sys,'argv',['presentation.py','--input',str(source),'--output',str(target)]), contextlib.redirect_stdout(io.StringIO()):
                presentation.main()
            self.assertEqual(source.read_bytes(),before)
            self.assertIn('Exact text.',target.read_text(encoding='utf-8'))

    def test_offline_formatter_cannot_overwrite_json_source(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.json';source.write_text('{}',encoding='utf-8')
            with patch.object(sr.sys,'argv',['presentation.py','--input',str(source),'--output',str(source)]), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    presentation.main()
            self.assertEqual(source.read_text(),'{}')


class LiteralReportTests(unittest.TestCase):
    def test_title_budget_preserves_valid_text_without_truncation(self):
        request = copy.deepcopy(REQUEST)
        request['ticket']['title'] = 'X' * 80
        snapshot = copy.deepcopy(request)
        self.assertEqual(sr.validate_request(request), snapshot)
        self.assertEqual(request, snapshot)

    def test_long_title_is_rejected_locally_before_credentials(self):
        with tempfile.TemporaryDirectory() as folder:
            request = copy.deepcopy(REQUEST)
            request['ticket']['title'] = 'X' * 81
            path = Path(folder) / 'request.json'
            path.write_text(json.dumps(request), encoding='utf-8')
            with patch.object(sr, 'Support', side_effect=AssertionError('No credentials needed')):
                with self.assertRaisesRegex(ValueError, '80-character drafting budget'):
                    sr.main(['--profile', 'FIXTURE', '--mode', 'AUTO', '--evidence-dir', folder,
                             'create', '--request-file', str(path), '--expected-tenancy', TENANCY, '--execute'])
            self.assertEqual(json.loads(path.read_text())['ticket']['title'], 'X' * 81)

    def test_approval_block_exposes_draft_fields_without_loading_credentials(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'request.json'
            path.write_text(json.dumps(REQUEST), encoding='utf-8')
            with patch.object(sr, 'Support', side_effect=AssertionError('No credentials needed')):
                with self.assertRaises(sr.ApprovalRequired) as caught:
                    sr.main(['--mode', 'MANUAL', '--profile', 'FIXTURE', '--evidence-dir', folder,
                             'create', '--request-file', str(path), '--expected-tenancy', TENANCY, '--execute'])
            report = caught.exception.user_report
            self.assertEqual(report['sr_fields']['ticket'], REQUEST['ticket'])
            self.assertEqual(report['execution']['source'], 'DRAFT_PAYLOAD')
            self.assertTrue(report['execution']['approval_required'])

    def test_draft_keeps_unicode_and_full_original_description(self):
        original = copy.deepcopy(REQUEST)
        original['ticket']['description'] = 'Original English question.\n\nCaf\u00e9, SQL: SELECT * FROM t;'
        record = {'state': 'draft_only', 'operation': 'create', 'mode': 'AUTO',
                  'requested_mode': 'AUTO', 'mandatory_review_reason': None,
                  'payload': original, 'config_file': '/private/config'}
        snapshot = copy.deepcopy(record)
        report = sr.literal_report(record)
        self.assertEqual(report['sr_fields']['ticket'], original['ticket'])
        self.assertNotIn('key', report['sr_fields'])
        self.assertNotIn('config_file', report['execution'])
        self.assertEqual(report['execution']['source'], 'DRAFT_PAYLOAD')
        self.assertEqual(report['execution']['mode'], 'AUTO')
        self.assertEqual(record, snapshot)

    def test_get_preserves_native_keys_nulls_and_html_without_request_fallback(self):
        ticket = {'title': 'Exact title', 'description': '<p>English\ntext</p>',
                  'lifecycle_state': 'ACTIVE', 'lifecycle_details': None}
        record = {'operation': 'get', 'status': 200, 'data': {'key': 'fixture-key', 'ticket': ticket},
                  'payload': {'ticket': {'description': 'Different unsaved draft'}}}
        report = sr.literal_report(record)
        self.assertEqual(report['sr_fields']['ticket'], ticket)
        self.assertEqual(report['execution']['source'], 'GET_RESPONSE')
        self.assertNotIn('severity', report['sr_fields']['ticket'])

    def test_write_acceptance_does_not_invent_persisted_state_or_use_draft(self):
        record = {'operation': 'create', 'status': 200, 'write_state': 'success',
                  'data': {'key': 'fixture-key'}, 'payload': REQUEST}
        report = sr.literal_report(record)
        self.assertEqual(report['sr_fields'], {'key': 'fixture-key'})
        self.assertEqual(report['execution']['source'], 'API_RESPONSE')

    def test_report_keeps_returned_classification_and_excludes_activity_history(self):
        tech = {'region': 'IAD', 'item': {'type': 'tech', 'category': {'categoryKey': 'returned-key'}}}
        activity = {'item': {'type': 'activity', 'comments': 'Long private correspondence'}}
        report = sr.literal_report({'operation': 'get', 'data': {'ticket': {
            'description': 'Exact description', 'resourceList': [activity, tech]}}})
        self.assertEqual(report['sr_fields']['ticket']['resourceList'], [tech])
        self.assertNotIn('classification_evidence', report)

    def test_cached_receipt_is_not_reported_as_fresh_api_response(self):
        result = {'operation': 'create', 'status': 200, 'data': {'key': 'fixture-key'}}
        report = sr.literal_report({'result': result, 'reused_receipt': True})
        self.assertEqual(report['execution']['source'], 'CACHED_RECEIPT')
        self.assertEqual(report['sr_fields']['key'], 'fixture-key')

    def test_main_draft_includes_literal_report_without_loading_credentials(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'request.json'
            path.write_text(json.dumps(REQUEST), encoding='utf-8')
            out = io.StringIO()
            with patch.object(sr, 'Support', side_effect=AssertionError('No credentials needed')), contextlib.redirect_stdout(out):
                result = sr.main(['--profile', 'FIXTURE', '--evidence-dir', folder,
                                  'create', '--request-file', str(path), '--expected-tenancy', TENANCY])
            self.assertEqual(result, 0)
            report = json.loads(out.getvalue())['user_report']
            self.assertEqual(report['sr_fields']['ticket'], REQUEST['ticket'])
            self.assertEqual(report['execution']['source'], 'DRAFT_PAYLOAD')


if __name__ == '__main__':
    unittest.main(verbosity=2)
