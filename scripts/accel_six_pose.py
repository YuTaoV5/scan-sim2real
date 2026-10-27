#!/usr/bin/env python3
"""Fit accelerometer bias and isotropic scale from 6+ static check reports.
Not a full cross-axis calibration. Physically reorient a removable rigid assembly;
do not tip a powered robot. Does not write LIO configuration.
"""
import argparse
import json
from pathlib import Path
import numpy as np


def fit(reports, gravity=9.81):
    if len(reports)<6: raise ValueError('Need 6 or more independent static orientations')
    if any(not r.get('static_window_pass') for r in reports):
        raise ValueError('Every orientation must pass static checks')
    a=np.array([r['mean_acceleration_m_s2'] for r in reports])
    directions=a/np.linalg.norm(a,axis=1)[:,None]
    if np.min(np.linalg.eigvalsh(directions.T@directions/len(a)))<.15:
        raise ValueError('Orientation coverage insufficient: include +/- X,Y,Z directions')
    if np.linalg.norm(directions.mean(axis=0))>.4:
        raise ValueError('Orientations do not cover opposing faces')
    A=np.column_stack([2*a,np.ones(len(a))]); rhs=np.sum(a*a,axis=1)
    result,_,rank,_=np.linalg.lstsq(A,rhs,rcond=None)
    if rank<4: raise ValueError('Unobservable fit')
    bias=result[:3];radius=np.sqrt(result[3]+bias@bias)
    scale=gravity/radius
    errors=np.linalg.norm((a-bias)*scale,axis=1)-gravity
    return dict(accelerometer_bias_candidate_m_s2=bias.tolist(),isotropic_scale_candidate=float(scale),
                corrected_norm_rmse_m_s2=float(np.sqrt(np.mean(errors**2))),
                correction_equation='a_corrected = scale * (a_raw - bias)',
                validation_required=True, written_to_runtime=False,
                limitation='Does not estimate cross-axis/non-orthogonality or lidar/body extrinsics. Validate with held-out poses.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('reports',nargs='+');p.add_argument('--output',required=True)
    a=p.parse_args();r=fit([json.loads(Path(f).read_text()) for f in a.reports])
    Path(a.output).write_text(json.dumps(r,indent=2,allow_nan=False)+'\n');print(json.dumps(r,indent=2))
