# DiffTGen 真实结果核验

## 续轮结论

配置复核和三次串行 180 秒搜索已完成，详情见 `CONTINUATION.md` 和 `audit/CONFIGURATION.md`。新增第 2 轮自动生成并初次三版本验证了 `DiffTGen0Test.java`：输入 `Fes`，期望 false，bug=false、patch=true、fix=false。新增第 1、3 轮未检出区分测试。每轮真实种子和耗时见 `continuation-result.csv`，各轮历史 result.csv 保留，顶层 result.csv 汇总全部轮次。

| 类别 | 结果 |
|---|---|
| 目标配置问题 | 未发现；三版本 class 哈希及实际来源不同，delta/oracle 行列匹配，异常不转为 false |
| 验证环境差异 | 初次验证 wildcard 加载 EvoSuite 内附 JUnit 4.12；显式 JUnit 4.11 回放已完成且结论相同 |
| 搜索未检出 | 原首轮、新增第 1 和第 3 轮；不说明候选补丁正确 |
| 自动检出 | 新增第 2 轮：Fes，assertFalse；JUnit 4.12 和显式 4.11 下均 bug/fix 通过，patch 断言失败；未插桩 class 也确认返回 false/true/false |
| 人工诊断 | 未执行；三轮仍无自动反例的条件不成立，没有人工输入计入自动成果 |

原始 EvoSuite 测试、筛选观察测试及最终测试的统一回放结果位于 `audit/replay`，采用显式 JUnit 4.11 并保留实际加载轨迹；最终完成状态见 CONTINUATION.md 的回放小节。

首轮内容保留性核验：`audit/first-run-preservation-check.json` 为 ChangedFiles=0。

## 首轮记录（保留历史）

实测目录：`runs/20261027-175712`。

| 阶段 | 实测 |
|---|---|
| 作者原版编译 | PASS；`author-compile.stdout.log` 含 BUILD SUCCESSFUL；0；9.837 秒 |
| bug / patch / fix 编译 | 各自退出 0 |
| 作者插桩及目标编译 | difftgen.stdout.log 对应 Done 标记齐全 |
| EvoSuite | target/0/0/rslt 含 Generated 120 tests、Done、Computation finished |
| 作者三版本运行 | 三版本 test/0/0/rslt 均 BUILD SUCCESSFUL |
| 最终区分测试 | NOT_GENERATED；Found Nothing；testcase 下没有 DiffTGen*Test.java |
| 区分断言验证 | NOT_VERIFIED；没有可验证的最终断言，未以历史测试替代 |

`generated/Lang_51_nopol/test/0/0/TestClass.java` 中，test007 位于 222 行，实际输入第 224 行是 `off`；test039 位于 1310 行，实际输入第 1312 行是 `X2f`。两者都调用 `BooleanUtils.toBoolean(String)`。

检查 `generated/Lang_51_nopol/{bug,patch,fix}/test/0/0/rslt`，对应方法输出均为 `TYPE:Boolean / VALUE:false`。日志证实实际运行了参考版，而不是只比较两个补丁或只检查退出码。fix 的 rslt_a、rslt_b 是作者 OracleRunner 的重复 oracle 运行记录，均保留。

输入源文件位置：

- bug/BooleanUtils.java 第 677 行为 `if (ch == 'Y')`，位于 toBoolean(String) 的 case 3。
- patch/BooleanUtils.java 第 677 行为 `if (str!=null)`；来自作者引用的 Nopol 补丁。
- fix/BooleanUtils.java 第 624 行是方法 javadoc 起始，第 649 行是方法声明，第 682 行是 case 3 末尾的 `return false;`。
- 作者生成目标 `generated/Lang_51_nopol/target/BooleanUtils.java` 的 Goal Locs 为 slc:680,6；插入目标计数代码后行号变化属于工具生成，不是修改原始差异位置。

EvoSuite 使用 `-Dassertions=false`，作者筛出的 TestClass 保留输入并通过输出插桩获取观察值。只有发现语义差异后，作者才依据 oracle 创建 DiffTGen*Test.java 断言；本轮没有走到该分支。所以“120 个原始测试”不等于“120 个区分测试”，也不构成补丁正确性证明。

当前阻碍：搜索输入没有暴露这处 Nopol 过拟合条件的差异。之后可以在明确增加预算、重复次数或更换另一个可追溯作者样例后继续实验；本轮没有伪造输入、篡改 oracle 或修改生成结果以制造成功。
