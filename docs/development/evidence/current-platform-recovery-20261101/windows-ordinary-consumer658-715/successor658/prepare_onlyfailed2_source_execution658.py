#!/usr/bin/env python3
"""Create only the independently705-qualified exact failed2 recovery plan and once runner."""
import ast
import hashlib
import json
from pathlib import Path
import sys

PACKET = Path(__file__).resolve().parent
ORIGINAL = Path('/root/nativecmpkit-source-proposals-20261104/javafx-ordinary-maven-current2ee707-route658')
if len(sys.argv) != 3:
    raise SystemExit('Exact named705 onlyfailed2 source qualification path and digest required')
review_path = Path(sys.argv[1])
review_raw = review_path.read_bytes()
assert hashlib.sha256(review_raw).hexdigest() == sys.argv[2]
recovery_path = PACKET / 'EXACT-ONLYFAILED2-STRUCTURAL-SOURCE-CONTROL-RECOVERY658.json'
recovery_raw = recovery_path.read_bytes()
assert hashlib.sha256(recovery_raw).hexdigest() == '635ae29f8678dabe5243a8dd73799470b3ce5d99c663a949b156f8011b353d6b'
recovery = json.loads(recovery_raw)
selected = recovery['only_selected_methods']
assert len(selected) == 2
plan = {
    'schema': 'nativecmpkit-javafx-onlyfailed2-structural-exact-plan658-v1',
    'scope': 'Only failed owning graph1 plus failed original NEW raw-capture1 structural controls; no accepted NEW coupling1, other9, Actionlint, Stop, old/helper/controller/native/build/Git/dispatch replay',
    'new-controls': {'selected_methods': selected, 'command': ['/usr/bin/python3', '-I', '-B', str(ORIGINAL / 'new_controls_audit_bootstrap.py'),
                     str(PACKET / 'proposed/scripts/ci/test_javafx_ordinary_maven_route.py'),
                     str(PACKET / 'ONLYFAILED2-STRUCTURAL-SOURCE-RECOVERY658/audit.json'), *selected], 'timeout_seconds': 120},
    'failed_owning_existing_graph_methods_requested': 1, 'failed_original_NEW_raw_capture_methods_requested': 1,
    'accepted_NEW_coupling_method_replayed': False, 'unchanged_nine_replayed': False,
    'Actionlint_replayed': False, 'accepted_private_library_Stop_replayed': False,
    'ROOT_worktree_Git_network_build_stage_native_or_dispatch': 0, 'original_packet_changed': False,
    'exact_two_control_fragment_recipe': {'path': str(recovery_path), 'bytes': len(recovery_raw), 'sha256': hashlib.sha256(recovery_raw).hexdigest()},
    'independent705_onlyfailed2_source_only_qualification': {'path': str(review_path), 'bytes': len(review_raw), 'sha256': hashlib.sha256(review_raw).hexdigest()},
    'original_failed3_result': recovery['original_source3_result'],
    'lead_authorization': 'Original exact first3 once and failure-preserving failed/changed-only recovery; only failed2 after705 exact structural source qualification',
}
with (PACKET / 'ONLYFAILED2-STRUCTURAL-EXECUTION-PLAN658.json').open('x') as output:
    json.dump(plan, output, indent=2, sort_keys=True); output.write('\n')
(PACKET / 'ONLYFAILED2-STRUCTURAL-EXECUTION-PLAN658.json').chmod(0o600)
runner = (PACKET / 'run_report_custody_selection_once658.py').read_text()
replacements = (
    ('"""Execute only the qualified changed owning graph1+NEW custody2 once."""', '"""Execute only the qualified failed owning graph1+failed NEW raw-capture1 once."""'),
    ("PLAN = PACKET / 'REPORT-CUSTODY-CHANGED1-NEW2-EXECUTION-PLAN658.json'", "PLAN = PACKET / 'ONLYFAILED2-STRUCTURAL-EXECUTION-PLAN658.json'"),
    ("QUALIFIED = PACKET / 'QUALIFIED-REPORT-CUSTODY-SOURCE-INPUTS658.json'", "QUALIFIED = PACKET / 'QUALIFIED-ONLYFAILED2-STRUCTURAL-SOURCE-INPUTS658.json'"),
    ("result_dir = PACKET / 'CHANGED1-NEW2-SOURCE658'", "result_dir = PACKET / 'ONLYFAILED2-STRUCTURAL-SOURCE-RECOVERY658'"),
    ("'schema': 'nativecmpkit-javafx-report-custody-changed1-NEW2-source-execution658-v1'", "'schema': 'nativecmpkit-javafx-onlyfailed2-structural-source-execution658-v1'"),
    ("'changed_existing_methods': 1, 'genuinely_NEW_methods': 2, 'unchanged_nine_replayed': False,", "'failed_owning_existing_graph_methods_requested': 1, 'failed_original_NEW_raw_capture_methods_requested': 1,\n          'accepted_NEW_coupling_method_replayed': False, 'unchanged_nine_replayed': False,"),
    ("'Only changed owning graph1 plus NEW raw/coupled-custody2 passive AST/text controls'", "'Only failed owning graph1 plus failed original NEW raw-capture1 structural AST/text controls'"),
)
for before, after in replacements:
    assert runner.count(before) == 1, before
    runner = runner.replace(before, after, 1)
ast.parse(runner)
with (PACKET / 'run_onlyfailed2_structural_selection_once658.py').open('x') as output:
    output.write(runner)
(PACKET / 'run_onlyfailed2_structural_selection_once658.py').chmod(0o600)
print(json.dumps({'passed': True, 'selected_methods': selected, 'accepted_NEW_coupling1_or_other9_lint_Stop_or_native_requested': False}, sort_keys=True))
