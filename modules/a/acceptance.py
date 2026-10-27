"""A-only acceptance: parse/generate, interface mock, correctness tests, preservation audit."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from interfaces.a_contract import validate_a

resume = len(sys.argv) == 3 and sys.argv[1] == '--resume'
if resume:
    out = Path(sys.argv[2]).resolve()
    if out.parent != (ROOT/'outputs/a').resolve() or not out.name.startswith('acceptance-'): raise ValueError('resume must target A acceptance evidence only')
    steps = json.loads((out/'manifest.json').read_text())['steps']
    assert [s['step'] for s in steps] == ['teaching', 'mock-b', 'lang51-compatibility', 'correctness-tests', 'baseline-preservation', 'author-source-preservation']
    assert all(s['exit_code'] == 0 for s in steps[:-1]) and steps[-1]['exit_code'] == 1
    assert not (out/'result.json').exists() and not (out/'resume-manifest.json').exists()
else:
    out = ROOT/'outputs/a'/('acceptance-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    out.mkdir(parents=True, exist_ok=False)
    steps = []
def step(name, cmd):
    start = time.monotonic()
    with (out/(name+'.stdout.log')).open('w') as stdout, (out/(name+'.stderr.log')).open('w') as stderr:
        p = subprocess.run(list(map(str, cmd)), cwd=ROOT, stdout=stdout, stderr=stderr, timeout=300)
    steps.append({'step': name, 'command': list(map(str, cmd)), 'exit_code': p.returncode, 'elapsed_seconds': round(time.monotonic()-start, 3)})
    (out/('resume-manifest.json' if resume else 'manifest.json')).write_text(json.dumps({'kind': 'A_acceptance_not_real_detection_statistics', 'statistics_eligible': False, 'steps': steps}, indent=2), encoding='utf-8')
    print(name, p.returncode, flush=True)
    if p.returncode: raise SystemExit(p.returncode)

if not resume:
    step('teaching', ['bash', ROOT/'modules/a/run.sh', '--request', ROOT/'examples/teaching/int-threshold/request.json', '--output', out/'teaching'])
    step('mock-b', [sys.executable, ROOT/'interfaces/mock_b.py', '--input', out/'teaching/analysis.json', '--output', out/'teaching/b-mock.json'])
    step('lang51-compatibility', ['bash', ROOT/'modules/a/run.sh', '--request', ROOT/'examples/a-compatibility/lang51/request.json', '--output', out/'lang51'])
    step('correctness-tests', [sys.executable, '-m', 'unittest', 'discover', '-s', ROOT/'tests/a', '-v'])
    step('baseline-preservation', ['git', 'diff', '--exit-code', 'HEAD', '--', 'outputs/reproduction'])
# Per-command setting only: author's checkout was created by Windows Git with CRLF.
step('author-source-preservation-normalized', ['git', '-c', 'core.autocrlf=true', '-C', ROOT/'work/DiffTGen', 'diff', '--exit-code', '--', 'src', 'build.xml', 'tclassrunner.xml'])

teaching = validate_a(json.loads((out/'teaching/analysis.json').read_text()))
compat = validate_a(json.loads((out/'lang51/analysis.json').read_text()))
mock = json.loads((out/'teaching/b-mock.json').read_text())
assert [x['arguments'][0]['value'] for x in teaching['candidates']] == [4, 5, 6]
assert all(x['arguments'][1]['value'] == 'allowed' and len(x['provenance']) == 2 for x in teaching['candidates'])
assert compat['support_status'] == 'unsupported' and not compat['candidates']
assert mock['run_kind'] == 'mock' and mock['statistics_eligible'] is False
assert all(x['oracle']['classification'] is None for x in mock['results'])
schemas = {p.name: json.loads(p.read_text()) for p in (ROOT/'contracts').glob('*.schema.json')}
schema_validation = 'JSON parsed; runtime v1 consumer checks passed (not a generic JSON Schema validator)'
try:
    import jsonschema
except ImportError:
    pass
else:
    jsonschema.validate(teaching, schemas['a-analysis.schema.json'])
    jsonschema.validate(compat, schemas['a-analysis.schema.json'])
    jsonschema.validate(mock, schemas['b-execution.schema.json'])
    jsonschema.validate(json.loads((ROOT/'examples/teaching/int-threshold/request.json').read_text()), schemas['a-request.schema.json'])
    schema_validation = 'full JSON Schema validation passed using installed jsonschema'
result = {'status': 'PASS', 'kind': 'A_mechanism_acceptance_only', 'statistics_eligible': False,
          'teaching_candidates': 3, 'lang51_new_strategy': 'unsupported; zero candidates; no baseline replay',
          'b_adapter': 'mock only; no target execution/oracle/reduction', 'schema_validation': schema_validation,
          'baseline_tracked_evidence_unchanged': True, 'author_source_unchanged': True}
if resume: result['audit_note'] = 'Initial WSL diff reported Windows CRLF checkout differences; normalized read-only audit passed. Original failure logs/manifest preserved; tests were not rerun.'
(out/'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2)); print('OUTPUT='+str(out))
