"""
数据表生成 Agent 的异步工具定义
"""
from typing import Dict, List, Optional, Any
import json
import asyncio
from models import TableInfo, Column


# 模拟数据库存储
MOCK_TABLE_DB = {
    ("test_db", "user_table"): {
        "name": "user_table",
        "nameZh": "用户表",
        "businessDomain": "user_management",
        "daName": "test_db",
        "levelType": "SUB",
        "type": "IAT",
        "tableProp": "NORMAL",
        "particleSize": "用户级别",
        "itOwner": "IT团队",
        "itGroup": "数据组",
        "businessOwner": "业务团队",
        "businessGroup": "用户组",
        "cols": [
            {
                "name": "user_id",
                "nameZh": "用户ID",
                "colProp": "DIM",
                "dataType": "string",
                "colType": 0
            },
            {
                "name": "user_name",
                "nameZh": "用户名",
                "colProp": "DIM",
                "dataType": "string",
                "colType": 0
            }
        ],
        "metricIds": ["metric_001"]
    }
}

MOCK_METRICS_DB = {
    "user_count": {
        "id": "metric_001",
        "name": "user_count",
        "nameZh": "用户数量",
        "description": "统计用户总数"
    },
    "active_user_count": {
        "id": "metric_002",
        "name": "active_user_count",
        "nameZh": "活跃用户数量",
        "description": "统计活跃用户总数"
    }
}


async def query_table(db_name: str, name: str) -> Optional[Dict[str, Any]]:
    """
    异步查询数据表信息

    Args:
        db_name: 数据库名称
        name: 表名称

    Returns:
        表信息字典，如果不存在则返回None
    """
    # 模拟异步数据库查询
    await asyncio.sleep(0.01)
    key = (db_name, name)
    if key in MOCK_TABLE_DB:
        return MOCK_TABLE_DB[key]
    return None