"""Compile/read a read-only JDT adapter; never execute the analyzed program."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]

def export_ast(source_path, evidence_dir):
    source_path, evidence_dir = Path(source_path), Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    java_home = Path(os.environ.get('JAVA_HOME', ROOT / 'work/deps/zulu8.94.0.17-ca-jdk8.0.492-linux_x64'))
    java, javac = java_home / 'bin/java', java_home / 'bin/javac'
    if not java.exists() or not javac.exists():
        raise ValueError('JDK 8 is required: set project JAVA_HOME or run prepare-project.ps1')
    lib = ROOT / 'work/DiffTGen/lib'
    if not (lib / 'org.eclipse.jdt.core.jar').exists():
        raise ValueError('Author JDT jars missing: initialize work/DiffTGen submodule')
    src = ROOT / 'modules/a/java/AstExport.java'
    # Separate cache; never rebuild or edit the author tool.
    key = hashlib.sha256(src.read_bytes()).hexdigest()[:16]
    cache = Path(os.environ.get('DIFFTGEN_A_CACHE_DIR', ROOT / 'work/a-build')).resolve()
    if not cache.is_relative_to((ROOT / 'work/a-build').resolve()):
        raise ValueError('A cache must remain under project work/a-build')
    build = cache / key
    build.mkdir(parents=True, exist_ok=True)
    cp = str(lib / '*')
    if not (build / 'AstExport.class').exists():
        compile_command = [str(javac), '-encoding', 'UTF-8', '-cp', cp, '-d', str(build), str(src)]
        (evidence_dir / 'bridge-compile.command.json').write_text(json.dumps(compile_command), encoding='utf-8')
        p = subprocess.run(compile_command, capture_output=True, text=True, timeout=90)
        (evidence_dir / 'bridge-compile.stdout.log').write_text(p.stdout, encoding='utf-8')
        (evidence_dir / 'bridge-compile.stderr.log').write_text(p.stderr, encoding='utf-8')
        if p.returncode: raise ValueError('AST adapter compilation failed; see bridge-compile.stderr.log')
    command = [str(java), '-Xmx512m', '-cp', str(build) + os.pathsep + cp, 'AstExport', str(source_path)]
    p = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=60)
    name = hashlib.sha256(str(source_path).encode()).hexdigest()[:12]
    (evidence_dir / (name + '.command.json')).write_text(json.dumps(command, ensure_ascii=False), encoding='utf-8')
    (evidence_dir / (name + '.stderr.log')).write_text(p.stderr, encoding='utf-8')
    (evidence_dir / (name + '.ast.json')).write_text(p.stdout, encoding='utf-8')
    if p.returncode: raise ValueError('JDT parsing adapter failed')
    result = json.loads(p.stdout)
    if result['errors']: raise ValueError('JAVA_SYNTAX_ERROR: ' + json.dumps(result['errors'], ensure_ascii=False))
    return result
