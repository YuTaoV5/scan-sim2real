# 验证证据说明

- `2026-10-27-status.json`、`docker-build.log`、`rootless-daemon.log`：旧云环境停止安装时的状态与错误。日志只归一化换行、去掉行尾空白；保留失败信息，不是新服务器运行记录。
- `validation.json`：本次交接仓库的实际验证范围。离线数值检查、Python 语法、链接检查和 shell 语法不能替代 ROS 编译/渲染或真实硬件测试。
- `offline-tests.txt`：本次 13 项离线数值/配置测试输出；其中参数生成使用临时假源码与 mock HEAD，只验证变换和 launch 契约，不是实际构建。
- `source-access.json`：全部六个固定提交的公开 GitHub 元数据核验；模型用公开 blob SHA1/size 与本地固定提交对象核对，再计算 SHA256。所有身份核验通过，不代表已完整 clone 或构建所有源。

下一轮在新服务器创建独立 evidence 记录，写明日期、主机架构、仓库提交、上游提交、命令、真实/合成数据、日志与验收结果。不要覆盖原失败历史冒充成功。
