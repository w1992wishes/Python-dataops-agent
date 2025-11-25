"""
Models模块 - 定义所有数据模型
重构后：从core和api模块导入
"""
from .core.table import (
    # 枚举
    LevelType, TableType, TableProp, ColProp, DataType, ColType, TableOperationType,
    # 基础模型
    MetricCol, Column, TableInfo,
    # 操作结果模型
    TableAnalysisResult, TableOperationResult
)

from .core.metric import (
    # 枚举
    MetricOperationType, ApplicationScenarios, MetricType, MetricLevel, SafeLevel,
    # 数据模型
    MetricField, PhysicalInfo, FieldInfo, MetricInfo,
    # 操作结果模型
    MetricAnalysisResult, MetricOperationResult
)

from .core.etl import ETLOperationResult

from .api import (
    # API请求
    BaseQueryRequest, TableDDLRequest, SchedulerRequest,
    BaseRequest, MetricRequest, MetricStreamingRequest, ETLRequest,
    # API响应
    TableDDLResponse, SchedulerResponse,
    TableResponse, ETLResponse, MetricResponse,
    # API结果
    TableDDLResult, SchedulerResult, APIErrorResponse,
    # 通用API模型
    BaseResponse, StreamingChunk, HealthResponse
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
    'ETLOperationResult',

    # API models
    'BaseQueryRequest', 'TableDDLRequest', 'SchedulerRequest',
    'BaseRequest', 'MetricRequest', 'MetricStreamingRequest', 'ETLRequest',
    'TableDDLResponse', 'SchedulerResponse',
    'TableResponse', 'ETLResponse', 'MetricResponse',
    'TableDDLResult', 'SchedulerResult', 'APIErrorResponse',
    'BaseResponse', 'StreamingChunk', 'HealthResponse'
]