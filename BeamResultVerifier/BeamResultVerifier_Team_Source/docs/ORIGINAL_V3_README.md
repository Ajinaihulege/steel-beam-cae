# BeamResultVerifier V3 / 炎核 CAX 2.0.14 后处理自动验证插件

> 状态说明（请先看）：核心 Python 分析器已通过本地自动测试，PythonAdapter 在仿真上下文中模拟调用通过；
> **真实的炎核平台注册、资源池下载、结果回传尚未在你的机器验证**。
> 当前 `BeamResultVerifier-3.0.0.1-REGISTER-CANDIDATE.zip` 是**依据你现有 CFF 截图生成的候选安装包**，
> 如果平台校验 ModuleFullName / APIName 失败，须确认真实注册标识后重新打包。

教程依据：《炎核 CAX 高效智能重构平台介绍与入门实操教程》，重点第 52～55 页、94～105 页、
134～147 页、169～171 页。
赛题依据：《第二届国创杯—开放 CAE 仿真软件集成与验证》题目，尤其第 1～4 页。

## 1. 你现在卡在什么位置？

你已经在 CFF 货架中新建 API，并能在 A6 的任务栏选择它，**但 A6 的插件栏仍然是“请选择”**。
这说明：业务 API 已有，但还没有确认对应的 PythonAdapter 实现已经安装、加载、与 API 匹配。
**不要继续重复创建 API。**

这和把 VTU 放到资源池是不同操作：

- CFF API：定义 A6 做什么、需要什么输入、产生什么输出。
- 插件注册：把 Python 程序、PluginConfig.xml 安装到平台，让 A6 真正有可运行的实现。
- 资源池：放模型、VTU 和输出报告；不是安装 Python 代码的地方。

## 2. 已有 CFF API 参数要保持稳定

依据你的截图：

- API 名称：`BeamResultVerifier`
- API 命令：`CommandAPI.Postprocessing.BeamResultVerifier`
- 所属模块：`Postprocessing.PostprocessingIO`（UI 显示“后处理IO模块(PostprocessingIO)”）
- 入参参数组：`inputParam`
- 入参参数：`filepath`，类型 `resource`，显示类型 `unbounded`，参数值留空
- 出参参数组：`outputParam`
- 出参参数：`filepath`，类型 `resource`，显示类型 `unbounded`，参数值留空

**不要新增第二个输入参数**；V3 与现有的 API 签名兼容。
同一个 `filepath` 支持 `.vtu` 或 `.zip` 两种文件：单 VTU 计算一份报告；
ZIP 中多份 VTU 会比较多工况/不同网格。

## 3. 在 Windows 上继续操作（从这里开始）

### 3.1 解压源码包

建议放在一个纯英文路径：

