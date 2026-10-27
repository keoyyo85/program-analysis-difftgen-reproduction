# A 模块：局部条件分析与边界输入

实现位置 `modules/a`，接口见 `docs/INTERFACES.md`、`contracts/*.schema.json`；职责和文件归属见 `docs/COLLABORATION.md`。

## 运行

在现有 WSL Ubuntu-22.04 中进入项目目录：

```bash
# 教学案例 → A 分析 JSON → 明确标注的 B mock
bash modules/a/demo.sh

# 解析/生成/接口/边界的正确性检查（不运行基线）
bash modules/a/check.sh

# 教学 + 旧样例适用性 + 正确性检查 + 基线保留性的最小验收
bash modules/a/acceptance.sh

# 单独处理请求，输出目录必须尚不存在
bash modules/a/run.sh --request examples/teaching/int-threshold/request.json \
  --output outputs/a/my-new-teaching-run
```

也可以从 PowerShell 用 `wsl -d Ubuntu-22.04 -- bash <项目Linux绝对路径>/modules/a/demo.sh` 调用。脚本相对自身定位项目，默认使用现有 `work/deps` JDK8，可由子进程 JAVA_HOME 覆盖；不修改系统默认 Java。缺少上游 jar 或 JDK 时按根 README 准备环境，不会静默联网安装。

## 分析与生成机制

1. 校验请求的 v1 字段白名单；不接收 reference、oracle、expected_output。验证统一 diff 的上下文、行数、修改覆盖是否与输入源码一致，拒绝错配或缺失 hunk。
2. `java/AstExport.java` 使用作者 lib 内的 Eclipse JDT 做结构解析。解析模式是作者库实际支持的 **JLS4 / Java7 语法**，运行环境仍为 JDK8；未使用正则解析 Java 结构，也未改作者源码。正则只识别 diff hunk 头。
3. 通过类名、方法名和参数类型签名匹配前后方法，用修改行与条件表达式 AST 范围交叉定位；每个匹配方法首版只接受唯一一个修改条件，歧义时拒绝猜配。
4. 顺序解释同一方法的局部变量声明、直接赋值；关联直接参数、String.length() 或数组 length。保留声明/赋值依据。赋值跨条件或循环的合流、算术反推、字段状态不猜测。
5. 将支持的比较统一为“参数度量 op 整数常量”；同时取修改前后常量的 -1、0、+1，检查 Java int 范围、长度域、资源预算和配置约束，再按“方法+全部参数值”去重并合并 provenance。
6. 输出候选只说明类型和允许配置已检查，业务有效性及路径可达性仍为 not_proven。对外层 if guard 记录分支上下文并标 partial，不把生成输入等同于已覆盖分支。

条件和 then/else 直接控制的语句节点范围来自 AST，行列为 1-based、偏移为 UTF-16。范围只表示语法控制范围，不是影响传播闭包，也不是覆盖率或全程序数据流。

## 支持情况

| 情况 | 首版处理 |
|---|---|
| Java int 参数与整数字面常量比较 | `< <= > >= == !=`；常量在左右两边均支持 |
| 负数、十六进制/八进制/二进制整数字面量 | 在 Java int 范围内解析；不做 long/浮点/命名字段常量求值 |
| String.length()、int[] / boolean[] / String[] 的 length | 直接参数或受支持局部别名；字符串用配置中的单个 ASCII 字符填充 |
| `int n; n=score; if(n>5)` 等直接赋值 | 支持；保留原始输入参数身份 |
| 临界值前、等于、后与修改前后不同常量 | 都考虑；同一输入合并前后两侧生成依据 |
| int 极值、零长度、负长度、过大长度 | 不溢出；允许 0；负长度跳过；超过资源或配置预算显式记录 |
| 多参数 | 非变化参数必须有显式基值并符合 Java 类型及声明约束；不默认填 0 |
| 数组元素 | 必须显式提供类型匹配的 fill 值，不把默认 0 当作业务合法值 |
| 外层 guard | 记录其条件/then/else 上下文；partial，路径可达性未证明 |
| 循环、switch/try 等复杂控制、跨分支别名合流 | unsupported，给出原因 |
| 算术关系、跨函数、反射、对象构造或字段状态 | unsupported；类声明有字段或继承时也保守拒绝，避免无 binding 的状态猜测 |
| 实例方法、构造器、可变参数、复杂参数类型 | unsupported |
| 方法签名变化、多个修改条件无法唯一配对 | unsupported / unhandled_changes，不猜配 |
| Java8+ 新语法、损坏 Java 或 diff | 错误 JSON + 非零退出码；不生成伪分析结果 |

没有跨文件 binding resolution：未知/复杂类型、命名常量和外部状态不求值。`String` 按 Java 常见隐式 java.lang.String 语法处理；同包另有同名 String 等跨文件遮蔽无法验证，应由配置审查或未来解析增强拒绝。本模块不宣称已解决任意 Java 项目的符号绑定。

## 预算与状态

默认最多 32 个候选，单长度上限 1024；允许配置范围分别为 0..1000、0..100000。不是对多个条件取笛卡尔积，只逐个变化关联参数。`generation.events` 记录每次跳过/截断的规则、侧别、边界、偏移和原因；truncated_attempts 是尝试数而非声称唯一未生成输入数。max_candidates=0 会记录全部截断。

support_status 表示局部条件分析能力；即使 supported，也可能因缺少其他参数基值或预算而没有候选，须同时看 generation.status/events。错误产物 `a.error.v1` 不属于 B 可执行的输入。

## 与 B、C 的边界

`interfaces/a_contract.py` 做 v1 消费端的版本、形状、参数顺序/类型和无 oracle 检查，不是通用 JSON Schema 引擎。`interfaces/mock_b.py` 只产生 MOCK_ONLY，run_kind=mock、statistics_eligible=false、oracle=not_evaluated、reduction=not_implemented。它不编译或运行目标。

B 接收完整 analysis.json，读取 candidates 的方法和有序 arguments，先核对 sources 的 SHA256 与其要执行的 before/patch，再用 B 自有配置持有参考版、隔离执行、判断 oracle、缩减反例。B 不应只根据 A 的 supported 决定统计资格。C 维护真实配置、批量执行和复查统计，必须排除 teaching、mock、尚未执行和 oracle 不可靠结果；这些模块本阶段没有实现。

每次输出新目录，包含输入哈希、A 代码/适配器哈希和解析证据；编译缓存只在 `work/a-build`，不覆盖作者 build 或旧 reproduction。已知首次 JLS8 适配失败的日志也保留，用于说明库版本兼容性修正。
