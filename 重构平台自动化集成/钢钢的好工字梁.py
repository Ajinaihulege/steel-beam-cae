CommonAPI.GUI.MainUI.taskFlowOperate({
    "content": {
        "OperateType": 1,
        "Version": "2.0.0",
        "ProjectName": "钢钢的好工字梁",
        "ProjectInfo": {
            "edges": [
                {
                    "fromPin": {
                        "nodeId": "2063273003"
                    },
                    "id": "2100000001",
                    "toPin": {
                        "nodeId": "73730590"
                    },
                    "type": "executable"
                },
                {
                    "fromPin": {
                        "nodeId": "73730590"
                    },
                    "id": "183372394",
                    "toPin": {
                        "nodeId": "1565723220"
                    },
                    "type": "executable"
                },
                {
                    "fromPin": {
                        "body": {
                            "param": "outParam",
                            "path": [
                                {
                                    "type": "name",
                                    "value": "filepath"
                                }
                            ]
                        },
                        "nodeId": "2063273003"
                    },
                    "id": "1823588594",
                    "toPin": {
                        "body": {
                            "param": "inParam",
                            "path": [
                                {
                                    "type": "name",
                                    "value": "filepath"
                                }
                            ]
                        },
                        "nodeId": "73730590"
                    },
                    "type": "dataShareable"
                },
                {
                    "fromPin": {
                        "body": {
                            "param": "outParam",
                            "path": [
                                {
                                    "type": "name",
                                    "value": "filepath"
                                }
                            ]
                        },
                        "nodeId": "73730590"
                    },
                    "id": "330612984",
                    "toPin": {
                        "body": {
                            "param": "inParam",
                            "path": [
                                {
                                    "type": "name",
                                    "value": "filepath"
                                }
                            ]
                        },
                        "nodeId": "1565723220"
                    },
                    "type": "dataShareable"
                }
            ],
            "nodes": [
                {
                    "$nodeType": "TaskNode",
                    "api": "SimulatorRunSolverCommand",
                    "id": "73730590",
                    "inParam": {
                        "kind": "entity",
                        "name": "RunSolverArgs",
                        "text": "求解器求解计算",
                        "value": {
                            "arguments": {
                                "domain": {
                                    "defaultValue": {
                                        "slot": null,
                                        "type": "string"
                                    },
                                    "domainType": "enum",
                                    "enumItems": [
                                        {
                                            "idx": 0,
                                            "value": {
                                                "slot": null,
                                                "type": "string"
                                            }
                                        },
                                        {
                                            "idx": 1,
                                            "name": "-d femsgc -f gcstatic",
                                            "value": {
                                                "slot": "-d femsgc -f gcstatic",
                                                "type": "string"
                                            }
                                        },
                                        {
                                            "idx": 2,
                                            "name": "-d femsgc -f gcvibration",
                                            "value": {
                                                "slot": "-d femsgc -f gcvibration",
                                                "type": "string"
                                            }
                                        },
                                        {
                                            "idx": 3,
                                            "name": "-d femsgc -f gcbuckling",
                                            "value": {
                                                "slot": "-d femsgc -f gcbuckling",
                                                "type": "string"
                                            }
                                        }
                                    ]
                                },
                                "inPin": "dataShareable",
                                "kind": "primitive",
                                "name": "arguments",
                                "outPin": "dataShareable",
                                "seq": 3,
                                "text": "启动参数",
                                "type": "string",
                                "value": {
                                    "slot": null,
                                    "type": "string"
                                }
                            },
                            "configfile": {
                                "inPin": "dataShareable",
                                "kind": "primitive",
                                "name": "configfile",
                                "outPin": "dataShareable",
                                "seq": 2,
                                "text": "配置文件",
                                "type": "uri",
                                "value": {
                                    "slot": null,
                                    "type": "uri"
                                }
                            },
                            "executeServer": {
                                "domain": {
                                    "defaultValue": {
                                        "slot": null,
                                        "type": "string"
                                    },
                                    "domainType": "enum",
                                    "enumItems": [
                                        {
                                            "idx": 0,
                                            "value": {
                                                "slot": null,
                                                "type": "string"
                                            }
                                        },
                                        {
                                            "idx": 1,
                                            "name": "172.16.45.62:20001",
                                            "value": {
                                                "slot": "172.16.45.62:20001",
                                                "type": "string"
                                            }
                                        },
                                        {
                                            "idx": 2,
                                            "name": "172.16.45.62:20002",
                                            "value": {
                                                "slot": "172.16.45.62:20002",
                                                "type": "string"
                                            }
                                        },
                                        {
                                            "idx": 3,
                                            "name": "172.16.45.62:20003",
                                            "value": {
                                                "slot": "172.16.45.62:20003",
                                                "type": "string"
                                            }
                                        },
                                        {
                                            "idx": 4,
                                            "name": "172.16.45.62:40001",
                                            "value": {
                                                "slot": "172.16.45.62:40001",
                                                "type": "string"
                                            }
                                        }
                                    ]
                                },
                                "inPin": "dataShareable",
                                "kind": "primitive",
                                "name": "executeServer",
                                "outPin": "dataShareable",
                                "seq": 4,
                                "text": "执行服务实例",
                                "type": "string",
                                "value": {
                                    "slot": null,
                                    "type": "string"
                                }
                            },
                            "filepath": {
                                "inPin": "dataShareable",
                                "kind": "primitive",
                                "name": "filepath",
                                "outPin": "dataShareable",
                                "seq": 1,
                                "text": "导入文件",
                                "type": "uri",
                                "value": {
                                    "slot": {
                                        "name": "34-2063273003.inp",
                                        "type": "Resource",
                                        "uuid": "c7ef715c-aca1-5801-8ded-e9d1691473ea"
                                    },
                                    "type": "uri"
                                }
                            },
                            "mathName": {
                                "domain": {
                                    "defaultValue": {
                                        "slot": null,
                                        "type": "string"
                                    },
                                    "domainType": "enum",
                                    "enumItems": [
                                        {
                                            "idx": 0,
                                            "value": {
                                                "slot": null,
                                                "type": "string"
                                            }
                                        },
                                        {
                                            "idx": 1,
                                            "name": "pardiso",
                                            "value": {
                                                "slot": "pardiso",
                                                "type": "string"
                                            }
                                        },
                                        {
                                            "idx": 2,
                                            "name": "mumps",
                                            "value": {
                                                "slot": "mumps",
                                                "type": "string"
                                            }
                                        },
                                        {
                                            "idx": 3,
                                            "name": "openss",
                                            "value": {
                                                "slot": "openss",
                                                "type": "string"
                                            }
                                        }
                                    ]
                                },
                                "inPin": "dataShareable",
                                "kind": "primitive",
                                "name": "mathName",
                                "outPin": "dataShareable",
                                "seq": 5,
                                "text": "数学库",
                                "type": "string",
                                "value": {
                                    "slot": null,
                                    "type": "string"
                                }
                            }
                        }
                    },
                    "inPin": "executable",
                    "outParam": {
                        "kind": "entity",
                        "name": "FileArgs",
                        "text": "用户创建、导入、保存、导出文件等操作的文件参数实体",
                        "value": {
                            "filepath": {
                                "inPin": "dataShareable",
                                "kind": "primitive",
                                "name": "filepath",
                                "outPin": "dataShareable",
                                "seq": 1,
                                "text": "文件路径",
                                "type": "uri",
                                "value": {
                                    "slot": {
                                        "name": "D:/OpenCAEHub/OpenCAEHubClient2.0.14/2.0.14/Client/temp/ncti_vtu_subcase1.vtu",
                                        "type": "Resource",
                                        "uuid": "9c30d913-e25c-5c9d-9457-ebe638357bce"
                                    },
                                    "type": "uri"
                                }
                            }
                        }
                    },
                    "outPin": "executable",
                    "pluginParam": {
                        "kind": "entity",
                        "value": {
                            "pluginImpl": {
                                "kind": "primitive",
                                "name": "pluginImpl",
                                "type": "int32",
                                "value": {
                                    "slot": 502,
                                    "type": "int32"
                                }
                            },
                            "pulginScript": {
                                "kind": "primitive",
                                "name": "pulginScript",
                                "type": "uri",
                                "value": {
                                    "slot": null,
                                    "type": "uri"
                                }
                            }
                        }
                    },
                    "posX": 705.0983167559294,
                    "posY": 169.16666666666663,
                    "seq": 2,
                    "state": "CompletedSuccess",
                    "type": "task"
                },
                {
                    "$nodeType": "TaskNode",
                    "api": "PostprocessingShowFormCommand",
                    "id": "1565723220",
                    "inParam": {
                        "kind": "entity",
                        "name": "PostViewArgs",
                        "text": "后处理显示",
                        "value": {
                            "filepath": {
                                "inPin": "dataShareable",
                                "kind": "primitive",
                                "name": "filepath",
                                "outPin": "dataShareable",
                                "seq": 1,
                                "text": "文件路径",
                                "type": "uri",
                                "value": {
                                    "slot": {
                                        "name": "D:/OpenCAEHub/OpenCAEHubClient2.0.14/2.0.14/Client/temp/ncti_vtu_subcase1.vtu",
                                        "type": "Resource",
                                        "uuid": "9c30d913-e25c-5c9d-9457-ebe638357bce"
                                    },
                                    "type": "uri"
                                }
                            },
                            "scaleFactor": {
                                "inPin": "dataShareable",
                                "kind": "primitive",
                                "name": "scaleFactor",
                                "outPin": "dataShareable",
                                "seq": 3,
                                "text": "缩放比例",
                                "type": "double",
                                "value": {
                                    "slot": null,
                                    "type": "double"
                                }
                            },
                            "variableName": {
                                "inPin": "dataShareable",
                                "kind": "primitive",
                                "name": "variableName",
                                "outPin": "dataShareable",
                                "seq": 2,
                                "text": "物理量",
                                "type": "string",
                                "value": {
                                    "slot": null,
                                    "type": "string"
                                }
                            }
                        }
                    },
                    "inPin": "executable",
                    "outPin": "executable",
                    "pluginParam": {
                        "kind": "entity",
                        "value": {
                            "pluginImpl": {
                                "kind": "primitive",
                                "name": "pluginImpl",
                                "type": "int32",
                                "value": {
                                    "slot": 540,
                                    "type": "int32"
                                }
                            },
                            "pulginScript": {
                                "kind": "primitive",
                                "name": "pulginScript",
                                "type": "uri",
                                "value": {
                                    "slot": null,
                                    "type": "uri"
                                }
                            }
                        }
                    },
                    "posX": 1348.3333333333333,
                    "posY": 141.16666666666663,
                    "seq": 3,
                    "state": "CompletedSuccess",
                    "type": "task"
                },
                {
                    "$nodeType": "TaskNode",
                    "api": "PreprocessingMeshSolidCommand",
                    "id": "2063273003",
                    "inParam": {
                        "kind": "entity",
                        "name": "MeshSolidArgs",
                        "text": "对模型一键生成3d四面体网格",
                        "value": {
                            "geoPath": {
                                "inPin": "dataShareable",
                                "kind": "primitive",
                                "name": "geoPath",
                                "outPin": "dataShareable",
                                "seq": 2,
                                "text": "几何文件",
                                "type": "uri",
                                "value": {
                                    "slot": {
                                        "name": "HW200x200x8x12.stp",
                                        "type": "Resource",
                                        "uuid": "e2f4c4bf-2be7-5ea7-aaea-9c8ea4aaa016"
                                    },
                                    "type": "uri"
                                }
                            },
                            "meshSize": {
                                "inPin": "dataShareable",
                                "kind": "primitive",
                                "name": "meshSize",
                                "outPin": "dataShareable",
                                "seq": 1,
                                "text": "网格大小",
                                "type": "double",
                                "value": {
                                    "slot": 10.0,
                                    "type": "double"
                                }
                            },
                            "meshType": {
                                "domain": {
                                    "defaultValue": {
                                        "slot": null,
                                        "type": "string"
                                    },
                                    "domainType": "enum",
                                    "enumItems": [
                                        {
                                            "idx": 0,
                                            "value": {
                                                "slot": null,
                                                "type": "string"
                                            }
                                        },
                                        {
                                            "idx": 1,
                                            "name": "TET",
                                            "value": {
                                                "slot": "TET",
                                                "type": "string"
                                            }
                                        },
                                        {
                                            "idx": 2,
                                            "name": "HEX",
                                            "value": {
                                                "slot": "HEX",
                                                "type": "string"
                                            }
                                        },
                                        {
                                            "idx": 3,
                                            "name": "TRI",
                                            "value": {
                                                "slot": "TRI",
                                                "type": "string"
                                            }
                                        },
                                        {
                                            "idx": 4,
                                            "name": "QUAD",
                                            "value": {
                                                "slot": "QUAD",
                                                "type": "string"
                                            }
                                        },
                                        {
                                            "idx": 5,
                                            "name": "HYB",
                                            "value": {
                                                "slot": "HYB",
                                                "type": "string"
                                            }
                                        }
                                    ]
                                },
                                "inPin": "dataShareable",
                                "kind": "primitive",
                                "name": "meshType",
                                "outPin": "dataShareable",
                                "seq": 3,
                                "text": "网格类型",
                                "type": "string",
                                "value": {
                                    "slot": "TET",
                                    "type": "string"
                                }
                            }
                        }
                    },
                    "inPin": "executable",
                    "outParam": {
                        "kind": "entity",
                        "name": "FileArgs",
                        "text": "用户创建、导入、保存、导出文件等操作的文件参数实体",
                        "value": {
                            "filepath": {
                                "inPin": "dataShareable",
                                "kind": "primitive",
                                "name": "filepath",
                                "outPin": "dataShareable",
                                "seq": 1,
                                "text": "文件路径",
                                "type": "uri",
                                "value": {
                                    "slot": {
                                        "name": "34-2063273003.inp",
                                        "type": "Resource",
                                        "uuid": "c7ef715c-aca1-5801-8ded-e9d1691473ea"
                                    },
                                    "type": "uri"
                                }
                            }
                        }
                    },
                    "outPin": "executable",
                    "pluginParam": {
                        "kind": "entity",
                        "value": {
                            "pluginImpl": {
                                "kind": "primitive",
                                "name": "pluginImpl",
                                "type": "int32",
                                "value": {
                                    "slot": 317,
                                    "type": "int32"
                                }
                            },
                            "pulginScript": {
                                "kind": "primitive",
                                "name": "pulginScript",
                                "type": "uri",
                                "value": {
                                    "slot": null,
                                    "type": "uri"
                                }
                            }
                        }
                    },
                    "posX": -83.02206069880134,
                    "posY": 164.10443764345837,
                    "seq": 1,
                    "state": "CompletedSuccess",
                    "type": "task"
                }
            ]
        }
    }
})