# A 阶段验收记录

最终完整验收目录：`outputs/a/acceptance-20261027-205800/`；result.json 为 PASS。

| 检查 | 真实结果 |
|---|---|
| 统一 diff + JDT 条件定位 + 直接赋值关联 | 教学案例 supported；score=4/5/6，各保留 label=allowed |
| 双侧依据及去重 | 每个候选含 before/after 两份 provenance；3 个候选，不是 6 次输入 |
| 正确性测试 | 20 项通过，82.447 秒测试框架时间；完整日志 correctness-tests.stderr.log |
| Java 极值、溢出、零/负长度和长度预算 | 测试通过；越界或不适用约束有明确跳过记录 |
| 方法/分支范围、UTF-16 位置、局部变量关联 | 真实 JDT 解析测试通过 |
| 复杂调用、循环、跨分支赋值、外部字段状态 | 输出 unsupported，无候选；外层 guard 标 partial |
| 输入/输出接口 | 已安装的 jsonschema 对请求、教学 A 产物、兼容性产物及 B mock 的完整 Schema 校验通过；v1 消费端也通过 |
| B mock | 3 条 simulated 记录，所有 value=MOCK_ONLY；oracle 未评估；statistics_eligible=false |
| Lang_51 新策略适用性 | unsupported，0 个候选；未调用 EvoSuite 或目标执行器 |
| 原实验记录 | git diff 核查 `outputs/reproduction` 无变化 |
| 作者源码/构建脚本 | 命令级 core.autocrlf=true 的只读核查通过；未改全局配置 |

这些是 **A 机制正确性和数据接口验收**，不是检出率、误报率或安全漏洞修复评估。教学源代码没有 reference；mock 没有实际执行目标；不将任何 mock 或 teaching 计入真实统计。

## 保留的中间记录

- `outputs/a/teaching-20261027-203752`：初次尝试 JLS8 时，作者旧 JDT 不含 JLS8/VERSION_1_8 常量，编译失败。随后仅修正独立适配器为作者已有 JLS4/Java7 语法；不修改作者库或工具。
- `outputs/a/teaching-20261027-204106`、`teaching-20261027-205052`：中间成功教学产物。
- `outputs/a/checks-*`：各阶段正确性检查记录；后续新增检查后运行最终完整 20 项。
- `outputs/a/acceptance-20261027-205348`：功能与 20 项测试已过，但 WSL Git 将 Windows CRLF checkout 与 LF 对象库比较，作者源码审计返回 1；原日志完整保留。Windows Git 只读 diff 无内容修改，最终按相同换行规则核查也通过。
- 恢复入口的 shell 参数最初未透传，已补齐 `"$@"`；因此额外产生了完整的 `205800` A 验收目录。没有覆盖旧目录，也没有因此运行历史 DiffTGen 基线。

最终可消费 JSON 示例来自 `205800`，存入 contracts/examples。后续不应把上述中间失败删掉或改为成功；应按具体运行目录引用最终证据。

## 没有完成的内容

B 的三版本隔离执行、oracle 与缩减、C 的真实配置/批量统计均未实现。A 不解决任意 Java 符号绑定、复杂跨函数依赖、对象状态、路径约束求解或全程序影响传播。分析和预算的限制见 README 及每份 analysis.json 的 limitations。
