# LIO 到 SCAN：坐标契约和命令

本文命令在本仓库容器中执行，每个终端先 `source /work/scripts/ros_env.sh`。机载原生部署将 /work 替换为仓库实际绝对路径并保持工作空间 overlay 顺序。不要把服务器 x86 二进制复制给 ARM64。

## 接口契约

| 话题/配置 | 锁定版本中的含义 |
|---|---|
| /livox/lidar | driver2 CustomMsg，原始雷达系且有逐点时间 |
| /livox/imu | MID360 内置 IMU |
| /rob2nav/livox_custom | 转为 lio/CustomMsg 的同格式消息，启动前检查 MD5 |
| /LIO/odom_imu | W 中 IMU 位姿 |
| /LIO/odom_vehicle | W 中机身位姿，取决于安装外参 |
| /LIO/clouds_lidar | **实际上是 W 系注册点云**，不可仅按名称判断 |
| /rob2nav/body_pose | 经一致世界高度平移的机身位姿，nav_odom 系 |
| /rob2nav/lidar_pose | 同系中的雷达位姿 |
| /rob2nav/cloud_world | 同系中的点云，仅平移世界原点，不重复旋转 |
| cloud_is_world / need_extrinsic | true / false，使用上面的适配输出时 |
| /rob2nav/cmd_vel_raw | SCAN 跟踪器输出的机身平面 vx、vy、wz，不自动连接 SDK |

source evidence：LIO `src/node/publish.cpp` 的 `publish_Dedistort_clouds_lidar` 调用 transLidar2World 并发布 frame=world；机身位姿用 T_W_I*T_I_L*T_L_B。SCAN `src/planner/plan_env/src/grid_map.cpp` 自己计算点坐标并有硬编码 lidar_extrinsic，不会因为发布了静态 TF 就自动改用该 TF。

适配器将最初实测机身位置的 z 调整到填写的站立高度，再对机身、雷达和世界点云统一加同一个 dz，使地面在初始 nav_odom 附近为 z=0。这是世界原点平移，不是安装倾角补偿。机身初始站在高台、坡面或不水平时不能套用这个初始化假设。

## 真实外参准备

复制 configs/calibration.template.json 到 data/calibration.json，完成测量并审阅后填写 reviewed=true。

```bash
python3 /work/scripts/prepare.py \
  --calibration /work/data/calibration.json \
  --lio /work/sources/lio --scan /work/sources/scan \
  --out /work/generated --navi-mode 1
```

程序先核对两个 upstream HEAD 与固定提交，再校验有限右手刚体矩阵。它会在 sources/lio/yaml 写入 sensors/rob2nav.yaml、runtime/rob2nav.yaml、root_rob2nav.yaml（原始 livox.yaml 保留），并输出 generated/scan_go2edu.launch。重复运行会覆盖这些特定生成文件，先归档每版实测参数。

映射关系：

```text
offset.imu_R_lidar / imu_t_lidar = T_I_L
offset.lidar_R_body / lidar_t_body = inverse(T_B_L)
```

LIO 高度和点云处理依赖正确原始配置。prepare 不自动改近场 blind 或机身滤除区域；默认 0.8 m 盲区可能删掉近处台阶，必须根据装机点云检查后调整，不能单纯照抄。Livox driver 的 extrinsic_parameter 保持 identity，避免预旋转两遍。

## 现场 driver 地址

driver 实际构建副本在 workspaces/livox/src/livox_ros_driver2，编辑其中 config/MID360_config.json，而不是仅编辑 sources 中未被启动的副本。确认主机雷达网卡与雷达 IP：修改 MID360.host_net_info 对应接收地址及 lidar_configs[0].ip，保持 extrinsic_parameter 零。用 Viewer 确认物理设备地址，不根据序列号盲猜；不要改当前 SSH/Go2 控制网卡。只有现场主机可达雷达时才启动 live driver。

## 分终端启动（离线回放优先）

A：`roscore -p 11321`，若 start_rviz.sh 已启动则复用。

B：原始 bag 回放，见文档 03；或现场 `roslaunch livox_ros_driver2 msg_MID360.launch`，两者只选一个。

C：

```bash
python3 /work/scripts/livox_relay.py
```

D：保持机器人初始静止，完成 LIO 初始化。bag 回放时先设 use_sim_time=true，先启动节点再取消暂停：

```bash
rosrun lio lio _config_path:=root_rob2nav.yaml
```

E：

```bash
python3 /work/scripts/pose_adapter.py --calibration /work/data/calibration.json
```

F：

```bash
roslaunch /work/generated/scan_go2edu.launch use_sim_time:=true
```

现场实时数据用 use_sim_time:=false；不能一半用回放时钟、一半用墙钟。bag 倒放/循环时重启 LIO/适配器，避免时间回跳污染状态。

G：RViz Fixed Frame 切到 nav_odom，添加 /rob2nav/cloud_world、/rob2nav/body_pose、TF 和 planning 的 Marker。当前 calibration.rviz 用于原始传感器检查，需要修改对应显示后保存为 data/navigation.rviz。

H：检查：

```bash
rostopic hz /rob2nav/body_pose
rostopic hz /rob2nav/cloud_world
rostopic echo -n 1 /rob2nav/body_pose
rosparam get /scan_planner_node/grid_map/cloud_is_world
rosparam get /scan_planner_node/grid_map/need_extrinsic
rostopic info /rob2nav/cmd_vel_raw
rostopic echo /rob2nav/cmd_vel_raw
```

两个参数分别 true/false；速度只应有一个 SCAN 跟踪器发布者。RViz 2D Nav Goal 可触发模式 1 的规划，但不应启动 SDK。检查地面、机身朝向、前进方向、静止漂移、墙面重影与云/位姿时间；“有话题、有频率”不等于定位正确。

bag 里位姿不会响应新的速度命令。因此 bag 回放只能验证感知与规划输出，不能声称完成新的物理闭环到达。闭环需真实机器人或正确接线的物理仿真。

## 模式 2/3

`--navi-mode 2` 要求 sources/scan/tools/keypoint.yaml 已有实测机身航点。上游 FSM 在运行中自行加载该路径；仅在 launch 加一份任意文件的 rosparam load 可能被覆盖。使用上游 keypoint_recorder.py 时显式 `--odom /rob2nav/body_pose`，并确认输出路径就是 tools/keypoint.yaml、frame 是 nav_odom。

模式 3 从 /initial_path 接收支撑面高度，内部会加 grid_map/body_height，且以 0.5 m 距离抽稀。生成器以实测 initial_base_height_m 设置该 body_height；路线发布与抽稀改动详见文档 06。当前仓库没有实现完整上层路线调度器。
