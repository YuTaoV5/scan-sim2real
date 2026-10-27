#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/noetic/setup.bash
test -f /work/sources/lio/src/main.cpp
test -f /work/sources/scan/src/planner/plan_manage/package.xml
if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then rosdep init; fi
rosdep update --include-eol-distros
rosdep install --from-paths /work/sources/lio /work/sources/scan/src \
  --ignore-src --rosdistro noetic -y --skip-keys nlohmann-json-dev
cmake -S /work/sources/livox_sdk -B /work/workspaces/livox-sdk-build -DCMAKE_BUILD_TYPE=Release
cmake --build /work/workspaces/livox-sdk-build -j2
cmake --install /work/workspaces/livox-sdk-build
ldconfig
mkdir -p /work/workspaces/livox/src /work/workspaces/lio/src
if [ ! -e /work/workspaces/livox/src/livox_ros_driver2 ]; then cp -a /work/sources/livox_driver /work/workspaces/livox/src/livox_ros_driver2; fi
if [ -L /work/workspaces/livox/src/livox_ros_driver2 ]; then echo 'Use a real driver workspace copy, not a source symlink.' >&2; exit 2; fi
cd /work/workspaces/livox/src/livox_ros_driver2
# Equivalent ROS1 package selection/build flags from upstream build.sh, without
# its recursive workspace cleanup or unbounded parallel build.
cp package_ROS1.xml package.xml
cd /work/workspaces/livox
catkin_make -j2 -DROS_EDITION=ROS1 -DCMAKE_BUILD_TYPE=Release
source /work/workspaces/livox/devel/setup.bash
if [ ! -e /work/workspaces/lio/src/Elevator-LIO ]; then ln -s /work/sources/lio /work/workspaces/lio/src/Elevator-LIO; fi
cd /work/workspaces/lio
catkin_make -j2 -DCMAKE_BUILD_TYPE=Release
source devel/setup.bash
cd /work/sources/scan
catkin_make -j2 -DUSE_GPU=OFF -DCMAKE_BUILD_TYPE=Release
source devel/setup.bash
rospack find scan_planner
rospack find lio
DRIVER_MD5=$(rosmsg md5 livox_ros_driver2/CustomMsg)
LIO_MD5=$(rosmsg md5 lio/CustomMsg)
[ "$DRIVER_MD5" = "$LIO_MD5" ] || { echo 'CustomMsg MD5 mismatch; inspect pinned schemas before relay.'; exit 2; }
echo 'Build completed. No sensor or robot controller started.'
