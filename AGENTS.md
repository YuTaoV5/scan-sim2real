# Agent 交接约定

开始前按顺序读 `README.md`、`docs/00-handoff.md`、`locks/sources.json` 和当前 `evidence/validation.json`。

- 目标：Go2 EDU、机载 ROS1、MID360 内置 IMU、Rob2Nav 原始 MoE；四个 16 cm 踢面、30 cm 踏面、120 cm 宽楼梯，上楼后下坡。安装角度未知，当前没有实机 bag 或标定值。
- 使用本仓库相对路径，在新服务器设置 NAV_ROOT；不得依赖旧服务器路径、端口、密码、桌面号或旧会话。
- 本仓库复现的是准备流程。ROS 编译、RViz、实际传感器接入和行走目前未验收；不要把数值单测或旧仿真记录写成实机通过。
- 依赖固定到 locks/sources.json 中的提交；不要静默切换 main 或 ROS2 社区分支。改版本时记录原因并重新验证接口。
- 普通 Docker 主机优先；容器安装遇到宿主 cgroup/网络命名空间限制时记录现象，使用其他正常主机。旧环境已拒绝创建并放宽 /dev/net/tun 权限，不得重试该操作或绕过拒绝。
- 安装角不能填成先前猜测的 7°。原始 bag 保留原样；重力对齐后的世界系地图不能再补一次安装角。详见 docs/03-bag-pcd.md。
- T_A_B 把 B 坐标变到 A。MID360 内部外参和机身安装外参独立。未知平移、偏航和坡长保持 null；不要让合成示例变成默认实机参数。
- 所有会向机器人发送命令的接线属于后续实机阶段。默认只做离线检查与速度预览；不得跳过 Rob2Nav 现有硬件资格检查，也不得让 SportClient 与 MoE 同时争夺控制。
- 本轮用户已授权收集、整理并推送此仓库。后续工作遵循后续用户明确范围；不要仅因脚本存在就启动机器人。
- 运行 `python -m unittest discover -s tests -v`、`python scripts/verify_bundle.py`；Linux 下还应运行 `bash -n scripts/*.sh`（建议逐文件），再更新 evidence/validation.json。新增 ROS 验证应记录命令、提交、环境和日志位置。
- 不提交密码、令牌、SSH key、设备凭据、原始私有 bag 或运行时 data/generated。上游源码由 fetch_sources.py 获取，保留各自许可证。

后续执行顺序与未完成工作在 docs/00-handoff.md。不要从历史参考手册复制原厂 SportClient 链路作为当前 MoE 部署。
