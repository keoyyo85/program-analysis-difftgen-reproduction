"""Record correctness checks without touching archived reproduction evidence."""
from pathlib import Path
import datetime
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
out = ROOT/'outputs/a'/('checks-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
out.mkdir(parents=True, exist_ok=False)
command = [sys.executable, '-m', 'unittest', 'discover', '-s', str(ROOT/'tests/a'), '-v']
started = time.monotonic()
with (out/'stdout.log').open('w') as stdout, (out/'stderr.log').open('w') as stderr:
    code = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr, timeout=240).returncode
(out/'result.json').write_text(json.dumps({'kind': 'A_correctness_checks_not_detection_experiment', 'command': command, 'cwd': str(ROOT), 'exit_code': code, 'elapsed_seconds': round(time.monotonic()-started, 3), 'statistics_eligible': False}, indent=2), encoding='utf-8')
print('Checks:', out, 'exit=', code)
sys.exit(code)
