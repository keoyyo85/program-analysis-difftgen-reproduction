# A 模块最小闭环交付

2026-10-31 独立交付更新见 [handoff/DELIVERY.md](handoff/DELIVERY.md)：A 分支、冻结接入说明、全新缓存编译及 24 项内容正确性测试；真实正例未取得，已单列欠缺。以下保留首次交付的历史说明与验收链接，不作为本轮复验的替代证据。

已实现独立于作者工具的局部条件/分支提取、直接参数与简单局部赋值关联、修改前后边界候选生成、预算/去重记录及 B mock 接口。未实现 B/C 完整模块，没有新增真实检出率结论。

## 文件归属

- `docs/COLLABORATION.md`：三人职责、目录归属、当前基线版本和证据位置。
- `docs/INTERFACES.md`、`contracts/*.schema.json`、`contracts/examples/`：v1 JSON 契约和完整示例。
- `modules/a/java/AstExport.java`：复用作者 JDT jar 的只读 AST 导出器。
- `modules/a/analysis.py`、`ast_bridge.py`、`cli.py`：diff 校验、条件/分支定位、局部关联和候选输入。
- `modules/a/{run,demo,check,acceptance}.sh`：可重复入口；Python 验收与检查日志脚本同目录。
- `interfaces/a_contract.py`、`interfaces/mock_b.py`：消费端校验及显式 mock，无实际 B 执行/判定。
- `examples/teaching/int-threshold/`：单独标记的教学源码对、diff 和配置。
- `examples/a-compatibility/lang51/`：对已有样例仅做适用性检查，无参考版本输入。
- `tests/a/`：20 项必要正确性检查。
- `docs/a/README.md`、`DEMO.md`、`VALIDATION.md`：使用、适用范围、短演示和验收说明。
- 根 README：新增 A 阶段入口；原版基线报告和证据未改动。

## 运行

在 WSL 中进入当前项目根目录：

```bash
bash modules/a/demo.sh
bash modules/a/check.sh
bash modules/a/acceptance.sh
```

现有 Windows 项目可直接调用：

```powershell
wsl -d Ubuntu-22.04 -- bash /mnt/d/CodexOutputs/2026-10-27/14-difftgen-https-github-com-qixin5/modules/a/demo.sh
```

每次新建时间戳输出目录，不覆盖历史。JDK8 和现有 JDT jar 仍在 work 下，本轮没有下载新依赖、重编译作者工具或重跑基线。

## 实测结果

最终验收为 [PASS](acceptance-20261027-205800/result.json)。

教学补丁 `current > 5` → `current >= 5`，通过局部赋值 `current=score` 关联参数 score，生成 4、5、6；其余参数保留显式配置 label=allowed。三个候选均保存修改前/后的生成规则，不含预期返回值或 oracle 答案。详见 [真实 A 产物](acceptance-20261027-205800/teaching/analysis.json)。

20 项正确性检查通过，包含真实 AST 解析、双侧不同常量、极值/溢出、字符串/数组长度、零长度/负长度、预算截断、其他参数配置、复杂状态拒绝、diff 错配及 UTF-16 位置；[完整测试日志](acceptance-20261027-205800/correctness-tests.stderr.log)。已有 jsonschema 的完整契约校验也通过。

Lang_51 输出 [unsupported、0 候选](acceptance-20261027-205800/lang51/analysis.json)。A 的首版不支持 switch 内的字符/null 关联，未硬编码或注入 Fes。原版基线成功仍保留，不能当作新策略成果。

## B 如何接入

读取完整 analysis.json → 调用 interfaces.a_contract.validate_a → 核对 before/patch SHA256 → 按 candidates 中的方法签名、有序 arguments 和 Java 类型读取输入。参考版配置仅在 B 持有；A 不能读取。之后由 B 自行实现三版本隔离、oracle 和反例缩减。

[当前模拟对接输出](acceptance-20261027-205800/teaching/b-mock.json) 的 run_kind=mock、statistics_eligible=false，三版本都是 MOCK_ONLY，oracle 未评估；这些不是真实执行结果，也没有进入统计。

## 适用范围

支持 Java int 与整数字面量的比较、String.length()、int[]/boolean[]/String[] 的 length，及直接参数/简单局部别名；前后边界并集、Java 范围、资源约束、去重、类型和配置检查。

只做局部语法分析和有限顺序关联，不保证路径可达或业务有效。仅一个文件对、每个未改签名的静态方法中一个唯一修改条件。复杂调用、反射、字段/继承状态、跨分支合流、实例/构造器、循环和复杂控制等拒绝推断；嵌套 guard 标 partial。解析器沿用旧 JDT 的 Java7 语法，不支持 Java8+ 新语法；不做任意项目跨文件 binding。

首轮适配编译失败及 CRLF 审计差异的中间记录均保留，详情在 docs/a/VALIDATION.md。新代码和文档位于当前本地项目，原有 GitHub 基线记录不受影响。
