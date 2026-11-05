# BeamResultVerifier — 钢梁 VTU 结果自动分析插件

> 小组仓库源码版 | 插件包版本 **3.0.2.0** | 适配目标：OpenCAEHub / 炎核 CAX Client 2.0.14

这是为“国创杯”钢梁仿真流程准备的后处理工具。它**不重新求解**，而是对现有 VTU 结果执行数据检查、位移/应力统计、网格尺寸比较，并生成便于展示的报告 ZIP。

## 目前真实进度（请先读）

- **已实现**：本地 Python 运行 VTU/ZIP 分析，生成 `analysis_report.html`、`metrics.csv`、`comparison.csv`、`validation.json`、`displacement_chart.svg`、`HOW_TO_READ.txt`、`beam_validation_report.zip`。
- **已进入**：炎核平台 PythonAdapter 的 `execute`，但平台传入的 `inParam.inputParam.filepath` 是空字符串 `""`。
- **尚未验证通过**：当前平台 A6/A7 对已选择 VTU 资源的自动下载/路径传递和输出回填。旧报告文件存在不代表本次成功。
- **本次源码更新**：新增 `input_resolver.py`，支持嵌套资源值、绝对路径、相对路径、唯一文件名匹配；当平台传空字符串时给出准确报错。可通过显式本地路径做诊断，**不会自行选定 10mm/15mm 网格**。
- **请勿误解**：代码无法从空字符串推导用户在 UI 中选中的资源。若 A6 仍返回空字符串，需要核对 CFF API 参数模板 / 资源传递机制。

## 目录结构

```text
BeamResultVerifier_Team_Source/
├── README.md                      本说明
├── PluginConfig.xml               平台注册 XML（CommonAPI 测试接口）
├── beam_analyzer.py               V3 分析核心，原样保留
├── beam_verifier_adapter.py       平台 PythonAdapter 入口
├── input_resolver.py              新增：可靠输入路径解析
├── build_plugin.py                生成可注册 ZIP
├── requirements.txt               依赖说明
├── example_beam_config.json       示例配置（数值为示例，必须核对工况）
├── CHANGELOG.md
├── .gitignore
├── docs/
│   ├── PLATFORM_A6_TROUBLESHOOTING.md
│   └── ORIGINAL_V3_README.md
└── tests/                         标准库 unittest
```

## 1. 快速本地运行（Windows）

需要 Python 3.11 或更高版本；分析核心只用 Python 标准库。

在源码目录打开 PowerShell，运行：

```powershell
python --version
python beam_analyzer.py --input "C:\实际路径\ncti_vtu_subcase1.vtu" --output-dir ".\beam_report"
```

对比两套网格时，先把两份 `.vtu` 按目录 `10mm/`、`15mm/` 放入**同一个输入 ZIP**（ZIP 内需包含实际 VTU 文件），然后运行：

```powershell
python beam_analyzer.py --input "C:\实际路径\beam_cases.zip" --output-dir ".\beam_report"
```

可选的参考配置：

```powershell
python beam_analyzer.py --input "C:\实际路径\beam_cases.zip" --output-dir ".\beam_report" --config example_beam_config.json
```

`example_beam_config.json` 中的材料参数、荷载、跨度、单位等是**示例/待核对假设**；实际竞赛报告必须以求解 INP、计算工况和队友确认的信息为准。

## 2. 在小组 Git 仓库中使用

将本源码 ZIP **解压**，把这个目录放入小组仓库（推荐 `tools/BeamResultVerifier/`），不要仅把压缩包作为无法审阅的单一文件提交。

建议操作：

```powershell
git add tools/BeamResultVerifier
git commit -m "Add BeamResultVerifier VTU analysis source and tests"
```

`.gitignore` 默认忽略 `*.vtu`、自动生成的报告、临时目录和 `dist/`，防止误提交大型仿真数据。是否采用开源许可证由小组决定；本包不替小组预设许可协议。

## 3. 运行测试

```powershell
python -m unittest discover -s tests -v
```

测试不会访问炎核平台、不会运行有限元求解器，也不会上传资源。用的是程序生成的小型合成 VTU。

## 4. 构建「插件注册 ZIP」

```powershell
python build_plugin.py
```

生成：

```text
dist/BeamResultVerifierCommonTest-3.0.2.0-REGISTER.zip
```

**注意**：仓库源码包与注册 ZIP 是两种产物。注册 ZIP 根目录直接包含 `PluginConfig.xml`，不要将整个源码目录压缩后直接作为注册包。

本 XML **保留当前测试 API 的映射**：

| 项目 | 值 |
|---|---|
| Name | `BeamResultVerifierCommonTest` |
| ModuleFullName | `Postprocessing.PostprocessingIO` |
| APIName | `BeamResultVerifierCommonTest` |
| LogicCommand | `beamResultVerify` |
| AppType | `PythonAdapter` |
| AppPath | `beam_verifier_adapter.py` |
| CFF 现有 API 命令 | `CommonAPI.Postprocessing.BeamResultVerifier` |
| 入参 | `inputParam.filepath`：Resource |
| 出参 | `outputParam.filepath`：Resource |

平台实际调用、映射和资源路径仍须在安装环境中验证。不要删除已经可用的官方 ParaView 或旧版插件。

## 5. A6/A7 输入为空时如何定位

本次平台上下文实际表现（省略与个人设备有关的路径）：

```json
{
  "inParam": {"inputParam": {"filepath": ""}},
  "logic_command": "beamResultVerify",
  "outParam": {"outputParam": {"filepath": ".../beam_validation_report.zip"}}
}
```

这代表 **插件没有收到输入文件路径**；不等于 VTU 从硬盘上消失。平台的资源库中可能仍有 VTU。

可用以下 PowerShell 直接本地验证算法（这是优先推荐的做法）：

```powershell
python beam_analyzer.py --input "C:\找到的准确VTU路径\ncti_vtu_subcase1.vtu" --output-dir ".\beam_report"
```

作为开发诊断，也可由**显式设置的环境变量** `BEAM_VERIFIER_INPUT_FILE` 指定输入；但它必须由启动插件的进程继承，且不应作为最终平台自动化集成方案。不要把本机路径或个人 UUID 提交到仓库。

详见 `docs/PLATFORM_A6_TROUBLESHOOTING.md`。

## 6. 科学结论的边界

- VTU 可以支持数值场结构检查、最大位移提取、不同网格结果差异观察。
- **不能单凭 VTU 证明**载荷、约束、材料参数、单位、收敛情况、力学正确性或结构安全。
- 未提供应力六分量顺序时，不将第 1 分量当作 von Mises；只有明确输入分量顺序，才能推算 von Mises。
- 两组网格结果接近是**网格敏感性证据之一**，并不等于完成严格的网格收敛研究。

## 7. 版本说明与来源

- 插件注册版本：`3.0.2.0`（本源码整理/输入路径诊断更新）。
- `beam_analyzer.py` 保留上传 V3 注册包中的分析核心，模块常量 `VERSION=3.0.0` 代表其算法版本，并非注册包版本。
- 平台 `open_cae_plugin` 模块由炎核运行环境提供，未复制、未伪造此依赖。
- 相关历史文档保存在 `docs/ORIGINAL_V3_README.md`，便于小组追踪功能来源。
