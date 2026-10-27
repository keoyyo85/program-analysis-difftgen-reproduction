# 第 14 题协作约定（接口 v1，2026-10-27）

项目：安全补丁的差分与回归评估。保留 DiffTGen 作者工具为原版基线，在其外部实现课程模块；不覆盖 `outputs/reproduction` 的历史证据，不把教学案例、模拟输出计入真实项目检出率。

| 成员 | 职责 | 拥有的目录 |
|---|---|---|
| A | 补丁条件、影响分支提取；简单参数关联；边界输入生成；最终集成 | `modules/a/`、`tests/a/`、`examples/teaching/`、`examples/a-compatibility/`、`docs/a/` |
| B | 三版本独立编译/执行、可靠 oracle 判定、反例缩减 | 未来 `modules/b/`、`tests/b/` |
| C | 真实样例配置、批量实验、日志复查、统计 | 未来 `cases/real/`、`experiments/`、`modules/c/` |
| 共享 | 接口定义与文档、模块适配入口 | `contracts/`、`interfaces/`、`docs/COLLABORATION.md`、`docs/INTERFACES.md` |

本阶段只实现 A 和显式模拟的 B 适配，不创建 B 执行器、oracle 或缩减器，不建立真实批量实验和检出统计。教学配置由 A 维护，真实配置由 C 接管。共享接口后续修改须先记录版本及兼容性说明并与三方协调；不得随意改动其他成员文件。

## 基线

- 本仓库阶段前 commit：`5b5e18168e213ef0e5657ce047ddeb8f9505e726`。
- 作者 DiffTGen 子模块：`cb16dfda75a5e5cca7f3e20aad7257e89f619427`。
- 原版入口：`outputs/reproduction/run-single.sh`；历史三轮：`run-three.sh`。
- 历史结果：`outputs/reproduction/runs/`；报告：`VALIDATION.md`、`CONTINUATION.md`；成功轮 `20261027-183648`，自动输入 Fes。A 不硬编码或复用该输入作为新生成成果。
- A 阶段输出：`outputs/a/`；每次演示新目录，禁止覆盖旧目录。编译缓存放 `work/a-build/`，不提交。

## 数据隔离

A 只读 before、patch、diff 及允许配置，不接收 reference/oracle 路径。正确参考实现只能由未来 B 配置或执行层持有，不进入生成器。A 不能判定补丁正确性，候选的路径可达性和业务有效性未被证明。

教学 `case_kind=teaching`，真实 `case_kind=real`；B mock 必须 `run_kind=mock`、`statistics_eligible=false`。统计层只接受真实来源、真实执行、明确 oracle 可靠性的结果；不能仅凭一个布尔字段将 mock 转为真实。A 输出本身不是检出效果。
