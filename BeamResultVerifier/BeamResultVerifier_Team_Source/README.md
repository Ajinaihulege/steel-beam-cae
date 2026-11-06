# BeamResultVerifier — 钢梁 VTU 结果自动分析插件

**小组仓库最终源码整理版 v3.0.3.1**  
目标平台：炎核 CAX / OpenCAEHub Client 2.0.14  
语言：Python 3.11+，核心分析只使用标准库；平台适配器需要平台自带 `open_cae_plugin`。

> 版本号 `3.0.3.1` 表示代码包与注册包一致，并不代表已通过炎核平台完整验收。

## 1. 当前状态（提交仓库前先读）

| 能力 | 验证情况 |
|---|---|
| 单个 ASCII VTU 的位移/应力统计 | 本地合成样本测试通过 |
| 多 VTU ZIP、网格结果对比 | 本地合成样本测试通过 |
| HTML/CSV/JSON/SVG/ZIP 报告 | 本地合成样本测试通过 |
| PythonAdapter 读取 VTU、生成 ZIP | 已在实际炎核运行中确认（11 月 6 日） |
| 炎核 CFF → PythonAdapter 的 Resource 输入 | **新账户已成功**，context 中有 VTU 完整路径 |
| PythonAdapter 输出路径转换 | **已修复 `_temp_relative_path` 不存在问题，待平台重测** |
| 炎核中的自动输出资源回填 | **尚未通过端到端验证** |
| 队友实际 32 MB VTU 的当前发布版回归测试 | 未包含在本包，尚需本机实测 |

**已经看到的实际错误上下文**（用户设备路径省略）：

```json
{
  "inParam": {"inputParam": {"filepath": ""}},
  "logic_command": "beamResultVerify",
  "outParam": {"outputParam": {"filepath": ".../beam_validation_report.zip"}}
}
```

上面是**旧账户/旧项目的历史故障**，不是当前新账户的最新状态。2026 年 11 月 6 日的新账户执行已经成功将 VTU 文件路径传给 PythonAdapter，且生成了 `beam_validation_report.zip`，但在最后调用 `self._temp_relative_path(...)` 时报错：`AttributeError: ... has no attribute '_temp_relative_path'`。**v3.0.3.1 已改用 Python 标准库自行转换 `Client/temp` 相对路径**，仍需注册后完成实际平台输出回填验收。

## 2. 源码结构

```text
BeamResultVerifier_Team_Source/
├── README.md
├── CHANGELOG.md
├── PluginConfig.xml                 自研插件注册配置
├── beam_analyzer.py                 核心分析（单 VTU 或多 VTU ZIP）
├── beam_verifier_adapter.py         平台 PythonAdapter
├── input_resolver.py                受限路径解析，避免误选网格
├── build_plugin.py                  生成可安装注册 ZIP
├── example_beam_config.json         工况示例（非已验证参数）
├── requirements.txt
├── tools/
│   └── diagnose_context.py         只读检测 context/result/报告时间
├── tests/                            单元及适配层模拟测试
└── docs/
    ├── PLATFORM_A6_TROUBLESHOOTING.md
    └── ORIGINAL_V3_README.md
```

## 3. 本地直接运行（建议先验证实际 VTU）

在解压出来的源码目录打开 PowerShell：

```powershell
python --version
python .\beam_analyzer.py --input "C:\TeamData\ncti_vtu_subcase1.vtu" --output-dir ".\beam_report"
```

把 `C:\TeamData\...` 换成你的**实际文件路径**。这会在 `beam_report` 中生成：

- `analysis_report.html` — 可用浏览器打开的分析报告
- `metrics.csv`、`comparison.csv` — 数值提取和网格对比
- `validation.json` — 数据检查及统计结果
- `displacement_chart.svg` — 位移可视化图表
- `HOW_TO_READ.txt`
- `beam_validation_report.zip` — 包含上述报告文件的集合

对比 10 mm/15 mm 时，将两份 VTU 放进一个 ZIP，按 `10mm/...` 和 `15mm/...` 组织路径：

```powershell
python .\beam_analyzer.py --input "C:\TeamData\beam_cases.zip" --output-dir ".\beam_report"
```

仅支持 ASCII 单 Piece VTU，若文件为 appended/binary 或多 Piece，应在 ParaView 中转换/合并后再分析。`example_beam_config.json` 中的跨度、材料、载荷仅为待核对的示例值。

