"""
ETL开发相关的数据模型定义
支持基于DDL变动的智能ETL代码修改
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ETLOperationResult(BaseModel):
    """ETL操作结果模型"""
    operation_type: str = Field(description="操作类型：create/update/optimize")
    status: str = Field(description="操作状态：success/error/no_changes")
    message: str = Field(description="操作结果消息")

    # 输入信息
    table_name: str = Field(description="表名")

    # 输出信息
    modified_etl_code: Optional[str] = Field(default=None, description="修改后的ETL代码")
    changes_summary: Optional[List[str]] = Field(default=None, description="修改摘要列表")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "operation_type": "update",
                    "status": "success",
                    "message": "ETL代码已根据DDL变更成功修改",
                    "table_name": "user_table",
                    "modified_etl_code": "INSERT INTO user_table SELECT user_id, user_name, user_age FROM source_table",
                    "changes_summary": [
                        "在SELECT语句中添加了user_age字段",
                        "保持了原有的数据加载逻辑"
                    ]
                },
                {
                    "operation_type": "create",
                    "status": "success",
                    "message": "ETL代码创建成功",
                    "table_name": "new_table",
                    "modified_etl_code": "INSERT INTO new_table SELECT id, name FROM source_table",
                    "changes_summary": [
                        "创建了完整的ETL加载逻辑",
                        "添加了必要的配置参数"
                    ]
                }
            ]
        }
    }