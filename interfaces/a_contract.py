"""Small, strict v1 consumer checks (not a general JSON Schema implementation)."""

def _valid(value, t):
    if t == 'int': return type(value) is int and -(2**31) <= value < 2**31
    if t == 'java.lang.String': return isinstance(value, str)
    if t == 'boolean': return type(value) is bool
    if t in ('int[]', 'boolean[]', 'java.lang.String[]'):
        return isinstance(value, list) and all(_valid(x, t[:-2]) for x in value)
    return False

def validate_a(data):
    fields = {'schema_version', 'artifact_kind', 'case_id', 'case_kind', 'statistics_eligible', 'support_status', 'scope', 'sources', 'diff_hunks', 'changes', 'unhandled_changes', 'candidates', 'generation', 'limitations'}
    if set(data) != fields: raise ValueError('A v1 top-level fields mismatch')
    if data['schema_version'] != 'a.analysis.v1' or data['artifact_kind'] != 'candidate_inputs_not_execution_results': raise ValueError('unsupported A artifact/version')
    if data['statistics_eligible'] is not False or data['case_kind'] not in ('teaching', 'real'): raise ValueError('invalid case/statistics metadata')
    if set(data['sources']) != {'before_source', 'patch_source', 'diff_path'}: raise ValueError('A must not contain reference source')
    if data['support_status'] not in ('supported', 'partial', 'unsupported'): raise ValueError('invalid support status')
    ids = set()
    for c in data['candidates']:
        if set(c) != {'candidate_id', 'case_id', 'method', 'arguments', 'provenance', 'validation'}: raise ValueError('candidate fields mismatch')
        if c['case_id'] != data['case_id'] or c['candidate_id'] in ids: raise ValueError('candidate identity mismatch')
        ids.add(c['candidate_id'])
        args, params = c['arguments'], c['method']['parameters']
        if [(x['name'], x['java_type']) for x in args] != [(x['name'], x['java_type']) for x in params]: raise ValueError('argument order/types do not match declaration')
        if not all(set(x) == {'name', 'java_type', 'value'} and _valid(x['value'], x['java_type']) for x in args): raise ValueError('invalid Java argument value/type')
        if not c['provenance'] or c['validation'].get('oracle_used') is not False: raise ValueError('invalid generation provenance or oracle leakage')
    return data
