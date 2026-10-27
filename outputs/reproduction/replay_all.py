"""Replay generated suites only; no hand-written distinguishing inputs here."""
import pathlib,subprocess,time,json,shlex,hashlib,csv,re
R=pathlib.Path(__file__).resolve().parent;T=R.parent.parent/'work/DiffTGen'
records=[]
for run in sorted((R/'runs').iterdir()):
    G=run/'generated/Lang_51_nopol'
    raw=G/'target/0/0/evosuite-tests/org/apache/commons/lang'
    if not raw.exists(): continue
    dest=R/'audit/replay'/run.name;dest.mkdir(parents=True,exist_ok=True)
    def call(label,cmd):
        start=time.monotonic()
        (dest/(label+'.command.txt')).write_text(shlex.join(map(str,cmd)))
        with (dest/(label+'.stdout.log')).open('w') as out,(dest/(label+'.stderr.log')).open('w') as err:
            try: c=subprocess.run(list(map(str,cmd)),stdout=out,stderr=err,timeout=90).returncode
            except subprocess.TimeoutExpired:c=124
        records.append(dict(run=run.name,stage=label,exit=c,seconds=round(time.monotonic()-start,3)))
        (R/'audit/replay/records.json').write_text(json.dumps(records,indent=2))
        return c
    dep=run/'faulty-with-dependencies.jar'
    auto_inputs=[]
    for f in (G/'testcase').glob('DiffTGen*Test.java'):
        for s in re.findall(r'BooleanUtils\.toBoolean\("((?:\\.|[^"\\])*)"\)',f.read_text()):
            value=json.loads('"'+s+'"')
            if value not in auto_inputs:auto_inputs.append(value)
    (dest/'automatic-final-test-inputs.json').write_text(json.dumps(auto_inputs))
    for v in ['bug','patch','fix']:
        plain=run/'classes'/v
        cp=f'{plain}:{dep}:{T}/lib/junit-4.11.jar:{T}/lib/hamcrest-all-1.3.jar:{T}/lib/*'
        b=dest/v;b.mkdir(exist_ok=True)
        files=sorted(raw.glob('*.java'))
        c=call('compile-raw-'+v,['javac','-cp',cp,'-d',b,*files])
        if c==0:
            call('raw-junit-'+v,['java','-verbose:class','-cp',f'{b}:{cp}','org.junit.runner.JUnitCore','org.apache.commons.lang.BooleanUtils_ESTest'])
        ic=G/v/'instru0/build/classes';tc=G/'test/0/0/build/classes'
        if tc.exists():
            call('selected-observation-'+v,['java','-verbose:class','-cp',f'{ic}:{tc}:{dep}:{T}/lib/*','org.apache.commons.lang.TestClass'])
        call('load-'+v,['java','-verbose:class','-cp',f'{R}/audit/helper:{cp}','LoadProbe','off','X2f',*auto_inputs])
        for final in (G/'testcase').glob('DiffTGen*Test.java'):
            verified=run/'verification'/v
            if verified.exists():
                finalcp=f'{verified}:{T}/lib/junit-4.11.jar:{T}/lib/hamcrest-all-1.3.jar:{dep}:{T}/lib/*'
                call('final-junit411-'+final.stem+'-'+v,['java','-verbose:class','-cp',finalcp,'org.junit.runner.JUnitCore','org.apache.commons.lang.'+final.stem])
        (dest/(v+'-class.sha256')).write_text(hashlib.sha256((plain/'org/apache/commons/lang/BooleanUtils.class').read_bytes()).hexdigest())
print('Replay saved:',R/'audit/replay')
