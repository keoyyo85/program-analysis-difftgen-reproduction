import copy
import unittest
from modules.a.analysis import generate, check_value, validate_request, INT_MIN, INT_MAX
from interfaces.mock_b import adapt

def change(before=5, after=5, t='int', measure='value', extra=False):
    params = [{'name': 'x', 'java_type': t, 'varargs': False}]
    if extra: params.append({'name': 'tag', 'java_type': 'java.lang.String', 'varargs': False})
    return {'change_id': 'c', 'support_status': 'supported', 'method': {'class_name': 'T', 'name': 'f', 'signature': 'T#f', 'parameters': params, 'return_type': 'int', 'is_static': True},
            **{side: {'text': 'condition', 'association': {'parameter': 'x', 'boundary': n, 'measure': measure, 'java_type': t}} for side, n in [('before', before), ('after', after)]}}

def values(candidates): return [c['arguments'][0]['value'] for c in candidates]

class BoundaryTests(unittest.TestCase):
    def test_union_of_both_changed_thresholds(self):
        c, g = generate([change(5, 8)], {}, 'teaching')
        self.assertEqual(values(c), [4, 5, 6, 7, 8, 9])
        self.assertEqual({p['side'] for x in c for p in x['provenance']}, {'before', 'after'})

    def test_dedup_retains_both_provenances(self):
        c, g = generate([change()], {}, 'teaching')
        self.assertEqual(values(c), [4, 5, 6])
        self.assertTrue(all(len(x['provenance']) == 2 for x in c))

    def test_int_overflow_not_wrapped(self):
        for bound, expected in [(INT_MAX, [INT_MAX-1, INT_MAX]), (INT_MIN, [INT_MIN, INT_MIN+1])]:
            c, g = generate([change(bound, bound)], {}, 'teaching')
            self.assertEqual(values(c), expected)
            self.assertTrue(any(e['reason'] == 'Java_int_overflow_avoided' for e in g['events']))

    def test_zero_negative_and_resource_lengths(self):
        c, g = generate([change(0, 2, 'java.lang.String', 'length')], {'max_length': 2}, 'teaching')
        self.assertEqual(values(c), ['', 'a', 'aa'])
        reasons = {e['reason'] for e in g['events']}
        self.assertEqual(reasons, {'negative_length', 'length_resource_budget'})

    def test_arrays_require_explicit_element_configuration(self):
        ch = change(0, 1, 'int[]', 'length')
        c, g = generate([ch], {}, 'teaching')
        self.assertEqual(c, [])
        self.assertIn('explicit_array_fill_required', {e['reason'] for e in g['events']})
        c, g = generate([ch], {'array_fill_values': {'int[]': 7}}, 'teaching')
        self.assertEqual(values(c), [[], [7], [7, 7]])

    def test_multiple_parameters_are_never_zero_filled(self):
        c, g = generate([change(extra=True)], {}, 'teaching')
        self.assertEqual(c, [])
        self.assertTrue(all('tag' in e['reason'] for e in g['events']))
        c, g = generate([change(extra=True)], {'base_arguments': {'tag': 'legal'}, 'parameter_constraints': {'tag': {'min_length': 1}}}, 'teaching')
        self.assertTrue(all(x['arguments'][1]['value'] == 'legal' for x in c))
        c, g = generate([change(extra=True)], {'base_arguments': {'tag': ''}, 'parameter_constraints': {'tag': {'min_length': 1}}}, 'teaching')
        self.assertEqual(c, [])

    def test_budget_records_each_truncation_and_zero_budget(self):
        c, g = generate([change(5, 8)], {'max_candidates': 2}, 'teaching')
        self.assertEqual(len(c), 2)
        self.assertEqual(g['truncated_attempts'], 4)
        self.assertTrue(all(e['reason'] == 'max_candidates' for e in g['events']))
        c, g = generate([change()], {'max_candidates': 0}, 'teaching')
        self.assertEqual(c, [])
        self.assertEqual(g['truncated_attempts'], 6)

    def test_types_and_configuration_domains(self):
        self.assertIsNotNone(check_value(True, 'int', {}))
        self.assertIsNotNone(check_value(INT_MAX+1, 'int', {}))
        self.assertIsNotNone(check_value([1, True], 'int[]', {}))
        self.assertIsNotNone(check_value(0, 'int', {'min': 1}))
        self.assertIsNotNone(check_value('abc', 'java.lang.String', {'min': 1}))
        self.assertIsNotNone(check_value(5, 'int', {'min_length': 1}))
        self.assertIsNone(check_value('😀', 'java.lang.String', {'min_length': 2, 'max_length': 2}))

    def test_oracle_and_unknown_configuration_rejected(self):
        r = dict(schema_version='a.request.v1', case_id='t', case_kind='teaching', before_source='a', patch_source='b', diff_path='d', config={})
        validate_request(r)
        for key in ('reference_source', 'oracle', 'expected_output'):
            bad = dict(r, **{key: 'SECRET_REFERENCE'})
            with self.assertRaises(ValueError): validate_request(bad)
        bad = copy.deepcopy(r); bad['config']['oracle'] = 'hidden'
        with self.assertRaises(ValueError): validate_request(bad)
        bad = dict(r, before_source=5)
        with self.assertRaises(ValueError): validate_request(bad)
        with self.assertRaises(ValueError): validate_request([])

    def test_mock_interface_is_explicit_and_not_statistical(self):
        c, _ = generate([change()], {}, 'teaching')
        a = dict(schema_version='a.analysis.v1', artifact_kind='candidate_inputs_not_execution_results', case_id='teaching', case_kind='teaching', statistics_eligible=False, candidates=c,
                 support_status='supported', scope='local', sources={'before_source': {}, 'patch_source': {}, 'diff_path': {}}, diff_hunks=[], changes=[], unhandled_changes=[], generation={}, limitations=[])
        b = adapt(a)
        self.assertEqual(len(b['results']), 3)
        self.assertEqual(b['run_kind'], 'mock'); self.assertFalse(b['statistics_eligible'])
        self.assertTrue(all(x['oracle']['classification'] is None for x in b['results']))
        a['schema_version'] = 'a.analysis.v2'
        with self.assertRaises(ValueError): adapt(a)

    def test_interface_rejects_argument_corruption(self):
        from interfaces.a_contract import validate_a
        c, _ = generate([change()], {}, 'teaching')
        a = dict(schema_version='a.analysis.v1', artifact_kind='candidate_inputs_not_execution_results', case_id='teaching', case_kind='teaching', statistics_eligible=False, candidates=c,
                 support_status='supported', scope='local', sources={'before_source': {}, 'patch_source': {}, 'diff_path': {}}, diff_hunks=[], changes=[], unhandled_changes=[], generation={}, limitations=[])
        validate_a(a)
        a['candidates'][0]['arguments'][0]['value'] = 'wrong-type'
        with self.assertRaisesRegex(ValueError, 'Java argument'): validate_a(a)

if __name__ == '__main__': unittest.main()
