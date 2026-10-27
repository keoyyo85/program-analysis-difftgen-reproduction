# 续轮前配置核查

核查对象是首轮 `runs/20261027-175712`，未覆盖其文件。

## 首轮两个测试的含义

`test/0/0/TestClass.java` 第 222–225 行：test007 调用 `BooleanUtils.toBoolean("off")`。
第 1310–1313 行：test039 调用 `BooleanUtils.toBoolean("X2f")`。
二者调用同一个重载 `public static boolean toBoolean(String)`。三版本 `rslt` 的 `TYPE:Boolean / VALUE:false` 是该方法的真实返回值，而不是比较器的判定。

`LoadProbe.java` 通过反射直接调用方法，正常返回时输出 RETURN，异常则单独输出 THREW，不做 false 转换。首轮 plain 和 output-instrumented 的三版本各自回放这两个输入，全部 RETURN=false，无 THREW。

## 源码关键差异

在字符串长度为 3 且首字符不是小写 y 时：

- bug 第 677 行继续检查 `ch == 'Y'`；不满足时落入 case 4。
- patch 同一行改为 `str!=null`；由于上面已排除 null，在此处总为真。方法仍以第二、三字符是否为 e/s 返回结果。
- fix 保留 `ch == 'Y'` 检查，并在 case 3 的最后（第 682 行）`return false;`，避免落入 case 4。

完整三版本源文件在 sample/{bug,patch,fix}/BooleanUtils.java；来源及组装方式沿用 sample/SOURCES.md。首轮保存的 generated/{bug,patch,fix}/BooleanUtils.java 与这些输入对应。没有改动参考实现。

## 编译和实际加载

首轮 compile-bug / compile-patch / compile-fix 均 exit 0。`class-hashes.json` 保存三个原始 class 及三个输出插桩 class 的 SHA256，各版本不同。`bytecode-*.stdout.log` 保存 javap 反汇编结果。

`load-*-plain.stdout.log` 和 `load-*-output-instrumented.stdout.log` 记录 `-verbose:class`、CodeSource、class resource 及直接返回值。classpath 各自版本目录位于 faulty dependency jar 之前，实际加载来源与该版本目录一致；helper 目录不包含 BooleanUtils。没有从 dependency jar 中误加载同一个 bug class。

这是对首轮产物的独立重放核验，不能声称首轮进程当时已开启 class loading trace。后续 audit/replay 对实际测试回放也记录 class loading trace。

作者输出插桩在 toBoolean 包装方法中 catch(Throwable) 后打印异常并 rethrow（首轮 bug/instru0/BooleanUtils.java 第 1068–1071 行），正常情况最后返回拆箱的真实结果。筛选 TestClass.main 会 catch(Throwable) 以继续下个输入，但异常观察值在此之前已由包装方法记录，不会改写为 false。

续轮初次独立 JUnit 验证日志实际报告 4.12：`lib/*` 的顺序使 EvoSuite jar 内附 JUnit 先于单独的 junit-4.11.jar。这与目标 BooleanUtils 三版本混用是两件事，后者已由 CodeSource 和哈希排除。最终 audit/replay 显式优先 junit-4.11.jar 与 hamcrest-all-1.3.jar，并保存实际加载轨迹；若两种 JUnit 版本结果一致，才将这项环境差异记为不影响本次区分结论。作者差分流水线的 Ant TestClass.main 比较不依赖 JUnit runner。

## delta / oracle 位置

逐字符校验见 positions.json：bug 与 patch 第 677 行、缩进 16 个空格；fix 第 624 行是该方法 javadoc 起始、缩进 4 个空格，第 649 行是 toBoolean(String) 声明。与实际 delta.txt / oracle.txt 一致。

## 作者是否认定候选补丁错误

有直接作者材料，不能仅依据 Nopol 产出的补丁一概判断：

- 作者 `expt0/testcase/Lang_51_nopol/patch/BooleanUtils.java` 第 699 行对同一 `if (str!=null)` 标注 `//Overfitting`。
- 作者 `expt0/testcase/Lang_51_nopol/testcase/DiffTGen0Test.java` 第 1869 行起的历史 test078 使用 `@es` 并 assertFalse；作者 README 将 DiffTGen0Test 定义为 regression-indicative。

历史测试只作为作者判断的证据，不计入本轮自动检出成果，也不注入本轮搜索。新增轮次的随机搜索不使用上述历史输入。

## 种子接口

原版 DiffTGen Main 没有 seed 参数。随附 EvoSuite 1.0.2 的 Properties 会读取 JVM 同名 system property，Randomness 从 RANDOM_SEED 初始化；字节码证据为 logs/seed-bytecode.txt。

seed-probe.stdout.log 实测 `-Drandom_seed=2026102701` 得到 CONFIGURED_RANDOM_SEED 和 ACTUAL_RANDOM_SEED 均为 2026102701。新增三次通过 JAVA_TOOL_OPTIONS 向 EvoSuite master/client 传递属性，并请求统计输出 Random_Seed，以每轮统计文件报告值为实际种子证据，不仅记录请求值。作者 Java 源码和 EvoSuite jar 无需修改。

## 日志可见性边界

驱动脚本保存顶层编译、DiffTGen 进程和独立回放的 stdout/stderr、退出码和耗时。作者原版 `src/util/CommandExecutor.java` 只 redirectOutput(output_f)，没有消费或导出子进程 stderr。因此原版嵌套 EvoSuite/Ant 调用的 rslt 是 stdout，无法声称包含这些子进程全部 stderr；本轮没有修改作者日志实现或在三轮之间改变工具代码。独立回放由外层 subprocess 分别保存 stdout/stderr，可补充真实执行证据，但不能追溯恢复原搜索子进程丢失的 stderr。
