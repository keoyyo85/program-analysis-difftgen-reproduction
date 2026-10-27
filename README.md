# 安全补丁的差分与评估：DiffTGen 最小复现

《编译原理与程序分析》大作业-安全补丁的差分与评估

本仓库保存作者原版 **DiffTGen** 的最小基线复现，包括真实运行日志、生成测试、三版本回放与验证记录；现已新增 A 模块的局部条件分析和边界输入生成。B 的真实执行/oracle/缩减及 C 的批量实验/统计尚未实现。

## A 模块最小闭环

- [协作职责与文件归属](docs/COLLABORATION.md)、[v1 JSON 接口](docs/INTERFACES.md)。
- [A 模块使用与适用范围](docs/a/README.md)、[简短演示材料](docs/a/DEMO.md)。
- 代码位于 `modules/a`，复用作者已有 JDT jar；不改作者工具，不读取正确参考版本。
- WSL 项目根目录运行 `bash modules/a/demo.sh`：自建教学例 `current > 5` → `current >= 5` 自动关联 score，生成 4、5、6；其他参数保留显式合法配置。教学和 mock 均不进入真实检出统计。
- 验收入口 `bash modules/a/acceptance.sh`；新产物在 `outputs/a/`，历史 `outputs/reproduction/` 保留。

以下为保留的原版基线记录，与新策略成果分开。

## 已完成的结果

- 作者仓库：<https://github.com/qixin5/DiffTGen>，固定 commit `cb16dfda75a5e5cca7f3e20aad7257e89f619427`，作为 `work/DiffTGen` 子模块引用。
- 在 WSL2 Ubuntu-22.04、JDK 8u492、Ant 1.10.15 下，执行作者 `ant compile` 成功。
- 真实样例：**Lang_51 / Nopol**。错误版、候选补丁版、正确参考版分别编译，核对实际 class 加载来源。
- 保留首轮 1 × 60 秒搜索；另做 3 次串行独立搜索，每次 180 秒，实际种子分别为 `2026102701`、`2026102702`、`2026102703`。
- 新增第 2 轮自动生成区分测试：`BooleanUtils.toBoolean("Fes")`，期望 `false`。错误版返回 false、Nopol 候选版返回 true、正确版返回 false。
- 生成的 `assertFalse` 在错误版与参考版通过、候选版断言失败；显式 JUnit 4.11 和未插桩 class 回放确认一致。

| 搜索 | 预算 | 实际种子 | DiffTGen 耗时 | 自动区分测试 |
|---|---:|---:|---:|---|
| 首轮 | 60 秒 | 未记录 | 138.350 秒 | 无 |
| 新增 1 | 180 秒 | 2026102701 | 293.857 秒 | 无 |
| 新增 2 | 180 秒 | 2026102702 | 290.228 秒 | 已生成并验证 |
| 新增 3 | 180 秒 | 2026102703 | 281.104 秒 | 无 |

未检出不能说明补丁正确。本仓库的区分反例来自自动搜索，不是人工构造，也没有使用作者历史测试代替本轮结果。

## 阅读材料

- [环境、复现命令及已知问题](outputs/reproduction/README.md)
- [续轮实验、种子和耗时](outputs/reproduction/CONTINUATION.md)
- [验证报告](outputs/reproduction/VALIDATION.md)
- [结果汇总 CSV](outputs/reproduction/continuation-result.csv)
- [样例来源与三版本组装](outputs/reproduction/sample/SOURCES.md)
- [作者代码改动记录](outputs/reproduction/CHANGES.md)
- [自动生成测试](outputs/reproduction/runs/20261027-183648/generated/Lang_51_nopol/testcase/DiffTGen0Test.java)
- [显式 JUnit 4.11 回放证据](outputs/reproduction/audit/replay/20261027-183648)

`runs/` 内每轮目录独立保留，日志中的绝对路径属于原实验环境，不应直接用于其他机器。

## 在新机器准备环境

需要 Windows、可用的 WSL2 Ubuntu-22.04、Git 和网络连接。将整个仓库克隆到 D 盘目录，例如 `D:\Development\Experiments\program-analysis-difftgen-reproduction`：

```powershell
git submodule update --init work/DiffTGen
powershell -ExecutionPolicy Bypass -File .\prepare-project.ps1
```

`prepare-project.ps1` 只在项目的 work/deps 中下载固定版本 JDK/Ant/Commons Lang 依赖，并调用项目内 setup-local.sh。不修改系统默认 Java，不安装 Docker。接着在 WSL 中进入本仓库目录，运行：

```bash
bash outputs/reproduction/run-single.sh --budget 180 --seed 2026102702
```

要重做三次串行实验，运行 `bash outputs/reproduction/run-three.sh`。新时间戳目录不会覆盖已有结果。当前的回放/汇总脚本也包含针对历史轮次名称的核查，应按报告中的命令和说明使用，不能将历史记录误认为新机器上的执行结果。

仓库不上传本地 JDK、下载包、依赖 jar、编译 class、构建缓存或课件摘录；脚本和历史源码/文本日志保留。上游引用与第三方代码说明见 [THIRD_PARTY.md](THIRD_PARTY.md)。
