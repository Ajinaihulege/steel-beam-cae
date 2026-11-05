# A6 / A7 资源参数排错说明（OpenCAEHub Client 2.0.14）

## 已观察到的真实事实

- 旧 API 运行时提示 `NameError: name 'CommandAPI' is not defined`。
- 使用 `CommonAPI.Postprocessing.BeamResultVerifier(...)` 后，已经出现带 `implId` 的调用，且 `result.json` 由 PythonAdapter 写出。
- 新的失败信息来自插件本身：`inParam.inputParam.filepath` 实际收到 `""`。
- 本地 `Client/temp/...` 与 `Client/Local/User-*/project-*/...` 可以找到 VTU，**不能推出该路径已经传递给插件**。
- 旧报告 HTML/ZIP 的时间可能早于新的 `result.json`；不要将旧文件误当本次执行成功的产物。

## 需要区分的两种情形

**情况一：上下文有非空 filepath**。例如：

```json
{"inParam":{"inputParam":{"filepath":"steel-beam-cae-main/10mm/cal/ncti_vtu/ncti_vtu_subcase1.vtu"}}}
```

此时 `input_resolver.py` 尝试寻找明确的文件，优先匹配直接路径、工作目录和 Client/temp，并在指定项目缓存中搜索。若多个同名 VTU 共存，将拒绝猜测。

**情况二：上下文为空**（当前真实问题）：

```json
{"inParam":{"inputParam":{"filepath":""}}}
```

插件没有任何能确定目标文件的信息。即使知道某些 VTU 在本机，也无法根据空字符串安全地决定应当分析哪一个网格。必须在平台配置或资源下载/参数转交环节排查。

## 建议开发者检查

1. CFF 参数组与参数名：`inputParam.filepath`，资源类型 `Resource`。
2. `PluginConfig.xml` 中的 `APIName` / `ModuleFullName` 与 CFF 新 API 是否匹配。
3. `APIParameterTemlate="filepath=%filepath%"` 的 `%filepath%` 在 2.0.14 中是否正确展开为资源下载后的路径。**该拼写 Temlate 是现有官方配置样例的字段名，不要擅自改为 Template。**
4. 对照系统自带的已成功运行的无界面、接收 Resource 类型文件的 PythonAdapter（如平台有此例）。
5. 检查 `OpenCaeHub.log`、运行任务的 `*_context.json` / `*_result.json`、`logs/plugin/plugin_wrapper.log`（若本机有日志），以确认输入从哪里变成空字符串。

## 本地诊断（无需注册插件）

```powershell
python beam_analyzer.py --input "C:\真正的VTU完整路径\ncti_vtu_subcase1.vtu" --output-dir ".\beam_report"
```

若算法成功，说明核心分析本身可运行，平台当前障碍仍在**资源参数交接**。

`BEAM_VERIFIER_INPUT_FILE` 仅用于开发人员主动设置一个**明确的、存在的**文件路径来验证插件入口；不要将环境变量默认值写进公共仓库或用于正式结果复现。

## 成功的验收标准

- A6/A7 独立执行后最新 `result.json` 显示 `status: success`。
- 本次 ZIP 的修改时间与执行时间一致且文件可打开。
- 任务输出 `filepath` 成功注册为可下载资源。
- 报告中的源文件、网格尺寸、结果范围能回溯到实际 VTU。
- 仅在此之后才可以把 A6 记为完成自动化闭环。
