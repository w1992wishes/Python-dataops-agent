"""
表相关数据模型 - 合并了原table.py和table_schemas.py
包含枚举定义、基础模型和操作结果模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


# ==================== 枚举定义 ====================

class LevelType(str, Enum):
    """表层级类型枚举"""
    SUB = "SUB"
    AGG = "AGG"


class TableType(str, Enum):
    """表类型枚举"""
    IAT = "IAT"  # 原子指标表
    IBT = "IBT"  # 派生指标表


class TableProp(str, Enum):
    """表应用类型枚举"""
    NORMAL = "NORMAL"  # 普通表
    TMP = "TMP"        # 临时表
    MID = "MID"        # 中间表


class ColProp(str, Enum):
    """字段属性枚举"""
    DIM = "DIM"      # 维度字段
    METRIC = "METRIC" # 指标字段
    NORMAL = "NORMAL" # 普通字段


class DataType(str, Enum):
    """字段数据类型枚举"""
    STRING = "string"
    DATE = "date"
    FLOAT = "float"


class ColType(int, Enum):
    """字段分类枚举"""
    NORMAL = 0    # 普通字段
    PARTITION = 2 # 分区键


class TableOperationType(str, Enum):
    """表操作类型"""
    CREATE = "create"
    UPDATE = "update"
    QUERY = "query"


# ==================== 基础数据模型 ====================

class MetricCol(BaseModel):
    """指标列模型"""
    id: str = Field(..., description="指标ID")


class Column(BaseModel):
    """表字段模型"""
    name: str = Field(..., description="字段英文名称")
    nameZh: str = Field(..., description="字段中文名称")
    colProp: ColProp = Field(..., description="字段属性")
    dataType: DataType = Field(..., description="字段数据类型")
    colType: ColType = Field(default=ColType.NORMAL, description="字段分类")
    tableId: Optional[str] = Field(default="", description="所属表ID，新增时为空，修改时必填")
    metrics: Optional[List[MetricCol]] = Field(None, description="关联的指标列表,仅指标字段有效，且可选")


class TableInfo(BaseModel):
    """数据表完整信息模型"""
    id: Optional[str] = Field(default=None, description="数据表ID，新增时为空，修改时必填")
    name: str = Field(..., description="表英文名称")
    nameZh: str = Field(..., description="表中文名称")
    businessDomainId: str = Field(..., description="表所属业务域id")
    daName: str = Field(default="default_db", description="表所属库名")
    levelType: LevelType = Field(..., description="表层级类型")
    type: TableType = Field(..., description="表类型")
    tableProp: TableProp = Field(..., description="表应用类型")
    particleSize: str = Field(default="明细", description="数据粒度")
    itOwner: str = Field(default="system", description="IT属主")
    itGroup: str = Field(default="data_team", description="IT属主分组")
    businessOwner: str = Field(default="待指定", description="业务属主")
    businessGroup: str = Field(default="待指定", description="业务属主分组")
    cols: List[Column] = Field(..., description="字段列表")

    class Config:
        use_enum_values = True


# ==================== 操作结果模型 ====================

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


# ==================== 表请求分析模型 ====================

class TableRequestAnalysis(BaseModel):
    """表请求分析结果模型"""
    operation_type: str = Field(description="操作类型: create/update/query")
    db_name: Optional[str] = Field(default=None, description="数据库名，如果用户明确指定")
    table_name: Optional[str] = Field(default=None, description="表名，如果用户明确指定")
    metric_name_zh_list: List[str] = Field(default_factory=list, description="指标中文名称列表")
    table_purpose: str = Field(description="表的用途和业务场景描述")


# ==================== 导出列表 ====================

__all__ = [
    # 枚举
    'LevelType',
    'TableType',
    'TableProp',
    'ColProp',
    'DataType',
    'ColType',
    'TableOperationType',

    # 基础模型
    'MetricCol',
    'Column',
    'TableInfo',

    # 分析模型
    'TableRequestAnalysis',

    # 操作结果模型
    'TableAnalysisResult',
    'TableOperationResult'
]