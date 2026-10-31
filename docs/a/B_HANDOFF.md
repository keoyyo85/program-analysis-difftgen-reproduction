# B 接入冻结版：a.analysis.v1

本轮不改变 A JSON 结构及版本；冻结文件为 contracts/a-request.schema.json、contracts/a-analysis.schema.json 与 interfaces/a_contract.py，字节指纹见 contracts/A_V1_FREEZE.json。b-execution.schema.json 仍只是暂定 mock 连接示例，不冻结 B 完整执行模型。B 可以在 A 独立分支指定提交上接入；分支 codex/a-independent-delivery，不要求合并 main。最终 SHA 见交付消息/该分支 Git 日志。本轮父提交 c0cf86be9c584110b44a86bca074909da1af32bb。后续不在此冻结分支继续改接口；需另开变更分支与三方确认版本。

## 最短操作

```bash
git fetch origin codex/a-independent-delivery
git switch --detach origin/codex/a-independent-delivery
# 新机器先按根 README 准备项目内依赖；已有环境不必重复下载
bash modules/a/run.sh --request examples/teaching/int-threshold/request.json --output outputs/a/b-first-read
python3 -c 'import json; from interfaces.a_contract import validate_a; a=validate_a(json.load(open("outputs/a/b-first-read/analysis.json"))); print([(c["candidate_id"], c["arguments"]) for c in a["candidates"]])'
```

后一个命令只读取 A 候选。示例中的教学来源不得进入真实统计。`contracts/examples/a-request.json` 和 `a-analysis.json` 是完整小型实例；旧产物中的绝对路径是历史路径，应重新生成或用 B 显式文件映射，不能盲目在新机器照搬。

## 字段/类型约定

| 字段 | 冻结语义 |
|---|---|
| schema_version / artifact_kind | 必须 a.analysis.v1 / candidate_inputs_not_execution_results；未知版本拒绝 |
| case_id / case_kind | 请求身份；kind 为 teaching 或 real。real 仅说明来源类别，不是实验合格标志 |
| statistics_eligible | A 永远 false；候选未执行，不能直接进入检出率 |
| sources | before_source / patch_source / diff_path；每项 path 与 sha256，SHA256 是原文件字节，包括换行；无 reference |
| changes | 修改的方法、前后条件、直接控制的分支范围、关联依据、局部支持状态 |
| unhandled_changes | 无法唯一配对等变更及原因；不能当作不存在修改 |
| candidates | 有序参数与 provenance；不含答案，ID 为 case_id+方法/参数内容的摘要，不等于跨源码版本唯一实验 ID |
| generation | retained、max_candidates、max_length、truncated_attempts、events、实现指纹；status 是说明性字符串，B 不应据此判断正确性 |
| limitations | 局部分析/路径和业务合法性未证明等限制 |

`method.class_name` 使用包名和内部类 `$` 名；`signature` 是 `包.类#方法(类型,类型)` 的项目约定，不是 JVM descriptor，也不含返回类型。`method.parameters` 与 `arguments` **都按 Java 声明顺序**，不可按参数名排序。`parameters` 含 name/java_type/varargs，本版 varargs 不生成候选。`return_type` 是源码的 JDT 类型文本，可能是 String 而非规范全名；不要把它当 JVM 描述符。

参数类型编码：int→JSON整数（-2147483648..2147483647，bool 不可冒充 int）；boolean→JSON布尔；java.lang.String→JSON字符串；int[] / boolean[] / java.lang.String[]→同类型非空引用数组，元素无 null。本版不生成 null、long、浮点、char 或多维数组。字符串长度按 UTF-16 code units，不按 Python len 或 Unicode 码点。长度生成采用一个可打印 ASCII 字符；数组元素来自显式 fill 配置。

`before` 指修改前版本，`after` 指候选补丁侧；注意 sources 使用键 patch_source。每侧 location 为条件表达式，statement_location 为 if，controlled_ranges 的 then/else 为直接语法节点。offset 从0计数、UTF-16单位、右端开区间；行列从1计数，end_line/end_column 是最后字符。不能把范围当动态覆盖。

provenance 保留 change_id、side、condition、parameter、boundary、offset(-1/0/1)、rule、measure；去重后可有多条依据。B 不应按 provenance 条数重复执行同一个 candidate。truncated_attempts 计尝试，不是唯一未生成数。

## 状态与安全读取

supported 只表示局部映射成立；partial 可能有外层 guard 或其他无法处理变更；unsupported 的对应条件不能生成输入。合法分析即使没有候选也退出0，不能把空集解读成补丁正确。检查整个产物与每个 change，按自身策略明确拒绝/记录 partial。不能静默执行未知类型。

请求非法、源码/diff错配、解析失败、子进程超时等输出 a.error.v1/error.json，退出2；这不是 analysis.json，禁止送执行器。输出目录已存在属于前置条件违反，命令失败且不覆盖旧文件，不保证生成 error.json。运行器仍须检查退出码和最终产物，崩溃/中断不得当作空候选。

消费时先用 contracts/a-analysis.schema.json 校验，再调用 validate_a 做参数顺序/值类型跨字段检查；后者是小型消费者校验器，**不能替代完整 JSON Schema 和源码哈希检查**。source哈希核对示例：

```python
import hashlib
from pathlib import Path
for role, item in a['sources'].items():
    # B 可以显式映射到本机文件；映射后的字节必须相同
    assert hashlib.sha256(Path(item['path']).read_bytes()).hexdigest() == item['sha256'], role
for candidate in a['candidates']:
    method = candidate['method']
    values_in_java_declaration_order = [arg['value'] for arg in candidate['arguments']]
```

B 在自己的目录添加 reference 路径、构建依赖、类加载隔离、超时、return/exception、可靠 oracle 与缩减。不要回写 A 产物。现有 b.execution.v1 仅演示基本连接；B 的真实返回字段尚未冻结，不必把真实运行硬塞进 mock 的 value 字符串。若需要扩展 B schema，与共享接口维护者先协调；本轮未修改 B 完整模块。

本轮对 A 的内部可靠性修正（静态导入未解析字段拒绝、超时转错误、隔离构建缓存）不改变候选 JSON 格式；更保守地产生 unsupported 是能力判断修正，不是 API 改名。旧 baseline/接受记录原样保留。
