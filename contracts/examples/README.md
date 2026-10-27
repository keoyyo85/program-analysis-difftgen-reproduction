# v1 JSON 示例

- `a-request.json`：可运行的教学请求，文件路径相对此目录解析。生成器只获得 before/patch/diff 及允许配置。
- `a-analysis.json`：从 `outputs/a/acceptance-20261027-205800/teaching/analysis.json` 原样复制的实测 A 输出示例，含源文件/实现哈希、条件位置、关联依据、3 个候选及双侧 provenance。
- `b-mock.json`：同一轮的模拟接口输出；所有版本均是 MOCK_ONLY。不是实际 Java 返回值，oracle 未评估，不进入真实统计。

输出的绝对源码路径属于本次实际运行环境，供证据溯源。新机器请运行 a-request.json 重新生成产物，不要直接执行示例里的旧绝对路径。
