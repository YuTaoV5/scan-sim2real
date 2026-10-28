# 完整修改点清单：Go2 EDU原厂MID360安装接入SCAN

本文补充 [11 安装差异审计](11-mid360-mounting.md)，覆盖当前锁定版本中从驱动、LIO、位姿/点云适配、SCAN建图/碰撞，到CPU/GPU仿真、路线和控制接入的安装相关修改点。**不是声称所有补丁已实现，更不包含实机验收通过。** 原厂支架的实际六自由度仍未知；照片、产品名、先前估计的7°都不能替代测量。

交付包括：

- [34项机器可读清单](../configs/mounting-change-checklist.json)：逐项动作、适用范围、实施状态、验收方法与源码定位符。
- [本轮源码定位报告](../evidence/mounting-source-audit.json)：23个文件的SHA256、原始Git blob身份和每个定位符的行号。外部源码来自官方GitHub API的固定提交，独立重算Git blob SHA1核对；本仓库文件记录工作树字节摘要。换行形式可能影响本仓库工作树摘要，不能据此误判物理标定。
- [只读复核脚本](../scripts/audit_mounting.py)：在新服务器核对固定checkout、tracked源文件是否修改和定位符是否存在，不写外参、不改驱动、不连接ROS或SDK。

统计：10项已有适配、7项现场必须填写/验收、9项需现场审查、7项仿真代码补丁、1项可选的直接body pose接线补丁。上述34项不是34项都必须改C++；实机推荐链可以绕过原厂安装不匹配的仿真模型。

## 推荐实机链路及责任

`MID360原始CustomMsg/内置IMU → livox_relay → Elevator-LIO → pose_adapter → SCAN → 速度预览/统一运行时`

| 本地输入 | 实际写入/消费位置 | 当前状态 |
|---|---|---|
| data/calibration.json:T_base_lidar | prepare求逆→sources/lio/yaml/sensors/rob2nav.yaml的lidar_R_body/lidar_t_body | 计算已实现，物理值待测 |
| T_imu_lidar | 同文件imu_R_lidar/imu_t_lidar；pose_adapter计算雷达位姿 | 内部名义值保留，坐标核对待现场 |
| initial_base_height_m | 适配器统一世界z平移；generated launch中body_height | 待测机身参考原点离地高度 |
| LIO的mapping.yaml过滤策略 | prepare复制→yaml/runtime/rob2nav.yaml | 当前不自动按新支架改盲区/体素，必须现场审查 |
| SCAN碰撞包络 | advanced_param.xml及generated launch中明确的参数覆盖 | 当前保留上游默认值，需按实际包络审查 |
| 真实地图及地点图 | 地图hash、T_navigation_map、frame与三维拓扑边 | 无私有实机数据，不生成假地图 |

注意：实际运行读取root_rob2nav.yaml引用的rob2nav配置，不是仅凭文件名读取原livox.yaml。驱动实际运行副本通常在workspaces/livox/src/livox_ros_driver2；只改sources中的副本未必生效。prepare重跑会重新生成指定配置，应先归档site参数与git diff，再生成。生成器目前没有自动导入任意“标准安装”模板，也不自动改变近场/碰撞包络。

## 逐项修改点

源码链接固定到 locks/sources.json 的提交；本仓库位置链接指向当前交付文件。每项状态指实施范围，不是实机通过状态。

### A 驱动、LIO与真实坐标链

**M01 机身与雷达原点/六自由度** — 现场必须填写/验收。

位置：[bundle/configs/calibration.template.json](../configs/calibration.template.json)。定义与MoE一致的B，填写实测T_base_lidar；不得按照片或标准产品名推算数值。

验收：原厂坐标基准、尺寸记录、旋转正交和独立地面/墙面检查。

**M02 安装矩阵求逆** — 已有适配；现场未验收。

位置：[bundle/scripts/prepare.py](../scripts/prepare.py)。prepare.py把T_B_L求逆写入lidar_R_body/lidar_t_body，覆盖LIO默认90度偏航和旧平移。

验收：带非零偏航/倾角/杆臂的矩阵逆与合成世界位姿回归。

**M03 MID360内部IMU外参** — 现场审查后决定修改。

