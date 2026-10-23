import time
import os 

doc.Clear()
doc.ResetCaseResult()

consID = [554,534,547,541]
forceID = [613]

#导入
start_time = time.time()
docRunCommand("cmd_ncti_import_file",File,modelname)
end_time = time.time()
elapsed_time = end_time - start_time
print(f"模型加载时间：{elapsed_time:.6f}秒")
start_time = end_time

#sel = NCTI.SelectionManager(doc)
#print(sel.ObjectNames)
#print(set.CellIDs)

sel = NCTI.SelectionManager(doc)
modelname = sel.ObjectNames[0]
#设置section的set
doc.RunCommand("cmd_ncti_mesh_add_set_geometry", "Element_Geo_Set3", modelname, 2)

#设置固定约束set1左端固定铰支座
sel = NCTI.SelectionManager(doc)
modelname = sel.ObjectNames[0]
consID = sel.CellIDs
doc.RunCommand("cmd_ncti_mesh_add_set_geometry", "Node_Geo_Set1", modelname,1,consID)

#设置固定约束set2右端滚动铰支座
sel = NCTI.SelectionManager(doc)
modelname = sel.ObjectNames[0]
consID = sel.CellIDs
doc.RunCommand("cmd_ncti_mesh_add_set_geometry", "Node_Geo_Set2", modelname,1,consID)

#参考点(设置集中力)
ref_pt = NCTI.Point(0,0,110)
doc.RunCommand("cmd_ncti_mesh_add_set_reference", "reference_node_set1", 0, [ref_pt])

#上顶面set
sel = NCTI.SelectionManager(doc)
modelname = sel.ObjectNames[0]
doc.RunCommand("cmd_ncti_mesh_add_set_geometry", "Face_Geo_Set1", modelname, 3)

#耦合
#param2:耦合名称
#param3:参考点set名称 reference_node_set1
#param4:面set名称 Face_Geo_Set1
#param5:耦合类型 0:Kinematic; 1:Continuum distributing 2:Structural distributing
#param6:影响半径 -1:到区域的最外点; >=0:指定
#param7:自由度数组
#param8:各自由度是否使用，1表示使用
#param9:自适应控制点以放置在表面上(0,1)
#param10:热膨胀系数（耦合类型为0 Kinematic 有效）
#param11:连续分布 结构分布 加权法（耦合类型为1 Distributing 有效） 0:Uniforrm; 1:Linear 2:Quadratic 3:Cubic(m_iCouplingType 1:Continuum distributing 2:Structural distributing)
CouplingType = 0
InfluenceRadius = 10
Adjust = 0
Alpha = -1
WeightingMethod = 0
doc.RunCommand("cmd_ncti_mesh_add_coupling", "coupling", "reference_node_set1", "Face_Geo_Set1", CouplingType, InfluenceRadius, [1,2,3], [1,1,1], Adjust, Alpha, WeightingMethod)

#材料属性
#param2:材料名称 Q235B
#param3:弹性模量 206000
#param4:剪切模量 79000
#param5:泊松比 0.25
#param6:密度 7.85e-09
#param7:热膨胀
#param8:说明
doc.RunCommand("cmd_ncti_mesh_add_mat", "Q235B", 206000.0, 79000, 0.25, 7.85e-09, None)

#section
#param2:section名称 section1
#param3:set名称 Element_Geo_Set3
#param4:材料名称 Q235B
#param5:类型 ：SOLID
#param6:SHELL Thickness 
#param7:SHELL Sampling （default：5）
doc.RunCommand("cmd_ncti_mesh_add_section", "section1", "Element_Geo_Set3", "Q235B", "SOLID")

#左端固定铰支座固定约束
#param2:约束名称 cons_left
#param3:set名称 Node_Geo_Set1
#param4:自由度数组
#param5:各自由度的值，0表示固定
doc.RunCommand("cmd_ncti_mesh_add_spc", "cons_left", "Node_Geo_Set1", [1,2,3], [0,0,0])

#右端滚动铰支座固定约束
#param2:约束名称 cons_right
#param3:set名称 Node_Geo_Set2
#param4:自由度数组
#param5:各自由度的值，0表示固定
doc.RunCommand("cmd_ncti_mesh_add_spc", "cons_right", "Node_Geo_Set2", [2,3], [0,0])

#集中力
#param2:力的名称 force
#param3:set名称 reference_node_set1
#param4:力的方向
#param5:力的大小
doc.RunCommand("cmd_ncti_mesh_add_force", "force", "reference_node_set1", NCTI.Vector(0, 0, -1), 20000.0)

#输出
field_output = 1
node_vars = ["U", "UR", "UT", "V", "VR", "VT","RF"]
element_vars =  ["E", "S"]
output_options = {}
node_options = {}
element_options = {"directions": "YES"}
#param2:输出的名称
#param3:输出类型，0-历史变量输出（history），1-场变量输出（field）
#param4:节点变量输出数组
#param5:单元变量输出数组
#param6:输出设置，可选
#param7:节点输出设置，可选
#param8:单元输出设置，可选
doc.RunCommand("cmd_ncti_mesh_add_output", "field", field_output, node_vars, element_vars, output_options, node_options, element_options)

#创建静态分析步
#param2:分析步名称
#param3:边界条件名称数组
#param4:力名称数组
#param5:变量输出名称数组
#param6:分析参数(1、初始增量步，2、分析步时间，3、最小增量步，4、最大增量步) :[1., 1., 1e-05, 1.]
#param7:是否考虑大变形，False-不考虑，True-考虑
doc.RunCommand("cmd_ncti_mesh_create_static_step", "Step_3",  ["cons_left", "cons_right", ], ["force"], ["field"],[1.0, 1.0, 1e-05, 1.0])

#生成体网络
#MeshSize:网格尺寸
#MeshType:网格类型 0:triangle,1:QuadDominant,2:FullQuad
#AngleTol:角度容差
#AutoCurvature:曲率自适应 0-否 1-是
#HighOrder:二阶网格 0-否 1-是
#Parallel:并行计算 0-否 1-是
#op = {"MeshSize":1, "MeshType":0, "AngleTol": 0, "AutoCurvature" : 0, "HighOrder":0, "Parallel": 0}
#doc.RunCommand("cmd_ncti_create_volume_mesh", sel.ObjectNames, op)
#sel = NCTI.SelectionManager(doc)
meshName = modelname + "_mesh"
doc.RunCommand("cmd_ncti_create_volume_mesh",[modelname], [meshName],{"MeshSize":15, "MeshType":0,"HighOrder":0})

filename = "C:\\Users\\16K\\Desktop\\ncti.inp"
doc.RunCommand("cmd_ncti_mesh_export_inp_file",filename,[meshName])



