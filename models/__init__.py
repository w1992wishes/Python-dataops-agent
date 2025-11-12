"""
Models模块 - 定义所有数据模型
"""
from .table import TableInfo, Column, LevelType, TableType, TableProp, ColProp, DataType, ColType
from .metric_schemas import (
    MetricField, MetricOperationType,
    ApplicationScenarios, MetricType, MetricLevel, SafeLevel, PhysicalInfo, FieldInfo,
    MetricInfo, MetricAnalysisResult, MetricOperationResult
)
from .table_schemas import (
    TableOperationType, TableAnalysisResult, TableOperationResult
)
from .ddl_schemas import (
    TableDDLRequest, TableDDLResponse, TableDDLResult, APIErrorResponse
)
from .etl_schemas import (
    ETLOperationResult
)

__all__ = [
    # Table models
    'TableInfo',
    'Column',
    'LevelType',
    'TableType',
    'TableProp',
    'ColProp',
    'DataType',
    'ColType',

    # ETL models

    # Metric models
    'MetricField',
    'MetricOperationType',
    'ApplicationScenarios',
    'MetricType',
    'MetricLevel',
    'SafeLevel',
    'PhysicalInfo',
    'FieldInfo',
    'MetricInfo',
    'MetricAnalysisResult',
    'MetricOperationResult',

    # Table operation models
    'TableOperationType',
    'TableAnalysisResult',
    'TableOperationResult',

    # DDL models
    'TableDDLRequest',
    'TableDDLResponse',
    'TableDDLResult',
    'APIErrorResponse',

    # ETL models
    'ETLOperationResult'
]