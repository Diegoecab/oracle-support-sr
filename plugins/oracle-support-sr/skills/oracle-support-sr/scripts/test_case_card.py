import copy
import unittest
import presentation
import sr


class CaseCardTests(unittest.TestCase):
    def test_full_description_and_all_submitted_context_are_kept(self):
        description = 'General database performance degradation.\n\n' + 'Exact diagnostic context. ' * 35
        payload = {'compartmentId': 'fixture-tenancy', 'userGroupId': 'fixture-group',
            'problemType': 'TECH', 'ticket': {'title': 'Database performance degradation',
                'description': description, 'severity': 'MEDIUM', 'businessImpact': 'Medium',
                'resourceList': [{'region': 'IAD', 'item': {'type': 'tech',
                    'resourceId': 'fixture-resource', 'category': {'categoryKey': 'actual-key'}}}]}}
        record = {'state': 'draft_only', 'operation': 'create', 'payload': payload}
        report = sr.literal_report(record)
        text = presentation.render_markdown(report)
        self.assertEqual(report['sr_fields'], payload)
        self.assertIn('fixture-tenancy', text)
        self.assertIn('fixture-group', text)
        self.assertIn('fixture-resource', text)
        self.assertIn('IAD', text)
        self.assertEqual(text.count('Exact diagnostic context.'), 35)
        self.assertIn('Medium', text)

    def test_requested_product_never_becomes_returned_classification(self):
        record = {'operation': 'create', 'status': 200, 'data': {'key': 'fixture-case'},
            'routing': {'requested_selection': [{'service_label': 'Requested product',
                'service_key': 'product-key', 'category_label': 'Requested category',
                'category_key': 'category-key', 'subcategory_label': 'Requested subcategory'}],
                'persisted_classification': 'NOT_VERIFIED', 'current_case_assignment': 'NOT_VERIFIED'}}
        report = sr.literal_report(record)
        text = presentation.render_markdown(report)
        self.assertIn('| Product / service | Requested product | product-key |', text)
        self.assertIn('**Persisted product/category for this SR:** NOT\_VERIFIED', text)
        self.assertIn('**Returned resource/product/category fields:** Not returned', text)
        self.assertNotIn('ticket', report['sr_fields'])

    def test_returned_classification_disagreement_is_visible_without_overwriting(self):
        record = {'operation': 'get', 'data': {'key': 'fixture', 'ticket': {
            'description': 'Exact stored English description.', 'resourceList': [
                {'item': {'type': 'tech', 'category': {'categoryName': 'Returned category', 'categoryKey': 'returned-key'}}}]}},
            'routing': {'requested_selection': [{'service_label': 'Requested product', 'category_label': 'Requested category'}],
                'persisted_classification': 'NOT_VERIFIED'}}
        snapshot = copy.deepcopy(record)
        text = presentation.render_markdown(sr.literal_report(record))
        for value in ['Requested category', 'Returned category', 'returned-key']:
            self.assertIn(value, text)
        self.assertEqual(record, snapshot)

    def test_historical_non_english_is_not_translated_or_presented_as_new(self):
        original = 'Descripción histórica guardada por Oracle.'
        report = sr.literal_report({'operation': 'get', 'data': {'ticket': {'description': original}},
            'payload': {'ticket': {'description': 'New unsaved English draft'}}})
        text = presentation.render_markdown(report)
        self.assertIn(original, text)
        self.assertNotIn('New unsaved', text)
        self.assertEqual(report['sr_fields']['ticket']['description'], original)

    def test_untrusted_resource_values_remain_inert(self):
        original = '<script>example()</script>\n![image](https://example.invalid/pixel)'
        report = {'execution': {'source': 'GET_RESPONSE'}, 'sr_fields': {
            'ticket': {'product': original, 'description': 'Exact description.'}}}
        text = presentation.render_markdown(report)
        self.assertNotIn('<script>', text)
        self.assertNotIn('![image]', text)
        self.assertIn('&lt;script&gt;', text)


if __name__ == '__main__':
    unittest.main()
