import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import unittest
import numpy as np
from imu_checks import analyze, ground_plane
from accel_six_pose import fit


class Check(unittest.TestCase):
    def test_tilt_and_bias(self):
        t=np.arange(1000)/200; angle=np.deg2rad(12)
        a=np.tile([-9.81*np.sin(angle),0,9.81*np.cos(angle)],(1000,1))
        w=np.tile([.002,-.003,.001],(1000,1))
        result=analyze(t,a,w,True)
        self.assertTrue(result['static_window_pass'])
        self.assertAlmostEqual(result['gravity_alignment_pitch_deg'],12)
        self.assertFalse(result['calibration_complete'])
        self.assertIsNone(result['T_base_lidar'])
    def test_motion_rejected(self):
        t=np.arange(1000)/200;a=np.tile([0,0,9.81],(1000,1));a[:,0]=np.sin(20*t)
        self.assertFalse(analyze(t,a,np.zeros_like(a))['static_window_pass'])
    def test_wrong_units(self):
        a=np.tile([0,0,1.],(1000,1))
        self.assertFalse(analyze(np.arange(1000)/200,a,np.zeros_like(a))['static_window_pass'])
    def test_duplicate_time(self):
        with self.assertRaises(ValueError):analyze(np.zeros(1000),np.ones((1000,3)),np.zeros((1000,3)))
    def test_floor(self):
        rng=np.random.default_rng(1);p=rng.uniform(-2,2,(1500,3));p[:,2]=-.5+rng.normal(0,.003,1500)
        r=ground_plane(p,[0,0,9.81]);self.assertTrue(r['valid']);self.assertAlmostEqual(r['sensor_to_plane_distance_m'],.5,places=2)
    def test_six_pose_bias(self):
        bias=np.array([.05,-.03,.02]);scale=1.01
        a=np.vstack([np.eye(3),-np.eye(3)])*9.81/scale+bias
        reports=[dict(static_window_pass=True,mean_acceleration_m_s2=v.tolist()) for v in a]
        result=fit(reports)
        np.testing.assert_allclose(result['accelerometer_bias_candidate_m_s2'],bias,atol=1e-10)
        self.assertAlmostEqual(result['isotropic_scale_candidate'],scale)
    def test_six_pose_degenerate(self):
        with self.assertRaises(ValueError):fit([dict(static_window_pass=True,mean_acceleration_m_s2=[0,0,9.81])]*6)


if __name__=='__main__':unittest.main()
