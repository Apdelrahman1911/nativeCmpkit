"""Genuinely NEW inert encoded-DTD refusal control against frozen pure validators."""
from pathlib import Path
import importlib.util
import unittest
import xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent

def contract():
    spec=importlib.util.spec_from_file_location('new_encoded_dtd_contract',P/'frozen/scripts/ci/android_permission_lifecycle_contract.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

class NewPermissionEncodedDtdTests(unittest.TestCase):
    def test_new_utf16_dtd_cannot_bypass_source_compiled_or_reporter_entity_refusals(self):
        c=contract()
        for domain in ('source','compiled','reporter'):
            with self.subTest(domain=domain):
                relative=c.MODULE+'/src/androidDeviceTest/AndroidManifest.xml' if domain=='reporter' else c.FIXTURE+'/src/main/AndroidManifest.xml'
                root=ET.fromstring((P/'frozen'/relative).read_bytes())
                if domain=='compiled':
                    root.set('package',c.PACKAGE);root.find('application').set(c.ANDROID+'debuggable','true')
                    ET.SubElement(root,'uses-sdk',{c.ANDROID+'minSdkVersion':'35',c.ANDROID+'targetSdkVersion':'37'})
                body=ET.tostring(root,encoding='unicode')
                # The old byte guard misses a DTD that the XML parser actually decodes.
                encoded=('<?xml version="1.0" encoding="utf-16"?><!DOCTYPE manifest [<!ENTITY unused "inert">]>'+body).encode('utf-16')
                self.assertNotIn(b'<!DOCTYPE',encoded)
                with self.assertRaises(ValueError):
                    if domain=='reporter':c.validate_reporter_source(encoded)
                    else:c.validate_manifest(encoded,compiled=domain=='compiled')

if __name__=='__main__':unittest.main(verbosity=2)
