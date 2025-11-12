"""
数据表生成 Agent 的异步工具定义
"""
from typing import Dict, Optional, Any
import asyncio

# 模拟数据库存储
MOCK_TABLE_DB = {
    "user_table": {
        "id": "table_001",
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

MOCK_DDL_DB = {
    "table_001": {
        "ddl_content": """
CREATE TABLE `user_table` (
  `user_id` string COMMENT '用户ID',
  `user_name` string COMMENT '用户名',
  `create_time` date COMMENT '创建时间',
  `update_time` date COMMENT '更新时间'
) COMMENT '用户表'
PARTITIONED BY (create_time)
STORED AS ORC;
        """.strip(),
        "format_version": "1.0",
        "last_modified": "2025-01-01T00:00:00Z"
    },
    "table_002": {
        "ddl_content": """
CREATE TABLE `order_table` (
  `order_id` string COMMENT '订单ID',
  `user_id` string COMMENT '用户ID',
  `order_amount` float COMMENT '订单金额',
  `order_time` date COMMENT '订单时间'
) COMMENT '订单表'
PARTITIONED BY (order_time)
STORED AS ORC;
        """.strip(),
        "format_version": "1.0",
        "last_modified": "2025-01-01T00:00:00Z"
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


async def query_table(name: str) -> Optional[Dict[str, Any]]:
    """
    异步查询数据表信息

    Args:
        name: 表名称

    Returns:
        表信息字典，如果不存在则返回None
    """
    # 模拟异步数据库查询
    await asyncio.sleep(0.01)
    if name in MOCK_TABLE_DB:
        return MOCK_TABLE_DB[name]
    return None


async def query_table_ddl(table_name: str) -> str:
    """
    根据表名直接获取DDL代码

    Args:
        table_name: 表名称

    Returns:
        DDL内容字符串
    """
    # 模拟异步数据库查询
    await asyncio.sleep(0.01)

    # 模拟数据库中存储的表DDL映射
    TABLE_DDL_MAPPING = {
        "user_table": """
CREATE TABLE `user_table` (
  `user_id` string COMMENT '用户ID',
  `user_name` string COMMENT '用户名',
  `user_age` int COMMENT '用户年龄',
  `create_time` date COMMENT '创建时间',
  `update_time` date COMMENT '更新时间'
) COMMENT '用户表'
PARTITIONED BY (create_time)
STORED AS ORC;
        """.strip(),

        "policy_renewal": """
CREATE TABLE `policy_renewal` (
  `policy_id` string COMMENT '保单号',
  `user_id` string COMMENT '用户ID',
  `renewal_date` date COMMENT '续期日期',
  `premium_amount` float COMMENT '保费金额',
  `policy_status` string COMMENT '保单状态',
  `create_time` date COMMENT '创建时间'
) COMMENT '保单续期表'
PARTITIONED BY (create_time)
STORED AS ORC;
        """.strip(),

        "new_table": """
CREATE TABLE `new_table` (
  `id` string COMMENT '主键',
  `user_data` string COMMENT '用户数据',
  `statistics` string COMMENT '统计信息',
  `process_date` date COMMENT '处理日期'
) COMMENT '新表'
PARTITIONED BY (process_date)
STORED AS ORC;
        """.strip()
    }

    # 返回对应表的DDL，如果没有找到则返回基础DDL
    if table_name in TABLE_DDL_MAPPING:
        return TABLE_DDL_MAPPING[table_name]
    else:
        # 返回默认DDL
        default_ddl = f"""
CREATE TABLE `{table_name}` (
  `id` string COMMENT '主键',
  `name` string COMMENT '名称',
  `create_time` date COMMENT '创建时间'
) COMMENT '{table_name}表'
PARTITIONED BY (create_time)
STORED AS ORC;
        """.strip()
        return default_ddl