## 4. 单元测试与打包

```powershell
python -m unittest discover -s tests -v
python .\build_plugin.py
```

生成：

`dist/BeamResultVerifierCommonTest-3.0.3.1-REGISTER.zip`

**两种 ZIP 的区别**：源码 ZIP 用于解压后提交到小组 Git 仓库；`-REGISTER.zip` 用于首页 → 插件 → 插件注册，要求 ZIP 根目录直接包含 `PluginConfig.xml`。不要将整个源码 ZIP 当作注册包上传。

### 小组 Git 仓库推荐放置方式

解压本源码包，得到 `BeamResultVerifier_Team_Source` 目录，将它整体放入小组仓库的 `tools/` 下。然后运行：

```powershell
git add tools/BeamResultVerifier_Team_Source
git commit -m "Add BeamResultVerifier v3.0.3.1 source and diagnostics"
```

大文件 VTU 和运行报告默认不提交到 Git；本包没有捆绑真实的仿真数据，也没有替小组指定开源许可。

## 5. 炎核平台注册映射（测试 API）

这个注册 ZIP **对应以下 CFF API**，不是系统自带 A5 的 `showForm`：

| 字段 | 值 |
|---|---|
| CFF API 名称 | `BeamResultVerifierCommonTest` |
| CFF API 命令 | `CommonAPI.Postprocessing.BeamResultVerifier` |
| ModuleFullName | `Postprocessing.PostprocessingIO` |
| Plugin Name / Dir | `BeamResultVerifierCommonTest` / `Plugins/BeamResultVerifierCommonTest` |
| XML APIName | `BeamResultVerifierCommonTest` |
| LogicCommand | `beamResultVerify` |
| AppType / HasUI | `PythonAdapter` / `false` |
| 输入 | `inputParam.filepath`，resource，unbounded |
| 输出 | `outputParam.filepath`，resource，unbounded |

`PluginConfig.xml` 中仍采用官方教程给出的：

```xml
APIParameterTemlate="filepath=%filepath%"
APIOutParameterTemlate="filepath=%projectId%/%taskId%/beam_validation_report.zip"
```

注意 `Temlate` 是平台现有 XML 字段的历史拼写，并非本包打字错误。**教程提供了这种写法，但尚不能证明对当前自建 CFF 的嵌套输入参数能够正确展开。** 不要未经验证改成 `%inputParam.filepath%`。

## 6. 在新账户中的最小验证步骤

1. 将队友已经求解完成的 **ASCII VTU** 上传到新项目的资源池。
2. 创建上述 CFF 测试 API（若该账户尚无），保持输入输出 resource 类型一致。
3. 上传本注册 ZIP，完成插件扫描匹配。
4. 在单个测试容器中选 `BeamResultVerifierCommonTest` API，插件选 `Beam VTU Result Verifier - CommonAPI Test`。
5. 输入选择真实 VTU，输出先留空；只执行该容器。
6. 检查**本次新生成**的 `*_context.json`、`*_result.json`、ZIP 修改时间，以及是否可以从平台下载报告。

如果 `sys_plugin_dir` 仍显示 `Plugins/BeamResultVerifier`，而不是 `Plugins/BeamResultVerifierCommonTest`，先检查节点插件选择和本次上下文时间。不要拿旧文件误判当前插件版本。

## 7. 一键只读诊断

```powershell
python .\tools\diagnose_context.py "C:\实际目录\38_1464901257_context.json" --plugin-xml .\PluginConfig.xml
```

诊断工具不会运行/修改任务，只检查空参数、插件目录、result.json 状态及报告文件时间。详见 `docs/PLATFORM_A6_TROUBLESHOOTING.md`。

## 8. 结论边界

- VTU 数据可以支持数值场结构检查、最大位移/应力分量统计及网格结果敏感性评估。
- VTU **不能独立证明**材料、荷载、边界条件、单位、求解器收敛或结构安全。
- 六分量应力若没有真实分量顺序，不应把第 0 分量直接称作 von Mises。
- 两组网格的结果接近，并不等于完成严格的网格收敛研究。

**当前下一步关键点：在已传入完整 VTU 路径的新账户中升级注册 v3.0.3.1，检查最新 `result.json` 是否为 `status: success`，并验证 ZIP 是否成功回填至平台输出资源。**
