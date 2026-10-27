import csv, datetime, json, os, pathlib, shlex, shutil, subprocess, sys, time, zipfile,argparse
p=argparse.ArgumentParser();p.add_argument('--budget',type=int,default=60);p.add_argument('--seed',type=int);p.add_argument('--compile-only',action='store_true');args=p.parse_args()
if args.seed is not None:
    os.environ['JAVA_TOOL_OPTIONS']=os.environ.get('JAVA_TOOL_OPTIONS','')+f' -Drandom_seed={args.seed} -Doutput_variables=TARGET_CLASS,Random_Seed,Coverage,Total_Goals,Covered_Goals'
REP=pathlib.Path(__file__).resolve().parent
ROOT=REP.parent.parent
TOOL=ROOT/'work/DiffTGen'
DEPS=ROOT/'work/deps'
RUN=REP/'runs'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
RUN.mkdir(parents=True)
(RUN/'configuration.json').write_text(json.dumps(dict(search_budget_seconds=args.budget,requested_seed=args.seed,trials=1,parallel=False,JAVA_TOOL_OPTIONS=os.environ.get('JAVA_TOOL_OPTIONS'),seed_interface='EvoSuite JVM random_seed property; no DiffTGen seed option'),indent=2))
rows=[]
def run(stage, cmd, cwd=TOOL, timeout=120, check=True):
    start=time.monotonic()
    (RUN/(stage+'.command.txt')).write_text('cwd='+str(cwd)+'\n'+shlex.join(map(str,cmd))+'\n')
    with (RUN/(stage+'.stdout.log')).open('w') as out, (RUN/(stage+'.stderr.log')).open('w') as err:
        try: code=subprocess.run(list(map(str,cmd)),cwd=cwd,stdout=out,stderr=err,timeout=timeout).returncode
        except subprocess.TimeoutExpired: code=124
    row=dict(stage=stage,status='PASS' if code==0 else 'FAIL',exit_code=code,elapsed_seconds=round(time.monotonic()-start,3),evidence=str(RUN.relative_to(REP)/(stage+'.stdout.log')))
    rows.append(row)
    with (RUN/'stages.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=row.keys());w.writeheader();w.writerows(rows)
    print(stage,code,row['elapsed_seconds'],flush=True)
    if check and code: raise SystemExit(code)
    return code
run('environment',['bash','-c','uname -a; git --version; java -version; javac -version; ant -version; df -h / /mnt/d'])
run('author-compile',['ant','compile'])
if '--compile-only' in sys.argv: sys.exit(0)
sample=REP/'sample'
fix=(sample/'fix/BooleanUtils.java').read_text()
needle="                return false;\n            }\n            case 4: {"
assert fix.count(needle)==1
bug=fix.replace(needle,"            }\n            case 4: {")
assert bug.count("if (ch == 'Y') {")==1
patch=bug.replace("if (ch == 'Y') {","if (str!=null) {")
(sample/'bug/BooleanUtils.java').write_text(bug)
(sample/'patch/BooleanUtils.java').write_text(patch)
for name in ('bug','patch','fix'):
    build=RUN/'classes'/name;build.mkdir(parents=True)
    run('compile-'+name,['javac','-cp',DEPS/'commons-lang-2.3.jar','-d',build,sample/name/'BooleanUtils.java'])
depjar=RUN/'faulty-with-dependencies.jar'
shutil.copyfile(DEPS/'commons-lang-2.3.jar',depjar)
run('bundle-faulty',['jar','uf',depjar,'-C',RUN/'classes/bug','.'])
delta=RUN/'delta.txt';oracle=RUN/'oracle.txt'
assert bug.splitlines()[676].strip()=="if (ch == 'Y') {"
assert fix.splitlines()[623].strip()=='/**'
delta.write_text(f'{sample}/bug/BooleanUtils.java:677,16\n{sample}/patch/BooleanUtils.java:677,16\n')
oracle.write_text(f'{sample}/fix/BooleanUtils.java:624,4\n')
runfile=TOOL/'run'
runfile.write_text('#!/bin/bash\n\nproj_dir='+str(TOOL)+' # project-local configuration\n\njava -cp :${proj_dir}/lib/*:${proj_dir}/build testgen.Main $*\n')
out=RUN/'generated';out.mkdir()
cmd=['timeout','--kill-after=10s','600s','bash',runfile,'-bugid','Lang_51','-repairtool','nopol','-difftgendpath',TOOL,'-evosuitejpath',TOOL/'lib/evosuite-1.0.2.jar','-dependjpath',depjar,'-outputdpath',out,'-inputfpath',delta,'-oracleinputfpath',oracle,'-evosuitetrials','1','-evosuitetimeout',str(args.budget),'-stopifoverfittingfound']
run('difftgen',cmd,timeout=620,check=False)
generated=out/'Lang_51_nopol'
tests=list((generated/'testcase').glob('DiffTGen*Test.java'))
verification=[]
if tests:
    helper=RUN/'helper';helper.mkdir()
    toolcp=f'{TOOL}/build:{TOOL}/lib/*'
    run('compile-verification-helper',['javac','-cp',toolcp,'-d',helper,REP/'InstrumentReference.java'])
    ref=generated/'fix/instru1';ref.mkdir(exist_ok=True)
    run('instrument-reference-for-verification',['java','-cp',f'{helper}:{toolcp}','InstrumentReference',sample/'fix/BooleanUtils.java',ref/'BooleanUtils.java'])
for test in tests:
    # DiffTGen assertions read oref_map: compile the author's test-instrumented
    # counterparts identically for all three versions, with no semantic edits.
    for version in ('bug','patch','fix'):
        vb=RUN/'verification'/version;vb.mkdir(parents=True,exist_ok=True)
        source=generated/version/'instru1/BooleanUtils.java'
        if not source.exists():
            verification.append(dict(test=test.name,version=version,status='MISSING_INSTRU1'))
            continue
        cp=f'{depjar}:{TOOL}/lib/*'
        c=run('verify-compile-'+test.stem+'-'+version,['javac','-cp',cp,'-d',vb,source,test],check=False)
        if c: continue
        c=run('verify-junit-'+test.stem+'-'+version,['java','-cp',f'{vb}:{cp}','org.junit.runner.JUnitCore','org.apache.commons.lang.'+test.stem],check=False)
        verification.append(dict(test=test.name,version=version,junit_exit=c))
(RUN/'verification.json').write_text(json.dumps(verification,indent=2))
subprocess.run(['python3',str(REP/'summarize.py'),str(RUN)],check=True)
print('RUN_DIRECTORY='+str(RUN),flush=True)
