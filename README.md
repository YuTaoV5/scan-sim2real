# SCAN sim2real：Go2 EDU + MID360 + Rob2Nav MoE

这是新服务器的独立交接项目：固定源码版本、准备 ROS1/Noetic 与 RViz、检测 MID360 IMU/安装外参、回放建图，并规划接入已有 MoE 的步骤。**目前没有实机 bag、实测外参或实机导航验收；ROS 容器构建与 RViz 显示也仍需在新服务器验证。**

机器人与任务条件：Go2 EDU，机载 ROS1，MID360 **内置 IMU**；安装倾角未知；Rob2Nav 原始 MoE 盲走策略；四个高 0.16 m、深 0.30 m、宽 1.20 m 的台阶，上楼后经斜坡下到平地。斜坡长度与顶部平台尺寸待测。

新 agent 先读 [AGENTS.md](AGENTS.md) 和 [交接状态](docs/00-handoff.md)，再按下表执行，不需要旧服务器或旧聊天。

| 阶段 | 文档 | 完成证据 |
|---|---|---|
| 新服务器与容器 | [01 环境、构建和 RViz](docs/01-new-server.md) | Docker 运行、源码版本、编译日志、实际 RViz 画面 |
| 传感器初始化 | [02 IMU 与安装标定](docs/02-calibration.md) | 原始 bag、静止/六面报告、实测外参 |
| 点云与地图 | [03 bag/PCD 是否按倾角变换](docs/03-bag-pcd.md) | 坐标系、重力对齐、地图与配套标定记录 |
| LIO → SCAN | [04 接线与运行命令](docs/04-lio-scan.md) | 真实机身位姿、世界系点云、SCAN 参数检查 |
| SCAN → MoE | [05 MoE 接口与待完成适配](docs/05-moe.md) | 模型 SHA、观测协议、命令时效与控制权验证 |
| 楼梯与多楼层 | [06 路线与验收](docs/06-missions.md) | 分段地形测试、任务状态与边缘约束 |
| 来源与排错 | [07 来源](docs/07-sources.md)、[08 排错](docs/08-troubleshooting.md) | 固定提交和明确的已知问题 |

无需 ROS 的第一步：

```bash
git clone https://github.com/YuTaoV5/scan-sim2real.git
cd scan-sim2real
export NAV_ROOT="$PWD"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python scripts/verify_bundle.py
python scripts/fetch_sources.py
```

获取 MoE 与其原始运行时（可选，网络和磁盘允许时）：

```bash
python scripts/fetch_sources.py --with-rob2nav --with-unitree-sdk
```

所有源码版本见 [sources.json](locks/sources.json)。默认不会下载大地图或私有 bag，也不会打开 DDS、连接 SDK 或给机器人发命令。脚本不安装 Docker 守护进程、不修改宿主设备节点。ROS 环境操作按文档在新的普通 Docker 主机进行。

**点云倾角的关键结论：原始 bag 保留；LIO 已重力对齐的世界系 PCD 不再补一次安装角。** 雷达转到机身时才应用安装外参；具体判定见文档 03。

`configs/*.template.*` 保留未知值；不能用 7°猜测或合成数据填入实机配置。`references/rob2nav/` 是历史来源，部分内容使用原厂 SportClient，当前 MoE 主线以本仓库文档 04/05 为准。

验证状态以 [evidence/validation.json](evidence/validation.json) 为准。CI 只验证离线代码和资料完整性，不能证明 ROS、RViz 或行走通过。

本仓库代码使用 MIT 许可；上游项目与模型保留原许可，见 [来源说明](THIRD_PARTY_NOTICES.md)。

## 语音与统一导航任务

新增 [09 语音、地图与技能状态机](docs/09-voice-control.md) 和 [10 服务器部署与验收](docs/10-server-acceptance.md)。支持常驻 ASR/TTS、地图地点与别名、三维拓扑路线、ROS1 SCAN 桥及原 Rob2Nav 技能合同。`demo` 使用合成任务反馈；`live` 保留设备资格与唯一控制写入者，现场验证状态见 [语音证据](evidence/voice-validation.json)。

MID360原厂安装与作者头部套件不同的参数对照、仿真45°/90°模型限制及实机更新步骤，见 [11 安装源码审计](docs/11-mid360-mounting.md)。
