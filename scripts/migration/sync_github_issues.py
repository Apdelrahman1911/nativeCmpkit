#!/usr/bin/env python3
"""Render or explicitly create/update deduplicated audit and actionable-upstream issues.

Default: local dry-run Markdown/JSON only. --apply writes to the specified fixed
independent repository, never to upstream. Each remote issue carries a stable
marker; resumptions reconcile state before creating anything. No automatic POST
retry occurs after an uncertain failure. Original users/timestamps are attribution,
not impersonated GitHub issue metadata. Does not publish releases/packages.
"""
from __future__ import annotations
import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[2]
REPO='Apdelrahman1911/nativeCmpkit'
BASE='af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6'
PREFIX='<!-- nativecmpkit-item:'
COLORS={'Critical':'b60205','High':'d93f0b','Medium':'fbca04','Low':'0e8a16'}


def managed_key(body):
    """Reject ambiguous/copied markers rather than editing an unrelated issue."""
    body=body or ''
    if PREFIX not in body: return None
    marker=re.match(re.escape(PREFIX)+r'(audit:[A-Z]+-[0-9]{3}|upstream:[0-9]+|upstream-topic:[0-9a-f]{20}) -->\r?\n',body)
    if not marker or body.count(PREFIX)!=1:
        raise ValueError('Ambiguous managed issue marker; refusing automatic mutation')
    return marker[1]


def merge_labels(remote, desired):
    """Only generator-owned classifications may be replaced; retain owner labels."""
    owned=re.compile(r'^(?:audit|upstream-actionable|priority:(?:critical|high|medium|low)|area:(?:build|hist|io|native|nav|perm|ui)|evidence:(?:confirmed-source|confirmed-test|risk|unverified|improvement))$')
    names=[x['name'] if isinstance(x,dict) else x for x in remote]
    return sorted(set(desired)|{name for name in names if not owned.fullmatch(name)})


def require_unchanged_content(remote, desired, previous):
    """Fail closed on human-edited bodies/titles; never silently replace them."""
    for field in ('body','title'):
        value=remote.get(field) or ''
        if value==desired[field]: continue
        if field=='body':
            unchanged=previous and hashlib.sha256(value.encode()).hexdigest()==previous.get('body_sha256')
        else: unchanged=previous and value==previous.get('title')
        if not unchanged:
            raise RuntimeError('Remote '+field+' has no matching previous managed receipt: '+desired['key'])


def should_close_initial_issue(is_new, previous, desired_state):
    # A later manual close/reopen is an owner decision, not generator drift.
    return desired_state=='closed' and (is_new or bool(previous and previous.get('pending_initial_close')))


def gh(endpoint, method='GET', data=None, paginate=False):
    cmd=['gh','api',endpoint]
    if paginate: cmd+=['--paginate','--slurp']
    if method!='GET': cmd+=['--method',method]
    if data is not None: cmd+=['--input','-']
    p=subprocess.run(cmd,input=None if data is None else json.dumps(data),text=True,capture_output=True,cwd=ROOT)
    if p.returncode: raise RuntimeError(f'GitHub {method} failed ({p.returncode}) for {endpoint}: {p.stderr[-1200:]}')
    return json.loads(p.stdout) if p.stdout.strip() else None


def flat_pages(data):
    return [item for page in data for item in page]


def source_links(locations):
    result=[]
    for loc in locations:
        path=loc['path']; lines=str(loc['lines'])
        first=None if lines.lower().startswith('binary') else re.search(r'(\d+)(?:\s*-\s*(\d+))?',lines)
        anchor=f'#L{first[1]}' + (f'-L{first[2]}' if first and first[2] else '') if first else ''
        url=f'https://github.com/{REPO}/blob/{BASE}/{quote(path,safe="/")}{anchor}'
        result.append(f'- [`{path}:{lines}`]({url}) — `{loc["symbol"]}`')
    return '\n'.join(result)


def bullets(items): return '\n'.join('- '+str(x) for x in items) or '- None identified.'


def calf_upstream_numbers(references):
    """Only Calf issue/PR numbers belong in the migration's original-number map."""
    pattern=re.compile(r'^https://github\.com/MohamedRejeb/Calf/(?:issues|pull)/(\d+)(?:[/?#]|$)',re.IGNORECASE)
    return sorted({int(match[1]) for url in references if (match:=pattern.match(url))})


def body_for(f, resolution):
    text=f'''{PREFIX}audit:{f['id']} -->
## Classification
- **Finding:** {f['id']}
- **Priority:** {f['priority']}
- **Evidence status:** `{f['status']}` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** {', '.join('`'+x+'`' for x in f['modules'])}
- **Estimated complexity:** {f['effort']}
- **Reviewed upstream baseline:** `{BASE}`; original commit preserved in this repository.

## Exact code / symbols
{source_links(f['locations'])}

## Root cause
{f['root_cause']}

## Impact and preconditions
{f['impact']}

## Supporting evidence
{bullets(f['evidence'])}

## Recommended solution
{f['recommendation']}

## Risks and compatibility
{f['risks']}

## Required tests / acceptance criteria
{bullets(f['required_tests'])}

## Dependencies
{bullets(f['dependencies'])}

## Historical context
{bullets(f['upstream_refs'])}
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/{REPO}/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/{f['id'].split('-')[0]}.json`](https://github.com/{REPO}/blob/main/docs/audit/findings/{f['id'].split('-')[0]}.json) · [Audit](https://github.com/{REPO}/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/{REPO}/blob/main/docs/roadmap/README.md)
'''
    if resolution:
        text+='\n## Migration remediation (baseline finding retained)\n'+resolution['reason']+'\n\nVerification files:\n'+bullets(resolution['verification'])+'\n\nRemaining caution: '+resolution['remaining_caution']+'\n'
    return text


