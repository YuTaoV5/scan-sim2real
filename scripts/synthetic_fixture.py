#!/usr/bin/env python3
"""Synthetic stationary sensor (12 deg pitch). No real sensor/robot topics."""
import math
import numpy as np


def main():
    import rospy
    from sensor_msgs.msg import Imu, PointCloud2
    from sensor_msgs.point_cloud2 import create_cloud_xyz32
    from std_msgs.msg import Header
    rospy.init_node('SYNTHETIC_mid360_fixture')
    if rospy.get_param('/use_sim_time',False):
        raise RuntimeError('Fixture uses wall time; use a separate master with use_sim_time=false')
    imu_pub=rospy.Publisher('/fixture/imu',Imu,queue_size=20)
    cloud_pub=rospy.Publisher('/fixture/cloud',PointCloud2,queue_size=1)
    pitch=math.radians(12);c,s=math.cos(pitch),math.sin(pitch)
    r=np.array([[c,0,s],[0,1,0],[-s,0,c]])
    x,y=np.meshgrid(np.linspace(-3,3,70),np.linspace(-3,3,70))
    world=np.column_stack([x.ravel(),y.ravel(),np.full(x.size,-.5)])
    points=(world@r).tolist();acc=r.T@np.array([0.,0.,9.81])
    rospy.logwarn('SYNTHETIC fixture, 12 degree pitch, no actual installation measurement')
    rate=rospy.Rate(200);tick=0
    while not rospy.is_shutdown():
        h=Header(stamp=rospy.Time.now(),frame_id='fixture_lidar')
        m=Imu();m.header=h;m.orientation_covariance[0]=-1
        m.linear_acceleration.x,m.linear_acceleration.y,m.linear_acceleration.z=acc
        m.angular_velocity.x=.002;m.angular_velocity.y=-.003;m.angular_velocity.z=.001
        imu_pub.publish(m)
        if tick%20==0:cloud_pub.publish(create_cloud_xyz32(h,points))
        tick+=1;rate.sleep()


if __name__=='__main__':main()
