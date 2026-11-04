# stdlib-only exact13 execution recorder; execute only on lead approval.
from pathlib import Path
import datetime,hashlib,json,os,re,stat,subprocess,sys,tempfile,time
PACKET=Path('/root/nativecmpkit-source-proposals-20261104/producer-failure-evidence711/joint-ingress-on714-compact-r1')
ROOT=Path('/root/projects/nativeCmpKit')
HERE=Path(__file__).resolve().parent
ANCHORS={
    'EXACT-JOINT-SOURCE-RECIPE711.json':'f0ba760f2f1df351cc0b70fc4039f6d2de17cf763858dc760b9dba4889ea5b4b',
    'NEW-CHANGED-FOCUSED-SELECTION711.json':'8ac6ae46595412a3a1c4e50cbb049783b7ef0c1e02eea6933613942a427f71f9',
    'SEAL-JOINT-INGRESS711.json':'1c172c5e56509e6a8ae5456b094845f72c167774323f4f716f66bc2e7a7ae8f6',
}
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(q,d):
    payload=(json.dumps(d,indent=2,sort_keys=True)+'\n').encode()
    with q.open('xb') as f:f.write(payload)
    q.chmod(0o600)
def metadata(m):return (m.st_dev,m.st_ino,m.st_mode,m.st_nlink,m.st_size,m.st_mtime_ns,m.st_ctime_ns)
def sample(q,maximum=4*1024*1024):
    before=q.lstat()
    if not(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=maximum and q.resolve(strict=True)==q.absolute()):
        raise ValueError('ordinary bounded declared input required: '+str(q))
    with q.open('rb') as f:
        if metadata(os.fstat(f.fileno()))!=metadata(before):raise ValueError('input replaced before read')
        payload=f.read(maximum+1)
        if metadata(os.fstat(f.fileno()))!=metadata(before):raise ValueError('input changed during read')
    if metadata(q.lstat())!=metadata(before) or len(payload)!=before.st_size:raise ValueError('input custody changed')
    return payload,{'path':str(q),'bytes':len(payload),'sha256':sha(payload),'mode_octal':format(before.st_mode&0o777,'04o')}
if sys.argv[1:]!=['--execute-authorized-first13']:
    raise SystemExit('No execution: exact lead-authorized flag required; no source/control imported.')
