import json
import unittest
from pathlib import Path
import test_ast_integration


class HandoffContentTests(unittest.TestCase):
    analyze_sources = test_ast_integration.AstIntegrationTests.analyze_sources

    def test_imported_static_state_in_return_is_rejected(self):
        src = '''import static other.State.VALUE;
public class T {
 public static int f(int n) {
  if (n > 5) return VALUE;
  return 0;
 }
}
'''
        result = self.analyze_sources(src, src.replace('n > 5', 'n >= 5'))
        self.assertEqual(result['support_status'], 'unsupported')
        self.assertEqual(result['candidates'], [])
        self.assertIn('unresolved_body_name_requires_binding:VALUE', str(result['changes'][0]['reasons']))

    def test_two_changed_conditions_are_not_paired_by_order(self):
        src = '''public class T {
 public static int f(int n) {
  if (n > 5) return 1;
  if (n < 9) return 2;
  return 0;
 }
}
'''
        result = self.analyze_sources(src, src.replace('n > 5', 'n >= 5').replace('n < 9', 'n <= 9'))
        self.assertEqual(result['support_status'], 'unsupported')
        self.assertEqual(result['candidates'], [])
        self.assertIn('ambiguous_condition', str(result['unhandled_changes']))

    def test_compound_assignment_is_not_original_parameter(self):
        src = '''public class T {
 public static int f(int n) {
  int k = n;
  k += 1;
  if (k > 5) return 1;
  return 0;
 }
}
'''
        result = self.analyze_sources(src, src.replace('k > 5', 'k >= 5'))
        self.assertEqual(result['candidates'], [])
        self.assertIn('compound_assignment', str(result['changes'][0]['reasons']))

    def test_complete_branch_span_and_parameter_order(self):
        src = '''public class T {
 public static int f(String tag, int n, boolean enabled) {
  int k;
  k = n;
  if (k > 5) {
   return n;
  } else {
   return 0;
  }
 }
}
'''
        result = self.analyze_sources(src, src.replace('k > 5', 'k >= 8'),
                                      {'base_arguments': {'tag': 'ok', 'enabled': True}})
        self.assertEqual(result['support_status'], 'supported')
        ch = result['changes'][0]
        self.assertEqual(ch['before']['controlled_ranges']['then']['start_line'], 5)
        self.assertEqual(ch['before']['controlled_ranges']['then']['end_line'], 7)
        self.assertEqual(ch['before']['controlled_ranges']['else']['start_line'], 7)
        self.assertEqual(ch['before']['controlled_ranges']['else']['end_line'], 9)
        self.assertEqual(ch['after']['association']['parameter'], 'n')
        self.assertEqual([c['arguments'][1]['value'] for c in result['candidates']], [4, 5, 6, 7, 8, 9])
        self.assertTrue(all([a['name'] for a in c['arguments']] == ['tag', 'n', 'enabled'] for c in result['candidates']))
        self.assertTrue(all(c['arguments'][0]['value'] == 'ok' and c['arguments'][2]['value'] is True for c in result['candidates']))


if __name__ == '__main__': unittest.main()
