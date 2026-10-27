import pathlib,subprocess,hashlib,json,time,shlex
R=pathlib.Path(__file__).resolve().parent;ROOT=R.parent.parent;T=ROOT/'work/DiffTGen';D=ROOT/'work/deps'
A=R/'audit';A.mkdir(exist_ok=True);B=A/'helper';B.mkdir(exist_ok=True)
records=[]
def run(name,cmd):
    start=time.monotonic()
    with (A/(name+'.stdout.log')).open('w') as out,(A/(name+'.stderr.log')).open('w') as err:
        p=subprocess.run(list(map(str,cmd)),stdout=out,stderr=err,timeout=90)
    records.append(dict(name=name,command=shlex.join(map(str,cmd)),exit=p.returncode,seconds=time.monotonic()-start))
    (A/'commands.json').write_text(json.dumps(records,indent=2))
    assert p.returncode==0,name
run('compile-probes',['javac','-cp',T/'lib/evosuite-1.0.2.jar','-d',B,R/'LoadProbe.java',R/'SeedProbe.java'])
run('seed-probe',['java','-Drandom_seed=2026102701','-cp',f'{B}:{T}/lib/evosuite-1.0.2.jar','SeedProbe'])
first=R/'runs/20261027-175712';G=first/'generated/Lang_51_nopol'
hashes={}
for v in ['bug','patch','fix']:
    c=first/'classes'/v
    hashes[v]={}
    for kind,folder in [('plain',c),('output-instrumented',G/v/'instru0/build/classes')]:
        f=folder/'org/apache/commons/lang/BooleanUtils.class'
        hashes[v][kind]=dict(file=str(f),sha256=hashlib.sha256(f.read_bytes()).hexdigest())
        run('load-'+v+'-'+kind,['java','-verbose:class','-cp',f'{B}:{folder}:{first}/faulty-with-dependencies.jar:{T}/lib/*','LoadProbe','off','X2f'])
    run('bytecode-'+v,['javap','-classpath',c,'-c','org.apache.commons.lang.BooleanUtils'])
(A/'class-hashes.json').write_text(json.dumps(hashes,indent=2))
bug=(R/'sample/bug/BooleanUtils.java').read_text().splitlines();patch=(R/'sample/patch/BooleanUtils.java').read_text().splitlines();fix=(R/'sample/fix/BooleanUtils.java').read_text().splitlines()
assert bug[676].strip()=="if (ch == 'Y') {" and len(bug[676])-len(bug[676].lstrip())==16
assert patch[676].strip()=='if (str!=null) {' and len(patch[676])-len(patch[676].lstrip())==16
assert fix[623].strip()=='/**' and fix[648].strip()=='public static boolean toBoolean(String str) {'
(A/'positions.json').write_text(json.dumps(dict(delta_bug='677,16',delta_patch='677,16',oracle_javadoc='624,4',oracle_declaration='649,4',status='MATCH'),indent=2))
print('AUDIT_PASS')