results=HERE/'results-FIRST13'
results.mkdir(mode=0o700)
launched=False
try:
    data={}
    for name,pinned in ANCHORS.items():
        payload,row=sample(PACKET/name)
        if row['sha256']!=pinned:raise ValueError('frozen execution anchor mismatch')
        data[name]=json.loads(payload)
    seal=data['SEAL-JOINT-INGRESS711.json']
    recipe=data['EXACT-JOINT-SOURCE-RECIPE711.json']
    selection=data['NEW-CHANGED-FOCUSED-SELECTION711.json']
    for record in [seal['recipe'],seal['selection'],seal['proposed_source_map'],seal['proposed_compact_hashes'],seal['actual_root714_beforeimages'],seal['source_validation'],seal['spec_operations'],seal['unexecuted_fixture_correction'],*seal['sources']]:
        payload,row=sample(PACKET/record['path'])
        if (row['sha256'],row['bytes'],row['mode_octal'])!=(record['sha256'],record['bytes'],record['mode_octal']):raise ValueError('sealed input mismatch')
    source_map=json.loads((PACKET/seal['proposed_source_map']['path']).read_bytes())
    root_rows=json.loads((PACKET/seal['actual_root714_beforeimages']['path']).read_bytes())['source_rows']
    methods=selection['methods'];argv=selection['exact_unittest_argv']
    if len(methods)!=len(set(methods)):raise ValueError('exact13 unique selection required')
    if not(len(methods)==13 and selection['changed_method_count']==7 and selection['genuinely_new_method_count']==6 and argv==['python3','-B','-m','unittest','-v']+methods):raise ValueError('exact frozen command required')
    if len(source_map['inputs'])!=282:raise ValueError('only finite282 source materialization permitted')
    named_before=[]
    for record in root_rows:
        payload,row=sample(ROOT/record['path'])
        if (row['sha256'],row['bytes'],row['mode_octal'])!=(record['sha256'],record['bytes'],record['mode_octal']):raise ValueError('ROOT714 beforeimage changed before child')
        named_before.append(row)
    for record in seal['sources']:
        payload,row=sample(PACKET/record['path']);named_before.append(row)
    model_before={};model_after={};model_dir=None;direct=None;elapsed=None;cleanup_complete=False
    with tempfile.TemporaryDirectory(prefix='nativecmpkit-joint711-first13-model-') as temporary:
        model=Path(temporary).resolve();model_dir=str(model)
        for relative,record in source_map['inputs'].items():
            parts=Path(relative).parts
            if Path(relative).is_absolute() or '..' in parts or not parts:raise ValueError('unsafe declared model path')
            source_file=Path(record['source_location_absolute'])
            if source_file!=(PACKET/'postimages'/relative) and source_file!=(ROOT/relative):raise ValueError('no external runtime proposal dependency')
            payload,row=sample(source_file)
            if (row['sha256'],row['bytes'],row['mode_octal'])!=(record['sha256'],record['bytes'],record['mode_octal']):raise ValueError('proposed source changed before materialization')
            destination=model/relative;destination.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            with destination.open('xb') as f:f.write(payload)
            destination.chmod(int(record['mode_octal'],8))
            copied,copied_row=sample(destination);model_before[relative]={key:copied_row[key] for key in ('bytes','sha256','mode_octal')}
            if copied!=payload:raise ValueError('model payload mismatch')
        environment=os.environ.copy();environment['PYTHONPATH']=str(model/'scripts/ci');environment['PYTHONDONTWRITEBYTECODE']='1'
        dump(results/'FIRST13-STARTED711.json',{'schema':'nativecmpkit-joint711-compact-r1-exact13-start-v1','started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'anchors':ANCHORS,'exact_argv':argv,'working_directory':str(model),'explicit_PYTHONPATH':environment['PYTHONPATH'],'finite_model_input_count':282,'named_actual_ROOT_plus_candidate_before':named_before,'model_before':model_before,'source_only':True,'original_FIRST10_replayed':False,'actual_scopes_compiler_native_Git_network_ROOT_mutations':0})
        print(json.dumps({'status':'STARTED_EXACT13_ONCE','started_record':str(results/'FIRST13-STARTED711.json'),'cwd':str(model),'methods':len(methods)}),flush=True)
        stdout_path=results/'FIRST13-stdout.txt';stderr_path=results/'FIRST13-stderr.txt'
        with stdout_path.open('xb') as stdout,stderr_path.open('xb') as stderr:
            stdout_path.chmod(0o600);stderr_path.chmod(0o600);start=time.monotonic();launched=True
            completed=subprocess.run(argv,cwd=model,env=environment,stdout=stdout,stderr=stderr,check=False)
            elapsed=time.monotonic()-start;direct=completed.returncode
        for relative in source_map['inputs']:
            payload,row=sample(model/relative);model_after[relative]={key:row[key] for key in ('bytes','sha256','mode_octal')}
    cleanup_complete=not Path(model_dir).exists()
    named_after=[]
    for row in named_before:
        payload,after=sample(Path(row['path']));named_after.append(after)
    stdout=(results/'FIRST13-stdout.txt').read_bytes();stderr=(results/'FIRST13-stderr.txt').read_bytes();text=stderr.decode('utf-8',errors='replace')
    case_lines=[];observed=[];statuses=[]
    for line in text.splitlines():
        found=re.fullmatch(r'(test[A-Za-z0-9_]+) \(([A-Za-z0-9_.]+)\) \.\.\. (ok|FAIL|ERROR)',line)
        if found:case_lines.append(line);observed.append(found.group(2));statuses.append(found.group(3))
    summaries=re.findall(r'^Ran (\d+) tests in ([0-9.]+)s$',text,re.M)
    result={'schema':'nativecmpkit-joint711-compact-r1-exact13-original-result-v1','ended_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'anchors':ANCHORS,'exact_argv':argv,'direct_returncode':direct,'outer_child_elapsed_seconds':elapsed,'selected_methods':methods,'original_case_status_lines':case_lines,'observed_methods':observed,'observed_case_statuses':statuses,'unittest_summary_observations':summaries,'named_actual_ROOT_plus_candidate_before':named_before,'named_actual_ROOT_plus_candidate_after':named_after,'named_actual_inputs_held':named_before==named_after,'model_before':model_before,'model_after':model_after,'all282_model_inputs_held':model_before==model_after,'owned_model_cleanup_absence':cleanup_complete,'stdout':{'path':'FIRST13-stdout.txt','bytes':len(stdout),'sha256':sha(stdout)},'stderr':{'path':'FIRST13-stderr.txt','bytes':len(stderr),'sha256':sha(stderr)},'accepted_populations_replayed':False,'v1_controls_executed':0,'original_FIRST10_replayed':False,'actual_scopes_compiler_native_Git_network_ROOT_mutations':0,'result_scope':'exact7changed+6NEW finite source/model controls only; no producer/native/reuse/consumer/security/issue/release acceptance'}
    dump(results/'FIRST13-RESULT711.json',result)
    print(json.dumps({'direct_returncode':direct,'outer_child_elapsed_seconds':elapsed,'cases_observed':len(observed),'ok':statuses.count('ok'),'FAIL':statuses.count('FAIL'),'ERROR':statuses.count('ERROR'),'summaries':summaries,'named_inputs_held':named_before==named_after,'model282_held':model_before==model_after,'model_cleanup_absent':cleanup_complete,'result_path':str(results/'FIRST13-RESULT711.json'),'result_sha256':sha((results/'FIRST13-RESULT711.json').read_bytes())}),flush=True)
    raise SystemExit(direct)
except SystemExit:
    raise
except BaseException as error:
    dump(results/'FIRST13-RECORDER-REFUSAL711.json',{'schema':'nativecmpkit-joint711-compact-r1-execution-recorder-refusal-v1','error_type':type(error).__name__,'message':str(error)[:1000],'unittest_child_launched':launched,'no_automatic_retry':True,'original_FIRST10_replayed':False})
    raise
