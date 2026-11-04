from pathlib import Path
import json,sys,unittest
P=Path(__file__).resolve().parents[1]
plan=json.loads((P/'IMPORTANT-ONLY24-AUTHORIZED-UNEXECUTED-PLAN607.json').read_bytes())
suite=unittest.defaultTestLoader.loadTestsFromNames(plan['test_ids'])
def flatten(suite):
 for test in suite:
  if isinstance(test,unittest.TestSuite):yield from flatten(test)
  else:yield test.id()
loaded=list(flatten(suite))
if loaded!=plan['test_ids']:
 raise AssertionError('Exactly the24 named real source controls must load, not placeholders')
result=unittest.TextTestRunner(verbosity=2).run(suite)
report={'testsRun':result.testsRun,'loaded_exact_test_ids':loaded,
        'failures':[{'id':t.id(),'traceback':s}for t,s in result.failures],
        'errors':[{'id':t.id(),'traceback':s}for t,s in result.errors],
        'skipped':[{'id':t.id(),'reason':s}for t,s in result.skipped],
        'expectedFailures':[t.id()for t,s in result.expectedFailures],
        'unexpectedSuccesses':[t.id()for t in result.unexpectedSuccesses],
        'wasSuccessful':result.wasSuccessful()}
(Path(__file__).parent/'WORKER-RESULT607.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
sys.exit(0 if result.wasSuccessful()else 1)
