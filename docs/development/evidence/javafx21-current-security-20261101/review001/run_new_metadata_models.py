"""One run of only the new private metadata models, with acquisition refused."""
from contextlib import ExitStack
import hashlib,io,json
from pathlib import Path
import subprocess,time,unittest
from unittest.mock import patch
import urllib.request
import xml.etree.ElementTree as ET
BASE=Path(__file__).resolve().parent
before={path.relative_to(BASE).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
    for tree in ('observations','frozen-references') for path in sorted((BASE/tree).rglob('*')) if path.is_file()}
before['review-facts.json']=hashlib.sha256((BASE/'review-facts.json').read_bytes()).hexdigest()
import test_metadata_current
calls=[]
def refuse(*args,**kwargs):calls.append(True);raise AssertionError('No network, processes, SDK, builds or native work in metadata models')
log=io.StringIO()
with ExitStack() as stack:
    for obj,name in ((subprocess,'run'),(subprocess,'Popen'),(urllib.request,'urlopen')):
        stack.enter_context(patch.object(obj,name,side_effect=refuse))
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(test_metadata_current.JavaFx21CurrentMetadataModels)
    assert suite.countTestCases()==8
    started=time.monotonic();result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite);seconds=time.monotonic()-started
after={path.relative_to(BASE).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
    for tree in ('observations','frozen-references') for path in sorted((BASE/tree).rglob('*')) if path.is_file()}
after['review-facts.json']=hashlib.sha256((BASE/'review-facts.json').read_bytes()).hexdigest()
assert before==after
out=BASE/'new-metadata-models';out.mkdir()
summary={'new_private_metadata_methods':result.testsRun,'passed':result.testsRun-len(result.errors)-len(result.failures)-len(result.skipped),
    'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'seconds':round(seconds,6),
    'evidence_inputs_held':before==after,'held_evidence_files':len(before),'additional_network_or_process_attempts':len(calls),
    'accepted_graph_query_or_test_replays':0,'native_or_build_executions':0,'source_or_test_repository_edits':0,
    'security_acceptance_or_issue_closure_inferred':False}
for name,value in (('summary.json',summary),('inputs-before.json',before),('inputs-after.json',after)):
    with (out/name).open('x',encoding='utf-8') as stream:stream.write(json.dumps(value,indent=2,sort_keys=True)+'\n')
with (out/'unittest.log').open('x',encoding='utf-8') as stream:stream.write(log.getvalue())
xml=ET.Element('testsuite',name='nativecmpkit.javafx21.metadata.source.models',tests=str(result.testsRun),failures=str(len(result.failures)),errors=str(len(result.errors)),skipped=str(len(result.skipped)),time=f'{seconds:.6f}')
props=ET.SubElement(xml,'properties')
for name,value in (('metadata_models_only','true'),('native_executions','0'),('builds','0'),('accepted_suite_replays','0')):
    ET.SubElement(props,'property',name=name,value=value)
for method in unittest.defaultTestLoader.getTestCaseNames(test_metadata_current.JavaFx21CurrentMetadataModels):
    ET.SubElement(xml,'testcase',classname='private.JavaFx21CurrentMetadataModels',name=method)
with (out/'TEST-source-javafx21-metadata.xml').open('xb') as stream:stream.write(ET.tostring(xml,encoding='utf-8',xml_declaration=True)+b'\n')
print(log.getvalue(),end='');print(json.dumps(summary,sort_keys=True))
raise SystemExit(0 if result.wasSuccessful() and not calls else 1)
