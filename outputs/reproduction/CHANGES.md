# 对作者仓库的改动

- 未修改任何 `src/**/*.java`、`build.xml`、`tclassrunner.xml` 或 EvoSuite jar。
- 唯一手动配置是 `run` 的 `proj_dir`，改为本项目绝对 Linux 路径。配置由驱动脚本写入；`author-changes.patch` 保存差异。
- Git for Windows checkout 的文本换行为 CRLF；脚本写入 `run` 时使用 LF，供 Linux shell 正常解析。
- `ant compile` 按作者构建步骤生成 `build/`，并重建 `lib/myprinter.jar`。这是原版构建产物，不是兼容性逻辑补丁。
- `InstrumentReference.java` 在仓库之外，仅调用作者原有 API 为正确参考版生成测试插桩，供独立 JUnit 验证。不改变正确版输入源码或预期值。
- `driver.py`、本地 Ant 启动脚本及样例组装代码在仓库之外，不替代作者测试生成实现。

完整状态见 `author-status.txt`；版本固定见 `author-commit.txt`。本轮没有兼容性源代码修复。

续轮新增的脚本只负责配置核查、种子 JVM 属性、独立输出目录及回放记录。没有修改作者 src、build.xml、tclassrunner.xml 或候选/参考实现。为实际记录种子，设置 EvoSuite 原有 random_seed 和 output_variables 属性；这不改变差分判定规则。初次验证发现通配 classpath 使用内附 JUnit 4.12，后续 replay_all 显式优先作者 junit-4.11.jar 核对，搜索工具代码保持相同。
