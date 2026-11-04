#!/usr/bin/env python3
"""Create only the changed1+NEW2 source-control plan and external once runner."""
import ast
import hashlib
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parent
ORIGINAL = Path('/root/nativecmpkit-source-proposals-20261104/javafx-ordinary-maven-current2ee707-route658')
CORRECTION = PACKET / 'EXACT-REPORT-CUSTODY-CLOSED-BASELINE-CORRECTION658.json'
correction_raw = CORRECTION.read_bytes()
assert hashlib.sha256(correction_raw).hexdigest() == '34090afea91d10fe1a49f1d94902142186ceafa99b11bd3b9b8876d1cdfffd38'
correction = json.loads(correction_raw)
REVIEW705 = Path('/root/nativecmpkit-source-proposals-20261104/producer-budget-review705/windows-ordinary-consumer658/FINAL-SUCCESSOR-PREEXECUTION-SOURCE-QUALIFICATION705.json')
review_raw = REVIEW705.read_bytes()
assert hashlib.sha256(review_raw).hexdigest() == '4b272823a92d6c0a3a1042c8e0405414fce270974c71929660462045cccee907'
review = json.loads(review_raw)
selected = correction['source_controls']['only_selected_methods']
assert len(selected) == 3 and len(correction['source_controls']['NEW_methods']) == 2 and selected == review['only_qualified_selection']
plan = {
    'schema': 'nativecmpkit-javafx-report-custody-changed1-NEW2-exact-plan658-v1',
    'scope': 'Only changed owning graph1 plus NEW raw/coupled-custody2 after passive source qualification; no discovery, unchanged source9, Actionlint, old/helper/controller/native/build/Git/dispatch replay',
    'new-controls': {'selected_methods': selected, 'command': ['/usr/bin/python3', '-I', '-B', str(ORIGINAL / 'new_controls_audit_bootstrap.py'),
                     str(PACKET / 'proposed/scripts/ci/test_javafx_ordinary_maven_route.py'),
                     str(PACKET / 'CHANGED1-NEW2-SOURCE658/audit.json'), *selected], 'timeout_seconds': 120},
    'changed_existing_methods': 1, 'genuinely_NEW_methods': 2, 'unchanged_nine_replayed': False,
    'Actionlint_replayed': False, 'accepted_private_library_Stop_replayed': False,
    'ROOT_worktree_Git_network_build_stage_native_or_dispatch': 0, 'original_packet_changed': False,
    'exact_current_source_recipe': {'path': str(CORRECTION), 'bytes': len(correction_raw), 'sha256': hashlib.sha256(correction_raw).hexdigest()},
    'independent705_current_source_only_qualification': {'path': str(REVIEW705), 'bytes': len(review_raw), 'sha256': hashlib.sha256(review_raw).hexdigest()},
    'independent705_current_postimage_pins': review['final_two_source_pins'],
    'lead_authorization': 'Lead message authorizes only exact changed owning graph1+NEW custody2 under final34090afe and705 source qualification4b272823; no native/adoption/lint replay',
}
with (PACKET / 'REPORT-CUSTODY-CHANGED1-NEW2-EXECUTION-PLAN658.json').open('x') as output:
    json.dump(plan, output, indent=2, sort_keys=True); output.write('\n')
(PACKET / 'REPORT-CUSTODY-CHANGED1-NEW2-EXECUTION-PLAN658.json').chmod(0o600)
runner = (ORIGINAL / 'run_new_route_selection_once.py').read_text()
replacements = (
    ('"""Execute only the qualified NEW passive selection or candidate Actionlint once."""', '"""Execute only the qualified changed owning graph1+NEW custody2 once."""'),
    ("PLAN = PACKET / 'NEW-ROUTE-EXECUTION-PLAN658.json'", "PLAN = PACKET / 'REPORT-CUSTODY-CHANGED1-NEW2-EXECUTION-PLAN658.json'"),
    ("QUALIFIED = PACKET / 'QUALIFIED-SOURCE-INPUTS658.json'", "QUALIFIED = PACKET / 'QUALIFIED-REPORT-CUSTODY-SOURCE-INPUTS658.json'"),
    ("sys.argv[1] not in ('new-controls', 'actionlint')", "sys.argv[1] != 'new-controls'"),
    ("('FIRST-NEW10-SOURCE658' if stage == 'new-controls' else 'FIRST-ACTIONLINT658')", "'CHANGED1-NEW2-SOURCE658'"),
    ("'schema': 'nativecmpkit-javafx-new-source-execution658-v1'", "'schema': 'nativecmpkit-javafx-report-custody-changed1-NEW2-source-execution658-v1'"),
    ("'automatic_retry': False, 'accepted_private_library_Stop_replayed': False}", "'automatic_retry': False, 'accepted_private_library_Stop_replayed': False,\n          'changed_existing_methods': 1, 'genuinely_NEW_methods': 2, 'unchanged_nine_replayed': False,\n          'Actionlint_replayed': False, 'original_packet_changed': False}"),
    ("record['selected_NEW_methods'] = plan[stage]['NEW_methods']", "record['selected_methods'] = plan[stage]['NEW_methods']"),
    ("'old_method_populations_requested': 0", "'unchanged_method_populations_requested': 0"),
    ("'NEW passive AST/text source controls only' if stage == 'new-controls'", "'Only changed owning graph1 plus NEW raw/coupled-custody2 passive AST/text controls' if stage == 'new-controls'"),
)
for before, after in replacements:
    assert runner.count(before) == 1, before
    runner = runner.replace(before, after, 1)
assert runner.count("plan[stage]['NEW_methods']") == 2
runner = runner.replace("plan[stage]['NEW_methods']", "plan[stage]['selected_methods']")
ast.parse(runner)
with (PACKET / 'run_report_custody_selection_once658.py').open('x') as output:
    output.write(runner)
(PACKET / 'run_report_custody_selection_once658.py').chmod(0o600)
print(json.dumps({'passed': True, 'selected_methods': selected, 'Actionlint_or_native_requested': False}, sort_keys=True))
