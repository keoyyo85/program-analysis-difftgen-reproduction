# 真实补丁纳入规则与筛选记录

本模块分析 Java7 语法、单文件、签名未变的静态方法。仅支持 int/长度与整数字面量比较、顺序直接别名；每方法唯一修改条件。复杂调用、字段/继承、对象状态、循环、跨分支赋值等保守拒绝。**本次按既有实现范围筛选，规则在此归档，不因某个样例改判定。**

纳入必须保存完整生产源码前后版本、固定提交、原始路径、完整 diff、字节 SHA256、标签依据与许可；不能截取/改写函数冒充原项目。仅生产修复标签不等于错误候选标签，也不等于安全漏洞/CVE。教学项目独立；A 的真实来源适配也不是检出实验。

生成器只接收 before/patch/diff 和白名单配置。不读取测试答案或独立正确参考版本。后续 B 自行准备 reference、验证语义与执行隔离。上游提交元数据可能列出测试 diff，但这些不作为输入生成规则或预期答案。

## 本次有界筛选（2026-10-31）

| 来源/固定修复提交 | 来源标签依据 | 筛选决定 |
|---|---|---|
| 本地 DiffTGen Lang_51/Nopol，作者 cb16dfda75a5e5cca7f3e20aad7257e89f619427 | 作者历史材料标 overfitting；当前基线有独立回放 | 保留 unsupported：switch/字符/null，不注入已知反例 |
| TheAlgorithms/Java dda712c0c7a77f80390dfd8caab14fb1a2480225；父 2b3e82fd4c76a5b9475521154f65baa86e24250c；Dynamic Programming/Fibonacci.java | 提交标题 bugfix #708 | 排除：fibMemo 的 n<=2→n<=1 虽有临界值，但递归/Map 状态；fibBotUp 循环与局部归纳变量 |
| TheAlgorithms/Java ef61ee8920d3db606d94160af4307f5d1a80459f；父 af9aad308151ffeda699acdabed09a7e90e194a6；src/main/java/com/thealgorithms/maths/SumOfSquares.java | 提交标题 reject negative input #7543 | 排除：新增 guard、抛异常对象及 isPerfectSquare 调用，不是本版唯一既有比较替换 |
| TheAlgorithms/Java 55f551b17bd0c48b7cb1ba7ecfb7092803c7a150；父 171bdc5cb06df69d9070d5ed1f95a3544a4276e9；src/main/java/com/thealgorithms/searches/ExponentialSearch.java | 提交标题 missing boundary elements #7556 | 排除：泛型实例、跨函数调用、循环、改动返回表达式 |

来源仓库 https://github.com/TheAlgorithms/Java ，提交可用 `/commit/<上述SHA>` 追溯。查询还返回了若干 feature/refactor 项，未当作修复样例纳入。

GitHub 公开 REST API 随后返回 `API rate limit exceeded`；已停止该端点操作，没有切换身份/IP/凭据或替代下载路径绕过限流。未取得并归档上述项目完整源码对，因此它们只是**排除线索，不是已适配或已执行的真实样例**。网络响应/筛选证据另保存在 outputs/a/handoff/source-screening.json。

本轮尚未取得符合全部规则的真实正例，不能声称真实样例适配已完成。已有可运行真实负例 Lang_51；正例取得完整可追溯输入并通过 A 内容验收前不纳入。暂不扩大数据集、放宽规则或把方法切片/教学例改名为真实样例。此项列为 A 待补；不依赖 B 才能补齐。
