#!/usr/bin/env bash
set -euo pipefail
command -v docker >/dev/null || { echo 'Install standard Docker on the new host first; see docs/01-new-server.md'; exit 2; }
docker info >/dev/null || { echo 'Docker daemon unavailable. Do not modify host device permissions to bypass this.'; exit 2; }
uname -m
docker version --format '{{.Server.Version}}'
docker info --format 'storage={{.Driver}} cgroup={{.CgroupDriver}} root={{.DockerRootDir}}'
df -h .
docker run --rm --network=host ros:noetic-ros-base-focal rosversion -d
echo 'Preflight completed: ROS base container can execute. RViz and navigation build are separate checks.'
