"""
Core数据模型包 - 核心业务模型
"""
from .table import (
    # 枚举
    LevelType, TableType, TableProp, ColProp, DataType, ColType, TableOperationType,
    # 基础模型
    MetricCol, Column, TableInfo,
    # 操作结果模型
    TableAnalysisResult, TableOperationResult
)

from .metric import (
    # 枚举
    MetricOperationType, ApplicationScenarios, MetricType, MetricLevel, SafeLevel,
    # 数据模型
    MetricField, PhysicalInfo, FieldInfo, MetricInfo,
    # 操作结果模型
    MetricAnalysisResult, MetricOperationResult
)

from .etl import (
    # ETL操作结果
    ETLOperationResult
)

__all__ = [
    # Table models
    'LevelType', 'TableType', 'TableProp', 'ColProp', 'DataType', 'ColType', 'TableOperationType',
    'MetricCol', 'Column', 'TableInfo', 'TableAnalysisResult', 'TableOperationResult',

    # Metric models
    'MetricOperationType', 'ApplicationScenarios', 'MetricType', 'MetricLevel', 'SafeLevel',
    'MetricField', 'PhysicalInfo', 'FieldInfo', 'MetricInfo',
    'MetricAnalysisResult', 'MetricOperationResult',

    # ETL models
    'ETLOperationResult'
]