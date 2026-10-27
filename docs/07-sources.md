# 来源与版本

具体提交和模型 SHA256 在 [locks/sources.json](../locks/sources.json)，fetch_sources.py 以此为准。此表提供用途和限制。

| 来源 | 用途 | 注意 |
|---|---|---|
| [SCAN-Planner](https://github.com/wuyi2121/SCAN-Planner) | ROS1 局部规划、模式 1/2/3 | 固定 ROS1 提交，不混社区 ROS2 配置 |
| [Elevator-LIO](https://github.com/xiaofan4122/Elevator-LIO) | MID360 定位/建图 | 固定版本注册云在 W；默认安装位置是示例 |
| [Livox SDK2](https://github.com/Livox-SDK/Livox-SDK2)、[driver2](https://github.com/Livox-SDK/livox_ros_driver2) | MID360 原始数据与 IMU | 用 ROS1 CustomMsg；不预应用未知安装角 |
| [MID360 官方手册](https://www.livoxtech.com/mid-360/downloads) | 坐标、内部 IMU 位置、FOV | 参考厂商坐标原点；FOV 下界 -7°不等于实际安装角 |
| [Rob2Nav](https://github.com/YuTaoV5/Rob2Nav) | 用户 MoE 运行时/模型和历史 Noetic 适配 | 取固定提交；旧 SportClient 部署不是 MoE 接线 |
| [RoboGauge](https://github.com/wty-yy/RoboGauge) | 预训练 MoE 来源 | 采用 Rob2Nav 内固定的 137k 权重，核 SHA |
| [Unitree SDK2 Python](https://github.com/unitreerobotics/unitree_sdk2_python) | 机载 MoE 的 DDS/LowCmd | 不要求规划器 ROS2；实际网卡和控制权待现场验证 |
| [LI-Init](https://github.com/hku-mars/LiDAR_IMU_Init) | 动态雷达/IMU 外参、时差、初始化 | 可选参考，不直接提供机身安装外参；需核对 driver 消息兼容 |
| [Elevation Mapping CuPy](https://github.com/leggedrobotics/elevation_mapping_cupy) | 局部高度、坡度、可通行性辅助 | 可选参考；不是自动接上 SCAN 的现成多楼层系统 |
| [TravExplorer](https://github.com/wuyi2121/TravExplorer) | 跨层拓扑/三维可通行性架构 | 2026-10-27 读取的 README 仍写代码待发布，后续需重新核实 |
| [Docker 官方安装](https://docs.docker.com/engine/install/ubuntu/)、[ROS 镜像](https://hub.docker.com/_/ros) | 正常新主机的 Noetic 容器 | Noetic apt 与镜像可用性需在新机器验证 |

本仓库不镜像第三方论文/PDF全文和完整源码。sources/ 是 fetch 得到的本地缓存，保留上游 LICENSE。references/rob2nav/ 保存可再分发的 MIT 来源材料，原相对链接已指向固定提交；历史内容与本仓库当前方案冲突时以本仓库当前主线为准。
