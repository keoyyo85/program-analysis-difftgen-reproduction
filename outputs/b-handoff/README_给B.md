# 发给 B：离线接入任务单

A 冻结代码：9bb8fc496ecd5f89f27b60555e1339960a206622，接口 a.analysis.v1。本包不需要访问 GitHub即可读入候选并核对源码；不含 JDK、JUnit、Commons Lang jar、作者 JDT jar 或完整作者工具。

## 先做什么

1. 解压，进入 A-to-B 目录，运行 `python smoke_read.py`（Windows也可 `py -3 smoke_read.py`）。它只用 Python 标准库，核对包清单与三个教学输入文件的 SHA256，调用 A 的消费端校验并打印有序候选。**这不是三版本执行，也不是 oracle 验证。**
2. 阅读 docs/a/B_HANDOFF.md 和 contracts/a-analysis.schema.json。A 的实际教学产物是 outputs/a/handoff/analysis.example.json；其原绝对路径已用 smoke_read.py 的显式角色映射核对，不修改历史产物。
3. 开发自己的 modules/b/、tests/b/，不要修改 modules/a/ 或冻结的 A schema。有接口问题先反馈给 A；b-execution.schema.json 目前只是 mock 示例，真实输出需要协商完善。

## 你负责实现的部分

1. **三版本独立构建与执行**：接收 A 的完整 analysis.json 和独立的 B 运行配置；B配置持有 before/patch/reference 实际位置、依赖、方法/类加载、超时。按 Java 声明顺序传参，分别在隔离进程/输出目录运行；保存 javac/java命令、class/source哈希、实际类加载来源、退出码、stdout/stderr和耗时，排除共用旧class和classpath串用。
2. **执行结果和 oracle**：分别记录 return、exception、timeout、compile_error、infrastructure_error；不要把异常/超时统一改成false。布尔返回false也不能与“比较不相等”的false混为一谈。reference必须有明确来源及可信依据；超时/构建失败/reference不可靠时记未判定，不能判补丁正确。明确比较策略与回归分类，缺少依据时保留 unknown。
3. **反例缩减**：只对已经真实区分且oracle可靠的输入做缩减。每次缩减都重新三版本回放，保留合法配置约束和区分性质；保存原输入、缩减输入、每次尝试、预算及停止原因。不能修改参考实现或预期答案。

## 怎么开始验证

- 教学例有 before/patch和候选4/5/6，适合先验证解析、参数顺序和执行 plumbing。**本包没有给教学例指定正确reference**；不能自行把before当正确答案来宣称真实回归。教学永远不计真实检出率。
- 本包另有原基线真实样例 `outputs/reproduction/sample/{bug,patch,fix}/BooleanUtils.java`，映射 B 的 before/patch/reference；来源在同目录 SOURCES.md。它只用于 B 的独立执行回归自测，不是 A 新策略生成案例。
- 原 DiffTGen 自动反例为 `BooleanUtils.toBoolean("Fes")`：历史独立回放是 bug=false、patch=true、fix=false。可用此已知回归测试检查 B 是否真实加载三份不同class。**标记 historical_baseline_replay，不能计为 A 新策略自动发现。** 历史生成测试及显式JUnit4.11日志随包保存，路径里的旧机器命令仅供溯源。
- 该类依赖 Commons Lang 2.3 的其余类；需从已合法取得的依赖获取，编译/运行时每版本自己的 BooleanUtils 必须优先于依赖jar，并核对加载位置。包不含依赖，不能声称解压就能完成Java三版本运行。
- Lang_51在 A 中是unsupported/零候选。B 不要给它伪造A候选。A尚欠缺范围内真实正例，后续由A补齐，再交你跑真实新策略候选。

## 请交回给 A 的东西

- B源码、README、可重复单样例命令及必要测试；不要求你访问共同仓库，可直接发zip。
- 实际执行结果JSON，逐项关联case_id/candidate_id、输入原值、三版本source/class哈希、返回/异常/超时、oracle依据/分类；给出schema与示例，与A确认后再固定。
- 一次三版本真实回放的完整小型日志与结果；失败也如实交回。
- 缩减报告：原始与最终输入、回放结果、尝试/预算。若尚未实现，明确not_implemented，不能用mock代替。

最小验收：同一输入真正进入三个独立版本；类型/参数顺序正确；异常不伪装返回值；历史Fes三版本结果与来源对应；缩减后保持判定性质。还要有类混用/超时/reference不可靠等失败路径检查。

teaching、mock、历史已知反例自测、仅A候选均不得混入真实新策略检出率。批量配置和统计属于C，不要求你实现。A的局部分析与候选生成已可接入，但“真实正例适配完成/检出率提高”尚不能宣称。
