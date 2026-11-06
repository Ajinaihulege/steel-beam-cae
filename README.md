# 典型钢结构受力性能仿真与分析

## 项目概况

本项目基于炎核CAX平台分析一根简支工字钢梁在跨中竖向荷载作用下的静力响应，并完成 15 mm、10 mm、8 mm 三种网格的收敛对比。

| 项目 | 参数 |
|---|---|
| 截面 | HW200×200×8×12 |
| 梁长 | 4000 mm |
| 材料 | Q235B |
| 弹性模量 | 206000 MPa |
| 泊松比 | 0.3 |
| 总荷载 | 20 kN，方向 -Z |
| 边界条件 | 左端下翼缘底部固定 Ux/Uy/Uz；右端下翼缘底部约束 Uy/Uz |
| 单元类型 | 四面体实体单元 |

## 目录结构

```text
BeamResultVerifier/
├─ BeamResultVerifier_Team_Source/   插件源代码
├─ BeamResultVerifier_REGISTER/      插件注册文件
└─ d340eb20bf9b2ac4204c1b9445b2d030_raw.mp4
                                      插件使用视频

工字钢梁15mm网格/
├─ 前处理/   CAE 模型、STEP、网格脚本和 INP
├─ 求解/     VTU/PVD 求解结果
├─ 后处理/   位移、应力、主应力云图
└─ Report/   BeamResultVerifier 插件验证结果

工字钢梁10mm网格/
├─ 前处理/
├─ 求解/
├─ 后处理/
└─ Report/

工字钢梁8mm网格/
├─ 前处理/
├─ 求解/
├─ 后处理/
└─ Report/
```

## 主要文件

- `.ncti`：CAE 前处理模型
- `.stp`：三维几何模型
- `*_网格剖分脚本.py`：平台自动化网格脚本
- `ncti.inp`：求解器输入文件
- `ncti_vtu.pvd` / `ncti_vtu_subcase1.vtu`：后处理结果
- `*.png`：结果云图
- `Report/`：BeamResultVerifier 插件生成的验证结果，包括 HTML、CSV、JSON 和图表
- `BeamResultVerifier/`：插件本体、注册文件和使用视频

## 网格收敛结果

| 网格尺寸 | 最大竖向位移 | 跨中下翼缘 Sxx | 局部最大 Mises | 节点数 / 单元数 |
|---|---:|---:|---:|---:|
| 15 mm | 3.050 mm | 约 43.8 MPa | 约 53.8 MPa | 20,904 / 60,876 |
| 10 mm | 3.044 mm | 约 44.1 MPa | 约 62.3 MPa | 48,120 / 141,600 |
| 8 mm | 3.044 mm | 约 43.9 MPa | 约 67.1 MPa | 75,246 / 222,292 |

理论参考值：

```text
跨中挠度：约 2.81 mm
跨中最大弯曲应力：约 43.4 MPa
```

10 mm 与 8 mm 结果的跨中挠度和弯曲应力变化均小于 1%，可认为网格已经收敛。局部最大 Mises 应力位于支座或加载区域附近，随网格变细会有所变化，不用于判断整体弯曲应力收敛。

## 打开方式

- CAE 前处理：打开对应网格目录中的 `前处理/` 下的 `.ncti` 或 `.stp`
- 后处理：打开对应网格目录中的 `求解/ncti_vtu/ncti_vtu.pvd`
- 求解器输入：查看对应网格目录中的 `前处理/ncti.inp`
- 插件验证结果：打开对应网格目录中的 `Report/analysis_report.html`
- 插件使用视频：打开 `BeamResultVerifier/d340eb20bf9b2ac4204c1b9445b2d030_raw.mp4`

## 说明

评价梁的整体弯曲性能时，建议使用跨中下翼缘的轴向弯曲应力 `Sxx` 和跨中竖向位移 `Uz`，不要直接使用支座或加载点附近的局部最大 Mises 应力。
