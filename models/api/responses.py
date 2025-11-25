"""
API响应模型
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


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


class SchedulerResponse(BaseModel):
    """调度查询响应模型"""
    schedule_name: str = Field(..., description="调度任务名称")
    system_name: str = Field(..., description="子系统英文名")
    version_no: str = Field(..., description="版本号")
    table_name: str = Field(..., description="表名")
    db_name: str = Field(..., description="库名")
    schedule_id: str = Field(..., description="调度任务ID")
    schedule_type: str = Field(..., description="调度类型",
                              examples=["daily", "hourly", "realtime", "manual"])
    cron_expression: str = Field(..., description="Cron表达式")
    schedule_status: str = Field(..., description="调度状态",
                                 examples=["running", "paused", "failed", "stopped"])
    priority: int = Field(..., description="优先级", ge=1, le=10)
    resource_config: Dict[str, Any] = Field(..., description="资源配置")
    schedule_level: str = Field(..., description="调度层级",
                                examples=["O", "D", "T", "S"])
    table_name_zh: Optional[str] = Field(None, description="表中文名称")
    schedule_description: Optional[str] = Field(None, description="调度描述")
    schedule_owner: str = Field(..., description="调度负责人")
    schedule_team: str = Field(..., description="调度负责团队")
    last_run_time: Optional[datetime] = Field(None, description="上次运行时间")
    next_run_time: Optional[datetime] = Field(None, description="下次运行时间")
    dependency_tasks: List[str] = Field(default_factory=list, description="依赖任务列表")
    created_time: Optional[datetime] = Field(None, description="创建时间")
    updated_time: Optional[datetime] = Field(None, description="更新时间")
    is_mock_schedule: bool = Field(False, description="是否为模拟调度信息")

    class Config:
        json_schema_extra = {
            "example": {
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
            }
        }


