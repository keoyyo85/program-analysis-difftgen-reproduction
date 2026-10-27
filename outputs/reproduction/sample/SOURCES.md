# Lang_51 / Nopol 的来源与组装

本例是作者真实实验样例，不是自建教学例。

- DiffTGen commit: `cb16dfda75a5e5cca7f3e20aad7257e89f619427`。
- `examples/lang51nopol_delta0.txt`：两版本 `BooleanUtils.java:677,16`。
- `examples/lang51nopol_oracle.txt`：正确版本方法 `BooleanUtils.java:624,4`。
- `expt0/testcase/Lang_51_nopol`：有错误版、候选版的历史测试插桩源码及作者历史测试；本轮未复用历史测试冒充生成结果。
- 作者明确引用的补丁库：<https://github.com/Spirals-Team/defects4j-repair/tree/master/results/2015-august>。
- 其 `Lang/51/NopolC/results.json`（本地保存为 `nopolc-results.json`）记录 CONDITIONAL 补丁 `str!=null`，第 677 行；与作者候选版一致。
- Defects4J `active-bugs.csv` 的第 51 项：bug revision `9da40ba6b5bcc7b6071fa7fe11eaeb1b97e53d81`，fixed revision `796b898281af571a510d96487dcd95699ac1e435`，LANG-365。
- 正确版本单文件原样来自 <https://raw.githubusercontent.com/apache/commons-lang/796b898281af571a510d96487dcd95699ac1e435/src/java/org/apache/commons/lang/BooleanUtils.java>。
- `Lang51.src.patch` 原样来自 <https://raw.githubusercontent.com/rjust/defects4j/master/framework/projects/Lang/patches/51.src.patch>。该文件方向是从正确版构造错误版：移除 case 3 末尾 `return false;`。
- `driver.py` 对正确版应用这一精确单行变更得到 bug，再把唯一的 `if (ch == 'Y')` 条件改为作者 Nopol 条件得到 patch。没有重写方法、截取方法或修改 oracle。
- 依赖使用 Maven Central `commons-lang:commons-lang:2.3`，仅下载约 239 KB 二进制及约 313 KB 源码包以检查依赖。依赖 jar 中的 BooleanUtils 由本例编译的错误版覆盖，形成作者要求的单一 faulty dependency jar。其他 Commons Lang 类保持 Maven 包原样。

因此这是选定类级的作者样例复现，不是完整 Defects4J checkout，也不运行完整 Commons Lang 原测试集。它足以检验该方法的作者多版本差分流水线，不能推广为全项目验证。

原仓库材料完整性：examples 只有配置；expt0 有多组历史结果/插桩源码及 HDRepair 补丁；expt1 有五程序修复日志、两补丁历史测试；lib 有 EvoSuite 1.0.2、JUnit 4.11、JDT 等。选中样例的正确参考源码和基础依赖需额外补齐。
