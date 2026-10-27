import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import numpy as np
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import prepare


class PrepareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_root=ROOT/'generated/test-tmp'
        cls.temp_root.mkdir(parents=True,exist_ok=True)

    def calibration(self):
        angle=np.deg2rad(17);c,s=np.cos(angle),np.sin(angle)
        t=np.array([[c,0,s,.2],[0,1,0,.03],[-s,0,c,.15],[0,0,0,1]])
        return dict(reviewed=True,initial_base_height_m=.4,T_base_lidar=t.tolist(),T_imu_lidar=np.eye(4).tolist())

    def test_unknown_template_rejected(self):
        with self.assertRaises(ValueError):prepare.load_calibration(ROOT/'configs/calibration.template.json')

    def test_reflection_rejected(self):
        t=np.eye(4);t[0,0]=-1
        with self.assertRaises(ValueError):prepare.transform(t)

    def test_nonfinite_rejected(self):
        t=np.eye(4);t[0,3]=np.nan
        with self.assertRaises(ValueError):prepare.transform(t)

    def setup_sources(self,root):
        lio=root/'lio';scan=root/'scan';(lio/'yaml/sensors').mkdir(parents=True);(lio/'yaml/runtime').mkdir()
        (lio/'yaml/sensors/livox.yaml').write_text(yaml.safe_dump(dict(offset={},topic_sub={})))
        (lio/'yaml/runtime/mapping.yaml').write_text(yaml.safe_dump(dict(elevator={},wheel={},pub={})))
        scan.mkdir()
        calibration=root/'c.json';calibration.write_text(json.dumps(self.calibration()))
        return lio,scan,calibration

    def test_measured_inverse_and_world_cloud_launch(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as d:
            root=Path(d);lio,scan,c=self.setup_sources(root)
            def head(cmd,**kwargs):return prepare.LIO_PIN if cmd[2]==str(lio) else prepare.SCAN_PIN
            with patch('subprocess.check_output',side_effect=head):prepare.generate(c,lio,scan,root/'out',3)
            config=yaml.safe_load((lio/'yaml/sensors/rob2nav.yaml').read_text())['offset']
            expected=np.linalg.inv(self.calibration()['T_base_lidar'])
            np.testing.assert_allclose(config['lidar_R_body'],expected[:3,:3])
            np.testing.assert_allclose(config['lidar_t_body'],expected[:3,3])
            xml=ET.parse(root/'out/scan_go2edu.launch').getroot()
            params={p.attrib['name']:p.attrib['value'] for p in xml.findall('param')}
            self.assertEqual(params['scan_planner_node/grid_map/need_extrinsic'],'false')
            self.assertEqual(params['scan_planner_node/grid_map/body_height'],'0.4')
            args={p.attrib['name']:p.attrib['value'] for p in xml.find('include').findall('arg')}
            self.assertEqual(args['cloud_is_world'],'true');self.assertEqual(args['navi_mode'],'3')
            self.assertIn('/rob2nav/cloud_world',args.values())

    def test_mode2_requires_real_waypoints_before_mutating_source(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as d:
            root=Path(d);lio,scan,c=self.setup_sources(root)
            def head(cmd,**kwargs):return prepare.LIO_PIN if cmd[2]==str(lio) else prepare.SCAN_PIN
            with patch('subprocess.check_output',side_effect=head):
                with self.assertRaises(ValueError):prepare.generate(c,lio,scan,root/'out',2)
            self.assertFalse((lio/'yaml/sensors/rob2nav.yaml').exists())

    def test_cloud_height_shift_preserves_other_fields_and_padding(self):
        for big in (False,True):
            order='>' if big else '<';point=struct.pack(order+'fffI',1,2,3,123)
            raw=point+b'PAD!'+point+b'PAD!'
            shifted=prepare.shift_cloud_z(raw,1,2,16,20,8,.4,big)
            self.assertAlmostEqual(struct.unpack_from(order+'f',shifted,8)[0],3.4,places=5)
            self.assertEqual(shifted[:8],raw[:8]);self.assertEqual(shifted[12:20],raw[12:20])
            self.assertEqual(shifted[36:40],b'PAD!')


if __name__=='__main__':unittest.main()
