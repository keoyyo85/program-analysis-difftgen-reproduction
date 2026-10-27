import pathlib,json,csv,re
R=pathlib.Path(__file__).resolve().parent
records=json.loads((R/'audit/replay/records.json').read_text())
rows=list(csv.DictReader((R/'result.csv').open()))
for rec in records:
    s=rec['stage'];p=R/'audit/replay'/rec['run']/(s+'.stdout.log')
    txt=p.read_text()
    status='PASS' if rec['exit']==0 else 'FAIL'
    if s.startswith('final-junit411-') and s.endswith('-patch') and rec['exit']==1:
        status='EXPECTED_ASSERTION_FAILURE' if 'java.lang.AssertionError:' in txt and 'Tests run: 1,  Failures: 1' in txt else 'FAIL'
    rows.append(dict(run=rec['run'],stage='replay/'+s,status=status,exit_code=rec['exit'],elapsed_seconds=rec['seconds'],evidence=str(p.relative_to(R))))
with (R/'result.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['run','stage','status','exit_code','elapsed_seconds','evidence']);w.writeheader();w.writerows(rows)
verified={}
for v in ['bug','patch','fix']:
    label='final-junit411-DiffTGen0Test-'+v
    rec=next(r for r in records if r['run']=='20261027-183648' and r['stage']==label)
    txt=(R/'audit/replay/20261027-183648'/(label+'.stdout.log')).read_text()
    assert 'JUnit version 4.11' in txt and 'from file:' in txt and f'verification/{v}/' in txt
    assert rec['exit']==(1 if v=='patch' else 0)
    if v=='patch':assert 'java.lang.AssertionError:' in txt and 'Tests run: 1,  Failures: 1' in txt
    else:assert 'OK (1 test)' in txt
    verified[v]=dict(junit_version='4.11',exit=rec['exit'],status='EXPECTED_ASSERTION_FAILURE' if v=='patch' else 'PASS')
summary=dict(final_test='runs/20261027-183648/generated/Lang_51_nopol/testcase/DiffTGen0Test.java',origin='DiffTGen automatic generation',input='Fes',expected=False,versions=verified,replay_processes=len(records),replay_process_seconds_sum=round(sum(r['seconds'] for r in records),3),manual_diagnostic='NOT_EXECUTED_AUTOMATIC_COUNTEREXAMPLE_FOUND')
(R/'audit/final-verification.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
