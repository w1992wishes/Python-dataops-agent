"""
API结果模型
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from .responses import TableDDLResponse, SchedulerResponse


class APIErrorResponse(BaseModel):
    """API错误响应模型"""
    success: bool = Field(False, description="固定为False")
    error: str = Field(..., description="错误消息")
    error_code: Optional[str] = Field(None, description="错误代码")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "缺少必填参数: system_name, db_name",
                "error_code": "INVALID_PARAMETERS",
                "details": {
                    "missing_params": ["system_name", "db_name"]
                },
                "timestamp": "2025-01-01T12:00:00Z"
            }
        }


class BaseResponse(BaseModel):
    """基础响应模型 - 用于Agent相关接口"""
    success: bool = Field(..., description="请求是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="返回数据")
    error: Optional[str] = Field(None, description="错误信息")
    operation_type: Optional[str] = Field(None, description="操作类型：create/update/query")
    entity_type: Optional[str] = Field(None, description="相应的实体类型")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    message: Optional[str] = Field(None, description="操作消息")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"key": "value"},
                "operation_type": "create",
                "entity_type": "TABLE",
                "timestamp": "2025-01-25T12:00:00Z",
                "message": "操作成功"
            }
        }


class StreamingChunk(BaseModel):
    """流式输出数据块"""
    step: str = Field(..., description="当前步骤")
    data: Optional[Dict[str, Any]] = Field(None, description="步骤数据")
    message: Optional[str] = Field(None, description="步骤消息")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

    class Config:
        json_schema_extra = {
            "example": {
                "step": "analyze_request",
                "data": {"progress": 50},
                "message": "正在分析请求...",
                "timestamp": "2025-01-25T12:00:00Z"
            }
        }


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(default="healthy")
    version: str = Field(default="3.0.0")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "3.0.0",
                "timestamp": "2025-01-25T12:00:00Z"
            }
        }


class TableDDLResult(BaseModel):
    """表DDL查询结果模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="结果消息")
    data: Optional[TableDDLResponse] = Field(None, description="DDL响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "message": "成功获取表 'user_table' 的DDL内容",
                    "data": {
                        "ddl_content": "CREATE TABLE `user_table` (...)",
                        "system_name": "user_management",
                        "version_no": "1.0.0",
                        "table_id": "table_001",
                        "table_name": "user_table",
                        "db_name": "warehouse",
                        "table_level_type": "SUB",
                        "table_name_zh": "用户表",
                        "ddl_format_version": "1.0",
                        "ddl_last_modified": "2025-01-01T00:00:00Z",
                        "is_mock_ddl": False
                    },
                    "timestamp": "2025-01-01T12:00:00Z"
                },
                {
                    "success": False,
                    "message": "表 'user_table' 在数据库 'warehouse' 中不存在",
                    "data": None,
                    "timestamp": "2025-01-01T12:00:00Z"
                }
            ]
        }


class SchedulerResult(BaseModel):
    """调度查询结果模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="结果消息")
    data: Optional[SchedulerResponse] = Field(None, description="调度响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "message": "成功获取表 'user_table' 的调度信息",
                    "data": {
                        "schedule_name": "user_table_daily_sync",
                        "system_name": "user_management",
                        "version_no": "1.0.0",
                        "table_name": "user_table",
                        "db_name": "warehouse",
                        "schedule_id": "sch_001",
                        "schedule_type": "daily",
                        "cron_expression": "0 2 * * *",
                        "schedule_status": "running",
                        "priority": 5,
                        "resource_config": {
                            "cpu": 2,
                            "memory": "4G",
                            "timeout": 3600
                        },
                        "schedule_level": "D",
                        "table_name_zh": "用户表",
                        "schedule_description": "用户表每日数据同步任务",
                        "schedule_owner": "WANQINFENG063",
                        "schedule_team": "数据开发团队",
                        "last_run_time": "2025-01-24T02:00:00Z",
                        "next_run_time": "2025-01-25T02:00:00Z",
                        "dependency_tasks": ["user_data_preprocessing"],
                        "created_time": "2025-01-01T00:00:00Z",
                        "updated_time": "2025-01-20T10:30:00Z",
                        "is_mock_schedule": False
                    },
                    "timestamp": "2025-01-25T10:00:00Z"
                },
                {
                    "success": False,
                    "message": "表 'user_table' 在系统 'user_management' 中未找到调度配置",
                    "data": None,
                    "timestamp": "2025-01-25T10:00:00Z"
                }
            ]
        }


# ========== Agent相关响应模型 ==========

class TableResponse(BaseResponse):
    """表结构响应"""
    pass  # 使用BaseResponse的data字段存储所有数据


class ETLResponse(BaseResponse):
    """ETL脚本响应"""
    pass  # 使用BaseResponse的data字段存储所有数据


class MetricResponse(BaseResponse):
    """指标响应"""
    pass  # 使用BaseResponse的data字段存储所有数据