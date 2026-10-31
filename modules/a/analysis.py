"""Conservative, intraprocedural AST analysis. Does not read an oracle or execute targets."""
from copy import deepcopy
import difflib
import hashlib
import json
from pathlib import Path
import re
from .ast_bridge import export_ast

INT_MIN, INT_MAX = -(2**31), 2**31 - 1
OPS = {'<', '<=', '>', '>=', '==', '!='}
REVERSE = {'<': '>', '<=': '>=', '>': '<', '>=': '<=', '==': '==', '!=': '!='}
ARRAY_TYPES = {'int[]', 'boolean[]', 'java.lang.String[]'}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def identifier(n):
    return n.get('identifier') if n and n.get('kind') == 'SimpleName' else None

def text_of(source, node):
    s = node['span']
    return source.encode('utf-16-le')[s['start_offset']*2:s['end_offset_exclusive']*2].decode('utf-16-le')

def touched(node, lines):
    return bool(node) and any(node['span']['start_line'] <= i <= node['span']['end_line'] for i in lines)

def children(node):
    if not isinstance(node, dict): return
    for k, v in node.items():
        if k == 'span': continue
        if isinstance(v, dict) and 'kind' in v: yield v
        elif isinstance(v, list):
            for x in v:
                if isinstance(x, dict) and 'kind' in x: yield x

def descendants(node):
    if not node: return
    yield node
    for ch in children(node): yield from descendants(ch)

