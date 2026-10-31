# A 独立交付 / B 稳定接入（2026-10-31）

交付分支 `codex/a-independent-delivery`，父提交 c0cf86be9c584110b44a86bca074909da1af32bb；最终提交编号以该分支 Git log 和本轮交付消息为准。本轮只推送独立分支，不合并 main。原作者源码、Lang_51 基线和全部历史实验不覆盖。未新增 B/C 完整实现。

## A 已完成

- 复查实际代码/历史证据；发现并修复 return 中未限定外部字段的漏拒绝。增加超时错误输出与隔离编译缓存，JSON 格式未变化。
- A 接口仍为 a.request.v1 / a.analysis.v1；[B 接入说明](../../../docs/a/B_HANDOFF.md) 明确参数声明顺序、类型编码、源码字节 SHA256、UTF-16位置、unsupported/partial/错误状态、mock 边界；[冻结指纹](../../../contracts/A_V1_FREEZE.json)。
- 完整小型实例：[本轮实际 analysis.json](analysis.example.json)、[请求](../../../contracts/examples/a-request.json)；例中路径是当前机器路径，新机器应重新生成。
- [独立实测结果](../handoff-check-20261031-122621/result.json)：**PASS**；全新缓存实际 javac 编译、README 单样例入口、24 项单元测试、内容断言、哈希检查、Lang_51 拒绝、非法请求 exit2、mock 接口均符合预期。
- [测试完整输出](../handoff-check-20261031-122621/correctness-tests.stderr.log)：24 tests / 88.282s / OK；[执行命令/退出码/耗时](../handoff-check-20261031-122621/manifest.json)，阶段耗时合计144.619秒；不是整个会话耗时。
- 教学源码实际提取 current>5→current>=5、current=score，生成4/5/6、label=allowed。测试另查5→8的双侧并集、int极值、零/负长度、数组配置、去重预算、多条件歧义、复合赋值及分支范围/三参数顺序。
- [报告](../../../docs/a/REPORT.md)、[短演示](../../../docs/a/DEMO.md)、[真实样例规则/排除记录](../../../docs/a/REAL_CASES.md)、[来源筛选证据](source-screening.json)。

## 怎么运行

已有 WSL 环境中，进入仓库根目录：

```bash
bash modules/a/handoff-check.sh
bash modules/a/run.sh --request examples/teaching/int-threshold/request.json --output outputs/a/my-new-run
```

每次使用新目录；handoff-check 需现有 Python3/jsonschema、项目JDK8及作者JDT依赖，未下载新组件。新的缓存仅在 work/a-build 下。当前机器也可从 PowerShell 调用：

```powershell
wsl -d Ubuntu-22.04 -- bash /mnt/d/CodexOutputs/2026-10-27/14-difftgen-https-github-com-qixin5/modules/a/handoff-check.sh
```

只提交小型源码、文档、JSON和验收日志；详细 AST 临时解析树不纳入本次提交；不提交依赖、class、密钥或大型实验产物。stdout/stderr 空文件也保留。根项目已有子模块 build/run 本地改动仍保留，未混入 A 提交。

## A 仍欠缺

**符合首版全部范围、完整可追溯源码对的真实正例尚未取得。** 已筛查的三个外部生产修复涉及递归/Map、循环/泛型、对象/新增guard等，不纳入；GitHub公开API随后限流，已停止，不绕过。它们不是已适配样例，更不是检出结果。Lang_51 是真实负例，保持 unsupported；教学例仍是教学例。正例适配是 A 尚待补齐项，不能等待 B 来替 A 完成。

此外仍无跨文件 binding、全程序影响、复杂状态、循环/跨函数或路径求解、Java8+语法与复杂多参数联立约束；这部分超出当前最小范围。

## 等待 B 后才能验证

B 在固定 A 分支/提交上读取完整候选、校验schema与参数/类型、核对三个源文件SHA256，再在自身配置中持有 reference。B实现三版本独立编译和实际类加载、返回/异常/超时归一、可靠oracle及缩减。A的supported、预算未检出与mock都不能替代真实判定。

当前没有新策略候选的三版本实际执行、经oracle验证的反例、缩减结果或检出率提升结论。真实执行与oracle可靠后，C才能统计真实合格样例；teaching/mock/A未执行候选一律排除。
