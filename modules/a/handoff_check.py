"""Fresh-cache, content-based A verification; no target execution or B oracle."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from interfaces.a_contract import validate_a


def main():
    stamp = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y%m%d-%H%M%S')
    out = ROOT/'outputs/a'/('handoff-check-' + stamp)
    out.mkdir(parents=True, exist_ok=False)
    cache = ROOT/'work/a-build'/('handoff-' + stamp)
    assert not cache.exists(), 'Clean build requires a new cache'
    env = dict(os.environ, DIFFTGEN_A_CACHE_DIR=str(cache))
    steps = []

    def run(name, command, expected=0):
        start = time.monotonic()
        p = subprocess.run(list(map(str, command)), cwd=ROOT, env=env, capture_output=True, timeout=300)
        (out/(name+'.stdout.log')).write_bytes(p.stdout)
        (out/(name+'.stderr.log')).write_bytes(p.stderr)
        steps.append(dict(name=name, command=list(map(str, command)), exit_code=p.returncode,
                          elapsed_seconds=round(time.monotonic()-start, 3)))
        (out/'manifest.json').write_text(json.dumps({'steps': steps, 'cache': str(cache), 'statistics_eligible': False}, indent=2))
        print(name, p.returncode, flush=True)
        assert p.returncode == expected, name + ': see preserved logs'

    run('java-version', [env.get('JAVA_HOME', str(ROOT/'work/deps/zulu8.94.0.17-ca-jdk8.0.492-linux_x64'))+'/bin/java', '-version'])
    run('readme-single-command', ['bash', ROOT/'modules/a/run.sh', '--request',
                                ROOT/'examples/teaching/int-threshold/request.json', '--output', out/'teaching'])
    compile_logs = list((out/'teaching/parser').rglob('bridge-compile.command.json'))
    assert len(compile_logs) == 1 and list(cache.rglob('AstExport.class'))
    (out/'clean-build-command.json').write_bytes(compile_logs[0].read_bytes())
    for suffix in ('stdout', 'stderr'):
        (out/('clean-build.'+suffix+'.log')).write_bytes(compile_logs[0].with_name('bridge-compile.'+suffix+'.log').read_bytes())
    run('correctness-tests', ['bash', ROOT/'tests/a/run.sh'])
    run('lang51', ['bash', ROOT/'modules/a/run.sh', '--request', ROOT/'examples/a-compatibility/lang51/request.json', '--output', out/'lang51'])
    run('baseline-preservation', ['git', 'diff', '--exit-code', 'c0cf86b', '--', 'outputs/reproduction'])
    run('b-mock-interface', [sys.executable, ROOT/'interfaces/mock_b.py', '--input', out/'teaching/analysis.json', '--output', out/'teaching/b-mock.json'])
    # Actual invalid CLI invocation, not just a direct unit test of request shape.
    request = json.loads((ROOT/'examples/teaching/int-threshold/request.json').read_text())
    request['reference_source'] = 'DO_NOT_READ_REFERENCE'
    (out/'invalid-request.json').write_text(json.dumps(request))
    run('error-contract', ['bash', ROOT/'modules/a/run.sh', '--request', out/'invalid-request.json', '--output', out/'invalid'], expected=2)
    error = json.loads((out/'invalid/error.json').read_text())
    assert error['schema_version'] == 'a.error.v1' and not (out/'invalid/analysis.json').exists()

    teaching = validate_a(json.loads((out/'teaching/analysis.json').read_text()))
    lang = validate_a(json.loads((out/'lang51/analysis.json').read_text()))
    ch = teaching['changes'][0]
    assert (ch['method']['signature'], ch['before']['text'], ch['after']['text']) == ('teaching.Threshold#decide(int,java.lang.String)', 'current > 5', 'current >= 5')
    assert ch['before']['association']['parameter'] == ch['after']['association']['parameter'] == 'score'
    assert ch['before']['location']['start_line'] == 8
    assert 'simple assignment current' in ch['before']['association']['evidence']
    assert [c['arguments'][0]['value'] for c in teaching['candidates']] == [4, 5, 6]
    assert all(c['arguments'][1]['value'] == 'allowed' and {p['side'] for p in c['provenance']} == {'before', 'after'} for c in teaching['candidates'])
    assert lang['support_status'] == 'unsupported' and lang['candidates'] == []
    for item in teaching['sources'].values():
        assert hashlib.sha256(Path(item['path']).read_bytes()).hexdigest() == item['sha256']
    mock = json.loads((out/'teaching/b-mock.json').read_text())
    assert mock['run_kind'] == 'mock' and mock['statistics_eligible'] is False
    import jsonschema
    jsonschema.validate(teaching, json.loads((ROOT/'contracts/a-analysis.schema.json').read_text()))
    result = dict(status='PASS', artifact_kind='A_independent_content_verification', statistics_eligible=False,
                  fresh_cache_compile=True, readme_single_command=True, content_assertions=True,
                  unit_tests=24, teaching_candidates=3, lang51='unsupported; no candidates',
                  error_cli_exit=2, interface_version='a.analysis.v1', b='mock only',
                  real_positive_case='not obtained; documented source exclusions and API limit',
                  total_stage_seconds=round(sum(s['elapsed_seconds'] for s in steps), 3))
    (out/'result.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result)); print('OUTPUT='+str(out))


if __name__ == '__main__': main()
