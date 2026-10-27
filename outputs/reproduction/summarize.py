import csv,json,pathlib,sys
rep=pathlib.Path(__file__).resolve().parent
r=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else sorted((rep/'runs').iterdir())[-1]
stages=list(csv.DictReader((r/'stages.csv').open()))
stdout=(r/'difftgen.stdout.log').read_text() if (r/'difftgen.stdout.log').exists() else ''
stderr=(r/'difftgen.stderr.log').read_text() if (r/'difftgen.stderr.log').exists() else ''
tests=list((r/'generated/Lang_51_nopol/testcase').glob('DiffTGen*Test.java'))
verification=json.loads((r/'verification.json').read_text()) if (r/'verification.json').exists() else []
rows=[]
for s in stages:
    if s['stage']=='difftgen':
        s['status']='PASS' if s['exit_code']=='0' and ('Compiling Test Case(s) Done.' in stdout or 'Found Nothing.' in stdout) and 'Failure.' not in stderr else 'FAIL'
    rows.append(s)
evo=r/'generated/Lang_51_nopol/target/0/0/rslt'
evo_text=evo.read_text() if evo.exists() else ''
rows.append(dict(stage='evosuite-input-generation',status='PASS' if '* Computation finished' in evo_text else 'INCOMPLETE',exit_code='',elapsed_seconds='',evidence=str(evo.relative_to(rep))))
three=True
for version in ('bug','patch','fix'):
    log=r/f'generated/Lang_51_nopol/{version}/test/0/0/rslt'
    three=three and log.exists() and 'BUILD SUCCESSFUL' in log.read_text()
rows.append(dict(stage='three-version-observation',status='PASS' if three else 'INCOMPLETE',exit_code='',elapsed_seconds='',evidence=str(r.relative_to(rep)/'generated/Lang_51_nopol')))
rows.append(dict(stage='distinguishing-test-generated',status='PASS' if tests else 'NOT_GENERATED',exit_code='',elapsed_seconds='',evidence=';'.join(str(p.relative_to(rep)) for p in tests)))
valid=False
for t in tests:
    v={i['version']:i.get('junit_exit') for i in verification if i['test']==t.name}
    valid=valid or (v.get('fix')==0 and v.get('patch')==1 and v.get('bug') in (0,1))
rows.append(dict(stage='distinguishing-test-validated',status='PASS' if valid else 'NOT_VERIFIED',exit_code='',elapsed_seconds='',evidence=str(r.relative_to(rep)/'verification.json')))
for dest in [r/'result.csv',rep/'result.csv']:
    with dest.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['stage','status','exit_code','elapsed_seconds','evidence']);w.writeheader();w.writerows(rows)
print('validated=',valid,'tests=',len(tests))
