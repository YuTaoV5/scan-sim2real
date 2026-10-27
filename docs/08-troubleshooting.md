# 已知问题与定位顺序

| 现象 | 优先检查 |
|---|---|
| git 指向 127.0.0.1:10809 失败 | 新机器的 git/env 代理是否有效；不要继承旧机器代理或把凭据写配置 |
| Docker Hub 超时 | 核实官方镜像源/代理，保存 digest；不要换不明镜像后声称完全相同 |
| default sandbox / read-only cgroup | 云宿主限制；换正常 Docker 主机，保留方案 |
| rootless 缺 TUN | 平台未提供用户态网络条件；不改设备权限绕过 |
| apt 无 Noetic 或签名过期 | Noetic/Focal 对应的官方签名仓库；不混新 Ubuntu deb |
| RViz Qt 无 display | 新服务器 DISPLAY、X11 socket、当前 Xauthority 与容器创建时环境 |
| RViz GLX/黑窗 | 软件 OpenGL、Mesa、桌面本身 GLX；先 glxinfo，再检查实际画面 |
| 原始云在 RViz 不显示 | CustomMsg 不能直接当 PointCloud2；用 calibration_check 转出 /calibration/cloud；Fixed Frame 用实际 frame |
| 找不到 livox CustomMsg | source driver 的 devel/setup.bash；核对实际 msg 类型和 MD5 |
| IMU 重力幅值约 1 | 驱动单位可能是 g；核实代码，不能静默缩放后仍标原始 |
| 检测超时 | topic、use_sim_time、bag 是否暂停、消息 header stamp、timeout 是否足够 |
| 地面候选不正确 | 原始雷达坐标/遮挡/桌面；不把平面距离当机身外参 |
| /LIO/clouds_lidar 进 SCAN 后地图飞走 | 它实际是 W 系，确认 cloud_is_world=true，避免再旋转平移 |
| TF 看似正确但 SCAN 错 | SCAN 自有外参计算不读取任意 TF；核 need_extrinsic 与实际 sensor_pose |
| 地图水平但狗姿态歪 | 安装 T_B_L 或取逆方向不对，不要旋转世界 PCD 掩盖机身输出错误 |
| 楼梯航点 z 过高 | 模式 3 自动加 body_height，是否重复加高 |
| 0.30 m 踏面路径点消失 | 模式 3 的 0.5 m 抽稀；保留关键点并参数化 |
| 近处台阶缺点 | LIO 默认 blind、机身遮挡、雷达垂直 FOV、去畸变和近场滤除 |
| /rob2nav/body_pose 不发布 | 真实 LIO frame/时间/四元数、初始高度、速度差分区间；不要用指令积分伪造 odom |
| /cmd_vel 有值但 MoE 不响应 | SCAN 输出未连接实际 MoE 输入；SportClient 不会调用 MoE |

## 已知实现局限

- 静止检查不是完整 Allan 噪声标定，六面工具只拟合偏置和整体比例系数。
- pose_adapter 的机身速度来自相邻实际位姿差分，存在噪声且依赖频率/时间戳；真实验收中应检查并评估滤波或更合适的状态估计输出。
- 锁定 SCAN 点云处理使用最近收到的 sensor_pose；运动较快时需检查与 cloud 时间配对和队列延迟，不能只靠消息名字一致。
- 目前没有实现最终 ROS→MoE 执行桥、任务状态仲裁、多楼层全局规划、边缘支撑约束。
- 地形路线的 xyz 高度不控制脚落点；运动学动画不能代替 MoE 物理闭环。

每个失败保存命令和日志，先定位输入坐标/时钟再调规划权重。不要通过反复翻转角度符号、清空障碍或缩小机器人几何来掩盖原因。