`D:\BeamResultVerifier_V3\`

你应看到：

```
beam_analyzer.py              数据读取、指标计算和报告生成
beam_verifier_adapter.py      炎核 PythonAdapter 适配层
PluginConfig.xml.template     配置模板（不能直接上传）
build_plugin.py               打包工具
example_beam_config.json      可选的物理参数/单位示例
tests/test_analyzer.py        独立可运行测试
README.md / CHANGELOG.md / requirements.txt
```

Python 本地版本为 3.13 时也可以运行**核心脚本和打包命令**（只用标准库）。
炎核 2.0.14 的内置插件运行环境按手册要求是 Python 3.11；本地版本不等于平台运行版本。

### 3.2 本地测试（你之前已完成过 V2，可以略过这一轮）

在资源管理器打开 `D:\BeamResultVerifier_V3` 后点地址栏输入 `powershell` 回车，
然后执行：

```powershell
python .\tests\test_analyzer.py
```

应当看到 `OK` 或 `PASSED`，但这**不代表平台注册已成功**。

也可以用你原有队友 VTU 再试：

```powershell
python .\beam_analyzer.py --input "C:\TeamData\steel-beam-cae-main\10mm\cal\ncti_vtu\ncti_vtu_subcase1.vtu" --output-dir "C:\TeamData\beam_report_10mm_v3"
```

注意改成你的真实 VTU 路径；某些电脑的目录名可能不同。

### 3.3 一键生成“候选安装包”

在 V3 源码目录运行：

```powershell
python .\build_plugin.py
```

它将使用你之前截图里的“候选值”：

- ModuleFullName = `Postprocessing.PostprocessingIO`
- APIName = `BeamResultVerifier`
- LogicCommand = `beamResultVerify`
- APIVersion = `1.0.0.1`

生成 `BeamResultVerifier-3.0.0.1-REGISTER-CANDIDATE.zip`。

**这四个字段中的前三个是安装时可能需要核验的运行标识**，特别是 APIName 和 LogicCommand。
手册要求以目标平台注册记录为准；如果审核时出现“API 不存在/命令不匹配”，不能凭猜测反复新建 API。
应从 CFF 当前 API 记录或平台注册错误详情核对真实标识，然后重新运行：

```powershell
python .\build_plugin.py --module "真实ModuleFullName" --api "真实APIName" --logic "真实LogicCommand" --api-version "1.0.0.1"
```

参数 `--api-version` 也应匹配你 CFF API 实际版本。
生成安装 ZIP 后可以双击查看：**ZIP 顶层直接有 `PluginConfig.xml`**，不是套一层文件夹。

## 4. **平台插件注册入口：手册第 52 页明确给出**

1. 点击软件左上角的“首页”，回到平台首页。
2. 在首页导航栏进入**“插件”**。
3. 找到**“插件注册”**页面（不要进入 CFF 货架“新建 API”）。
4. 点击“添加”，选择 `BeamResultVerifier-3.0.0.1-REGISTER-CANDIDATE.zip`，也可拖进去。
5. 按手册向导依次点击“下一步”：进行 ZIP 内容审核、填写插件基本信息、确认。
6. 到**“已安装插件”**列表确认看到 `Beam VTU Result Verifier` 或 `BeamResultVerifier`。
7. 返回原来的 `liang` 项目，在 A6 的“插件”下拉框重新选择。
8. 如果列表没有刷新，先关闭项目页重开，再检查插件是否真的注册成功。

**若插件注册页面不存在或审核/权限拒绝：**记录弹窗原文，并向平台管理员确认权限；
不要把安装 ZIP 上传到资源池，也不要手动覆盖 `D:\OpenCAEHubPlugins` 下的现有软件文件。

## 5. A6 单容器验证（不要点全局）

把 A6 改成：

- 任务：已有的 `BeamResultVerifier`（不需要重建 API）。
- 输入 `filepath`：选择资源池中一份 `ncti_vtu_subcase1.vtu`。
- 插件：`Beam VTU Result Verifier`（成功注册后才出现）。
- 输出 `filepath`：不手动填死路径，执行后由插件返回。

只执行 A6：点击 A6 右上角 `≡` → “执行容器”。
在 A6 下方查看输出 `filepath`，应该指向 `beam_validation_report.zip`。
下载/解压压缩包后看到：

- `analysis_report.html`：带中文说明和英文字段/图表的可打印报告。
- `displacement_chart.svg`：位移对比条形图。
- `metrics.csv`：每份 VTU 的节点、单元、位移、应力分量摘要和 SHA256。
- `comparison.csv`：两两相邻网格位移/第一应力分量峰值差异。
- `validation.json`：所有完整指标、检查结论、异常解释。
- `HOW_TO_READ.txt`：简明使用方法。

两个/多个 VTU 一起比较时，**需要把它们放在同一个 ZIP 中，然后把该 ZIP 导入资源池作为一个 `filepath`**。
不需要修改 CFF 输入定义。注意 V3 不接受把 A5 的可视化窗口直接接到 A6；
应由求解/格式转换节点输出同一个 VTU，再分别连接 A5、A6。

## 6. V3 新增能力、含义与局限

| 功能 | 数值指标 | 能证明什么 |
|---|---|---|
| 解析 ASCII VTU | 节点、单元、位移向量、应力分量 | 数据结构是否可读取 |
| 结果质量检查 | NaN/Inf、网格类型、点数组维数 | 基础数值有效性 |
| 自动摘要 | 最大总位移、最大 |Uz|、P95 |Uz|、位移极值坐标 | 用于比较的可复核指标 |
| 网格差异 | 粗细网格最大 |Uz| 百分比变化 | 初步稳定性，不是完整收敛证明 |
| 应力分量 | 0～5 分量峰值，及变化 | 成分级结果，不自动等于 von Mises |
| 可选 Mises | 仅提供应力分量顺序后计算 | 避免静态数组分量误认 |
| 可选理论对标 | 简支梁 Euler-Bernoulli 理论挠度 | 与理想化理论值对照 |
| 报告可追溯 | SHA256、源文件名、配置、检查状态 | 可检查输入版本 |

**重要：**单凭 VTU 不能确认实际钢材 Q235B、泊松比、边界条件、受力总量或求解是否收敛；
需要另外核对 INP 和 CalculiX/原求解器日志。两网格位移变化很小不等于所有应力都收敛，
尤其是集中荷载点可能存在局部应力奇异性。V3 不输出工程安全认证。

### 单文件模式与多网格比较

A6 `filepath` 绑定单个 VTU，生成该文件的指标报告。
如果绑定一个 ZIP，程序会自动查找其中全部 `.vtu`，根据目录中的 `15mm/10mm` 等信息推测网格尺寸，
并在报告中按网格大小/单元数量比较。建议每个算例文件命名时标清网格大小和载荷。

为了让理论值与物理单位更加明确，建议队友在 ZIP 顶层加一个可选配置文件：
`beam_validation_config.json`（源码包附了 `example_beam_config.json`，修改后重命名）。
请核对其中材料、几何与载荷是否与最终 INP 一致；未核对前不要把理论对比写成验证结论。

单独本地运行时也可以用：

```powershell
python .\beam_analyzer.py --input "D:\CAX_Beam\all_cases.zip" --config .\example_beam_config.json --output-dir .\report_out
```

如果 `StaticStress` 的六个分量有**官方明确的顺序**，你可以在配置中加入：

```json
"stress_voigt_order": ["xx", "yy", "zz", "xy", "yz", "xz"]
```

注意这只是示范顺序，**不能在未知分量含义时直接套用**。没有可信顺序时，V3 只报告原始分量。

## 7. A6 的插件下拉框仍然为空时怎么查？

最先判断：插件注册向导中是否出现“成功”，并且“已安装插件”列表是否存在相应条目。

- 如果列表没有：你还没完成插件安装，不是 VTU 的问题。
- 如果 ZIP 审核失败：检查 `PluginConfig.xml` 顶层、Name、版本、`ModuleFullName`、`APIName`、`LogicCommand`。
- 如果“已安装插件”有但 A6 没有：确认你选择的 A6 API 是同一模块下的 `BeamResultVerifier`；
  关闭重新打开项目页，再查平台插件列表加载状态。
- 如果注册成功但执行时报找不到 `open_cae_plugin`：检查平台 Python3.11 环境及 `Plugins/base` 的 PYTHONPATH。
- 如果执行报输入不存在：检查 A6 `filepath` 是否是 `resource`，是否成功从资源池下载成真实文件路径。
- 如果绿色对勾但找不到报告：查看 A6 输出 `filepath`，任务输出 ZIP 是否存于 `%MainDir%temp`，
  `APIOutParameterTemlate` 与脚本输出文件名是否一致。
- 插件主日志：相对平台主安装目录的 `logs/plugin/plugin_wrapper.log`（手册第 145 页）。
- 流程调试：单独执行 A6（手册第 169 页），无需为了 A6 的问题重跑 A1～A4。

## 8. 用于比赛展示的边界

该插件属于“后处理分析 + OpenCAX PythonAdapter 软件集成”的自研功能，
可以计入接口设计、功能扩展、数值验证、流程复现等成果；**不是新的有限元求解器**。
正式比赛还需 A4 求解能跑通，或者证明另一条完整求解链路可复现。

提交时保存：源代码、注册成功截图、A6 执行截图、VTU 输入、输出报告 ZIP、
日志、流程模板和可重复运行的操作说明。

## 9. GitHub 更新

在你们原有 GitHub 仓库中，建议建 `BeamResultVerifier/` 目录提交源代码和 `tests/`，
不要只把候选安装 ZIP 放进代码仓库。建议提交信息：

`feat: improve BeamResultVerifier VTU diagnostics and reports (v3)`

旧 V2 可以保留历史提交，不需要覆盖它或删除记录。将 GitHub README 中的“平台注册”状态
标明为 `Pending`，直到你亲自完成真实平台注册和 A6 成功执行。
