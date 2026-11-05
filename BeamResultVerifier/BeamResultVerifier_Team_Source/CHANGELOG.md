# 更新记录

## 3.0.2.0 — 小组源码版 / 输入诊断
- 基于实际上传的 V3 源码整理 Git 仓库可用结构，不改动原有 `beam_analyzer.py` 计算逻辑。
- 新增 `input_resolver.py`：解析嵌套参数、资源 `slot.name`、绝对及相对路径，约束在客户端临时目录和当前项目缓存内搜索。
- 出现多个同名 VTU 时拒绝猜测；收到空 `filepath` 时明确指出 CFF 资源参数尚未传入。
- 支持**显式指定** `BEAM_VERIFIER_INPUT_FILE` 进行本机排错，不作为正式自动化闭环。
- 新增单元测试、独立构建脚本、`.gitignore` 和 A6 诊断手册。
- XML 映射沿用 `BeamResultVerifierCommonTest` 测试插件，版本提高到 3.0.2.0。
- 不宣称解决平台空参数的原因，也不宣称报告回填已经通过平台验收。

## 3.0.1.0 — CommonAPI 测试插件
- 独立注册名称与 `BeamResultVerifierCommonTest` API 映射。
- 保留旧插件，不覆盖原实现。

## 3.0.0 — VTU 核心分析
- 支持单个 ASCII VTU 或含多组 VTU 的 ZIP。
- 位移/应力分量统计，网格比较，HTML/CSV/JSON/SVG/ZIP 报告。
- 可选理论梁参考对比及显式应力分量顺序。
- 不进行求解；不提供物理正确性或结构安全保证。
