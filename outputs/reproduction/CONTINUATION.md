# 续轮：配置核查与三次独立搜索

首轮 `runs/20261027-175712` 保留，续轮使用新目录。详细配置核查在 `audit/CONFIGURATION.md`；原文件内容哈希清单在 `audit/first-run-preservation.csv`。

## 已确认的配置

首轮两个输入是 toBoolean(String) 的 `off`、`X2f`，false 为真实返回值。原始及输出插桩 class 各版本哈希不同、实际加载路径不同；源文件位置 677,16 和 oracle 624,4 均匹配。没有发现目标 classpath 混用或异常改写为 false。独立验证中的 JUnit 通配路径差异另作显式 4.11 回放核查，不隐瞒为全程同一版本。

作者 patch 源码在对应条件后明确写 `//Overfitting`，并保存对应历史 regression-indicative 测试。本轮不复用该历史测试，不向搜索注入历史输入。

## 执行协议

```powershell
wsl -d Ubuntu-22.04 -- bash /mnt/d/CodexOutputs/2026-10-27/14-difftgen-https-github-com-qixin5/outputs/reproduction/run-three.sh
```

脚本串行调用三次 `run-single.sh --budget 180 --seed <seed>`，每次独立进程、独立输出目录，且每个 DiffTGen 调用只设 1 trial。种子分别为 2026102701、2026102702、2026102703。

DiffTGen 本身没有 seed 参数；通过随附 EvoSuite 支持的 JVM `random_seed` 属性设置，先用 SeedProbe 验证，再以各轮 statistics.csv 的 Random_Seed 确认。未修改作者 Java 源码、EvoSuite jar、参考版本或判定规则。`output_variables` 属性只增加种子统计字段。

各轮 configuration.json 保存实际 JAVA_TOOL_OPTIONS、预算、请求种子；difftgen.command.txt 保存完整工具命令；target/0/0/run_evosuite 是作者实际生成的 EvoSuite 参数。180 秒是搜索预算，不包含初始化、最小化、编译检查和三版本运行。外层总超时仍为 600 秒，未扩大搜索预算或无限重试。

时间预算下的随机搜索即使使用固定种子，也不保证跨机器得到逐字相同测试。

## 结果

三轮搜索全部完成，退出码均为 0，未触发外层超时。

| 轮次 | 输出目录 | 实际种子 | 搜索预算 | DiffTGen 完整耗时 | EvoSuite 报告原始测试数 | 最终区分测试 |
|---|---|---:|---:|---:|---:|---|
| 保留首轮 | 20261027-175712 | 未记录 | 60 秒 | 138.350 秒 | 120 | 无 |
| 新增 1 | 20261027-183131 | 2026102701 | 180 秒 | 293.857 秒 | 117 | 无 |
| 新增 2 | 20261027-183648 | 2026102702 | 180 秒 | 290.228 秒 | 122 | DiffTGen0Test.java |
| 新增 3 | 20261027-184225 | 2026102703 | 180 秒 | 281.104 秒 | 122 | 无 |

新增三次 DiffTGen 实际完整执行耗时之和为 **865.189 秒（14 分 25.189 秒）**，不包含外层环境检查、Ant 编译、独立 JUnit 验证及统一回放；这些步骤分别记录在 stages.csv 和 audit/replay/records.json。540 秒为三次配置搜索预算之和，不能用它冒充完整实验耗时。种子均由各轮 statistics.csv 的 Random_Seed 实际报告值确认；首轮未记录的种子没有追溯猜测。

计入三轮环境检查、编译、合包及初次最终测试验证后，各轮已测子进程耗时总计 **940.902 秒**，详见 audit/measured-stage-totals.json。另有统一回放 242.170 秒，合计 **1183.072 秒**；该合计是有记录的子进程耗时之和，不包含人工检查、脚本 I/O、文档整理，不能称为整次聊天或整个工作的墙钟时间。

