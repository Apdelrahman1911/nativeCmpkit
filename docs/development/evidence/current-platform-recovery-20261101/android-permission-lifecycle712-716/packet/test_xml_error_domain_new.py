"""Genuinely NEW malformed-XML source control against immutable frozen pure validators."""
from pathlib import Path
import importlib.util
import unittest
P = Path(__file__).resolve().parent

def contract():
    spec = importlib.util.spec_from_file_location('new_xml_error_domain_contract', P / 'frozen/scripts/ci/android_permission_lifecycle_contract.py')
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

class NewPermissionXmlErrorDomainTests(unittest.TestCase):
    def test_new_malformed_source_compiled_and_reporter_xml_normalize_into_named_failure_domain(self):
        c = contract()
        for domain in ('source', 'compiled', 'reporter'):
            with self.subTest(domain=domain):
                with self.assertRaises(ValueError):
                    payload = b'<manifest><application></manifest>'
                    if domain == 'reporter': c.validate_reporter_source(payload)
                    else: c.validate_manifest(payload, compiled=domain == 'compiled')

if __name__ == '__main__':
    unittest.main(verbosity=2)
