"""
指标管理相关的数据模型
"""
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class MetricOperationType(Enum):
    """指标操作类型"""
    CREATE = "create"
    UPDATE = "update"
    QUERY = "query"


@dataclass
class MetricField:
    """指标字段"""
    code: str
    name: str
    nameZh: str
    type: str
    description: Optional[str] = None
    required: bool = False


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


@dataclass
class PhysicalInfo:
    """物理信息，用于派生指标"""
    metricId: str