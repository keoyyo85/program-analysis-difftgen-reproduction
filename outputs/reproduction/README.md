# DiffTGen 最小基线复现

本轮只编译作者工具、运行作者 Lang_51 / Nopol 单样例，未实现课程新增模块。

**最新结果：** 后续 3 次独立 180 秒搜索中，第 2 次自动生成 `Fes` 区分测试；实际三版本回放及显式 JUnit 4.11 验证均确认 bug/fix 通过、Nopol patch 断言失败。首轮保留不变。见 `CONTINUATION.md`、`VALIDATION.md` 和 `continuation-result.csv`。

## 首轮实测结论（保留历史）

后续三轮与配置复核见 `CONTINUATION.md`；此节只描述原始首轮，不代表后续自动检出状态。

运行目录 `runs/20261027-175712`。原版 `ant compile` 成功（退出码 0，9.837 秒）；三版本源码和目标插桩均编译成功；DiffTGen 进程退出码 0，耗时 138.350 秒，执行到 `Found Nothing.`。这是流程完成但未发现区分测试，不能认定 Nopol 补丁正确。

EvoSuite 原始输出显示生成 **120 个测试**、总长度 191、综合覆盖率约 91%。作者按修改位置筛出 `test007`（`toBoolean("off")`）和 `test039`（`toBoolean("X2f")`）；三版本的两个结果全部是 `false`。本次没有生成任何 `DiffTGen0Test/1Test/2Test.java`，没有已验证的区分版本断言。实际命令使用作者的 `-Dassertions=false`：这些 EvoSuite 原始测试是输入生成结果，不能当作已生成 oracle 断言的最终 DiffTGen 测试。

失败原因是本轮搜索未取得能使错误版和候选版产生不同观察输出的输入，不是编译失败、缺少 oracle 或超时。预算为 1 trial × 60 秒搜索，整个流水线包括测试生成收尾和三版本执行，约 138 秒。预算已用完，未追加隐含轮次；提高预算或重复运行仍不保证发现反例。

逐项证据和源码位置在 `VALIDATION.md`；`result.csv` 给出分阶段状态。本次没有进入生成后 JUnit 验证分支，`verification.json` 为 `[]`。脚本保留了后续若生成最终测试时的验证分支，但该分支本轮未执行验证，不能声称它已通过。

## 目录和环境

当前独立项目根目录：`D:\CodexOutputs\2026-10-27\14-difftgen-https-github-com-qixin5`。
本文件所在 `outputs/reproduction` 为交付目录；作者仓库在 `work/DiffTGen`，下载及独立环境在 `work/deps`。遵守本轮指定的当前目录，不移动既有项目。

复用 WSL2 Ubuntu-22.04，Linux 6.6.87.2-microsoft-standard-WSL2，x86_64；Git for Windows 2.53.0.windows.2。初检 WSL 无 java/javac/ant，Windows 只有可发现的 JRE 8，不能替代 Linux JDK。D 盘约 600 GiB 可用。

项目环境：Azul Zulu JDK 8u492 b09 Linux x64；Apache Ant 1.10.15（官方 Maven 核心、launcher 及 junit 组件），EvoSuite 使用作者 `lib/evosuite-1.0.2.jar`，JUnit 使用作者 4.11。实测版本见 `runs/*/environment.*.log`。

仅脚本子进程设置 JAVA_HOME、ANT_HOME、PATH、JAVA_TOOL_OPTIONS；单 JVM 最大堆 1 GiB、可见处理器数 2，串行执行。没有 update-alternatives、修改系统默认 Java、安装 Docker、改动 PatchEval 或其镜像，也没有模型 API。

## 重复执行

在当前目录的 PowerShell 中：

```powershell
wsl -d Ubuntu-22.04 -- bash /mnt/d/CodexOutputs/2026-10-27/14-difftgen-https-github-com-qixin5/outputs/reproduction/setup-local.sh
wsl -d Ubuntu-22.04 -- bash /mnt/d/CodexOutputs/2026-10-27/14-difftgen-https-github-com-qixin5/outputs/reproduction/run-single.sh
```

`setup-local.sh` 使用已下载的项目内压缩包和 Ant jar，不修改系统。仅编译可给 `run-single.sh` 追加 `--compile-only`。每次运行创建新时间戳目录，避免覆盖历史结果。脚本要求本项目 `work` 保留，移动整个项目后仍可计算相对根目录。重跑会根据绝对路径重新配置作者 `run` 的 proj_dir。

实际运行先执行原版 `ant compile`，再编译三版本 BooleanUtils 和合并依赖 jar，最后调用作者 `run`。完整命令逐阶段保存在 `runs/<时间戳>/*.command.txt`。

## 预算及判定

一次串行 EvoSuite trial，search_budget 60 秒。作者内层 shell 超时由其代码计算为 5 分钟，外层 GNU timeout 600 秒并在 10 秒后强制收尾。搜索预算不等于整条流水线总耗时。未传 `-runparallel`；该参数是布尔开关，传 `false` 也会被当成开启，因此直接省略。

作者主程序有部分失败路径仍返回退出码 0；不能只据进程退出码判断流水线成功。应同时查看 stderr、阶段完成标记、生成文件和独立 JUnit 结果。`result.csv` 记录最终阶段状态；每次执行原始进程状态在 `runs/*/stages.csv`，其中 PASS 只表示对应进程 exit=0。

生成测试若存在，保存在 `runs/*/generated/Lang_51_nopol/testcase`；EvoSuite 原始测试、控制台、三版本输出保存在该目录树下的 test/target 等子目录。历史仓库测试没有拷贝到本轮 generated 中。

独立验证不改生成断言：通过 JUnit 分别运行作者测试插桩版本。作者默认只为 bug/patch 输出 instru1；验证脚本调用作者原有 `ClassUnderTestInstrumentor.getTestCaseInstrumentedClass` 为 fix 生成相同类型插桩，参考输入文件保持不变。辅助 Java 文件属于验证脚本，不属于作者工具补丁。

## 来源、改动和限制

版本来源和样例组装详见 `sample/SOURCES.md`。没有下载完整 Defects4J/Vul4J 数据集。当前依赖组合支持选定类级实验，不代表完整 Defects4J 环境。随机生成结果可能随重跑变化；未找到测试不能说明补丁正确。

作者代码改动详见 `author-changes.patch` 和 `CHANGES.md`。构建本身会重新生成作者 lib/myprinter.jar，需与语义代码修改区分。

## 课程后续

第 14 题还需实现补丁影响输入/分支提取、邻近输入生成、多版本比较、参考实现或规格 oracle、最小反例，以及原测试集与追加测试的对照。需在更多真实补丁上测错误补丁检出率、误报率、开销，单列 oracle 不可靠情况；再按课件选择 Vul4J 安全修复扩展。自造不完整补丁应单独标注。本轮未做这些新增模块或评估。