新增第 2 轮自动生成 `DiffTGen0Test.java`：test040 的输入为 `Fes`，断言是 assertFalse。bug/fix 通过、patch 断言失败。该文件第 1304 行调用 toBoolean("Fes")，第 1308 行开始 oracle 断言；不是作者历史测试拷贝，也不是人工添加输入。

其原始三版本观察结果为 bug=false、patch=true、fix=false。原因是字符串长度为 3、首字符 F 不属于 y/Y；候选补丁的 str!=null 条件仍为真，错误地只检查后两个字符 e/s，因此返回 true。参考实现返回 false，与原有规格中只有 true/on/yes 忽略大小写匹配为 true 一致。

## 回放与结果分类

`replay_all.sh` 在三轮结束后，分别回放各轮的完整原始 EvoSuite JUnit suite、作者筛选后的 TestClass.main、最终 DiffTGen 测试（如有）；全部使用各自版本 class，并保存实际 class 加载轨迹。最终断言的正确版测试插桩由作者原 API 生成，输入参考源码与断言保持不变。

原始 EvoSuite suite 使用 assertions=false，不应把它们的 JUnit 通过解释为补丁正确。自动检出必须以最终 oracle 断言在正确版通过、候选版失败，并检查失败类型为断言差异为依据。

统一回放已全部完成，`audit/replay/records.json` 共 51 个独立进程记录，执行耗时之和 242.170 秒（不等于含脚本开销的整体墙钟时间）。四轮原始 suite 分别为 120、117、122、122 个测试，在三版本上均实际运行并通过；由于没有最终 oracle 断言，这不证明候选补丁正确。

对第 2 轮最终测试，显式 JUnit **4.11** 的三版本结果为：

| 版本 | JUnit 结果 | 退出码 |
|---|---|---:|
| bug | OK (1 test) | 0 |
| Nopol patch | test040 的 assertFalse 发生 AssertionError；1 test, 1 failure | 1 |
| fix | OK (1 test) | 0 |

加载轨迹确认 JUnitCore 来自作者 junit-4.11.jar、BooleanUtils 分别来自 verification/bug、verification/patch、verification/fix。与初次 JUnit 4.12 回放一致，故验证依赖的优先级差异不影响这次区分结论。失败不是编译、缺少字段、找不到类或参考版异常。

独立 plain class 回放也确认 `Fes` 得到 bug=false、patch=true、fix=false，见 audit/replay/20261027-183648/load-{bug,patch,fix}.stdout.log，排除差异仅由插桩产生。

分类结论：目标配置未发现错误；验证环境曾有 JUnit 版本优先级差异，已显式 4.11 核对；首轮和新增 1、3 属于搜索未检出；新增 2 属于自动检出并验证成功。人工诊断未执行，因为“三轮仍无自动区分测试”的条件不成立，没有人工输入计入自动成果。未开发课程新增模块。

可重复执行的核查与汇总命令（搜索命令见上文）：

```powershell
wsl -d Ubuntu-22.04 -- bash /mnt/d/CodexOutputs/2026-10-27/14-difftgen-https-github-com-qixin5/outputs/reproduction/audit.sh
wsl -d Ubuntu-22.04 -- bash /mnt/d/CodexOutputs/2026-10-27/14-difftgen-https-github-com-qixin5/outputs/reproduction/replay_all.sh
wsl -d Ubuntu-22.04 -- python3 /mnt/d/CodexOutputs/2026-10-27/14-difftgen-https-github-com-qixin5/outputs/reproduction/collect-continuation.py
wsl -d Ubuntu-22.04 -- python3 /mnt/d/CodexOutputs/2026-10-27/14-difftgen-https-github-com-qixin5/outputs/reproduction/finalize-continuation.py
```

collect 重建顶层阶段汇总，finalize 在其后加入回放阶段状态；历史每轮 result.csv 不改动。退出 1 的 patch 断言失败标为 EXPECTED_ASSERTION_FAILURE，而不是基础设施故障。原版嵌套子进程 stderr 的可见性限制见 audit/CONFIGURATION.md；独立回放 stdout/stderr 均分开保存。
