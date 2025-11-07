"""
指标管理工具函数
"""
import asyncio
from typing import Dict, List, Optional, Any

from config.logging_config import get_logger
logger = get_logger(__name__)


# 模拟指标数据库 - 使用新的MetricSchema格式
MOCK_METRIC_DB = {
    "revenue_monthly": {
        "id": "metric_001",
        "nameZh": "月度收入",
        "name": "revenue_monthly",
        "code": "REVENUE_MONTHLY",
        "applicationScenarios": "HIVE_OFFLINE",
        "type": "IA",
        "lv": "T1",
        "processDomainId": "domain_001",
        "safeLv": "S1",
        "businessCaliberDesc": "统计每个月的总收入金额，包含所有产品线和服务",
        "businessOwner": "张三",
        "businessTeam": "财务部",
        "statisticalObject": "订单",
        "statisticalRule": "按月汇总订单金额",
        "statisticalRuleIt": "SELECT SUM(amount) FROM orders WHERE MONTH(create_time) = MONTH(CURRENT_DATE)",
        "statisticalTime": "月",
        "physicalInfoList": None,
        "create_time": "2023-01-01T00:00:00Z",
        "update_time": "2023-10-15T10:30:00Z"
    },
    "user_count": {
        "id": "metric_002",
        "nameZh": "用户数量",
        "name": "user_count",
        "code": "USER_COUNT",
        "applicationScenarios": "HIVE_OFFLINE",
        "type": "IA",
        "lv": "T2",
        "processDomainId": "domain_002",
        "safeLv": "S1",
        "businessCaliberDesc": "统计平台的活跃用户总数，按月统计",
        "businessOwner": "李四",
        "businessTeam": "运营部",
        "statisticalObject": "用户",
        "statisticalRule": "统计月活跃用户数",
        "statisticalRuleIt": "SELECT COUNT(DISTINCT user_id) FROM user_logs WHERE last_login >= date_trunc('month', current_date)",
        "statisticalTime": "月",
        "physicalInfoList": None,
        "create_time": "2023-02-01T00:00:00Z",
        "update_time": "2023-11-01T15:45:00Z"
    },
    "conversion_rate": {
        "id": "metric_003",
        "nameZh": "转化率",
        "name": "conversion_rate",
        "code": "CONVERSION_RATE",
        "applicationScenarios": "OLAP_ONLINE",
        "type": "IB",
        "lv": "T1",
        "processDomainId": "domain_002",
        "safeLv": "S2",
        "businessCaliberDesc": "计算从注册到首次付费的用户转化率，按月统计",
        "businessOwner": "王五",
        "businessTeam": "运营部",
        "statisticalObject": "用户",
        "statisticalRule": "付费用户数/注册用户数*100%",
        "statisticalRuleIt": "(SELECT COUNT(DISTINCT paid_users) / COUNT(DISTINCT registered_users)) * 100",
        "statisticalTime": "月",
        "physicalInfoList": [
            {"metricId": "metric_001"},
            {"metricId": "metric_002"}
        ],
        "create_time": "2023-03-01T00:00:00Z",
        "update_time": "2023-10-20T09:15:00Z"
    }
}


async def query_metric_by_name_zh(metric_name_zh: str) -> Optional[Dict[str, Any]]:
    """根据指标中文名称查询指标"""
    logger.info(f"🔍 根据中文名称查询指标: {metric_name_zh}")

    # 模拟异步查询延迟
    await asyncio.sleep(0.1)

    # 在模拟数据库中搜索匹配的指标
    result = None
    for metric_data in MOCK_METRIC_DB.values():
        if metric_data.get("nameZh") == metric_name_zh:
            result = metric_data
            break

    if result:
        logger.info(f"✅ 找到指标: {result.get('nameZh', 'N/A')} ({result.get('code', 'N/A')})")
    else:
        logger.info(f"ℹ️ 未找到指标: {metric_name_zh}")

    return result

async def get_metric_domains() -> List[Dict[str, Any]]:
    """获取业务域列表"""
    # 模拟异步查询延迟
    await asyncio.sleep(0.05)
    return [
        {"id": "domain_001", "name": "财务域", "nameZh": "财务"},
        {"id": "domain_002", "name": "用户域", "nameZh": "用户"},
        {"id": "domain_003", "name": "产品域", "nameZh": "产品"},
        {"id": "domain_004", "name": "运营域", "nameZh": "运营"}
    ]