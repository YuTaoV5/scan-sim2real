# 新服务器、ROS1、Docker 与 RViz

## 环境选择

机载 ROS1 保持原环境；新服务器使用普通 Linux Docker 主机，容器内 Ubuntu 20.04 + ROS Noetic。主机可以是较新 Ubuntu；不要向主机 Jazzy/Foxy Python 环境混装 Noetic 包。x86_64 服务器编译结果不能复制给 ARM64 Go2；ARM64 需要原生编译及单独验证。

Noetic 是旧发行版，apt 镜像和签名可能变化。Dockerfile 是可执行配方，不是已经打包验证的离线镜像。若 apt key 过期，按官方 ROS 源恢复签名；不要用 trusted=yes、关闭 TLS 或混入 Jammy/Noble deb。将最终可用镜像保存 digest 和 apt 版本清单。

主机建议预留至少 30 GB 空间；存储驱动若只能使用 vfs，需要更多。Docker 安装采用 [官方 Ubuntu 指引](https://docs.docker.com/engine/install/ubuntu/)，本仓库不自动安装 daemon、不启用 privileged、不修改 /dev/net/tun。

## 取得并记录源码

```bash
export NAV_ROOT="$PWD"  # 当前为本仓库根目录
python3 scripts/fetch_sources.py
bash scripts/preflight.sh
```

preflight 拉取并运行 ros:noetic-ros-base-focal。Docker Hub 不通时可在核对来源后使用 Docker 官方库的 ECR 镜像：

```bash
docker pull public.ecr.aws/docker/library/ros:noetic-ros-base-focal
docker tag public.ecr.aws/docker/library/ros:noetic-ros-base-focal ros:noetic-ros-base-focal
bash scripts/preflight.sh
```

旧机器实际拉到的多架构 manifest digest 为 `sha256:72b8bc59035dc0a5b8e07aae28c16caa84192971d72d207c72ed734fb1d5e97d`，作为历史证据，不保证该 tag 未来不变。可通过 Dockerfile 的 ROS_BASE build arg 指定经新机器验证的 digest，并记录在 evidence/。

fetch_sources.py 不会 reset 已存在 checkout；HEAD 不符或有修改就报错。prepare.py 生成 LIO 配置后该源码会变脏，这是预期，要保留实测配置；不要为通过 fetch 检查而 reset 它。

## 构建与容器

```bash
bash scripts/build_image.sh
bash scripts/container.sh start
bash scripts/container.sh shell
```

进入容器后：

```bash
source /work/scripts/ros_env.sh
bash /work/scripts/build_navigation.sh 2>&1 | tee /work/logs/navigation-build.log
source /work/scripts/ros_env.sh
rosversion -d
rospack find scan_planner
rospack find lio
rosmsg md5 livox_ros_driver2/CustomMsg
rosmsg md5 lio/CustomMsg
dpkg-query -W > /work/logs/dpkg-versions.txt
```

两个 MD5 必须一致。Livox 上游 build.sh 会调整包文件、递归清理工作空间并使用默认并行度；本仓库在 workspaces/livox 的独立副本执行等价的 ROS1 package 选择和 `catkin_make -j2 -DROS_EDITION=ROS1`，保留 sources/livox_driver 原始提交。build_navigation.sh 还用 rosdep 补齐固定 package.xml 声明的依赖，已由 Dockerfile 安装的 nlohmann-json3-dev 对应旧 rosdep key 单独跳过。rosdep 下载/解析失败应修复而不是忽略退出码。无传感器情况下先验证编译；不要启动实时雷达驱动。

默认 master 为 http://127.0.0.1:11321，隔离常见的 11311。每个容器终端先 source ros_env.sh。新服务器不需要安装 Unitree SDK 才能运行 LIO/SCAN/RViz；SDK 只在后续 MoE 实机阶段使用。

## RViz 必须实际显示

先在新服务器图形桌面终端获取环境：

```bash
printf '%s\n' "$DISPLAY" "$XAUTHORITY"
bash scripts/start_rviz.sh
docker exec scan-sim2real-noetic bash -c 'source /work/scripts/ros_env.sh; rosnode list'
docker exec scan-sim2real-noetic pgrep -a rviz
tail -80 logs/rviz.log
```

脚本使用新的 DISPLAY 和当前用户 Xauthority，通过本地 X11 socket 显示；不会假定旧服务器 :20，也不执行 xhost +。若容器已在没有 DISPLAY 的终端创建，先停止它并人工核对挂载，再用新的 SCAN_CONTAINER 名称在桌面终端重新创建。

检查 `/rviz` 节点、无 Qt/GLX 错误、桌面窗口可见、点云可渲染，再记录截图/日志。仅有后台 PID 或启动请求成功不算渲染通过。纯 SSH 无桌面时可用正常远程桌面；SSH X forwarding 的授权和 DISPLAY/TCP 路径不同，不能照搬 X11 socket 脚本。也可在现场/客户端运行 RViz，按后文配置可达 ROS 网络。

合成消息烟测：在容器不同终端分别运行：

```bash
source /work/scripts/ros_env.sh
python3 /work/scripts/synthetic_fixture.py
```

```bash
source /work/scripts/ros_env.sh
python3 /work/scripts/calibration_check.py --imu /fixture/imu --cloud /fixture/cloud \
  --cloud-type sensor_msgs/PointCloud2 --seconds 10 --timeout 30 \
  --output /work/data/synthetic-static.json --keep-view
```

RViz Fixed Frame 选 `fixture_lidar`，显示 `/calibration/cloud` 和 `/calibration/gravity`。这是合成平面与 12°合成姿态，仅检查软件消息链，不代表真实角度。

## bag 上传优先；实时网络需另外配置

服务器只开放 SSH 端口时，不能自动接收现场所有 ROS1 TCPROS 连接。推荐机载录 bag、上传 data/ 后离线回放。若做实时 ROS1，机载与服务器必须通过同一可路由局域网/VPN，双方 ROS_IP/ROS_HOSTNAME 可互达，并开放 ROS master 与动态 TCPROS 端口。把默认 127.0.0.1 改为实际地址前先核对拓扑；不把网页/SSH 转发当作 ROS 网络桥。

## Docker 受限时的停止条件

`failed to create default sandbox`、cgroup 只读、TUN 不可用表示云宿主限制。记录日志并换正常 Docker 主机，或在本地 Ubuntu20.04/Noetic 原生构建。保留本仓库作为方案，不通过改设备权限或特权容器绕过平台限制。
