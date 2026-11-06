# CHANGELOG

## 3.0.3.1 — 修复实际平台运行时 AttributeError

- 新账户项目的实测 context 已包含非空 VTU 本地完整路径；输入 Resource 映射在这次执行中成功。
- PythonAdapter 已成功生成本次 `beam_validation_report.zip`（5,737 字节），但返回输出时因基类缺失 `_temp_relative_path` 而 `status: failed`。
- 移除对该未提供方法的依赖，使用 `Path.resolve().relative_to(sys_main_dir/temp)` 生成平台要求的 `projectId/taskId/beam_validation_report.zip`。
- 显式检查报告必须位于 `Client/temp` 下，防止上传路径逃逸。
- 回归测试中的模拟 BasePluginAdapter **故意不提供** `_temp_relative_path`，避免此前测试掩盖平台缺失方法。
- 分析核心计算逻辑未更改；平台输出资源注册仍需执行后验证。

## 3.0.3.1 — 双包最终整理与回归检测

- 复核 v3.0.2.0 源码包与注册包，确认两份 ZIP CRC 正常、注册 XML 位于 ZIP 根目录。
- 核对炎核 CAX 教程第 104、105、135、137、141、146 页；保留已验证的 XML 字段拼写和官方模板写法。
- 改进 `input_resolver.py`：显式相对路径必须匹配对应目录后缀；禁止仅凭同名文件误选另一个网格。
- 解析空 `filepath` 时报告具体 Resource → PythonAdapter 映射问题，不假装已经下载成功。
- `BEAM_VERIFIER_INPUT_FILE` 仅用于开发者显式指定**绝对路径**的可控排错；不自动选文件。
- 新增 `tools/diagnose_context.py`，只读查看最新 context/result、插件目录与过期报告文件。
- 新增 PythonAdapter 模拟环境契约测试和输入冲突回归测试。
- 统一插件 XML 与分析模块版本号为 `3.0.3.1`，不改动核心统计公式。
- 清理历史 README 中用户电脑的实际路径示例，便于提交团队仓库。
- **已知未解决**：实际平台 `inParam.inputParam.filepath=""`；正式资源回填、实际 32 MB VTU、服务器端兼容性需要进一步验证。

## 3.0.2.0 — 源码包与输入解析

- 添加 Git 仓库结构、构建器、测试和输入解析。
- 防止平台空输入时自动猜测钢梁网格；保留环境变量显式调试入口。

## 3.0.1.0 — CommonAPI 试验映射

- 新建独立 `BeamResultVerifierCommonTest` 插件/目录，避免覆盖旧插件。

## 3.0.0 — 分析核心

- 支持单 ASCII VTU、多 VTU ZIP，位移/应力统计、网格对比及报告输出。
- 不执行有限元求解，不提供物理正确性或安全性认证。
