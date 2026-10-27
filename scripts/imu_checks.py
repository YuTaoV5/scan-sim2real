"""Pure numerical checks. T_A_B maps B coordinates into A. No ROS required."""
import math
import numpy as np


def analyze(stamps, acceleration, gyro, body_level=False):
    t = np.asarray(stamps, dtype=float)
    a = np.asarray(acceleration, dtype=float)
    w = np.asarray(gyro, dtype=float)
    if len(t) < 100 or a.shape != (len(t), 3) or w.shape != a.shape:
        raise ValueError('At least 100 matched IMU samples required')
    if not all(np.isfinite(x).all() for x in (t, a, w)):
        raise ValueError('Non-finite IMU data')
    dt = np.diff(t)
    if np.any(dt <= 0):
        raise ValueError('IMU timestamps repeat or go backwards')
    am, wm = a.mean(axis=0), w.mean(axis=0)
    astd, wstd = a.std(axis=0, ddof=1), w.std(axis=0, ddof=1)
    norm = float(np.linalg.norm(am))
    units_ok = 8.5 < norm < 11.0
    looks_g = 0.85 < norm < 1.15
    stationary = bool(units_ok and np.linalg.norm(astd) < .15 and
                      np.linalg.norm(wstd) < .015 and np.linalg.norm(wm) < .10)
    phi = math.atan2(am[1], am[2])
    theta = math.atan2(-am[0], math.hypot(am[1], am[2]))
    warnings = []
    if looks_g:
        warnings.append('Acceleration resembles units of g, not ROS SI m/s^2; verify driver. No automatic rescaling applied.')
    elif not units_ok:
        warnings.append('Mean acceleration magnitude is inconsistent with stationary SI data.')
    if not stationary:
        warnings.append('Static-window checks failed; do not use gyro mean as a calibrated bias.')
    if not body_level:
        warnings.append('Body level was not established: angles describe sensor relative to gravity, NOT mounting extrinsics.')
    hz = float(1.0 / np.median(dt))
    if not 150 <= hz <= 250:
        warnings.append('Rate differs from the expected approximately 200 Hz MID360 IMU stream.')
    if dt.max() > .05:
        warnings.append('IMU timestamp gap exceeds 50 ms.')
    return dict(samples=len(t), duration_s=float(t[-1]-t[0]), median_rate_hz=hz,
                max_gap_s=float(dt.max()), mean_acceleration_m_s2=am.tolist(),
                acceleration_norm_m_s2=norm, acceleration_std_m_s2=astd.tolist(),
                gyro_mean_rad_s=wm.tolist(), gyro_std_rad_s=wstd.tolist(),
                gyro_bias_candidate_rad_s=wm.tolist() if stationary else None,
                static_window_pass=stationary, body_level_assumed=body_level,
                gravity_alignment_roll_deg=math.degrees(phi),
                gravity_alignment_pitch_deg=math.degrees(theta),
                mounting_roll_pitch_candidate_deg=[math.degrees(phi), math.degrees(theta)]
                    if stationary and body_level else None,
                yaw_observable=False, translation_observable=False,
                accelerometer_bias_observable=False, lidar_imu_time_offset_observable=False,
                T_base_lidar=None, calibration_complete=False, warnings=warnings)


def ground_plane(points, up, seed=42):
    """Gravity-guided RANSAC: diagnostic plane, not an extrinsic estimator."""
    p = np.asarray(points, dtype=float)
    p = p[np.isfinite(p).all(axis=1)]
    up = np.asarray(up, dtype=float); up /= np.linalg.norm(up)
    # Require points below the sensor; walls and ceilings must not win the fit.
    p = p[(p @ up < -.10) & (np.linalg.norm(p, axis=1) < 8)]
    if len(p) < 150:
        return dict(valid=False, reason='Insufficient below-sensor points; check FOV/masking')
    rng = np.random.default_rng(seed)
    p = p[rng.choice(len(p), min(12000, len(p)), replace=False)]
    best = None
    for _ in range(100):
        q = p[rng.choice(len(p), 3, replace=False)]
        n = np.cross(q[1]-q[0], q[2]-q[0]); length = np.linalg.norm(n)
        if length < 1e-8: continue
        n /= length
        if n @ up < 0: n = -n
        if n @ up < math.cos(math.radians(25)): continue
        d = -float(n @ q[0]); mask = np.abs(p @ n + d) < .025
        if best is None or mask.sum() > best.sum(): best = mask
    if best is None or best.sum() < 150:
        return dict(valid=False, reason='No sufficiently supported near-horizontal plane')
    inliers = p[best]; center = inliers.mean(axis=0)
    _, _, vh = np.linalg.svd(inliers-center, full_matrices=False)
    n = vh[-1]
    if n @ up < 0: n = -n
    d = -float(n @ center)
    return dict(valid=True, inliers=int(best.sum()), candidate_points=len(p),
                normal_lidar=n.tolist(), plane_offset_m=d,
                sensor_to_plane_distance_m=abs(d),
                rmse_m=float(np.sqrt(np.mean((inliers @ n+d)**2))),
                gravity_normal_difference_deg=math.degrees(math.acos(float(np.clip(n @ up,-1,1)))),
                note='May be a tabletop or another floor. Visually select a known flat floor; this distance is not base-to-lidar translation.')
