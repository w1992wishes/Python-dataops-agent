"""
指标数据模型定义
基于metric_data格式的Pydantic模型，融入了原metric.py的所有枚举和定义
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field


# ==================== 枚举定义 ====================

class MetricOperationType(str, Enum):
    """指标操作类型"""
    CREATE = "create"
    UPDATE = "update"
    QUERY = "query"


class ApplicationScenarios(str, Enum):
    """指标应用场景"""
    HIVE_OFFLINE = "HIVE_OFFLINE"
    OLAP_ONLINE = "OLAP_ONLINE"


class MetricType(str, Enum):
    """指标类型"""
    IA = "IA"  # 原子指标
    IB = "IB"  # 派生指标


class MetricLevel(str, Enum):
    """指标重要等级"""
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"


class SafeLevel(str, Enum):
    """安全等级"""
    S1 = "S1"  # 普通数据
    S2 = "S2"
    S3 = "S3"
    S4 = "S4"
    S5 = "S5"  # 国密数据


# ==================== 数据类定义 ====================

@dataclass
class MetricField:
    """指标字段"""
    code: str
    name: str
    nameZh: str
    type: str
    description: Optional[str] = None
    required: bool = False


@dataclass
class PhysicalInfo(BaseModel):
    """物理信息，用于派生指标"""
    metricId: Optional[str] = Field(default=None, description="关联的指标ID，派生指标使用")


class FieldInfo(BaseModel):
    """字段信息，用于原子指标"""
    fieldName: str = Field(description="字段名称")
    fieldType: str = Field(description="字段类型")
    fieldDesc: str = Field(description="字段描述")


# ==================== Pydantic模型定义 ====================

class MetricInfo(BaseModel):
    """指标信息模型，基于metric_data格式"""
    id: Optional[str] = Field(default=None, description="指标ID，新增时为空，修改时必填")
    nameZh: str = Field(description="指标中文名称")
    name: str = Field(description="指标英文名称")
    code: str = Field(default="", description="指标编码")
    applicationScenarios: str = Field(default="HIVE_OFFLINE", description="应用场景")
    type: str = Field(default="IA", description="指标类型：IA原子指标/IB派生指标")
    lv: str = Field(default="T2", description="指标等级：T1/T2/T3")
    processDomainId: str = Field(default="domain_001", description="业务域ID")
    safeLv: str = Field(default="S1", description="安全等级：S1-S5")
    businessCaliberDesc: str = Field(default="", description="业务口径描述，是通俗易懂的业务能读懂的指标定义")
    businessOwner: str = Field(default="待指定", description="业务负责人")
    businessTeam: str = Field(default="待指定", description="业务团队")
    statisticalObject: str = Field(default="待定义", description="统计对象")
    statisticalRule: str = Field(default="待定义", description="统计规则")
    statisticalRuleIt: str = Field(default="待定义", description="IT统计规则")
    statisticalTime: str = Field(default="日", description="统计时间粒度")
    unit: str = Field(default="个", description="指标单位")
    physicalInfoList: Optional[List[PhysicalInfo]] = Field(default=None, description="物理信息列表，派生指标的来源指标metricId信息")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "metric_001",
                "nameZh": "月度收入",
                "name": "revenue_monthly",
                "code": "REVENUE_MONTHLY",
                "applicationScenarios": "HIVE_OFFLINE",
                "type": "IA",
                "lv": "T1",
                "processDomainId": "domain_001",
                "safeLv": "S1",
                "businessCaliberDesc": "统计每个月的总收入金额，包含所有产品线和服务",
                "businessOwner": "张三",
                "businessTeam": "财务部",
                "statisticalObject": "订单",
                "statisticalRule": "按月汇总订单金额",
                "statisticalRuleIt": "SELECT SUM(amount) FROM orders WHERE MONTH(create_time) = MONTH(CURRENT_DATE)",
                "statisticalTime": "月",
                "unit": "元",
                "physicalInfoList": None
            }
        }
    }


class MetricOperationResult(BaseModel):
    """指标操作结果模型"""
    operation_type: str = Field(description="操作类型：create/update/query")
    status: str = Field(description="操作状态：success/exist/not_exist/error")
    message: str = Field(description="操作结果消息")
    metric_info: Optional[MetricInfo] = Field(default=None, description="指标信息")
    existing_metric: Optional[MetricInfo] = Field(default=None, description="已存在的指标信息")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "operation_type": "create",
                    "status": "exist",
                    "message": "指标已存在，无需重复创建",
                    "metric_info": {
                        "nameZh": "月度收入",
                        "name": "revenue_monthly",
                        "code": "REVENUE_MONTHLY",
                        "type": "IA",
                        "lv": "T1"
                    },
                    "existing_metric": {
                        "nameZh": "月度收入",
                        "name": "revenue_monthly",
                        "code": "REVENUE_MONTHLY",
                        "type": "IA",
                        "lv": "T1"
                    }
                },
                {
                    "operation_type": "update",
                    "status": "not_exist",
                    "message": "指标不存在，无法修改",
                    "metric_info": None,
                    "existing_metric": None
                },
                {
                    "operation_type": "create",
                    "status": "success",
                    "message": "指标创建成功",
                    "metric_info": {
                        "nameZh": "新指标",
                        "name": "new_metric",
                        "code": "",
                        "type": "IA",
                        "lv": "T2"
                    },
                    "existing_metric": None
                }
            ]
        }
    }