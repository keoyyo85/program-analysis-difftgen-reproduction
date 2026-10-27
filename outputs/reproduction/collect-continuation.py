import pathlib,json,csv,re
R=pathlib.Path(__file__).resolve().parent
rows=[]
for p in sorted((R/'runs').iterdir()):
    cfg=json.loads((p/'configuration.json').read_text()) if (p/'configuration.json').exists() else {}
    stages=list(csv.DictReader((p/'stages.csv').open()))
    d=next((i for i in stages if i['stage']=='difftgen'),{})
    G=p/'generated/Lang_51_nopol'
    stat=G/'target/0/0/evosuite-report/statistics.csv'
    stats=list(csv.DictReader(stat.open())) if stat.exists() else []
    actual=stats[0].get('Random_Seed','UNRECORDED') if stats else 'UNAVAILABLE'
    log=(G/'target/0/0/rslt').read_text() if (G/'target/0/0/rslt').exists() else ''
    n=re.search(r'Generated (\d+) tests',log)
    final=list((G/'testcase').glob('DiffTGen*Test.java'))
    verify=json.loads((p/'verification.json').read_text()) if (p/'verification.json').exists() else []
    good=[]
    for t in final:
        v={i['version']:i.get('junit_exit') for i in verify if i['test']==t.name}
        if v.get('fix')==0 and v.get('patch')==1:good.append(t.name)
    rows.append(dict(run=p.name,phase='baseline' if not cfg else 'continuation',budget_seconds=cfg.get('search_budget_seconds',60),requested_seed=cfg.get('requested_seed','UNRECORDED'),actual_seed=actual,difftgen_exit=d.get('exit_code',''),difftgen_seconds=d.get('elapsed_seconds',''),raw_tests=n.group(1) if n else '',final_tests=len(final),validated_patch_vs_fix_tests=';'.join(good) or 'NONE',evidence=str(p.relative_to(R))))
with (R/'continuation-result.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
with (R/'result.csv').open('w',newline='') as f:
    allstages=[]
    for p in sorted((R/'runs').iterdir()):
        src=p/'result.csv'
        if src.exists():
            for row in csv.DictReader(src.open()):allstages.append(dict(run=p.name,**row))
    w=csv.DictWriter(f,fieldnames=['run','stage','status','exit_code','elapsed_seconds','evidence']);w.writeheader();w.writerows(allstages)
print(json.dumps(rows,indent=2));print('Continuation DiffTGen total seconds:',sum(float(r['difftgen_seconds']) for r in rows if r['phase']=='continuation' and r['difftgen_seconds']))
