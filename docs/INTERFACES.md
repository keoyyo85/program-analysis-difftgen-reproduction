# 公共接口 v1

UTF-8 JSON。A 请求版本 `a.request.v1`，A 产物版本 `a.analysis.v1`；未来 B 返回版本 `b.execution.v1`。本版只接受一个文件对；路径相对请求 JSON 所在目录解析。禁止请求未声明字段，特别是 reference/oracle/expected_output。

## A 请求

```json
{
  "schema_version": "a.request.v1",
  "case_id": "teaching-int-threshold",
  "case_kind": "teaching",
  "before_source": "before/Threshold.java",
  "patch_source": "patch/Threshold.java",
  "diff_path": "patch.diff",
  "config": {
    "base_arguments": {"label": "allowed"},
    "parameter_constraints": {"label": {"min_length": 1}},
    "max_candidates": 8,
    "max_length": 64,
    "string_fill": "a",
    "array_fill_values": {"int[]": 1}
  }
}
```

before/patch 含义是错误版本/候选补丁版本，不是 oracle。config 只允许类型合法的基值、声明式单参数范围/长度约束及预算。其他参数必须显式提供合法基值；不默认填 0。配置声明不等于业务正确性证明，不允许表达式执行或根据参考答案生成输入。

## A 产物 / B 输入

完整实测产物见 `outputs/a/*/analysis.json`。顶层含 schema_version、artifact_kind、case_id、case_kind、statistics_eligible=false、scope、sources、changes、candidates、generation、limitations。

- `sources`：before/patch/diff 路径、SHA256；无 reference。
- `changes`：change_id、file、method（类名、方法名、类型和参数、签名）、before/after 条件文本和位置、分支直接控制范围、关联参数、分析依据、支持状态和原因。
- `candidates`：candidate_id、case_id、method、按声明顺序排列的 `arguments=[{name,java_type,value}]`、`provenance`（前/后条件、临界值、偏移、规则）、`validation`（仅配置和类型检查，无 oracle）。同一方法同一输入合并依据。
- `generation`：预算、保留数、截断数、拒绝或跳过记录。整数使用 JSON number，范围为 Java int；字符串 ASCII 填充（长度等于 UTF-16 code units）；数组为 JSON array，元素来自显式 fill 配置。
- 支持状态：supported / partial / unsupported；partial 包括无法证明外层 guard 可达。unsupported 不生成该条件的输入。

位置 `start_offset/end_offset_exclusive` 是 Java UTF-16 源码偏移；行/列为 1-based，end_line/end_column 指向最后一个字符。分支范围是 AST 节点语法范围，不是动态覆盖或数据依赖闭包。

生成不含 expected value、is_correct、oracle 分类。B 应读取每个候选参数序列和方法签名，自行隔离三版本并调用 oracle；不要把 A 的 supported 当成已执行或判定通过。

## B 返回接口及 mock

```json
{
  "schema_version": "b.execution.v1",
  "case_id": "teaching-int-threshold",
  "case_kind": "teaching",
  "run_kind": "mock",
  "statistics_eligible": false,
  "results": [{
    "candidate_id": "<A生成的ID>",
    "execution_status": "simulated",
    "versions": {
      "before": {"status": "simulated", "value": "MOCK_ONLY"},
      "patch": {"status": "simulated", "value": "MOCK_ONLY"},
      "reference": {"status": "simulated", "value": "MOCK_ONLY"}
    },
    "oracle": {"status": "not_evaluated", "classification": null},
    "reduction": {"status": "not_implemented"}
  }]
}
```

`interfaces/mock_b.py` 仅验证 A 产物并演示连接，不启动 Java 目标，不读取参考版本，不产生检出结论。未来 B 的真实实现应使用 `run_kind=real`，实际输出 return/exception/timeout 等结果、加载证据和可靠 oracle 状态，再按真实案例类别决定统计资格；本阶段不定义或冒充这部分实现。

v1 消费端至少校验版本、case_id、candidate_id、方法签名、参数顺序及 Java 类型。JSON Schema 在 contracts；脚本还做跨字段和类型约束校验。对不认识的版本必须拒绝，不能静默解释。

完整 JSON 请求、实测 A 产物和明确标注 B mock 的示例保存在 `contracts/examples/`。生产 B 消费端在执行前还应核对 A.sources 的 SHA256 与其持有的 before/patch 文件一致；reference 只由 B 的执行配置持有。

源文件损坏、diff 不匹配、请求字段非法时 CLI 返回 2，输出 `a.error.v1`（status=error、reason、statistics_eligible=false），不能交给执行器当候选处理。合法但不受支持的结构仍返回合法 `a.analysis.v1`，support_status=unsupported、candidates=[] 和具体原因。
