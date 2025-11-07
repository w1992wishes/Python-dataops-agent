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
        "description": "保费续签ETL脚本",
        "source_table": "policy_renewal_source",
        "target_table": "policy_renewal_target",
        "script_type": "hive_sql",
        "database": "insurance_dw",
        "code": '''-- 保费续签数据ETL脚本
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
    },
    "customer_profile": {
        "name": "customer_profile",
        "description": "客户画像ETL脚本",
        "source_table": "customer_info",
        "target_table": "customer_profile",
        "script_type": "hive_sql",
        "database": "insurance_dw",
        "code": '''-- 客户画像数据ETL脚本
INSERT OVERWRITE TABLE insurance_dw.customer_profile
SELECT
    customer_id,
    COUNT(*) AS policy_count,
    SUM(premium_amount) AS total_premium,
    AVG(premium_amount) AS avg_premium,
    MAX(premium_amount) AS max_premium,
    MIN(premium_amount) AS min_premium,
    current_timestamp() AS process_time
FROM insurance_dw.customer_info
GROUP BY customer_id;''',
        "select_statement": '''SELECT
    customer_id,
    COUNT(*) AS policy_count,
    SUM(premium_amount) AS total_premium,
    AVG(premium_amount) AS avg_premium,
    MAX(premium_amount) AS max_premium,
    MIN(premium_amount) AS min_premium,
    current_timestamp() AS process_time
FROM insurance_dw.customer_info
GROUP BY customer_id''',
        "insert_statement": '''INSERT OVERWRITE TABLE insurance_dw.customer_profile
SELECT
    customer_id,
    COUNT(*) AS policy_count,
    SUM(premium_amount) AS total_premium,
    AVG(premium_amount) AS avg_premium,
    MAX(premium_amount) AS max_premium,
    MIN(premium_amount) AS min_premium,
    current_timestamp() AS process_time
FROM insurance_dw.customer_info
GROUP BY customer_id;''',
        "created_at": "2024-10-31T10:00:00",
        "updated_at": "2024-10-31T10:00:00"
    }
}


async def get_etl_script(table_name: str) -> Optional[Dict[str, Any]]:
    """
    异步获取ETL脚本代码

    Args:
        table_name: 表名

    Returns:
        ETL脚本代码字符串，如果不存在则返回None
    """
    # 模拟异步查询
    await asyncio.sleep(0.01)

    # 查找匹配的脚本
    for script_name, script_info in MOCK_ETL_DB.items():
        if script_info["target_table"] == table_name or script_name == table_name:
            return script_info.get("code")

    return None




# 导出工具列表
TOOLS = [get_etl_script]