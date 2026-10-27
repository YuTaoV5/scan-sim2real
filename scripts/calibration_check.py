#!/usr/bin/env python3
"""Read-only MID360 diagnostic; never sends SDK commands or writes LIO config."""
import argparse
import json
from pathlib import Path
import threading
import time
import numpy as np
from imu_checks import analyze, ground_plane


def main():
    import rospy
    import roslib.message
    from sensor_msgs.msg import Imu, PointCloud2
    from sensor_msgs import point_cloud2
    from visualization_msgs.msg import Marker
    from geometry_msgs.msg import Point
    from std_msgs.msg import Header
    p = argparse.ArgumentParser()
    p.add_argument('--imu', default='/livox/imu')
    p.add_argument('--cloud', default='/livox/lidar')
    p.add_argument('--cloud-type', default='livox_ros_driver2/CustomMsg')
    p.add_argument('--seconds', type=float, default=20)
    p.add_argument('--timeout', type=float, default=90)
    p.add_argument('--body-level', action='store_true', help='Only if body axes were physically levelled')
    p.add_argument('--keep-view', action='store_true', help='Keep publishing raw cloud to RViz after saving report')
    p.add_argument('--output', default='/work/data/calibration_report.json')
    args = p.parse_args(rospy.myargv()[1:])
    if args.seconds < 5 or args.timeout < args.seconds:
        p.error('Use at least 5 s data and a timeout greater than duration')
    rospy.init_node('mid360_calibration_check')
    lock = threading.Lock(); samples = []; clouds = []; frame = [None]; seen = [0]
    cloud_pub = rospy.Publisher('/calibration/cloud', PointCloud2, queue_size=1)
    gravity_pub = rospy.Publisher('/calibration/gravity', Marker, queue_size=1)
    def imu_cb(msg):
        a = msg.linear_acceleration; w = msg.angular_velocity
        stamp = msg.header.stamp.to_sec()
        with lock:
            samples.append((stamp, [a.x,a.y,a.z], [w.x,w.y,w.z],msg.header.frame_id))
    def cloud_cb(msg):
        seen[0] += 1
        if seen[0] % 3: return
        if isinstance(msg, PointCloud2):
            pts = np.array(list(point_cloud2.read_points(msg,field_names=('x','y','z'),skip_nans=True)))
        else:
            pts = np.array([[q.x,q.y,q.z] for q in msg.points])
        if pts.size == 0: return
        pts = pts.reshape(-1,3)[::max(1,len(pts)//5000)]
        frame[0] = msg.header.frame_id
        cloud_pub.publish(point_cloud2.create_cloud_xyz32(msg.header,pts.tolist()))
        with lock:
            clouds.append(pts)
            del clouds[:-8]
            mean = np.mean([s[1] for s in samples[-200:]],axis=0) if samples else None
        if mean is not None and np.linalg.norm(mean)>0:
            marker=Marker(); marker.header=msg.header; marker.ns='gravity'; marker.id=0
            marker.type=Marker.ARROW; marker.action=Marker.ADD; marker.pose.orientation.w=1
            marker.scale.x=.025; marker.scale.y=.06; marker.scale.z=.08
            marker.color.g=1.; marker.color.a=1.
            up=mean/np.linalg.norm(mean)
            marker.points=[Point(0,0,0),Point(*up.tolist())]
            gravity_pub.publish(marker)
    imu_sub = rospy.Subscriber(args.imu,Imu,imu_cb,queue_size=2000)
    cls=roslib.message.get_message_class(args.cloud_type)
    if cls is None: raise RuntimeError('Message type unavailable; source driver workspace: '+args.cloud_type)
    rospy.Subscriber(args.cloud,cls,cloud_cb,queue_size=2)
    start=time.monotonic(); completed=False
    rospy.logwarn('Keep sensor stationary. Do not walk. No robot control is connected.')
    while not rospy.is_shutdown() and time.monotonic()-start<args.timeout:
        with lock:
            completed=len(samples)>100 and samples[-1][0]-samples[0][0]>=args.seconds
        if completed: break
        time.sleep(.1)
    imu_sub.unregister()
    with lock: captured=list(samples); points=np.vstack(clouds) if clouds else None
    report={'schema':1,'complete_window':completed,'imu_topic':args.imu,'cloud_topic':args.cloud,
            'cloud_frame':frame[0],'raw_lidar_coordinates_required':True,
            'mounting_transform_written':False,'runtime_bias_written':False}
    try:
        if not completed: raise ValueError('No complete IMU window before timeout; check topics, ROS clock and networking')
        report.update(analyze([s[0] for s in captured],[s[1] for s in captured],[s[2] for s in captured],args.body_level))
        report['imu_frames']=sorted(set(s[3] for s in captured))
        report['floor']=ground_plane(points,report['mean_acceleration_m_s2']) if points is not None else {'valid':False,'reason':'No raw cloud received'}
        if len(report['imu_frames'])!=1: report['warnings'].append('IMU frame changed during capture')
    except ValueError as exc: report.update(calibration_complete=False,error=str(exc))
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report,indent=2,allow_nan=False))
    if 'error' in report: raise SystemExit(2)
    if args.keep_view:
        rospy.spin()


if __name__=='__main__': main()
