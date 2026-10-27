#!/usr/bin/env bash
# Source inside the container or a native Noetic environment.
source /opt/ros/noetic/setup.bash
for SETUP in /work/workspaces/livox/devel/setup.bash /work/workspaces/lio/devel/setup.bash /work/sources/scan/devel/setup.bash; do
  if [ -f "$SETUP" ]; then source "$SETUP"; fi
done
export ROS_MASTER_URI=${ROS_MASTER_URI:-http://127.0.0.1:11321}
export ROS_IP=${ROS_IP:-127.0.0.1}
