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

#自动化找ID
#sel = NCTI.SelectionManager(doc)
#print(sel.ObjectNames)
#print(sel.CellIDs)

#sel = NCTI.SelectionManager(doc)
#modelname = sel.ObjectNames[0]
#设置section的set
doc.RunCommand("cmd_ncti_mesh_add_set_geometry", "Element_Geo_Set3", 'grp_ncti_display_model_body_15', 2,[])

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
meshName =  'grp_ncti_display_model_body_15'+ "_mesh"
doc.RunCommand("cmd_ncti_create_volume_mesh", ['grp_ncti_display_model_body_15'], [meshName],{"MeshSize":15, "MeshType":0,"HighOrder":0})

#设置固定约束set1左端固定铰支座
#sel = NCTI.SelectionManager(doc)
#modelname = sel.ObjectNames[0]
#consID = sel.CellIDs
doc.RunCommand("cmd_ncti_mesh_add_set_geometry", "Node_Geo_Set1", 'grp_ncti_display_model_body_15',1,[44])

#设置固定约束set2右端滚动铰支座
#sel = NCTI.SelectionManager(doc)
#modelname = sel.ObjectNames[0]
#consID = sel.CellIDs
doc.RunCommand("cmd_ncti_mesh_add_set_geometry", "Node_Geo_Set2", 'grp_ncti_display_model_body_15',1,[57])

#参考点
ref_pt = NCTI.Point(0,0,110)
doc.RunCommand("cmd_ncti_mesh_add_set_reference", "reference_node_set1", 0, [ref_pt])


#设置集中力
doc.RunCommand("cmd_ncti_mesh_add_set", "Node_Set3", 'grp_ncti_display_model_body_15_mesh',[72057594037928381, 72057594037928659, 72057594037931417, 72057594037931683, 72057594037931949, 72057594037932215, 72057594037932481, 72057594037932747, 72057594037933013, 72057594037933279, 72057594037933545, 72057594037933811, 72057594037934077, 72057594037934343])

#验证是否选中节点集
#set_names = doc.GetSets()
#print("所有集合：", set_names)
#pyObj = NCTI.Object(doc)
#info = pyObj.GetObjectData(["Node_Set3"])
#print(info)
#node_index = info[0][2].get("element_index", [])
#print("集合内节点数量：", len(node_index))
#print("集合类型：", info[0][1])


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
#param3:set名称 Node_Set3
#param4:力的方向
#param5:力的大小
N = 14
doc.RunCommand("cmd_ncti_mesh_add_force", "force", "Node_Set3",NCTI.Vector(0, 0, -1), 20000.0/N)

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

filename = "C:\\Users\\16K\\Desktop\\ncti.inp"
doc.RunCommand("cmd_ncti_mesh_export_inp_file",filename,[meshName])



