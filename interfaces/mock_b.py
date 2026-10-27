"""Interface demonstration only. Does NOT compile/execute targets or call an oracle."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from interfaces.a_contract import validate_a

def adapt(data):
    validate_a(data)
    if data.get('schema_version') != 'a.analysis.v1': raise ValueError('unsupported A interface version')
    if data.get('artifact_kind') != 'candidate_inputs_not_execution_results' or data.get('statistics_eligible') is not False: raise ValueError('not an A candidate artifact')
    ids = set(); results = []
    for candidate in data['candidates']:
        if candidate['case_id'] != data['case_id'] or candidate['candidate_id'] in ids: raise ValueError('inconsistent case/candidate identity')
        ids.add(candidate['candidate_id'])
        args, params = candidate['arguments'], candidate['method']['parameters']
        if [(x['name'], x['java_type']) for x in args] != [(x['name'], x['java_type']) for x in params]: raise ValueError('argument order/types do not match declaration')
        results.append({'candidate_id': candidate['candidate_id'], 'execution_status': 'simulated',
                        'versions': {v: {'status': 'simulated', 'value': 'MOCK_ONLY'} for v in ('before', 'patch', 'reference')},
                        'oracle': {'status': 'not_evaluated', 'classification': None}, 'reduction': {'status': 'not_implemented'}})
    return {'schema_version': 'b.execution.v1', 'case_id': data['case_id'], 'case_kind': data['case_kind'],
            'run_kind': 'mock', 'statistics_eligible': False, 'results': results}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--input', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); result = adapt(json.loads(a.input.read_text(encoding='utf-8')))
    with a.output.open('x', encoding='utf-8') as f: json.dump(result, f, ensure_ascii=False, indent=2)
    print('MOCK ONLY: no target execution, no oracle, excluded from real statistics')

if __name__ == '__main__': main()
