# 平台 A6/A7 最终排错说明

## 新账户的最新进展：输出路径方法不存在

2026-11-06 的项目 40 任务 913069841（仅为示例；其他项目 ID 会不同）：

```json
{
  "inParam": {
    "inputParam": {
      "filepath": "C:/.../Client/temp/ncti_vtu_subcase1.vtu"
    }
  }
}
```

`sys_plugin_dir` 已指向 `Plugins/BeamResultVerifierCommonTest`，且本次生成了报告 ZIP。但是 `result.json` 报：

```text
'BeamResultVerifierAdapter' object has no attribute '_temp_relative_path'
```

这说明**本次分析过程已到最后的输出路径返回阶段**。v3.0.3.1 已改为独立计算：

```python
relative = target.resolve().relative_to(
    (Path(ctx["sys_main_dir"]) / "temp").resolve()
).as_posix()
```

按照实际任务目录，期望输出 `40/913069841/beam_validation_report.zip`。这不需要更换 VTU、创建新 CFF API 或重建模型。

**升级后验收**：最新 `result.json` 状态为 `success`，且输出可以从平台下载。若仍失败，依据新报错判断，不重复排查已经解决的空 filepath。

---

目标：确认炎核 OpenCAEHub Client 2.0.14 是否将 UI 选择的 VTU 转交给 PythonAdapter。所有检查均不修改求解文件。

## 一、此前的真实证据

界面执行命令中有非空资源标识，例如：

```text
CommonAPI.Postprocessing.BeamResultVerifier(...)
input.inputParam.filepath.value.slot.name = "ncti_vtu_subcase1.vtu"
input.inputParam.filepath.value.slot.type = "Resource"
```

但是运行任务的 `*_context.json` 显示：

```json
{
  "inParam": {"inputParam": {"filepath": ""}},
  "logic_command": "beamResultVerify"
}
```

同时 VTU 确实存在于客户端 `Client/temp/steel-beam-cae-main/10mm/...` 以及 `Client/Local/...` 缓存，约 32.4 MB。

这至少说明界面选择与插件获得的文件路径之间出现了不匹配。**尚不能单凭现有日志区分**是 CFF 层参数组结构、`%filepath%` 模板展开、Resource 下载、执行服务配置中的哪一个环节导致。

## 二、版本一致性检查

当前测试包：

```text
Plugin Name: BeamResultVerifierCommonTest
Dir:         Plugins/BeamResultVerifierCommonTest
Module:      Postprocessing.PostprocessingIO
APIName:     BeamResultVerifierCommonTest
LogicCommand: beamResultVerify
```

旧日志出现：

```text
sys_plugin_dir: .../Plugins/BeamResultVerifier//
```

这意味着**该份上下文**由旧目录插件执行。确认 `*_context.json` 的修改时间晚于重新注册和选择插件的时间，否则不能据此判断最新版本是否生效。

不要重新绑定官方 A5 `GUI.PostUI` 插件，也不要将本分析插件的 XML 改为 `showForm`。

## 三、最省事的诊断方法

在源码目录打开 PowerShell，执行：

```powershell
python .\tools\diagnose_context.py "C:\实际目录\38_1464901257_context.json" --plugin-xml .\PluginConfig.xml
```

你需要查看四行：`INPUT EMPTY`、`Runtime plugin`、`status`、`Report ZIP predates result.json`。

如果任务节点 ID 改变，必须用**新的 context.json**，不能继续检查旧目录。

### 使用 PowerShell 查找最近的上下文

```powershell
$base = "$env:LOCALAPPDATA\Programs\OpenCAEHub\Client\2.0.14\Client"
Get-ChildItem "$base\temp" -Filter "*_context.json" -File -Recurse -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 10 FullName, LastWriteTime
```

选择最新的对应 A6/A7 的 context 路径再执行诊断。

## 四、如果 filepath 仍为空

**不要继续重做网格、换模型或改 vtU 统计算法**。将以下信息发给平台技术人员：

1. CFF API 命令 `CommonAPI.Postprocessing.BeamResultVerifier`。
2. CFF 的输入实体 `inputParam.filepath` 类型为 resource；客户端界面已经关联真实资源名称/UUID。
3. 注册 XML 使用官方示例中的 `APIParameterTemlate="filepath=%filepath%"`。
4. PythonAdapter `context.json` 的 `inParam.inputParam.filepath` 为 `""`。
5. 宿主客户端 `OpenCaeHub.log` 与该任务的 `context.json`、`result.json`。
6. 请确认：嵌套实体参数的展开规则、资源下载配置以及正确的 Resource 输入模板占位符是什么。

目前官方教程的示例只说明 `%变量名%` 会展开，不能直接确定该平台对嵌套 CFF 参数是否支持 `%inputParam.filepath%`。不要把未验证的语法写入正式发布包。

## 五、本地验证不受此问题影响

直接读取已下载的队友 VTU（以实际路径为准）：

```powershell
python .\beam_analyzer.py --input "C:\TeamData\ncti_vtu_subcase1.vtu" --output-dir .\beam_report
```

`BEAM_VERIFIER_INPUT_FILE` 可在**开发者控制的插件进程启动前**设为精确的绝对路径，以单独检查入口和输出映射。但它不能安全地从空上下文猜出用户在平台中选中的文件，也不是跨用户、跨服务器的正式集成修复。

## 六、验收条件

1. 最新 `context.json` 提供可解析的 `filepath`。
2. 最新 `result.json` 为 `{"status":"success", ...}`。
3. 新 ZIP 修改时间不早于执行开始时间。
4. 从平台资源池可以获取 ZIP，并确认 HTML/CSV/JSON 与本次真实 VTU 一致。
5. 对照 INP/求解设置确认工况、单位、边界条件和物理意义。

仅 HTML 能打开或任务目录中存在旧 ZIP，不算平台执行成功。
