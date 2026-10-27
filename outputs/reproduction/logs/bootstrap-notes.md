# 环境准备记录

此文件是准备阶段的审计说明，不冒充逐字控制台日志。编译、样例执行及验证的逐字 stdout/stderr、命令、退出码和耗时均在 runs 时间戳目录。

1. `wsl --list --verbose`：沙箱普通调用被拒绝；经工具正常权限审核后可列出 Ubuntu、Ubuntu-22.04、kali-linux（WSL2）。Ubuntu 默认发行版启动遇到其 ext4.vhdx 的 E_ACCESSDENIED；没有尝试修复权限或绕过，选择本来即可启动的 Ubuntu-22.04。
2. Ubuntu-22.04 的 `command -v git java javac ant` 只发现 git。Linux、磁盘和后续项目版本实测输出见 environment 日志。
3. `git clone https://github.com/qixin5/DiffTGen.git work/DiffTGen` 首次沙箱网络失败，原始输出在 clone.log；通过工具的正常网络权限审核后原路径克隆成功，退出码 0。没有覆盖已有 checkout，首轮失败没有留下仓库。
4. 官方 JDK URL：`https://cdn.azul.com/zulu/bin/zulu8.94.0.17-ca-jdk8.0.492-linux_x64.tar.gz`。第一次 180 秒传输超时，收到 84192293/107255476 字节；断点续传被服务器以不支持 Range 拒绝（jdk-resume.log）。重新传到 jdk8-complete.tar.gz，600 秒上限内完成（jdk-download.log），随后 tar 成功解压。没有绕过内容或访问限制。
5. 尝试官方同名 `.sha256` 地址返回 404，见 jdk-checksum-download.log；没有获得官方校验值。记录了下载文件自身 SHA256，但它仅用于本地追踪，不声称是官方校验通过。
6. Maven Central 下载：`org/apache/ant/ant/1.10.15/ant-1.10.15.jar`、`ant-launcher/1.10.15/ant-launcher-1.10.15.jar`、`ant-junit/1.10.15/ant-junit-1.10.15.jar`；`commons-lang/commons-lang/2.3/commons-lang-2.3.jar` 和 sources.jar。主机均为 `https://repo.maven.apache.org/maven2/`。均仅落在 work/deps。

实际依赖未经过 apt、sudo 安装，不修改 WSL 或 Windows 的系统全局 Java 配置。没有调用 Docker、删除旧目录或改动 PatchEval。
