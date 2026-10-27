import difflib
import json
from pathlib import Path
import tempfile
import unittest
from modules.a.analysis import analyze, verify_diff

class AstIntegrationTests(unittest.TestCase):
    def analyze_sources(self, before, patch, config=None):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root/'before.java').write_text(before, encoding='utf-8')
            (root/'patch.java').write_text(patch, encoding='utf-8')
            (root/'change.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True), patch.splitlines(True), fromfile='a/T.java', tofile='b/T.java')), encoding='utf-8')
            r = dict(schema_version='a.request.v1', case_id='integration-teaching', case_kind='teaching', before_source='before.java', patch_source='patch.java', diff_path='change.diff', config=config or {})
            return analyze(r, root, root/'parser')

    def test_ast_alias_assignment_ranges_and_changed_constants(self):
        src = '''package teaching;
public class T {
 public static int f(int score, String tag) {
  int n;
  n = score;
  if (n > 5) { return 1; } else { return 2; }
 }
}
'''
        a = self.analyze_sources(src, src.replace('n > 5', 'n >= 8'), {'base_arguments': {'tag': 'legal'}})
        self.assertEqual(a['support_status'], 'supported')
        ch = a['changes'][0]
        self.assertEqual(ch['before']['association']['parameter'], 'score')
        self.assertIn('simple assignment n', ch['before']['association']['evidence'])
        self.assertEqual(ch['before']['location']['start_line'], 6)
        self.assertEqual(ch['before']['controlled_ranges']['then']['start_line'], 6)
        self.assertIsNotNone(ch['before']['controlled_ranges']['else'])
        self.assertEqual([x['arguments'][0]['value'] for x in a['candidates']], [4, 5, 6, 7, 8, 9])

    def test_ast_string_array_and_reversed_comparisons(self):
        src = '''public class T {
 public static int s(String input) {
  String alias = input;
  int length = alias.length();
  if (length > 0) return 1;
  return 0;
 }
 public static int a(int[] items) {
  int[] alias = items;
  if (alias.length < 1) return 1;
  return 0;
 }
 public static int r(int n) {
  if (0xF < n) return 1;
  return 0;
 }
}
'''
        patch = src.replace('length > 0', 'length >= 2').replace('alias.length < 1', 'alias.length <= 1').replace('0xF < n', '0xF <= n')
        a = self.analyze_sources(src, patch, {'array_fill_values': {'int[]': 7}})
        self.assertEqual(len(a['changes']), 3)
        by = {x['method']['name']: x for x in a['changes']}
        self.assertTrue(all(x['support_status'] == 'supported' for x in by.values()))
        self.assertEqual(by['s']['before']['association']['parameter'], 'input')
        self.assertEqual(by['a']['before']['association']['measure'], 'length')
        self.assertEqual(by['r']['before']['association']['boundary'], 15)
        self.assertEqual(by['r']['before']['association']['operator'], '>')

    def test_complex_calls_loop_and_control_dependent_assignment_unsupported(self):
        src = '''public class T {
 public static int unknown(int n) { return n; }
 public static int f(int n) {
  if (unknown(n) > 5) return 1;
  return 0;
 }
 public static int loop(int n) {
  while (n > 5) { n--; }
  return n;
 }
 public static int join(int n) {
  int k = n;
  if (n > 0) k = 0;
  if (k > 5) return 1;
  return 0;
 }
}
'''
        patch = src.replace('unknown(n) > 5', 'unknown(n) >= 5').replace('while (n > 5)', 'while (n >= 5)').replace('if (k > 5)', 'if (k >= 5)')
        a = self.analyze_sources(src, patch)
        self.assertEqual(a['support_status'], 'unsupported'); self.assertEqual(a['candidates'], [])
        reasons = json.dumps([x['reasons'] for x in a['changes']])
        self.assertIn('MethodInvocation', reasons)
        self.assertIn('loop_condition', reasons)
        self.assertIn('control_flow_assignment', reasons)

    def test_signature_change_and_ambiguous_pair_not_guessed(self):
        a = self.analyze_sources('public class T { public static int f(int n) { if(n>5)return 1;return 0;} }\n',
                                 'public class T { public static int f(long n) { if(n>=5)return 1;return 0;} }\n')
        self.assertEqual(a['candidates'], [])
        self.assertTrue(all('signature_changed' in x['reason'] for x in a['unhandled_changes']))

    def test_syntax_error_is_not_silently_analyzed(self):
        with self.assertRaisesRegex(ValueError, 'JAVA_SYNTAX_ERROR'):
            self.analyze_sources('public class T { public static int f(int n) { if(n>)return 1;return 0;} }\n',
                                 'public class T { public static int f(int n) { if(n>=5)return 1;return 0;} }\n')

    def test_mismatched_or_incomplete_diff_rejected(self):
        before, patch = 'a\nb\nc\n', 'a\nx\ny\n'
        bad = '--- a/T\n+++ b/T\n@@ -2 +2 @@\n-b\n+x\n'
        with self.assertRaisesRegex(ValueError, 'INCOMPLETE'): verify_diff(before, patch, bad)
        with self.assertRaisesRegex(ValueError, 'MISMATCH'): verify_diff(before, patch, bad.replace('-b', '-z'))

    def test_utf16_source_positions_and_no_oracle_fields(self):
        src = '// 😀\npublic class T { public static int f(int n) { if(n>5)return 1;return 0;} }\n'
        a = self.analyze_sources(src, src.replace('n>5', 'n>=5'))
        self.assertEqual(a['changes'][0]['before']['text'], 'n>5')
        self.assertNotIn('reference_source', a['sources'])
        self.assertTrue(all(x['validation']['oracle_used'] is False for x in a['candidates']))

    def test_ast_integer_extremes_and_enclosing_guard(self):
        src = '''public class T {
 public static int high(int n) {
  if (n < 2147483647) return 1;
  return 0;
 }
 public static int low(int n) {
  if (n > -2147483648) return 1;
  return 0;
 }
 public static int guarded(int n) {
  if (n != 0) {
   if (n > 5) return 1;
  }
  return 0;
 }
}
'''
        patch = src.replace('n < 2147483647', 'n <= 2147483647').replace('n > -2147483648', 'n >= -2147483648').replace('n > 5', 'n >= 5')
        a = self.analyze_sources(src, patch)
        by = {x['method']['name']: x for x in a['changes']}
        self.assertEqual(by['low']['before']['association']['boundary'], -(2**31))
        self.assertEqual(by['high']['after']['association']['boundary'], 2**31-1)
        self.assertEqual(by['guarded']['support_status'], 'partial')
        for c in a['candidates']:
            self.assertTrue(-(2**31) <= c['arguments'][0]['value'] <= 2**31-1)

    def test_external_state_in_controlled_branch_is_not_guessed(self):
        src = '''public class T {
 static int shared = 10;
 public static int f(int n) {
  if (n > 5) return shared;
  return 0;
 }
}
'''
        a = self.analyze_sources(src, src.replace('n > 5', 'n >= 5'))
        self.assertEqual(a['support_status'], 'unsupported')
        self.assertEqual(a['candidates'], [])
        self.assertIn('binding_state_analysis', str(a['changes'][0]['reasons']))

if __name__ == '__main__': unittest.main()