位置：[lio/yaml/sensors/livox.yaml](https://github.com/xiaofan4122/Elevator-LIO/blob/1d79af77f3d9747ea57ef52a9b01d326a8ec561a/yaml/sensors/livox.yaml#L5)。整机换支架不修改T_I_L；确认使用内置IMU且驱动未预旋转。

验收：按原始IMU/点云轴和厂家坐标定义审阅。

**M04 驱动网络与唯一数据流** — 现场必须填写/验收。

位置：[livox_driver/config/MID360_config.json](https://github.com/Livox-SDK/livox_ros_driver2/blob/21445540f0d100dc86a7e6df312dd70bbdb4afdf/config/MID360_config.json#L13)。现场填写host_net_info和lidar_configs.ip；停用会重复占雷达的原厂驱动。

验收：抓包/话题来源、雷达IMU时间戳与频率，不改SSH/SDK网卡。

**M05 驱动不预变换原始点云** — 现场审查后决定修改。

位置：[livox_driver/config/MID360_config.json](https://github.com/Livox-SDK/livox_ros_driver2/blob/21445540f0d100dc86a7e6df312dd70bbdb4afdf/config/MID360_config.json#L31)。extrinsic_parameter保持identity，安装变换由LIO/适配器负责。

验收：原始bag保存原坐标、确认没有第二处同角度补偿。

**M06 CustomMsg类型适配** — 已有适配；现场未验收。

位置：[bundle/scripts/livox_relay.py](../scripts/livox_relay.py)。driver2消息中继到lio/CustomMsg，保留逐点offset_time/tag/line。

验收：消息MD5、点数和时间保留；不换成丢失逐点时间的简化点云。

**M07 近场球形盲区** — 现场审查后决定修改。

位置：[lio/yaml/runtime/mapping.yaml](https://github.com/xiaofan4122/Elevator-LIO/blob/1d79af77f3d9747ea57ef52a9b01d326a8ec561a/yaml/runtime/mapping.yaml#L3)。复核mapping.yaml中blind=0.8，依据原始点云选择阈值。

验收：比较处理前后0.3m踏面/近边缘；不直接按物理0.1m极限设软件阈值。

**M08 自身遮挡盒坐标与运动包络** — 现场必须填写/验收。

位置：[lio/yaml/runtime/mapping.yaml](https://github.com/xiaofan4122/Elevator-LIO/blob/1d79af77f3d9747ea57ef52a9b01d326a8ec561a/yaml/runtime/mapping.yaml#L4)。按实际T_B_L把机身/支架包络转到L系，拟合保守box_corner；启用盒子路径会替代球形blind。

验收：检查站立及运动数据，不误删脚前/腹下可通行踏面。

**M09 降采样保真** — 现场审查后决定修改。

位置：[lio/yaml/runtime/mapping.yaml](https://github.com/xiaofan4122/Elevator-LIO/blob/1d79af77f3d9747ea57ef52a9b01d326a8ec561a/yaml/runtime/mapping.yaml#L16)。复核filter_size、point_filter_num、自适应target_points/min_voxel/max_voxel，避免粗体素吞掉16cm台阶。

验收：对比原始/保留点云与台阶立面和边缘，记录负载下实际体素。

**M10 真实机身位姿链** — 已有适配；现场未验收。

位置：[lio/src/node/publish.cpp](https://github.com/xiaofan4122/Elevator-LIO/blob/1d79af77f3d9747ea57ef52a9b01d326a8ec561a/src/node/publish.cpp#L95)。确认T_W_B=T_W_I*T_I_L*T_L_B，不能把MID360 IMU pose当机身pose。

验收：原地转身检查机身原点和墙面；机身朝向/速度方向与MoE一致。

**M11 LIO世界系点云** — 已有适配；现场未验收。

位置：[lio/src/node/publish.cpp](https://github.com/xiaofan4122/Elevator-LIO/blob/1d79af77f3d9747ea57ef52a9b01d326a8ec561a/src/node/publish.cpp#L128)。锁定LIO已调用transLidar2World；不要依赖clouds_lidar这个话题名称猜frame。

验收：确认原始点和世界点不混用，位姿运动时静态墙保持静止。

**M12 独立雷达位姿** — 已有适配；现场未验收。

位置：[bundle/scripts/pose_adapter.py](../scripts/pose_adapter.py)。pose_adapter从T_W_I*T_I_L得到雷达原点，不能用body点代替光线原点。

验收：非零杆臂时平移和姿态均正确；机身/雷达/云共用世界原点。

**M13 SCAN实机输入重映射** — 已有适配；现场未验收。

位置：[bundle/scripts/prepare.py](../scripts/prepare.py)。使用body_pose/lidar_pose/cloud_world三路适配输出；不接仿真odom。

验收：确认话题类型、frame、时间与来源；运行时启动/重放时钟不混用。

**M14 世界系云开关** — 已有适配；现场未验收。

位置：[scan/src/planner/plan_manage/launch/run.launch](https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/planner/plan_manage/launch/run.launch#L26)。生成cloud_is_world=true，修正原run.launch的false分支。

验收：确认世界系云不再经sensor_r*point+ray_pos二次变换。

**M15 硬编码内部外参绕过** — 已有适配；现场未验收。

位置：[scan/src/planner/plan_env/src/grid_map.cpp](https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/planner/plan_env/src/grid_map.cpp#L57)。雷达pose已是T_W_L时need_extrinsic=false；不把T_B_L塞入T_I_L位置。

验收：rosparam与传入pose语义一致；对比射线起点与LiDAR位置。

**M16 直接body pose接SCAN的可选路线** — 仅直接接body pose时需源码补丁。

位置：[scan/src/planner/plan_env/include/plan_env/grid_map.h](https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/planner/plan_env/include/plan_env/grid_map.h#L91)。只有坚持传body pose才需参数化grid_map.h/cpp完整T_B_L；不自动从TF读取。

验收：矩阵方向/正交/单位校验、重新编译；不得与M12/M15重复施加。

**M17 机身高度与世界原点** — 现场必须填写/验收。

位置：[scan/src/planner/plan_manage/launch/advanced_param.xml](https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/planner/plan_manage/launch/advanced_param.xml#L50)。initial_base_height_m量B离初始水平地面高度；body_height不能填LiDAR离地高度。

验收：地面/机身/雷达共同平移，跨高度路径只加减一次机身参考高度。

### B 碰撞、可视化与真实反馈

**M18 双圆柱碰撞体与检查函数** — 现场审查后决定修改。

位置：[scan/src/planner/plan_env/include/plan_env/grid_map.h](https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/planner/plan_env/include/plan_env/grid_map.h#L367)。按实际支架/狗身运动包络审查radius/offset；头部或背部突出不能仅修外参。

验收：查看真实碰撞包络；必要时扩展几何模型而非只放宽距离阈值。

**M19 垂直碰撞膨胀及显示一致性** — 现场审查后决定修改。

位置：[scan/src/planner/plan_manage/src/scan_replan_fsm.cpp](https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/planner/plan_manage/src/scan_replan_fsm.cpp#L49)。上下膨胀与实际机身/载荷匹配，核对FSM self_inflation Marker与算法。

验收：狭窄通道/横杆/平台处同时检查collision与Marker，不能只改可视化。

**M20 真实模式不发布仿真关节/位姿** — 已有适配；现场未验收。

位置：[scan/src/planner/plan_manage/launch/run.launch](https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/planner/plan_manage/launch/run.launch#L53)。使用generated launch，不启动go2_gait_publisher和go2_kinematic_sim作为反馈。

验收：如需机器人模型显示，从实测关节发布joint_states；不把假步态当物理验证。

**M21 TF和RViz** — 现场必须填写/验收。

位置：[bundle/configs/calibration.rviz](../configs/calibration.rviz)。校准页看livox_frame，导航页看nav_odom；核对唯一TF发布者与父子关系。

验收：原地旋转/平移时云与真实机器人一致；仅显示TF不能修改C++点坐标。

### C 仿真CPU/GPU完整链

**M22 CPU发布的雷达安装变换** — 仿真一致性需补丁；尚未实施。

位置：[scan/src/simulator/local_sensing/src/pointcloud_render_node.cpp](https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/simulator/local_sensing/src/pointcloud_render_node.cpp#L212)。publishLidarPose使用完整T_W_B*T_B_L，不仅叠加pitch且复用body位置。

验收：零/非零xyz与三轴旋转测试，发布位姿与渲染完全相同。

**M23 CPU射线与筛选原点** — 仿真一致性需补丁；尚未实施。

位置：[scan/src/simulator/local_sensing/src/pointcloud_render_node.cpp](https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/simulator/local_sensing/src/pointcloud_render_node.cpp#L1006)。将近邻查询、距离、方位/俯仰裁剪、输出点反变换一起改为真实LiDAR原点/姿态。

验收：非零杆臂时遮挡和墙面命中均正确；不能仅改odom发布。

**M24 CPU非对称垂直视场** — 仿真一致性需补丁；尚未实施。

位置：[scan/src/simulator/local_sensing/src/pointcloud_render_node.cpp](https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/simulator/local_sensing/src/pointcloud_render_node.cpp#L1086)。所有俯仰裁剪、极坐标行号和反投影使用L系elevation_min/max，不只把90改59。

验收：L系-7与52度边界、360度方位和完整roll/pitch/yaw扫描边界。

**M25 GPU节点杆臂与近裁剪** — 仿真一致性需补丁；尚未实施。

位置：[scan/src/simulator/local_sensing/src/opengl_render_node.cpp](https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/simulator/local_sensing/src/opengl_render_node.cpp#L1024)。renderSensedPoints与publishLidarPose共用完整T_B_L；统一min_raylength与传给render的near值。

验收：CPU/GPU同地图同T_B_L对比；解决节点min_raylength与setParameters硬编码0.1差异。

**M26 GPU渲染参数和反投影** — 仿真一致性需补丁；尚未实施。

位置：[scan/src/simulator/local_sensing/include/opengl_sim.hpp](https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/simulator/local_sensing/include/opengl_sim.hpp#L1263)。opengl_sim.hpp的setParameters、uniform、投影行号及点云回读要携带非对称俯仰边界。

验收：图像尺寸/像素中心/高度偏置与CPU同约定，点云回读无额外旋转。

**M27 GPU顶点着色器** — 仿真一致性需补丁；尚未实施。

位置：[scan/src/simulator/local_sensing/include/360camera.vs](https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/simulator/local_sensing/include/360camera.vs#L75)。360camera.vs将关于0对称的俯仰投影改为[min,max]偏置映射，边界丢弃与回读一致。

验收：上下边界、跨正负方位、近远范围和NaN/空图测试。

**M28 GPU片元阶段** — 现场审查后决定修改。

位置：[scan/src/simulator/local_sensing/include/camera.fs](https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/simulator/local_sensing/include/camera.fs#L14)。camera.fs目前只透传颜色，若深度/有效性编码不变无需因换安装另改。

验收：不要仅在片元颜色中修倾角；先检查顶点和回读路径。

**M29 launch参数向CPU/GPU同时传递** — 仿真一致性需补丁；尚未实施。

位置：[scan/src/planner/plan_manage/launch/simulator.xml](https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/planner/plan_manage/launch/simulator.xml#L27)。simulator.xml为两个节点增加同一完整T_B_L、俯仰上下限及近裁剪参数，避免默认45/90/1m。

验收：切use_gpu不改变安装语义；实机模式不启动这些节点。

**M30 URDF与仿真机载遮挡** — 现场审查后决定修改。

位置：[scan/src/simulator/Utils/go2_description/urdf/go2_description.urdf](https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/simulator/Utils/go2_description/urdf/go2_description.urdf#L748)。新增明确mid360_link/joint表示实测安装，不冒用原radar_joint；遮挡需实际几何而非仅可视mesh。

验收：比较模型光线/实机原始云，确认支架和狗身遮挡；不改MoE本体惯量来伪装修外参。

### D 楼梯路线、地图与SDK

**M31 30cm踏面关键航点** — 现场审查后决定修改。

位置：[scan/src/planner/plan_manage/src/scan_replan_fsm.cpp](https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/planner/plan_manage/src/scan_replan_fsm.cpp#L378)。模式3抽稀min_dist=0.5可能删中间点；末点保留不能保护所有中间台阶；逐边桥接与整条路线分开验收。

验收：按当前分段终点/整条路径分别检查，保留楼梯入口、顶部、坡顶/坡底关键点。

**M32 模式3支撑面高度** — 已有适配；现场未验收。

位置：[scan/src/planner/plan_manage/src/scan_replan_fsm.cpp](https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/planner/plan_manage/src/scan_replan_fsm.cpp#L374)。上游path z加body_height；语音桥从机身目标减一次高度后发布。

验收：每层z与机身高度分离；避免重复加高或将雷达高度当机身高度。

**M33 地图与地点版本** — 现场必须填写/验收。

位置：[bundle/scripts/init_voice_map.py](../scripts/init_voice_map.py)。原始bag不预旋转；更新外参后重新建图/校验配准并重新绑定地点图hash。

验收：地图重力对齐、T_navigation_map、frame和初始原点验证。

**M34 机载SDK运行与动作资格** — 现场必须填写/验收。

位置：[bundle/voice_agent/runtime_worker.py](../voice_agent/runtime_worker.py)。只启用已有硬件合格的MoE/技能，保持唯一writer、实时反馈和独立watchdog。

验收：低速平地、停止/失联验收，再按段验收16cm台阶及下坡；无数据不标通过。

## 仿真补丁的统一数学契约（待实施）

若要让仿真体现你的标准安装，而不是只让实机运行，M22–M29必须一起完成。这里列设计契约，不提供未经编译/运行验证的假补丁：

1. CPU、GPU统一消费完整T_B_L，不再把只含俯角的Ry当成全部安装。计算`R_W_L=R_W_B*R_B_L`、`p_W_L=p_W_B+R_W_B*t_B_L`，所有光线距离和邻域查询使用p_W_L。
2. 在真正L坐标计算`p_L=R_W_L.T*(p_W-p_W_L)`，用`atan2(z,hypot(x,y))`求俯仰。MID360采用厂家范围-7°至52°，不将对称vertical_fov=59°误当成等效安装。
3. CPU极坐标矩阵的高度、行索引、视场边界、光线方向和反投影全部使用相同上下界；近远裁剪同样以p_W_L为原点。1800行附近的其他动态/补点分支也要搜索，不能只改一处主循环。
4. GPU节点、opengl_sim.hpp的setParameters/uniform、360camera.vs顶点投影，以及深度图回读反投影共同改动。该版本GPU节点传给render的near硬编码0.1m，而节点min_raylength默认1.0m，两处必须统一定义。只改ROS参数不能保证渲染结果使用该值。
5. GPU图像行数和像素中心约定须与非对称上下界一一对应，改变顶点映射时同步改回读时的v0/俯仰偏置，避免图像看似正确但输出点云偏转。camera.fs当前仅透传颜色，若编码未改通常无需改它。
6. publishLidarPose、可视TF、GPU uniform和实际命中点必须来自同一个T_W_L。URDF不是算法数据来源，原radar_joint不能冒充新增MID360 link。机身/支架可视mesh也不等于光线遮挡已实现。

建议的最小仿真回归集：零安装；仅非零xyz杆臂；独立roll/pitch/yaw及组合；机身转动；静态墙/平地/台阶；上下界恰好内外的射线；360°接缝；近远距离边界；CPU/GPU同输入对照；真实支架遮挡。编译日志和点云误差未提供前，这7项仍标为required_simulation_patch。

## 在新服务器复核

先获取项目已锁定的源码，然后在**尚未修改上游tracked文件**时审计：

```bash
python scripts/fetch_sources.py
python scripts/audit_mounting.py --scan sources/scan --lio sources/lio --livox-driver sources/livox_driver --output generated/mounting-before.json
```

脚本拒绝版本不一致、源文件与锁定Git blob不一致、缺失定位符和目录越界。它不会因为某个符号存在就声称物理配置正确。开始改源码/过滤默认值后，原始身份检查报失败是预期的；应保存before报告、修改diff和独立after测试，不能删除失败项或把修改后的文件冒称原始上游。

原版源码审计通过后，现场按 [02 标定](02-calibration.md) 填写本地data/calibration.json，再按 [04 接线](04-lio-scan.md) 生成配置。当前现场无数据，使用template运行prepare应被拒绝；不要通过给null随便填一个角度来消除拒绝。

## 哪些不需要因换支架而修改

- 同一刚性MID360内部T_I_L不因整机换位置而改变；IMU bias/噪声/时间同步是另一类测量，不能重复在驱动与LIO减bias。
- 使用真实LiDAR且sensor_type=lidar时，不靠深度相机fx/fy/cx/cy或depth_extrinsic修正雷达安装。
- 不旋转原始bag来“补平”；LIO已重力对齐的世界系PCD不再额外旋转。改标定后优先重建/校验地图配准与地点图。
- 不因导航目标变化修改MoE输入归一化、关节映射或动作缩放。物理载荷变化若影响策略，另做部署合同/性能验收，不能伪装成外参修复。

## 范围与缺项

本轮已完成源码对照、定位、hash报告、现场修改清单和回归测试；没有改造或编译CPU/GPU C++渲染器，没有实测原厂安装、ROS消息、RViz渲染或机器人。LAN 5090与Go2由用户部署，不等待其SSH。硬件姿态/平移、遮挡和滤波最终值只能由现场数据补齐，所有动作资格保持原状态。