def inherited_body(d):
    return f'''## Imported actionable historical item
- **Original:** {d['url']} (#{d['upstream_number']}, {d['kind']})
- **Original author:** `{d['original_author']}`
- **Original ID:** `{d['original_id']}`; node ID `{d['original_node_id']}`
- **Original creation / update:** `{d['created_at']}` / `{d['updated_at']}`
- **Original state at observation:** `{d['state']}`
- **Priority:** {d['priority']}
- **Assessment:** `{d['disposition']}` — not a newly confirmed bug unless separately demonstrated.

This is a newly created nativeCmpkit issue. GitHub author/timestamp/number metadata cannot be transplanted faithfully. The original full text, comments, timelines and public revisions remain in the independent [raw archive](https://github.com/{REPO}/tree/main/docs/migration/upstream-metadata).

## Current-source assessment / evidence
{d['rationale']}

{source_links(d['locations'])}

## Recommended next step
{d['recommended_next_step']}

## Risks and required verification
Do not treat the historical report as a current reproduction, or an implemented permission as a complete data API. Define explicit platform capability, unsupported/error/cancel behavior and compatibility before implementing. Add a minimal current-baseline reproduction or a scoped acceptance test matrix; record runtime/OS/browser versions and classify confirmed behavior separately from assumptions. No major rewrite or release is authorized by this issue.

## Deduplication / rationale
Stable topic key: `{d['dedupe_key']}`. Disposition and code references are preserved in [upstream-actionable-decisions.json](https://github.com/{REPO}/blob/main/docs/migration/upstream-actionable-decisions.json). Already implemented requests and requests covered by audit findings are not blindly recreated.
'''


