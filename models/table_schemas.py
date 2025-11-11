"""
表操作结果模型定义
参考metric_schemas.py的结构，提供统一的表操作结果格式
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field

from .table import TableInfo, LevelType, TableType, TableProp


# ==================== 枚举定义 ====================

class TableOperationType(str, Enum):
    """表操作类型"""
    CREATE = "create"
    UPDATE = "update"
    QUERY = "query"


# ==================== Pydantic模型定义 ====================

class TableAnalysisResult(BaseModel):
    """表分析结果模型 - 包含操作类型和基本的表信息"""
    operation_type: str = Field(description="操作类型：create/update/query")
    db_name: Optional[str] = Field(default=None, description="数据库名称")
    table_name: Optional[str] = Field(default=None, description="表名称")
    table_name_zh: Optional[str] = Field(default=None, description="表中文名称")
    table_purpose: str = Field(default="", description="表的用途和业务场景描述")
    metric_name_zh_list: List[str] = Field(default_factory=list, description="关联的指标中文名称列表")

    model_config = {
        "json_schema_extra": {
            "example": {
                "operation_type": "create",
                "db_name": "warehouse",
                "table_name": "user_order_fact",
                "table_name_zh": "用户订单事实表",
                "table_purpose": "存储用户订单相关的事实数据，包含订单金额、时间等关键指标",
                "metric_name_zh_list": ["订单金额", "用户活跃度", "转化率"]
            }
        }
    }


class TableOperationResult(BaseModel):
    """表操作结果模型"""
    operation_type: str = Field(description="操作类型：create/update/query")
    status: str = Field(description="操作状态：success/exist/not_exist/error")
    message: str = Field(description="操作结果消息")
    table_info: Optional[TableInfo] = Field(default=None, description="表信息")
    existing_table: Optional[TableInfo] = Field(default=None, description="已存在的表信息")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "operation_type": "create",
                    "status": "exist",
                    "message": "表已存在，无需重复创建",
                    "table_info": {
                        "name": "user_order_fact",
                        "nameZh": "用户订单事实表",
                        "businessDomainId": "domain_001",
                        "daName": "warehouse",
                        "levelType": "SUB",
                        "type": "IAT",
                        "tableProp": "NORMAL",
                        "particleSize": "明细",
                        "itOwner": "system",
                        "itGroup": "data_team",
                        "businessOwner": "product_team",
                        "businessGroup": "product_team",
                        "cols": []
                    },
                    "existing_table": {
                        "name": "user_order_fact",
                        "nameZh": "用户订单事实表",
                        "businessDomainId": "domain_001",
                        "daName": "warehouse",
                        "levelType": "SUB",
                        "type": "IAT",
                        "tableProp": "NORMAL",
                        "particleSize": "明细",
                        "itOwner": "system",
                        "itGroup": "data_team",
                        "businessOwner": "product_team",
                        "businessGroup": "product_team",
                        "cols": []
                    }
                },
                {
                    "operation_type": "update",
                    "status": "not_exist",
                    "message": "表不存在，无法修改",
                    "table_info": None,
                    "existing_table": None
                },
                {
                    "operation_type": "create",
                    "status": "success",
                    "message": "表创建成功",
                    "table_info": {
                        "name": "new_table",
                        "nameZh": "新表",
                        "businessDomainId": "domain_001",
                        "daName": "warehouse",
                        "levelType": "SUB",
                        "type": "IAT",
                        "tableProp": "NORMAL",
                        "particleSize": "明细",
                        "itOwner": "system",
                        "itGroup": "data_team",
                        "businessOwner": "待指定",
                        "businessGroup": "待指定",
                        "cols": []
                    },
                    "existing_table": None
                }
            ]
        }
    }