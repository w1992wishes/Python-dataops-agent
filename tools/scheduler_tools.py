"""
调度信息查询工具 - Mock实现
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import random


async def query_scheduler_info(
    system_name: str,
    version_no: str,
    table_name: str,
    db_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    根据system_name, version_no, db_name, table_name查询调度信息

    Args:
        system_name: 子系统英文名
        version_no: 版本号
        db_name: 库名(可选)
        table_name: 表名

    Returns:
        Dict: 调度信息字典，如果未找到返回None
    """
    # Mock数据 - 模拟调度系统查询结果
    mock_schedulers = {
        ("user_management", "1.0.0", "warehouse", "user_table"): {
            "schedule_name": "user_table_daily_sync",
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
            "dependency_tasks": ["user_data_preprocessing"],
            "last_run_time": datetime.now() - timedelta(days=1, hours=2),
            "next_run_time": datetime.now() + timedelta(hours=2),
            "created_time": datetime.now() - timedelta(days=30),
            "updated_time": datetime.now() - timedelta(days=5)
        },
        ("user_management", "1.0.0", None, "user_table"): {
            "schedule_name": "user_table_daily_sync",
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
            "dependency_tasks": ["user_data_preprocessing"],
            "last_run_time": datetime.now() - timedelta(days=1, hours=2),
            "next_run_time": datetime.now() + timedelta(hours=2),
            "created_time": datetime.now() - timedelta(days=30),
            "updated_time": datetime.now() - timedelta(days=5)
        },
        ("order_management", "2.1.0", "warehouse", "order_table"): {
            "schedule_name": "order_table_hourly_update",
            "schedule_id": "sch_002",
            "schedule_type": "hourly",
            "cron_expression": "0 * * * *",
            "schedule_status": "running",
            "priority": 8,
            "resource_config": {
                "cpu": 4,
                "memory": "8G",
                "timeout": 7200
            },
            "schedule_level": "D",
            "table_name_zh": "订单表",
            "schedule_description": "订单表小时级数据更新任务",
            "schedule_owner": "WANQINFENG063",
            "schedule_team": "数据开发团队",
            "dependency_tasks": ["order_raw_data_ingestion"],
            "last_run_time": datetime.now() - timedelta(minutes=30),
            "next_run_time": datetime.now() + timedelta(minutes=30),
            "created_time": datetime.now() - timedelta(days=45),
            "updated_time": datetime.now() - timedelta(days=2)
        },
        ("report_system", "3.0.0", "analytics", "report_table"): {
            "schedule_name": "report_table_weekly_generation",
            "schedule_id": "sch_003",
            "schedule_type": "weekly",
            "cron_expression": "0 3 * * 1",  # 每周一凌晨3点
            "schedule_status": "paused",
            "priority": 3,
            "resource_config": {
                "cpu": 8,
                "memory": "16G",
                "timeout": 14400
            },
            "schedule_level": "O",
            "table_name_zh": "报表表",
            "schedule_description": "报表表周报生成任务",
            "schedule_owner": "WANQINFENG063",
            "schedule_team": "数据开发团队",
            "dependency_tasks": ["daily_report_aggregation"],
            "last_run_time": datetime.now() - timedelta(days=7, hours=19),
            "next_run_time": datetime.now() + timedelta(days=1, hours=19),
            "created_time": datetime.now() - timedelta(days=90),
            "updated_time": datetime.now() - timedelta(days=10)
        }
    }

    # 查找匹配的调度配置
    key = (system_name, version_no, db_name, table_name)
    if key in mock_schedulers:
        schedule_data = mock_schedulers[key].copy()
        schedule_data["system_name"] = system_name
        schedule_data["version_no"] = version_no
        schedule_data["table_name"] = table_name
        schedule_data["db_name"] = db_name or "default_db"
        schedule_data["is_mock_schedule"] = False
        return schedule_data

    # 如果没有精确匹配，返回None表示未找到调度配置
    return None


