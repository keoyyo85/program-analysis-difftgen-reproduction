#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from modules.a.analysis import analyze

def main():
    parser = argparse.ArgumentParser(description='A: JDT local condition analysis; no reference/oracle access')
    parser.add_argument('--request', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path, help='new directory; existing evidence never overwritten')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    try:
        request = json.loads(args.request.read_text(encoding='utf-8'))
        result = analyze(request, args.request.resolve().parent, args.output/'parser')
        (args.output/'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'case_id': result['case_id'], 'support_status': result['support_status'], 'candidates': len(result['candidates']), 'output': str(args.output)}, ensure_ascii=False))
        return 0
    except (ValueError, OSError) as e:
        (args.output/'error.json').write_text(json.dumps({'schema_version': 'a.error.v1', 'status': 'error', 'reason': str(e), 'statistics_eligible': False}, ensure_ascii=False, indent=2), encoding='utf-8')
        print(str(e), file=sys.stderr); return 2

if __name__ == '__main__': sys.exit(main())
