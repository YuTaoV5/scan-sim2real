ARG ROS_BASE=ros:noetic-ros-base-focal
FROM ${ROS_BASE}
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-noetic-rviz ros-noetic-tf ros-noetic-tf2-ros ros-noetic-pcl-ros \
    ros-noetic-pcl-conversions ros-noetic-robot-state-publisher ros-noetic-xacro \
    ros-noetic-message-generation ros-noetic-cv-bridge ros-noetic-image-transport \
    ros-noetic-message-filters ros-noetic-std-srvs ros-noetic-roslib \
    python3-numpy python3-yaml python3-scipy python3-catkin-tools python3-rosdep \
    build-essential cmake git ca-certificates curl libeigen3-dev libopencv-dev \
    libyaml-cpp-dev libtbb-dev qtbase5-dev nlohmann-json3-dev libarmadillo-dev \
    libgl1-mesa-dri libgl1-mesa-glx mesa-utils libboost-all-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /work
CMD ["bash"]
