#!/usr/bin/env python3
"""Sole original read-only acquisition; this is reviewer tooling, never candidate execution."""
from pathlib import Path
import datetime, hashlib, json, subprocess, sys
ROOT=Path(__file__).resolve().parent
PREFIX='/repos/Apdelrahman1911/nativeCmpkit/actions'
RUN=41810510161
kind=sys.argv[1]
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
ledger=ROOT/'GET-LEDGER.jsonl'
previous=[json.loads(line) for line in ledger.read_text().splitlines() if line]
if kind=='run':
 count=1+sum(x.get('kind')=='metadata' and x.get('request','').startswith('run-metadata-') and x.get('status')=='intent' for x in previous)
 request=f'run-metadata-{count:03}'
 endpoint=f'{PREFIX}/runs/{RUN}'
 out=ROOT/'metadata'/f'run-{count:03}.json'
 k='metadata'
elif kind in {'jobs','artifacts'}:
 terminal=sorted((ROOT/'metadata').glob('run-*.json'))[-1]
 if json.loads(terminal.read_text()).get('status')!='completed':raise SystemExit('Refuse post-terminal metadata before completed run')
 page=int(sys.argv[2]) if len(sys.argv)>2 else 1
 request=f'{kind}-metadata-page{page}'
 endpoint=f'{PREFIX}/runs/{RUN}/{kind}?per_page=100&page={page}'+('&filter=all' if kind=='jobs' else '')
 out=ROOT/'metadata'/f'{kind}-page{page}.json'
 k='metadata'
 if any(x.get('request')==request and x.get('status')=='intent' for x in previous):raise SystemExit('Refuse duplicate post-terminal metadata acquisition')
elif kind in {'log','artifact'}:
 terminal=sorted((ROOT/'metadata').glob('run-*.json'))[-1]
 if json.loads(terminal.read_text()).get('status')!='completed':raise SystemExit('Refuse original download before completed run')
 ident=int(sys.argv[2])
 request=f'original-{kind}-{ident}'
 k='original'
 if any(x.get('request')==request and x.get('status')=='intent' for x in previous):raise SystemExit('Refuse duplicate original GET intent; no retry after uncertainty')
 meta=[]
 for p in (ROOT/'metadata').glob('jobs-page*.json' if kind=='log' else 'artifacts-page*.json'):
  meta.extend(json.loads(p.read_text())['jobs' if kind=='log' else 'artifacts'])
 if ident not in {x['id'] for x in meta}:raise SystemExit('Refuse ID outside this original metadata')
 endpoint=f'{PREFIX}/jobs/{ident}/logs' if kind=='log' else f'{PREFIX}/artifacts/{ident}/zip'
 out=ROOT/'originals'/ (f'job-{ident}.log' if kind=='log' else f'artifact-{ident}.zip')
else:raise SystemExit('Unsupported acquisition kind')
if out.exists():raise SystemExit('Refuse original or metadata overwrite')
err=out.with_suffix(out.suffix+'.stderr.txt')
intent={'request':request,'kind':k,'endpoint':endpoint,'utc':utc(),'status':'intent','output':str(out.relative_to(ROOT))}
with ledger.open('a') as f:f.write(json.dumps(intent)+'\n')
try:
 with out.open('xb') as f,err.open('xb') as e:
  p=subprocess.run(['gh','api','--method','GET',endpoint],stdout=f,stderr=e,timeout=300 if k=='original' else 120)
 exit_code=p.returncode
 exception=None
except Exception as error:
 exit_code=None
 exception=type(error).__name__
completion={**intent,'status':'completed' if exit_code==0 else 'rejected-or-unknown','exit':exit_code,'exception':exception,'finished_utc':utc(),'bytes':out.stat().st_size if out.exists() else 0,'sha256':hashlib.sha256(out.read_bytes()).hexdigest() if out.exists() else None,'stderr_bytes':err.stat().st_size if err.exists() else None}
with ledger.open('a') as f:f.write(json.dumps(completion)+'\n')
if exit_code!=0:
 print(json.dumps(completion));raise SystemExit(1)
if kind=='run':
 d=json.loads(out.read_text())
 print(json.dumps({key:d.get(key) for key in ['id','status','conclusion','head_sha','head_branch','event','run_attempt','updated_at']},indent=2))
else:
 print(json.dumps(completion))
