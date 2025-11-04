"""
数据表生成 Agent 的 Pydantic 模型定义
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


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

class MetricCol(BaseModel):
    id: str = Field(..., description="指标ID")

class Column(BaseModel):
    """表字段模型"""
    name: str = Field(..., description="字段英文名称")
    nameZh: str = Field(..., description="字段中文名称")
    colProp: ColProp = Field(..., description="字段属性")
    dataType: DataType = Field(..., description="字段数据类型")
    colType: ColType = Field(default=ColType.NORMAL, description="字段分类")
    tableId: str = Field(default=..., description="所属表ID，新增时为空，修改时必填")
    metrics: Optional[List[MetricCol]] = Field(None, description="关联的指标列表,仅指标字段有效，且可选")


class TableInfo(BaseModel):
    """数据表完整信息模型"""
    name: str = Field(..., description="表英文名称")
    nameZh: str = Field(..., description="表中文名称")
    businessDomainId: str = Field(..., description="表所属业务域id")
    daName: str = Field(..., description="表所属库名")
    levelType: LevelType = Field(..., description="表层级类型")
    type: TableType = Field(..., description="表类型")
    tableProp: TableProp = Field(..., description="表应用类型")
    particleSize: str = Field(..., description="数据粒度")
    itOwner: str = Field(..., description="IT属主")
    itGroup: str = Field(..., description="IT属主分组")
    businessOwner: str = Field(..., description="业务属主")
    businessGroup: str = Field(..., description="业务属主分组")
    cols: List[Column] = Field(..., description="字段列表")

    class Config:
        use_enum_values = True