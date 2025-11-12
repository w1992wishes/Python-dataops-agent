"""
ETL Agent 工具函数
"""
from typing import Optional, Dict, Any
import asyncio
from config.logging_config import get_logger
logger = get_logger(__name__)

# 模拟Hive ETL脚本数据库
MOCK_ETL_DB = {
    "policy_renewal": {
        "name": "policy_renewal",
        "version_id": "version_id",
        "source_table": "policy_renewal_source",
        "target_table": "policy_renewal_target",
        "rel_id": "rel_id",
        "database_name": "insurance_dw",
        "etl_code": '''-- 保费续签数据ETL脚本
INSERT OVERWRITE TABLE insurance_dw.policy_renewal_target
SELECT
    policy_id,
    customer_id,
    premium_amount,
    renewal_date,
    policy_status,
    current_timestamp() AS process_time
FROM insurance_dw.policy_renewal_source
WHERE renewal_date >= DATE_SUB(CURRENT_DATE, 30);''',
        "select_statement": '''SELECT
    policy_id,
    customer_id,
    premium_amount,
    renewal_date,
    policy_status,
    current_timestamp() AS process_time
FROM insurance_dw.policy_renewal_source
WHERE renewal_date >= DATE_SUB(CURRENT_DATE, 30)''',
        "insert_statement": '''INSERT OVERWRITE TABLE insurance_dw.policy_renewal_target
SELECT
    policy_id,
    customer_id,
    premium_amount,
    renewal_date,
    policy_status,
    current_timestamp() AS process_time
FROM insurance_dw.policy_renewal_source
WHERE renewal_date >= DATE_SUB(CURRENT_DATE, 30);''',
        "created_at": "2024-10-31T10:00:00",
        "updated_at": "2024-10-31T10:00:00"
    }
}


async def get_etl_script(table_name: str) -> Optional[Dict[str, Any]]:
    """
    异步获取ETL脚本完整信息

    Args:
        table_name: 表名

    Returns:
        ETL脚本完整信息，如果不存在则返回None
    """
    # 模拟异步查询
    await asyncio.sleep(0.01)

    # 查找匹配的脚本
    for script_name, script_info in MOCK_ETL_DB.items():
        if script_info["target_table"] == table_name or script_name == table_name:
            return {
                "etl_code": script_info.get("etl_code"),
                "rel_id": script_info.get("rel_id"),
                "target_table": script_info.get("target_table"),
                "database_name": script_info.get("database_name"),
                "version_id": script_info.get("version_id"),
                "rel_type": 'RS'
            }

    return None


# 导出工具列表
TOOLS = [get_etl_script]