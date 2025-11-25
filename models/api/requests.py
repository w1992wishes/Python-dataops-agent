"""
API请求模型
"""
from typing import Optional
from pydantic import BaseModel, Field


class BaseQueryRequest(BaseModel):
    """基础查询请求模型 - 被DDL和调度API共用"""
    system_name: str = Field(..., description="子系统英文名", max_length=100)
    version_no: str = Field(..., description="版本号", max_length=50)
    db_name: Optional[str] = Field(None, description="库名", max_length=100)
    table_name: str = Field(..., description="表名", max_length=100)
    user_input: str = Field(default="", description="用户输入的需求描述")

    class Config:
        json_schema_extra = {
            "example": {
                "system_name": "user_management",
                "version_no": "1.0.0",
                "db_name": "warehouse",
                "table_name": "user_table",
                "user_input": "查询用户表的相关信息"
            }
        }


class TableDDLRequest(BaseQueryRequest):
    """表DDL查询请求模型"""

    class Config:
        json_schema_extra = {
            "example": {
                "system_name": "user_management",
                "version_no": "1.0.0",
                "db_name": "warehouse",
                "table_name": "user_table",
                "user_input": "查询用户表的DDL结构"
            }
        }


class SchedulerRequest(BaseQueryRequest):
    """调度查询请求模型"""

    class Config:
        json_schema_extra = {
            "example": {
                "system_name": "user_management",
                "version_no": "1.0.0",
                "db_name": "warehouse",
                "table_name": "user_table",
                "user_input": "查询用户表的调度信息"
            }
        }


# ========== Agent相关请求模型 ==========

class BaseRequest(BaseModel):
    """基础请求模型 - 用于Agent相关接口"""
    user_input: str = Field(..., description="用户自然语言输入")


class MetricRequest(BaseModel):
    """指标管理请求模型"""
    user_input: str = Field(..., description="用户自然语言输入")
    um: str = Field(..., description="用户账号")
    metric_name_zh: str = Field(..., description="指标中文名称")

    class Config:
        json_schema_extra = {
            "example": {
                "user_input": "创建一个用户活跃度指标",
                "um": "WANQINFENG063",
                "metric_name_zh": "用户活跃度"
            }
        }


class MetricStreamingRequest(BaseModel):
    """指标流式请求"""
    user_input: str = Field(..., description="用户自然语言输入")
    um: str = Field(..., description="用户账号")
    metric_name_zh: str = Field(..., description="指标中文名称")

    class Config:
        json_schema_extra = {
            "example": {
                "user_input": "创建一个用户活跃度指标",
                "um": "WANQINFENG063",
                "metric_name_zh": "用户活跃度"
            }
        }


class ETLRequest(BaseRequest):
    """ETL脚本请求模型"""
    table_name: str = Field(..., description="目标表名")

    class Config:
        json_schema_extra = {
            "example": {
                "user_input": "为用户表生成ETL脚本",
                "table_name": "user_table"
            }
        }