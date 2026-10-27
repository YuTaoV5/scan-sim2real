# SCAN 到 Rob2Nav MoE

## 正确控制链

```text
MID360 raw data → LIO → real body/lidar pose + world cloud
→ SCAN local planner → closed_loop_controller → /rob2nav/cmd_vel_raw
→ 带任务/时效/状态检查的 MoE 命令适配（待现场接入）
→ MoE 推理 → 唯一 Unitree SDK LowCmd 控制者
```

旧 Rob2Nav Noetic 手册的 velocity_gate.py 在执行模式调用 SportClient.Move，控制的是原厂运动服务。它并不会驱动 MoE。历史手册仅作来源，不按其中“只替换终端 G”的步骤接入本任务。

## 固定权重与协议

`fetch_sources.py --with-rob2nav --with-unitree-sdk` 获取固定 Rob2Nav 提交及 Unitree SDK Python，并验证模型：

```text
sources/rob2nav/vendor/RoboGauge/resources/models/go2/go2_moe_cts_137k_0.6739.pt
SHA256 2206659a6a23886446dcfc05d86888d6cdc9b8a4e31f44cbbc4e2d17ba3d6ead
```

manifest 来源见 references/rob2nav/walk_moe.json。策略频率 50 Hz，45 维本体观测；历史编码为 5×45，不能只把一次 45 维观测直接传入一个不匹配的网络入口。检查同版本 runtime/policies 和原始模型加载器。

观测拼接（以源码为准）：gyro×0.25、机身系重力、速度命令×[2,2,0.25]、关节位置偏差、dq×0.05、上一动作。动作缩放 0.25；manifest 中 kp=20、kd=0.5 和关节顺序是合约内容，不能直接把策略关节顺序当 SDK 电机编号。已有部署成功经验仍应记录实际模型、默认姿态、history reset、控制频率与 SDK 映射。

检查到的 `rob2nav/deployment/service.py` 从 stdin 读换行 JSON，速度入口为：

```json
{"velocity": [0.1, 0.0, 0.0]}
```

值使用物理单位 m/s、m/s、rad/s，观测缩放在 runtime 内部完成。`{"stop":true}` 是其操作员停止/故障锁存入口。运行时及 profile 有硬件资格检查，仓库 manifest 当前 hardware_qualified=false；不要为了运行而把它直接改 true。用户现有实机 MoE 部署可能是另一个脚本，需要先对应真实入口，不能凭这条 JSON 文档假定已连接。

## 新 agent 需实现/验证的命令适配

当前提供了接线方案与真实源码定位，**没有提交一个声称硬件合格的实时 ROS→MoE 执行器**。下一步应在用户已有 MoE 进程增加入口或由它主动读取 ROS 速度，保留唯一 LowCmd writer。

建议合约包含 task/session ID、序号、接收的 monotonic 时间、当前模式、速度、允许范围；Twist 没有任务 ID 和时间戳，需要接收侧时效检查，不能直接长期保持最后一条速度。用 bounded queue/最新命令替换，不能让遥控输入积压几秒后再执行。

独立验证：

1. 使用记录输入和假的执行器，验证 vx/vy/wz 符号、单位、机身坐标、限幅与加速度限制。
2. 分别停止 SCAN、点云、里程计、命令桥和通讯，确认 MoE 的失效处理；kill/断电时不能依赖 Python finally。
3. 重新启用时清除旧任务/命令，等待新的任务和轨迹；遥控接管优先。
4. 新规划失败或到达时下发符合现有 runtime 的停止状态，不把悬空、故障状态交给规划器自救。
5. 在仿真和现场分别记录唯一控制者、命令时延与停车行为。

不要同时运行 SportClient.Move 与当前 MoE 的 LowCmd 控制。SDK 不依赖 ROS2 规划器，机载导航可保持 ROS1；SDK 的 DDS 通道和 ROS1 TCPROS 是不同网络路径。

## 服务器与机载分工

服务器可进行源码检查、bag 回放、建图与仿真；实际控制循环建议在机载本地运行，避免把公网往返时延放进 50 Hz 推理/电机循环。服务器只提供路线/目标时，也必须由机载处理任务丢失和停止。

已有网页/MuJoCo/PhysX 结果是历史限定场景记录。8 cm 台阶或低台仿真不能证明该 MoE 已通过 16 cm 台阶和下坡连接。当前任务应固定同一 MoE，分别验收楼梯、坡顶、坡面与停车，再接导航。
