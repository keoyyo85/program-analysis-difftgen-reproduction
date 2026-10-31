"""Build a small offline B handoff from an explicit allowlist; no downloads."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
BASE = '9bb8fc496ecd5f89f27b60555e1339960a206622'

SMOKE = '''import hashlib, json
from pathlib import Path
from interfaces.a_contract import validate_a
root = Path(__file__).resolve().parent
manifest = json.loads((root/'MANIFEST.json').read_text(encoding='utf-8'))
for name, sha in manifest['files_sha256'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest() == sha, name
a = validate_a(json.loads((root/'outputs/a/handoff/analysis.example.json').read_text(encoding='utf-8')))
mapping = {'before_source': 'examples/teaching/int-threshold/before/Threshold.java',
           'patch_source': 'examples/teaching/int-threshold/patch/Threshold.java',
           'diff_path': 'examples/teaching/int-threshold/patch.diff'}
for role, name in mapping.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest() == a['sources'][role]['sha256'], role
for c in a['candidates']:
    print(c['candidate_id'], c['method']['signature'], c['arguments'])
print('PASS: package integrity + A consumer checks + mapped source hashes; no Java execution/oracle')
'''


def main():
    names = {'THIRD_PARTY.md', 'docs/a/B_HANDOFF.md', 'docs/a/TO_B_OFFLINE.md',
             'docs/a/REAL_CASES.md', 'docs/a/REPORT.md', 'docs/a/README.md',
             'docs/INTERFACES.md', 'docs/COLLABORATION.md', 'contracts/A_V1_FREEZE.json',
             'outputs/a/handoff/analysis.example.json', 'outputs/a/handoff/source-screening.json',
             'outputs/a/handoff-check-20261031-122621/result.json',
             'outputs/a/handoff-check-20261031-122621/correctness-tests.stderr.log',
             'outputs/reproduction/VALIDATION.md', 'outputs/reproduction/sample/SOURCES.md',
             'outputs/reproduction/sample/Lang51.src.patch', 'outputs/reproduction/sample/nopolc-results.json',
             'outputs/reproduction/runs/20261027-183648/generated/Lang_51_nopol/testcase/DiffTGen0Test.java'}
    for folder in ('modules/a', 'tests/a', 'interfaces', 'contracts', 'examples/teaching/int-threshold', 'examples/a-compatibility/lang51'):
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc', '.class', '.jar', '.zip'):
                names.add(p.relative_to(ROOT).as_posix())
    for version in ('bug', 'patch', 'fix'):
        names.add('outputs/reproduction/sample/'+version+'/BooleanUtils.java')
    replay = ROOT/'outputs/reproduction/audit/replay/20261027-183648'
    names.update(p.relative_to(ROOT).as_posix() for p in replay.glob('final-junit411-*.log'))
    data = {name: (ROOT/name).read_bytes() for name in sorted(names)}
    data['smoke_read.py'] = SMOKE.encode()
    data['README_FIRST.md'] = (ROOT/'docs/a/TO_B_OFFLINE.md').read_bytes()
    manifest = {'kind': 'offline_B_handoff_not_execution_results', 'a_frozen_commit': BASE,
                'interface': 'a.analysis.v1', 'contains_reference': 'B-only historical Lang51 fix; never pass to A generator',
                'files_sha256': {n: hashlib.sha256(b).hexdigest() for n, b in data.items()}}
    data['MANIFEST.json'] = json.dumps(manifest, ensure_ascii=False, indent=2).encode()
    out = ROOT/'outputs/b-handoff'
    out.mkdir(parents=True, exist_ok=True)
    archive = out/'A-to-B-9bb8fc4.zip'
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
        for name, content in data.items(): z.writestr('A-to-B/'+name, content)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert all(z.read('A-to-B/'+n) == b for n, b in data.items())
    report = {'archive': archive.name, 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
              'size_bytes': archive.stat().st_size, 'files': len(data), 'zip_integrity': 'PASS',
              'a_frozen_commit': BASE, 'statistics_eligible': False}
    (out/'package-result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (out/'README_给B.md').write_bytes(data['README_FIRST.md'])
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__': main()