async def generate_mock_schedule_info(
    system_name: str,
    version_no: str,
    table_name: str,
    db_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    生成Mock调度信息

    Args:
        system_name: 子系统英文名
        version_no: 版本号
        db_name: 库名(可选)
        table_name: 表名

    Returns:
        Dict: Mock调度信息字典
    """
    # 随机生成调度类型和配置
    schedule_types = ["daily", "hourly", "realtime", "manual", "weekly", "monthly"]
    schedule_statuses = ["running", "paused", "failed", "stopped"]
    schedule_levels = ["O", "D", "T", "S"]

    schedule_type = random.choice(schedule_types)
    schedule_status = random.choice(schedule_statuses)
    schedule_level = random.choice(schedule_levels)

    # 根据类型生成Cron表达式
    cron_expressions = {
        "daily": "0 2 * * *",
        "hourly": "0 * * * *",
        "realtime": "* * * * *",
        "manual": "0 0 1 * *",
        "weekly": "0 3 * * 1",
        "monthly": "0 4 1 * *"
    }

    # 生成调度名称
    schedule_name = f"{table_name}_{schedule_type}_schedule"

    # 生成资源配置
    cpu_count = random.choice([1, 2, 4, 8])
    memory_size = random.choice(["2G", "4G", "8G", "16G"])
    timeout_value = random.choice([1800, 3600, 7200, 14400])

    # 生成时间
    now = datetime.now()
    hours_offset = random.randint(1, 24)

    return {
        "schedule_name": schedule_name,
        "schedule_id": f"sch_mock_{random.randint(1000, 9999)}",
        "schedule_type": schedule_type,
        "cron_expression": cron_expressions.get(schedule_type, "0 0 * * *"),
        "schedule_status": schedule_status,
        "priority": random.randint(1, 10),
        "resource_config": {
            "cpu": cpu_count,
            "memory": memory_size,
            "timeout": timeout_value
        },
        "schedule_level": schedule_level,
        "system_name": system_name,
        "version_no": version_no,
        "table_name": table_name,
        "db_name": db_name or "default_db",
        "table_name_zh": f"{table_name}表",  # 简单的中文映射
        "schedule_description": f"{table_name}表的{schedule_type}调度任务",
        "schedule_owner": "WANQINFENG063",
        "schedule_team": "数据开发团队",
        "dependency_tasks": [],  # Mock数据暂时不包含依赖
        "last_run_time": now - timedelta(hours=hours_offset) if schedule_status in ["running", "failed"] else None,
        "next_run_time": now + timedelta(hours=hours_offset) if schedule_status == "running" else None,
        "created_time": now - timedelta(days=random.randint(10, 100)),
        "updated_time": now - timedelta(days=random.randint(1, 10)),
        "is_mock_schedule": True
    }


def validate_scheduler_params(
    system_name: str,
    version_no: str,
    table_name: str,
    db_name: Optional[str] = None
) -> tuple[bool, str]:
    """
    验证调度查询参数

    Args:
        system_name: 子系统英文名
        version_no: 版本号
        table_name: 表名
        db_name: 库名(可选)

    Returns:
        tuple: (是否有效, 错误信息)
    """
    if not system_name or not system_name.strip():
        return False, "system_name不能为空"

    if not version_no or not version_no.strip():
        return False, "version_no不能为空"

    if not table_name or not table_name.strip():
        return False, "table_name不能为空"

    # 验证长度限制
    if len(system_name) > 100:
        return False, "system_name长度不能超过100个字符"

    if len(version_no) > 50:
        return False, "version_no长度不能超过50个字符"

    if len(table_name) > 100:
        return False, "table_name长度不能超过100个字符"

    if db_name and len(db_name) > 100:
        return False, "db_name长度不能超过100个字符"

    # 验证格式（只允许字母、数字、下划线、短横线、点号）
    import re
    system_pattern = r'^[a-zA-Z0-9_-]+$'
    version_pattern = r'^[a-zA-Z0-9_.-]+$'  # 允许点号，支持版本号如 1.0.0
    name_pattern = r'^[a-zA-Z0-9_-]+$'

    if not re.match(system_pattern, system_name):
        return False, "system_name只能包含字母、数字、下划线、短横线"

    if not re.match(version_pattern, version_no):
        return False, "version_no只能包含字母、数字、点号、下划线、短横线"

    if not re.match(name_pattern, table_name):
        return False, "table_name只能包含字母、数字、下划线、短横线"

    if db_name and not re.match(name_pattern, db_name):
        return False, "db_name只能包含字母、数字、下划线、短横线"

    return True, ""