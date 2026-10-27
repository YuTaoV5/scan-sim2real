# 点云 bag/PCD 是否需要按安装倾角转换

**原始 bag 保留原样。已由 LIO 重力对齐、去畸变和配准的世界系地图，通常不需要再旋转安装倾角。** 是否变换由坐标系决定，和扩展名 bag/pcd 无关。

| 数据 | 通常坐标 | 应怎么做 |
|---|---|---|
| 原始 Livox CustomMsg bag | 每帧 L 雷达系，带逐点时间 | 保留原样；由 LIO 使用内置 IMU 去畸变/建图 |
| 原始雷达系单帧 PCD | L | 要表达在 B 时应用 T_B_L，要表达在 W 时用该帧 T_W_L |
| LIO 注册点云话题的 bag | 可能已经是 W | 先核对发布代码及 frame，不再按原始雷达处理 |
| LIO 正确导出的全局 PCD | W，通常重力对齐 | 不再补安装倾角；需要其他地图系时应用有定义的 T_M_W |
| 错误建图产生的 PCD | 可能倾斜/重影/畸变 | 先排查原因；刚性旋转无法修复错误去畸变与位姿估计 |

本项目使用 MID360 内置 IMU：LIO 根据重力建立 W，即使传感器倾斜，正确 W 系地图的水平地面仍应水平。安装外参用于正确计算机身位姿：

```
T_W_L = T_W_I * T_I_L
T_W_B = T_W_I * T_I_L * T_L_B
T_L_B = inverse(T_B_L)
```

仅 T_B_L 不准确时，LIO 内部 IMU 系地图可能仍正确，而 Go2 机身姿态/位置错误；应更新机身输出后核验地图和路线。若 T_I_L、时间戳或逐点时间错误，应重跑原始 bag。

## 确定已有地图是否应变换

1. 查生成 PCD 的程序与配置，不能只看文件名。PCD 可能没有可靠的坐标系语义。
2. 在 RViz 看静止地面法向是否与世界 z 一致、同一墙面旋转后是否重影、已知距离尺度是否正确。
3. 如果是一个正确地图需要转换到另一个坐标约定，对所有地图点、机器人位姿、目标、路线应用同一 T_M_W。修改 frame_id 字符串不等于变换坐标。
4. 如果只有整体坐标系朝向未对齐，可以估刚性变换；如果地图内部变形，修参数重建。

禁止把猜测的 7°同时加到驱动、LIO 外参、SCAN 硬编码矩阵和导出的 PCD 上。每一个坐标变换只应用一次。

## bag → 地图 PCD

录制 `/livox/lidar` CustomMsg、`/livox/imu` 与必要元数据。不要先把每帧转成 XYZ-only PCD 再交给 LIO，逐点时间与 tag 等信息可能丢失。

```bash
source /work/scripts/ros_env.sh
rosparam set /use_sim_time true
# 先 --pause，其他终端启动中继、LIO、适配器；确认它们等待时钟，再按空格。
rosbag play --clock --pause /work/data/site.bag --topics /livox/lidar /livox/imu
```

LIO 配置 `pcd_save.global_map_save_enable=true`，正常退出后等待保存完成。在 sources/lio/PCD/ 查找实际输出（以 pinned save.cpp 和运行日志为准），不要 kill -9 导致丢图。保存 PCD、原始 bag、标定 JSON、运行参数、轨迹、源码提交与 SHA256。

```
原始 bag → LIO 去畸变/配准/建图 → 世界系全局 PCD
```

`bag_to_pcd` 逐帧导出不能替代这一步。在线 SCAN 直接使用真实里程计和注册点云，不要求先有 PCD。PCD 主要用于保存地图、复定位、离线仿真；它本身不含任务路线或地形可通行性。

Elevator-LIO 的简单重定位需靠近原始采集起点和相近朝向，不应当成任意地点的全局重定位。多楼层地图还需统一原点/楼层配准，详见文档 06。