def verify_diff(before, patch, diff):
    """Parse/verify unified diff hunks, not Java structure. One file pair only."""
    old, new, lines = before.splitlines(), patch.splitlines(), diff.splitlines()
    if sum(s.startswith('--- ') for s in lines) != 1 or sum(s.startswith('+++ ') for s in lines) != 1:
        raise ValueError('DIFF_FORMAT: exactly one unified file diff is required')
    changed_old, changed_new, ranges = set(), set(), []
    i = 0
    while i < len(lines):
        m = re.match(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', lines[i])
        if not m:
            i += 1; continue
        a, ac, b, bc = (int(m[1]), int(m[2] or 1), int(m[3]), int(m[4] or 1))
        oi, ni, used_o, used_n = a-1 if ac else a, b-1 if bc else b, 0, 0
        ranges.append({'before_start': a, 'before_count': ac, 'patch_start': b, 'patch_count': bc})
        i += 1
        while used_o < ac or used_n < bc:
            if i >= len(lines): raise ValueError('DIFF_FORMAT: truncated hunk')
            line = lines[i]; i += 1
            if line.startswith('\\ No newline'): continue
            if not line or line[0] not in ' +-': raise ValueError('DIFF_FORMAT: invalid hunk line')
            op, content = line[0], line[1:]
            if op in ' -':
                if oi >= len(old) or old[oi] != content: raise ValueError('DIFF_MISMATCH: before hunk does not match source')
                if op == '-': changed_old.add(oi+1)
                oi += 1; used_o += 1
            if op in ' +':
                if ni >= len(new) or new[ni] != content: raise ValueError('DIFF_MISMATCH: patch hunk does not match source')
                if op == '+': changed_new.add(ni+1)
                ni += 1; used_n += 1
            if used_o > ac or used_n > bc: raise ValueError('DIFF_FORMAT: hunk counts inconsistent')
    if not ranges or not (changed_old or changed_new): raise ValueError('DIFF_FORMAT: no changed lines')
    # A valid subset of hunks is insufficient: reject omitted changes as well.
    matcher = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
    for tag, a, ae, b, be in matcher.get_opcodes():
        if tag != 'equal' and (not set(range(a+1, ae+1)) <= changed_old or not set(range(b+1, be+1)) <= changed_new):
            raise ValueError('DIFF_INCOMPLETE: source differences omitted from supplied diff')
    return changed_old, changed_new, ranges

def unsupported(reason): return {'kind': 'unsupported', 'reason': reason}

def int_literal(n):
    if n['kind'] == 'ParenthesizedExpression': return int_literal(n['expression'])
    if n['kind'] == 'PrefixExpression' and n['operator'] in ('-', '+'):
        v = int_literal(n['operand'])
        if v is None: return None
        if n['operator'] == '-': return INT_MIN if v == INT_MIN else -v
        return v
    if n['kind'] != 'NumberLiteral': return None
    t = n['token'].replace('_', '')
    if t.lower().endswith('l') or '.' in t: return None
    if not t.lower().startswith('0x') and t.lower().endswith(('f', 'd')): return None
    try:
        if t.lower().startswith('0x'): v = int(t[2:], 16)
        elif t.lower().startswith('0b'): v = int(t[2:], 2)
        elif len(t) > 1 and t.startswith('0'): v = int(t, 8)
        else: return int(t, 10)
        if v > 0xffffffff: return None
        return v - 2**32 if v > INT_MAX else v
    except ValueError: return None

def resolve(n, env):
    if not n: return unsupported('missing_expression')
    kind = n['kind']
    if kind == 'ParenthesizedExpression': return resolve(n['expression'], env)
    if kind == 'SimpleName': return deepcopy(env.get(identifier(n), unsupported('unresolved_name:' + identifier(n))))
    val = int_literal(n)
    if val is not None:
        return {'kind': 'constant', 'value': val, 'value_type': 'int', 'evidence': ['integer literal AST']}
    if kind == 'MethodInvocation' and identifier(n['name']) == 'length' and not n['arguments']:
        base = resolve(n.get('expression'), env)
        if base.get('kind') == 'parameter' and base['value_type'] == 'java.lang.String':
            return dict(base, measure='length', value_type='int', evidence=base['evidence'] + ['String.length() AST'])
        return unsupported('length_receiver_not_direct_string_parameter_or_alias')
    if kind in ('QualifiedName', 'FieldAccess') and identifier(n['name']) == 'length':
        base = resolve(n.get('qualifier', n.get('expression')), env)
        if base.get('kind') == 'parameter' and base['value_type'] in ARRAY_TYPES:
            return dict(base, measure='length', value_type='int', evidence=base['evidence'] + ['array.length AST'])
        return unsupported('length_receiver_not_supported_array_parameter_or_alias')
    return unsupported('unsupported_expression:' + kind + '; no interprocedural/object/reflection inference')

def writes(stmt):
    out = set()
    for n in descendants(stmt):
        if n['kind'] == 'Assignment':
            name = identifier(n['leftHandSide'])
            if name: out.add(name)
        if n['kind'] in ('PrefixExpression', 'PostfixExpression') and n['operator'] in ('++', '--'):
            name = identifier(n['operand'])
            if name: out.add(name)
    return out

def java_type(n):
    if n['kind'] == 'PrimitiveType': return n['primitiveTypeCode']
    if n['kind'] == 'SimpleType':
        name = n['name']
        if name['kind'] == 'SimpleName': return 'java.lang.String' if name['identifier'] == 'String' else name['identifier']
    return None

def complex_features(node):
    """Conservative syntactic exclusions, including opaque controlled statements."""
    if not node: return []
    if node['kind'] in ('SimpleType', 'QualifiedType', 'ArrayType', 'PrimitiveType'): return []
    reasons = []
    k = node['kind']
    if k == 'MethodInvocation' and (identifier(node['name']) != 'length' or node['arguments']):
        reasons.append('cross_function_or_reflective_call_not_supported:' + str(identifier(node['name'])))
    if k in ('ClassInstanceCreation', 'ThisExpression', 'SuperMethodInvocation', 'SuperFieldAccess', 'AnonymousClassDeclaration'):
        reasons.append('complex_object_state_not_supported:' + k)
    if k in ('QualifiedName', 'FieldAccess') and identifier(node['name']) != 'length':
        reasons.append('field_or_external_state_not_supported')
    for ch in children(node): reasons.extend(complex_features(ch))
    return sorted(set(reasons))


def unresolved_body_names(method):
    """Reject opaque unqualified state too (e.g. an imported static field).

    This is a syntactic rejection check, not symbol binding or value inference.
    """
    known = {p['name'] for p in method['parameters']}
    for n in descendants(method.get('body')):
        if n['kind'] in ('VariableDeclarationFragment', 'SingleVariableDeclaration'):
            known.add(identifier(n['name']))
    unknown = set()
    def visit(n):
        if not n or n['kind'] in ('SimpleType', 'QualifiedType', 'ArrayType', 'PrimitiveType'): return
        if n['kind'] == 'SimpleName':
            if identifier(n) not in known: unknown.add(identifier(n))
            return
        for key, value in n.items():
            if key == 'span': continue
            # Method/field name is separately checked by complex_features/resolve.
            if key == 'name' and n['kind'] in ('MethodInvocation', 'QualifiedName', 'FieldAccess'): continue
            if isinstance(value, dict) and 'kind' in value: visit(value)
            elif isinstance(value, list):
                for x in value:
                    if isinstance(x, dict) and 'kind' in x: visit(x)
    visit(method.get('body'))
    return ['unresolved_body_name_requires_binding:' + x for x in sorted(unknown)]

def condition_records(method, source):
    records = []
    env = {p['name']: {'kind': 'parameter', 'parameter': p['name'], 'java_type': p['java_type'],
                      'value_type': p['java_type'], 'measure': 'value', 'evidence': ['method parameter ' + p['name']]}
           for p in method['parameters']}
    def walk(stmt, env, guards, blocked):
        if not stmt: return
        kind = stmt['kind']
        if kind == 'Block':
            local = deepcopy(env); existing = set(env); declared = set()
            for s in stmt['statements']:
                if s['kind'] == 'VariableDeclarationStatement':
                    declared.update(identifier(f['name']) for f in s['fragments'])
                walk(s, local, guards, blocked)
            for name in existing - declared: env[name] = local[name]
        elif kind == 'VariableDeclarationStatement':
            t = java_type(stmt['type'])
            for f in stmt['fragments']:
                name = identifier(f['name']); value = resolve(f.get('initializer'), env)
                # Arrays may have dimensions on either type/name; conservatively accept
                # alias if initializer's value type agrees with source declaration text.
                decl = text_of(source, stmt['type']).replace('String', 'java.lang.String')
                if decl.startswith('java.lang.java.lang.'): decl = decl.replace('java.lang.java.lang.', 'java.lang.')
                decl += '[]' * (f.get('extraDimensions', 0) + len(f.get('extraDimensions2', [])))
                if value.get('value_type') != decl: value = unsupported('local_type_or_initializer_not_supported')
                elif value.get('kind') != 'unsupported': value['evidence'].append('local declaration ' + name)
                if value.get('kind') == 'unsupported': value['value_type'] = decl
                env[name] = value
        elif kind == 'ExpressionStatement':
            e = stmt['expression']
            if e['kind'] == 'Assignment' and identifier(e['leftHandSide']):
                name = identifier(e['leftHandSide']); old = env.get(name, {})
                v = resolve(e['rightHandSide'], env) if e['operator'] == '=' else unsupported('compound_assignment')
                if v.get('kind') != 'unsupported' and old.get('value_type') == v.get('value_type'):
                    v['evidence'].append('simple assignment ' + name)
                elif v.get('kind') != 'unsupported': v = unsupported('assignment_type_or_binding_unknown')
                env[name] = v
            else:
                for name in writes(stmt): env[name] = unsupported('mutation_before_condition')
        elif kind in ('IfStatement', 'WhileStatement', 'ForStatement', 'DoStatement'):
            e = stmt.get('expression')
            direct = {}
            if kind == 'IfStatement':
                direct = {'then': stmt['thenStatement']['span'], 'else': stmt['elseStatement']['span'] if stmt.get('elseStatement') else None}
            else: direct = {'body': stmt['body']['span']}
            reason = blocked or (None if kind == 'IfStatement' else 'loop_condition_or_loop_carried_state_not_supported')
            if e:
                records.append({'text': text_of(source, e), 'location': e['span'], 'statement_location': stmt['span'],
                                'control_kind': kind, 'controlled_ranges': direct, 'guards': guards,
                                '_expression': e, '_env': deepcopy(env), '_blocked': reason})
            for child in ('thenStatement', 'elseStatement', 'body'):
                branch = {'thenStatement': 'then', 'elseStatement': 'else', 'body': 'body'}[child]
                nextguards = guards + ([{'condition': text_of(source, e), 'location': e['span'], 'branch': branch}] if e else [])
                if stmt.get(child): walk(stmt[child], deepcopy(env), nextguards, reason)
            for name in writes(stmt):
                if name in env: env[name] = unsupported('control_flow_assignment_requires_dataflow_join')
        else:
            if kind not in ('ReturnStatement', 'ThrowStatement', 'EmptyStatement', 'BreakStatement', 'ContinueStatement'):
                for ch in children(stmt):
                    walk(ch, deepcopy(env), guards, blocked or 'complex_statement_control_not_supported:' + kind)
                for name in writes(stmt):
                    if name in env: env[name] = unsupported('complex_statement_write')
    walk(method.get('body'), env, [], None)
    return records

def normalize(record):
    if record['_blocked']: return unsupported(record['_blocked'])
    n = record['_expression']
    while n['kind'] == 'ParenthesizedExpression': n = n['expression']
    if n['kind'] != 'InfixExpression' or n['operator'] not in OPS or n.get('extendedOperands'):
        return unsupported('condition_is_not_one_supported_comparison')
    left, right = resolve(n['leftOperand'], record['_env']), resolve(n['rightOperand'], record['_env'])
    op = n['operator']
    if left.get('kind') == 'constant' and right.get('kind') == 'parameter': left, right, op = right, left, REVERSE[op]
    if left.get('kind') != 'parameter' or right.get('kind') != 'constant':
        return unsupported('comparison_needs_one_parameter_measure_and_integer_constant: ' + str([left, right]))
    if left['value_type'] != 'int' or (left['measure'] == 'value' and left['java_type'] != 'int'):
        return unsupported('only_Java_int_values_or_supported_lengths')
    if not INT_MIN <= right['value'] <= INT_MAX: return unsupported('comparison_constant_outside_Java_int')
    return dict(left, operator=op, boundary=right['value'], evidence=left['evidence'] + right['evidence'])

def check_value(value, t, constraints):
    permitted = {'min', 'max'} if t == 'int' else ({'min_length', 'max_length'} if t == 'java.lang.String' or t in ARRAY_TYPES else set())
    if set(constraints) - permitted: return 'constraint_not_applicable_to_parameter_type'
    if t == 'int':
        if type(value) is not int or not INT_MIN <= value <= INT_MAX: return 'not_Java_int'
        if value < constraints.get('min', INT_MIN) or value > constraints.get('max', INT_MAX): return 'configured_numeric_domain'
    elif t == 'boolean':
        if type(value) is not bool: return 'not_boolean'
    elif t == 'java.lang.String':
        if not isinstance(value, str): return 'not_string'
        length = len(value.encode('utf-16-le'))//2
        if length < constraints.get('min_length', 0) or length > constraints.get('max_length', INT_MAX): return 'configured_length_domain'
    elif t in ARRAY_TYPES:
        if not isinstance(value, list): return 'not_array'
        if len(value) < constraints.get('min_length', 0) or len(value) > constraints.get('max_length', INT_MAX): return 'configured_length_domain'
        elem = t[:-2]
        for v in value:
            if elem == 'boolean':
                if type(v) is not bool: return 'not_boolean_element'
            elif check_value(v, elem, {}): return 'invalid_array_element'
    else: return 'unsupported_parameter_type:' + t
    return None

def validate_request(r):
    required = {'schema_version', 'case_id', 'case_kind', 'before_source', 'patch_source', 'diff_path', 'config'}
    if not isinstance(r, dict) or set(r) != required or r.get('schema_version') != 'a.request.v1': raise ValueError('REQUEST_SCHEMA: exact v1 fields required; reference/oracle/unknown fields forbidden')
    if any(not isinstance(r[k], str) or not r[k] for k in ('before_source', 'patch_source', 'diff_path')): raise ValueError('REQUEST_SCHEMA: source/diff paths must be nonempty strings')
    if r['case_kind'] not in ('teaching', 'real') or not isinstance(r['case_id'], str) or not r['case_id']: raise ValueError('REQUEST_SCHEMA: invalid case identity')
    c = r['config']
    allowed = {'base_arguments', 'parameter_constraints', 'max_candidates', 'max_length', 'string_fill', 'array_fill_values'}
    if not isinstance(c, dict) or set(c)-allowed: raise ValueError('CONFIG_SCHEMA: unknown/forbidden config field')
    for key, default, upper in [('max_candidates', 32, 1000), ('max_length', 1024, 100000)]:
        v = c.get(key, default)
        if type(v) is not int or not 0 <= v <= upper: raise ValueError('CONFIG_SCHEMA: invalid ' + key)
    if not isinstance(c.get('base_arguments', {}), dict) or not isinstance(c.get('array_fill_values', {}), dict): raise ValueError('CONFIG_SCHEMA: arguments/fills must be objects')
    for t, value in c.get('array_fill_values', {}).items():
        if t not in ARRAY_TYPES or check_value([value], t, {}): raise ValueError('CONFIG_SCHEMA: invalid typed array fill')
    fill = c.get('string_fill', 'a')
    if not isinstance(fill, str) or len(fill) != 1 or not 32 <= ord(fill) <= 126: raise ValueError('CONFIG_SCHEMA: string_fill must be one printable ASCII character')
    cons = c.get('parameter_constraints', {})
    if not isinstance(cons, dict): raise ValueError('CONFIG_SCHEMA: constraints must be object')
    for name, values in cons.items():
        if not isinstance(values, dict) or set(values)-{'min', 'max', 'min_length', 'max_length'}: raise ValueError('CONFIG_SCHEMA: unsupported constraint')
        if any(type(v) is not int for v in values.values()): raise ValueError('CONFIG_SCHEMA: constraint bounds must be integers')
        if values.get('min', INT_MIN) > values.get('max', INT_MAX) or values.get('min_length', 0) < 0 or values.get('min_length', 0) > values.get('max_length', INT_MAX): raise ValueError('CONFIG_SCHEMA: inconsistent constraint domain')

def generate(changes, config, case_id):
    candidates, seen, events = [], {}, []
    limit, maxlen = config.get('max_candidates', 32), config.get('max_length', 1024)
    truncated = 0
    for change in changes:
        if change['support_status'] == 'unsupported': continue
        for side in ('before', 'after'):
            relation = change[side]['association']; params = change['method']['parameters']
            target, boundary = relation['parameter'], relation['boundary']
            for delta in (-1, 0, 1):
                v = boundary + delta
                prov = {'change_id': change['change_id'], 'side': side, 'condition': change[side]['text'], 'parameter': target,
                        'boundary': boundary, 'offset': delta, 'rule': 'threshold_minus_equal_plus_one', 'measure': relation['measure']}
                reason = None
                if not INT_MIN <= v <= INT_MAX: reason = 'Java_int_overflow_avoided'
                elif relation['measure'] == 'length':
                    if v < 0: reason = 'negative_length'
                    elif v > maxlen: reason = 'length_resource_budget'
                    elif relation['java_type'] == 'java.lang.String': v = config.get('string_fill', 'a') * v
                    else:
                        fills = config.get('array_fill_values', {})
                        if relation['java_type'] not in fills: reason = 'explicit_array_fill_required'
                        else: v = [deepcopy(fills[relation['java_type']]) for _ in range(v)]
                args = []
                if not reason:
                    for p in params:
                        name, t = p['name'], p['java_type']
                        if name == target: value = v
                        elif name in config.get('base_arguments', {}): value = deepcopy(config['base_arguments'][name])
                        else: reason = 'explicit_legal_base_argument_required:' + name; break
                        bad = check_value(value, t, config.get('parameter_constraints', {}).get(name, {}))
                        if bad: reason = name + ':' + bad; break
                        args.append({'name': name, 'java_type': t, 'value': value})
                if reason:
                    events.append(dict(prov, disposition='skipped', reason=reason)); continue
                key = json.dumps([change['method']['signature'], args], sort_keys=True, ensure_ascii=True)
                if key in seen:
                    seen[key]['provenance'].append(prov); continue
                if len(candidates) >= limit:
                    truncated += 1; events.append(dict(prov, disposition='truncated', reason='max_candidates')); continue
                item = {'candidate_id': case_id + '-' + digest(key.encode())[:12], 'case_id': case_id,
                        'method': change['method'], 'arguments': args, 'provenance': [prov],
                        'validation': {'type_and_config_checked': True, 'business_validity': 'not_proven', 'path_feasibility': 'not_proven', 'oracle_used': False}}
                candidates.append(item); seen[key] = item
    return candidates, {'max_candidates': limit, 'max_length': maxlen, 'retained': len(candidates), 'truncated_attempts': truncated, 'events': events}

def analyze(request, request_dir, evidence_dir):
    validate_request(request)
    paths = {k: (Path(request_dir) / request[k]).resolve() for k in ('before_source', 'patch_source', 'diff_path')}
    raw = {k: p.read_bytes() for k, p in paths.items()}
    sources = {k: {'path': str(paths[k]), 'sha256': digest(raw[k])} for k in paths}
    source = {k: v.decode('utf-8') for k, v in raw.items()}
    oldlines, newlines, hunks = verify_diff(source['before_source'], source['patch_source'], source['diff_path'])
    asts = {k: export_ast(paths[k], Path(evidence_dir)/k) for k in ('before_source', 'patch_source')}
    methods = {k: {m['signature']: m for m in a['methods']} for k, a in asts.items()}
    changes, unhandled = [], []
    for signature in sorted(set(methods['before_source']) | set(methods['patch_source'])):
        bm, pm = methods['before_source'].get(signature), methods['patch_source'].get(signature)
        if not (touched(bm, oldlines) or touched(pm, newlines)): continue
        if not bm or not pm:
            unhandled.append({'file': str(paths['before_source']), 'signature': signature, 'support_status': 'unsupported', 'reason': 'method_added_removed_or_signature_changed'}); continue
        br = [x for x in condition_records(bm, source['before_source']) if any(x['location']['start_line'] <= n <= x['location']['end_line'] for n in oldlines)]
        pr = [x for x in condition_records(pm, source['patch_source']) if any(x['location']['start_line'] <= n <= x['location']['end_line'] for n in newlines)]
        if len(br) != 1 or len(pr) != 1:
            unhandled.append({'file': str(paths['before_source']), 'signature': signature, 'support_status': 'unsupported', 'reason': 'ambiguous_condition_mapping_or_not_one_modified_condition', 'before_conditions': [x['text'] for x in br], 'after_conditions': [x['text'] for x in pr]}); continue
        b, p = br[0], pr[0]
        bc, pc = normalize(b), normalize(p)
        reasons = []
        reasons.extend(complex_features(bm.get('body')))
        reasons.extend(complex_features(pm.get('body')))
        reasons.extend(unresolved_body_names(bm))
        reasons.extend(unresolved_body_names(pm))
        if b['text'] == p['text']: reasons.append('condition_text_unchanged_body_only_or_same_line_change')
        if bm['constructor'] or not bm['is_static'] or not pm['is_static']: reasons.append('instance_state_or_constructor_not_supported')
        if bm.get('owner_has_fields_or_inheritance') or pm.get('owner_has_fields_or_inheritance'): reasons.append('declaring_class_fields_or_inheritance_require_binding_state_analysis')
        if any(x.get('varargs') for x in bm['parameters']): reasons.append('varargs_not_supported')
        if any(x['java_type'] not in ({'int', 'boolean', 'java.lang.String'} | ARRAY_TYPES) for x in bm['parameters']): reasons.append('complex_or_unsupported_parameter_type')
        for side, relation in [('before', bc), ('after', pc)]:
            if relation['kind'] == 'unsupported': reasons.append(side + ':' + relation['reason'])
        info = {k: bm[k] for k in ('class_name', 'name', 'signature', 'parameters', 'return_type', 'is_static')}
        status = 'unsupported' if reasons else ('partial' if b['guards'] or p['guards'] else 'supported')
        change = {'change_id': 'change-' + str(len(changes)+1), 'file': str(paths['before_source']), 'method': info,
                  'support_status': status, 'reasons': reasons, 'analysis_basis': ['JDT structural AST', 'validated unified diff hunk overlap', 'unique changed condition per matching method signature', 'straight-line local alias substitution only'],
                  'before': {k: v for k, v in b.items() if not k.startswith('_')}, 'after': {k: v for k, v in p.items() if not k.startswith('_')}}
        change['before']['association'] = bc; change['after']['association'] = pc
        if status == 'partial': change['reasons'].append('enclosing_guard_path_feasibility_not_proven')
        changes.append(change)
    known = {p['name'] for d in methods.values() for m in d.values() for p in m['parameters']}
    c = request['config']
    if (set(c.get('base_arguments', {})) | set(c.get('parameter_constraints', {}))) - known: raise ValueError('CONFIG_SCHEMA: configured parameter not declared')
    candidates, generation = generate(changes, c, request['case_id'])
    generation['status'] = 'candidates_available' if candidates else ('budget_exhausted' if generation['truncated_attempts'] else 'no_candidates; see unsupported reasons and skipped events')
    here = Path(__file__).resolve()
    generation['implementation'] = {'version': 'a.local.v1', 'python_analysis_sha256': digest(here.read_bytes()),
        'ast_adapter_sha256': digest((here.parent/'java/AstExport.java').read_bytes()),
        'parser': 'author Eclipse JDT JLS4, Java7 syntax', 'binding_resolution': False}
    if not changes and not unhandled:
        unhandled.append({'file': str(paths['before_source']), 'signature': None, 'support_status': 'unsupported', 'reason': 'diff_outside_supported_method_conditions'})
    status = 'unsupported' if not any(x['support_status'] != 'unsupported' for x in changes) else ('partial' if unhandled or any(x['support_status'] != 'supported' for x in changes) else 'supported')
    return {'schema_version': 'a.analysis.v1', 'artifact_kind': 'candidate_inputs_not_execution_results',
            'case_id': request['case_id'], 'case_kind': request['case_kind'], 'statistics_eligible': False,
            'support_status': status, 'scope': 'local syntactic condition and straight-line parameter association; not whole-program impact',
            'sources': sources, 'diff_hunks': hunks, 'changes': changes, 'unhandled_changes': unhandled,
            'candidates': candidates, 'generation': generation,
            'limitations': ['No target execution, oracle, or counterexample reduction', 'No interprocedural/reflection/complex object analysis', 'No guarantee of path reachability or business-valid inputs', 'No Cartesian product across independent conditions; one parameter varied at a time', 'One file pair; exactly one changed condition per unchanged static method signature', 'Integer literal comparisons only; no arithmetic inversion or named field constant resolution']}
