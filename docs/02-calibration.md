# MID360 IMU 初始化检查与安装外参

## 三类参数独立

T_A_B 把 B 中的点变到 A：p_A=R_A_B p_B+t_A_B。I 为 MID360 内置 IMU，L 为原始雷达，B 为 Go2 机身参考原点，W 为 LIO 世界系。

MID360 手册说明 IMU 轴方向与雷达轴相同，IMU 在雷达系的位置是 [0.011,0.02329,-0.04412] m。因此名义内部参数 T_I_L 的旋转为单位阵、平移为 [-0.011,-0.02329,0.04412] m。这是厂家几何初值，需验证驱动没有额外旋转/缩放。

整体安装倾斜改变 T_B_L，不改变传感器内部 T_I_L。安装角度未知，不能把之前估计的 7°填入配置。机身原点按实际模型/控制器定义，不能随意改成雷达中心或 base_footprint。

IMU 零偏、噪声与时间误差也不等同安装外参。LIO 自身有静止初始化，不应在驱动减一次 bias 后又在 LIO 重复减。

## 采集真实数据

在机载干净 Noetic 环境启动 master 与唯一 Livox 驱动，保持驱动 extrinsic_parameter 为零（原始雷达坐标），使用 CustomMsg 而不是丢失逐点时间的简化点云。

```bash
roslaunch livox_ros_driver2 msg_MID360.launch
rostopic hz /livox/imu
rostopic hz /livox/lidar
rosbag record -O static_01.bag /livox/imu /livox/lidar /tf /tf_static
```

每个采集动作单独记录：机身姿态、是否水平、安装照片、传感器固件、日期、温度、驱动版本。先静止 20–60 s，再录单独的慢速旋转/移动段。不要把运动段拿去估静止 bias。

上传 bag 到 data/，不要提交 GitHub。用 sha256sum 记录数据哈希。驱动数据单位按 ROS SI：角速度 rad/s，加速度 m/s²；看到约 1 的重力幅值时先查驱动，不静默乘 9.81。

## 静止检测

```bash
source /work/scripts/ros_env.sh
python3 /work/scripts/calibration_check.py --seconds 20 \
  --output /work/data/static_01.json --keep-view
```

默认订阅 /livox/imu 与 livox_ros_driver2/CustomMsg 的 /livox/lidar。若输入实际是雷达系 PointCloud2，显式指定 `--cloud-type sensor_msgs/PointCloud2 --cloud 真实话题`。不能输入已经变成世界系的 /LIO/clouds_lidar。

输出包括时间戳单调性、采样频率/间隙、加速度幅值、静止窗口、陀螺均值/标准差、相对重力的 roll/pitch、地面候选平面及其重力一致性。阈值是工程初筛，标准差不是噪声密度或随机游走；要估后者需长时间静态数据与 Allan 方差等分析。

只有独立确认机身坐标轴调平后才能加 `--body-level`，此时 roll/pitch 仍只是安装候选。单次静止无法求安装偏航和平移，也无法区分全部加速度偏置与重力，不会写入 T_base_lidar 或自动宣布标定完成。匀速绕重力方向旋转可能骗过仅 IMU 的静止阈值，采集者必须确保物理静止并结合点云观察。

平面拟合假设原始 IMU/雷达轴一致，寻找传感器下方近水平大平面。桌面、平台也可能被选中；平面距离不等于机身到雷达平移。必须在 RViz 检查。

## 六面加速度计候选

安全拆下刚性传感器组件后，用 +/-X、+/-Y、+/-Z 朝上的六个静止姿态各采一次（不要翻倒上电的机器人）。每次报告必须通过静止检查：

```bash
python3 /work/scripts/accel_six_pose.py /work/data/pose_*.json \
  --output /work/data/accel_candidate.json
```

拟合 a_corrected=scale*(a_raw-bias)，输出三轴偏置和一个整体比例系数；不拟合轴不正交、逐轴比例或安装外参。用额外姿态验证残差，再决定由哪个模块负责补偿。对正常 MID360 内置 IMU，可以先检查厂家数据和 LIO 初始化，不必先假设硬件失准。

## 完整安装外参

1. 明确 Go2 B 系前/左/上、原点和站立参考高度。
2. 测量安装座、雷达坐标原点相对 B 的 xyz，使用厂家 CAD/尺寸图，不能量壳体边缘代替原点。
3. 用水平机身、重力、已知地面/墙面检查 roll/pitch；用机身前向基准和环境方向检查 yaw。单地面不足以确定 yaw 和平移。
4. 如使用外部同步机身位姿，可做有充分转动激励的手眼校准；需说明时间同步、参考位姿误差与可观测性。
5. 对 T_I_L/时间同步有疑问时，用 LI-Init 做动态验证；它解决雷达与 IMU 关系，不能自动替代雷达与机身标定。

将候选写到 configs/calibration.template.json 的本地副本 `data/calibration.json`。检查旋转正交、det=+1、单位米、方向无反，再设 reviewed=true。这不是本仓库替你实测的认证。保持原始 bag 与每版配置，后续 LIO/SCAN 更新见文档 04。
