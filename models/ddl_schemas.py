"""
表DDL查询相关的数据模型
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TableDDLRequest(BaseModel):
    """表DDL查询请求模型"""
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
                "user_input": "查询用户表的DDL结构"
            }
        }


class TableDDLResponse(BaseModel):
    """表DDL查询响应模型"""
    ddl_content: str = Field(..., description="DDL内容")
    system_name: str = Field(..., description="子系统英文名")
    version_no: str = Field(..., description="版本号")
    table_id: str = Field(..., description="表ID")
    table_name: str = Field(..., description="表名")
    db_name: str = Field(..., description="库名")
    table_level_type: str = Field(..., description="表层级类型")
    table_name_zh: Optional[str] = Field(None, description="表中文名称")
    ddl_format_version: Optional[str] = Field("1.0", description="DDL格式版本")
    ddl_last_modified: Optional[str] = Field(None, description="DDL最后修改时间")
    is_mock_ddl: bool = Field(False, description="是否为模拟DDL")

    class Config:
        json_schema_extra = {
            "example": {
                "ddl_content": "CREATE TABLE `user_table` (\n  `user_id` string COMMENT '用户ID',\n  `user_name` string COMMENT '用户名'\n) COMMENT '用户表';",
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