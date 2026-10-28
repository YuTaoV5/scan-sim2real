import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('audit_mounting', ROOT/'scripts/audit_mounting.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class MountingAuditTests(unittest.TestCase):
    def setUp(self):
        folder = ROOT/'generated/test-tmp'
        folder.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=folder)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'source.cpp').write_bytes(b'line one\nSENSOR_ANCHOR\n')
        self.inventory = {'changes':[dict(id='MTEST', scope='live', title='fixture',
            implementation_status='site_required', sources=[dict(repository='scan',
                path='source.cpp', anchor='SENSOR_ANCHOR')])]}
        self.blobs = {('scan','source.cpp'):audit.git_blob((self.root/'source.cpp').read_bytes())}

    def report(self):
        return audit.inspect_sources({'scan':self.root}, {'scan':'a'*40}, self.blobs, self.inventory)

    def test_original_source_locations_do_not_certify_hardware(self):
        before = (self.root/'source.cpp').read_bytes()
        report = self.report()
        self.assertTrue(report['source_audit_passed'])
        self.assertEqual(report['changes'][0]['locations'][0]['lines'], [2])
        self.assertEqual(report['changes'][0]['implementation_status'], 'site_required')
        self.assertFalse(report['hardware_tested'])
        self.assertFalse(report['upstream_patches_applied'])
        self.assertEqual(before, (self.root/'source.cpp').read_bytes())

    def test_modified_source_fails_even_if_anchor_survives(self):
        (self.root/'source.cpp').write_bytes(b'SENSOR_ANCHOR\nmodified\n')
        self.assertFalse(self.report()['source_audit_passed'])

    def test_missing_anchor_fails_even_for_valid_blob(self):
        self.inventory['changes'][0]['sources'][0]['anchor'] = 'MISSING'
        self.assertFalse(self.report()['source_audit_passed'])

    def test_source_path_cannot_escape_checkout(self):
        for relative in ('../outside.cpp', str(self.root.resolve()/'source.cpp')):
            with self.assertRaises(ValueError):audit.source_file(self.root, relative)

    def test_wrong_upstream_head_rejected(self):
        roots = {x:self.root for x in ('scan','lio','livox_driver')}
        with patch.object(audit.subprocess, 'check_output', return_value='b'*40):
            with self.assertRaises(ValueError):
                audit.checkout_identities(roots, self.inventory, {x:'a'*40 for x in roots})

    def test_checklist_ids_and_all_physical_values_remain_unknown(self):
        inventory = json.loads((ROOT/'configs/mounting-change-checklist.json').read_text(encoding='utf-8'))
        ids = [row['id'] for row in inventory['changes']]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertFalse(inventory['real_mounting_values_known'])
        calibration = json.loads((ROOT/'configs/calibration.template.json').read_text(encoding='utf-8'))
        self.assertIsNone(calibration['T_base_lidar'])
        self.assertIsNone(calibration['mounting_angle_deg'])


if __name__ == '__main__':unittest.main()
