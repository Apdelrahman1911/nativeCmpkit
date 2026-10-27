"""Additive exact HTML target recount; preserve the prior reviewer's hardcoded count error."""
from pathlib import Path
from html.parser import HTMLParser
import datetime as dt,hashlib,json
ROOT=Path('/root/projects/nativeCmpKit');BASE=Path(__file__).parent;OUT=ROOT/'docs/development/evidence/ci-preflight-20261027-031'
original=(OUT/'lead-review.json').read_bytes();review=json.loads(original)
class Ids(HTMLParser):
 def __init__(self):super().__init__();self.ids=set()
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k=='id':self.ids.add(v)
outputs=review['actual_document_output_checks']
for row in outputs:
 data=(BASE/'site'/row['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256']
 parser=Ids();parser.feed(data.decode());assert row['actual_anchor_verified'] in parser.ids
paths={r['path'] for r in outputs};assert len(outputs)==66 and len(paths)==25
assert review['commands']==23 and review['python_tooling_methods']==1297 and review['source_input_count']==18590
final=dict(review);final['unique_output_files']=len(paths);final['reviewed_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
final['prior_review_preserved_sha256']=hashlib.sha256(original).hexdigest();final['prior_unique_output_files_field_was_hardcoded_wrong']=24
final['all_actual_HTML_hashes_and_anchors_rechecked']=True
final['reviewer_assertion_and_hardcoded_field_failures_retained']=True
final['lightweight_commands_or_tests_repeated_by_recount']=False
final['scope']='23 held lightweight commands/1297 overlapping Python methods at18590 inputs;66 actual anchors/25 distinct new HTML files, strict MkDocs/actionlint/audit/migration/current indexes/both whitespace checks. Reviewer count24 and its first assertion are preserved, corrected by an actual distinct-path recount, not fewer target checks. Additive archive/context links are not circular later-source, Native/consumer/ABI/legal/security/release certification.'
(OUT/'lead-final-recount.json').write_text(json.dumps(final,indent=2,sort_keys=True)+'\n');(OUT/'final-recount.py').write_bytes(Path(__file__).read_bytes())
(OUT/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(OUT))+'\n' for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'))
print(json.dumps({'passed':True,'actual_anchors':len(outputs),'actual_distinct_targets':len(paths),'prior_error_preserved':True},indent=2))
