# 工字钢梁 VTU 自动验证插件 · V1（OpenCAEHub / 炎核 CAX）

**当前进度：核心分析程序已在队友的真实 `steel-beam-cae-main.zip` 上运行通过；平台插件注册与执行尚待你电脑上的联调。**

## 这个程序做什么？

输入队友已有的整个 ZIP（里面需要包含 `15mm` 和 `10mm` 目录中的各一份 `.vtu` 文件），自动输出：

- `analysis_report.html`：中文网页分析报告，可用浏览器打开；
- `metrics.csv`：Excel 也能打开的对比数据表；
- `validation.json`：供后续自动化流程读取的数值与检查结果；
- `beam_validation_report.zip`：把上面三个文件打包，便于平台资源池统一存储。

程序会检查：VTU 是否可以读取、位移数据是否包含非法数、四面体单元类型、两组网格位移敏感性，并计算简化梁理论的参考挠度。
**它不会重新求解，也无法仅凭 VTU 证明材料、约束、载荷、求解器残差是否正确。**
注意：`StaticStress` 有 6 个未命名的分量，程序只报告第一分量（component 0）的峰值，**绝不当作 Mises 应力**。

## 0. 先在自己电脑测试，不用打开炎核

在 Windows 解压此源码包到英文路径，例如 `D:\BeamResultVerifierV1`，安装 Python 3.11 或使用已有 Python 3.11。

PowerShell 或 CMD 进入文件夹后运行：

```bat
py -3.11 beam_analyzer.py --team-zip "D:\CAX_Beam\steel-beam-cae-main.zip" --output-dir "D:\CAX_Beam\beam_reports"
```

将路径改成你自己电脑上的真实 ZIP 路径即可。
如果原 ZIP 不存在，也可以单独指定两份 VTU：

```bat
py -3.11 beam_analyzer.py --vtu15 "D:\CAX_Beam\15mm.vtu" --vtu10 "D:\CAX_Beam\10mm.vtu" --output-dir "D:\CAX_Beam\beam_reports"
```

成功后直接双击 `beam_reports\analysis_report.html`。不需要安装 NumPy、VTK 或 ParaView 来运行本分析器。
如 VTU 是 binary/appended 格式，V1 会提示暂不支持；目前队友原文件的 ASCII 格式支持并已测试。

## 1. 集成前先在炎核平台创建自己的 API（不是资源池导入）

你之前打开过 `CFF货架体系` 对话框，里面有「当前API」「新建API」。

在一个新任务容器里点任务右侧三角 →「新建API」，填写：

- 建议显示名称：`钢梁自动验证`
- 所属模块：后处理（以平台实际显示为准）
- 建议命令：`CommandAPI.Postprocessing.BeamResultVerify`（如果平台要求不同格式，以平台为准）
- 输入参数组：inputParam，添加 `filepath`，类型为文件资源/uri，必填
- 输出参数组：outputParam，添加 `filepath`，类型为文件资源/uri

**不要在「资源池→导入资源」里上传插件 ZIP！** 资源池是输入/输出数据文件的存放处，不是插件注册入口。

创建 API 后，需要确认该 API 在你平台中的**真实** `ModuleFullName` 和 `APIName`。
这两个值必须与后台注册数据完全一致，不可只凭显示名称猜测。
本文档不能提前知道你平台实际生成的值。

## 2. 打包插件（完成上一步后）

进入源码所在文件夹，确认平台中新 API 的准确 ModuleFullName 和 APIName：

```bat
py -3.11 build_plugin.py --module "这里填真实ModuleFullName" --api "这里填真实APIName"
```

得到 `BeamResultVerifier-1.0.0.1.zip`，ZIP 根目录直接有 `PluginConfig.xml`。

根据炎核官方教程通过平台**插件管理/插件注册入口**上传此 ZIP，登记该 API 的实现。
实际菜单位置、权限和版本因平台部署而异，应以你现在 2.0.14 的界面为准。
如果提示 ModuleFullName/APIName 不存在，回到第 1 步核对，不能随便改源码绕过。

平台环境还必须能导入 `open_cae_plugin.py`（通常由平台 `Plugins/base` 提供）。

## 3. 在项目里配置 A6

- 建议额外创建 A6，而不是覆盖已经能用的 A5。
- A6 任务选择刚新建的「钢梁自动验证」。
- A6 的插件选择「Beam VTU Result Verifier」。
- 输入 `filepath`：选择资源池中上传的**队友完整原始 ZIP**（不是单独的 VTU）。
- 执行 A6 容器。
- 输出 `filepath`：应返回 `beam_validation_report.zip`，下载解压查看 HTML/CSV/JSON。

V1 的文件接口采用官方 CSV 汇总插件同样的单输入 `filepath`、单输出 `filepath` 模式。
后续可升级为两个 VTU 作为两个独立输入，再通过平台数据线接到上游。

## 4. 为什么这里没有直接给一个「上传即用」插件 ZIP？

当前尚不知道你账号下新建 API 的 **ModuleFullName 和 APIName**；
这两个字段在 `PluginConfig.xml` 中是强制匹配的。
所以提供可运行源码 + 已验证的核心算法 + XML 模板 + 打包脚本。
这并不是已经在你炎核平台注册成功的最终插件，请不要把它写成已完成的平台集成。

## 5. 下一版可以加什么？

- 分离输入为 `vtu15File` 与 `vtu10File` 两个资源槽，接入其它网格结果；
- 增加第三种网格尺寸，进行三网格位移收敛研究；
- 使用确定的应力分量标签和测点，避免误判局部应力峰值；
- 读取模型 INP/求解日志，核对材料、载荷、约束以及求解是否真正完成；
- 报告导出 PDF 和质量评分，但结论必须体现适用范围。

**特别注意**：A4 CalculiX 之前的红叉仍需最终处理，现阶段 A6 可以独立分析队友已有计算结果；完整求解闭环的自动化尚未完成。