def inherited_items(decisions):
    priorities={'Critical':0,'High':1,'Medium':2,'Low':3}
    seen=set(); groups={}
    for d in decisions:
        if d['upstream_number'] in seen: raise ValueError('Repeated upstream disposition number')
        seen.add(d['upstream_number'])
        if d['disposition'] not in {'needs_reproduction','separate_improvement','actionable'} or d['finding_ids']: continue
        if not d['dedupe_key']: raise ValueError('Missing upstream topic key')
        groups.setdefault(d['dedupe_key'],[]).append(d)
    items=[]
    for topic,group in sorted(groups.items()):
        group.sort(key=lambda d:d['upstream_number'])
        numbers=[d['upstream_number'] for d in group]
        priority=min((d['priority'] for d in group),key=priorities.get)
        key='upstream-topic:'+hashlib.sha256(topic.encode()).hexdigest()[:20]
        body=f'{PREFIX}{key} -->\n'+'\n\n---\n\n'.join(inherited_body(d) for d in group)
        evidence='unverified' if any(d['disposition']=='needs_reproduction' for d in group) else 'improvement'
        items.append({'key':key,'topic':topic,'finding_ids':[],'upstream_numbers':numbers,'title':f'[{priority}][Upstream '+', '.join('#'+str(n) for n in numbers)+'] '+group[0]['title'],'body':body,'labels':['upstream-actionable','priority:'+priority.lower(),'evidence:'+evidence],'state':'open'})
    return items


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--delay',type=float,default=2.0,help='Seconds between remote issue mutations (minimum 2)')
    args=parser.parse_args()
    findings=[]
    for p in sorted((ROOT/'docs/audit/findings').glob('*.json')): findings+=json.loads(p.read_text())
    if len({f['id'] for f in findings})!=len(findings): raise ValueError('Duplicate IDs in input')
    priorities={'Critical':0,'High':1,'Medium':2,'Low':3}
    findings.sort(key=lambda x:(priorities[x['priority']],x['id']))
    resolutions=json.loads((ROOT/'docs/audit/migration-resolutions.json').read_text())
    decisions=json.loads((ROOT/'docs/migration/upstream-actionable-decisions.json').read_text())
    items=[]
    for f in findings:
        resolution=resolutions.get(f['id'])
        items.append({'key':'audit:'+f['id'],'finding_ids':[f['id']],'upstream_numbers':calf_upstream_numbers(f['upstream_refs']),'title':f'[{f["priority"]}][{f["id"]}] {f["title"]}','body':body_for(f,resolution),'labels':['audit','priority:'+f['priority'].lower(),'area:'+f['id'].split('-')[0].lower(),'evidence:'+f['status']],'state':'closed' if resolution and resolution['state']=='closed' else 'open'})
    items.extend(inherited_items(decisions))
    if len({item['key'] for item in items})!=len(items): raise ValueError('Duplicate final issue keys')
    rendered=ROOT/'docs/audit/issue-drafts';rendered.mkdir(exist_ok=True)
    for item in items:
        if len(item['body'].encode('utf-8'))>64000: raise ValueError('Issue body too large: '+item['key'])
        (rendered/(item['key'].replace(':','-')+'.md')).write_text('# '+item['title']+'\n\n'+item['body'])
        item['body_sha256']=hashlib.sha256(item['body'].encode()).hexdigest()
    plan={'schema_version':1,'repository':REPO,'baseline':BASE,'count':len(items),'findings':len(findings),'items':[{k:v for k,v in item.items() if k!='body'} for item in items]}
    (ROOT/'docs/audit/issue-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({'dry_run':not args.apply,'findings':len(findings),'issues':len(items),'priorities':dict(Counter(f['priority'] for f in findings))}),flush=True)
    if not args.apply: return
    repo=gh('repos/'+REPO)
    if (repo.get('fork') or repo['owner']['login']!='Apdelrahman1911'
            or repo.get('full_name','').casefold()!=REPO.casefold()):
        raise RuntimeError('Unexpected destination identity/ownership/independence')
    owner=gh('user')['login']
    if owner.lower()!=repo['owner']['login'].lower(): raise RuntimeError('Authenticated account is not the expected repository owner')
    existing_labels={x['name']:x for x in flat_pages(gh(f'repos/{REPO}/labels?per_page=100',paginate=True))}
    desired=sorted({label for item in items for label in item['labels']})
    for label in desired:
        if label in existing_labels: continue
        color=COLORS.get(label.split(':')[-1].capitalize(),'c5def5')
        gh(f'repos/{REPO}/labels','POST',{'name':label,'color':color,'description':'nativeCmpkit audit classification: '+label})
        time.sleep(max(2,args.delay))
    existing={}
    for issue in flat_pages(gh(f'repos/{REPO}/issues?state=all&per_page=100',paginate=True)):
        if 'pull_request' in issue: continue
        key=managed_key(issue.get('body'))
        if key:
            if issue['user']['login'].lower()!=owner.lower(): raise RuntimeError('Managed marker on an issue authored by another account: '+key)
            if key in existing: raise RuntimeError('Duplicate remote stable marker: '+key)
            existing[key]=issue
    map_path=ROOT/'docs/migration/issue-map.json'
    prior=json.loads(map_path.read_text()) if map_path.exists() else {'repository':REPO,'items':[]}
    if prior['repository']!=REPO: raise RuntimeError('Prior issue map belongs to a different repository')
    prior_entries={entry['key']:entry for entry in prior['items']}
    saved=dict(prior_entries)
    mapping={'schema_version':1,'repository':REPO,'baseline':BASE,'synced_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'complete':False,'items':[]}
    def persist():
        mapping['items']=list(saved.values())
        temporary=map_path.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(mapping,indent=2)+'\n');temporary.replace(map_path)
    for index,item in enumerate(items,1):
        remote=existing.get(item['key']);modified=False
        is_new=remote is None
        previous=prior_entries.get(item['key'])
        if previous and remote is None:
            raise RuntimeError('Previously managed issue marker is missing; reconcile manually: '+item['key'])
        if previous and remote and previous['number']!=remote['number']: raise RuntimeError('Remote issue number changed for managed key: '+item['key'])
        close_initial=should_close_initial_issue(is_new,previous,item['state'])
        if remote is None:
            remote=gh(f'repos/{REPO}/issues','POST',{'title':item['title'],'body':item['body'],'labels':item['labels']});modified=True
            # Record the successful POST immediately, before any subsequent request.
            existing[item['key']]=remote
        else:
            require_unchanged_content(remote,item,previous)
            labels=merge_labels(remote['labels'],item['labels'])
            same=(remote['title']==item['title'] and (remote.get('body') or '')==item['body'] and set(x['name'] for x in remote['labels'])==set(labels))
            if not same:
                remote=gh(f'repos/{REPO}/issues/{remote["number"]}','PATCH',{'title':item['title'],'body':item['body'],'labels':labels});modified=True
        entry={k:v for k,v in item.items() if k not in {'body','labels'}}
        entry.update(number=remote['number'],url=remote['html_url'],actual_state=remote['state'],github_created_at=remote['created_at'],github_author=remote['user']['login'])
        entry['pending_initial_close']=close_initial and remote['state']!='closed'
        saved[item['key']]=entry;persist()
        if modified: time.sleep(max(2,args.delay))
        if close_initial and remote['state']!='closed':
            gh(f'repos/{REPO}/issues/{remote["number"]}','PATCH',{'state':'closed','state_reason':'completed'})
            entry['actual_state']='closed';entry['pending_initial_close']=False;persist();time.sleep(max(2,args.delay))
        if index%10==0 or index==len(items): print(json.dumps({'processed':index,'total':len(items),'last_issue':remote['number']}),flush=True)
    mapping['complete']=True
    persist()

if __name__=='__main__': main()
