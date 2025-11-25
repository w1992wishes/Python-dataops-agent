"""
调度查询服务
"""
from typing import Dict, Any, Optional
from datetime import datetime

from tools.scheduler_tools import query_scheduler_info, generate_mock_schedule_info, validate_scheduler_params
# from models.api.responses import SchedulerResponse  # 不再需要，返回字典格式
from config.logging_config import get_logger

logger = get_logger(__name__)


class SchedulerService:
    """调度查询服务类"""

    def __init__(self):
        """初始化调度服务"""
        logger.info("⏰ 调度服务初始化完成")

    async def get_scheduler_info_with_validation(
        self,
        system_name: str,
        version_no: str,
        table_name: str,
        db_name: Optional[str] = None,
        user_input: str = ""
    ) -> Dict[str, Any]:
        """
        带参数验证的调度信息查询

        Args:
            system_name: 子系统英文名
            version_no: 版本号
            db_name: 库名(可选)
            table_name: 表名
            user_input: 用户输入描述

        Returns:
            Dict: 包含查询结果的标准化响应
        """
        try:
            logger.info(f"🔍 开始调度查询: {system_name} v{version_no}, 表: {db_name}.{table_name if db_name else table_name}")
            if user_input:
                logger.info(f"📝 用户需求: {user_input[:100]}...")

            # 1. 参数验证
            is_valid, error_msg = validate_scheduler_params(system_name, version_no, table_name, db_name)
            if not is_valid:
                error_result = {
                    "success": False,
                    "message": f"参数验证失败: {error_msg}",
                    "data": None
                }
                logger.warning(f"⚠️ 参数验证失败: {error_msg}")
                return error_result

            # 2. 查询调度信息
            schedule_data = await query_scheduler_info(system_name, version_no, table_name, db_name)

            if schedule_data:
                # 找到了调度配置
                logger.info(f"✅ 找到调度配置: {schedule_data.get('schedule_name', 'N/A')}")

                # 转换为字典格式（BaseResponse的data字段期望dict类型）
                response_data = schedule_data

                success_result = {
                    "success": True,
                    "message": f"成功获取表 '{table_name}' 的调度信息",
                    "data": response_data
                }
                logger.info(f"📊 调度信息: {schedule_data.get('schedule_type', 'N/A')} - {schedule_data.get('schedule_status', 'N/A')}")
                return success_result
            else:
                # 未找到调度配置，生成Mock数据
                logger.info(f"ℹ️ 未找到表 '{table_name}' 的调度配置，生成Mock数据")

                mock_schedule_data = await generate_mock_schedule_info(system_name, version_no, table_name, db_name)

                # 直接使用字典格式
                response_data = mock_schedule_data

                success_result = {
                    "success": True,
                    "message": f"成功获取表 '{table_name}' 的调度信息（Mock数据）",
                    "data": response_data
                }
                logger.info(f"📊 Mock调度信息: {mock_schedule_data.get('schedule_type', 'N/A')} - {mock_schedule_data.get('schedule_status', 'N/A')}")
                return success_result

        except Exception as e:
            error_msg = f"调度查询服务异常: {str(e)}"
            logger.error(f"💥 {error_msg}")

            error_result = {
                "success": False,
                "message": error_msg,
                "data": None
            }
            return error_result

    async def get_scheduler_info(
        self,
        system_name: str,
        version_no: str,
        table_name: str,
        db_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取调度信息（简化版本）

        Args:
            system_name: 子系统英文名
            version_no: 版本号
            db_name: 库名(可选)
            table_name: 表名

        Returns:
            Dict: 调度信息字典，如果未找到返回None
        """
        try:
            # 直接查询调度信息
            schedule_data = await query_scheduler_info(system_name, version_no, table_name, db_name)

            if schedule_data:
                return schedule_data
            else:
                # 生成Mock数据
                mock_schedule_data = await generate_mock_schedule_info(system_name, version_no, table_name, db_name)
                return mock_schedule_data

        except Exception as e:
            logger.error(f"💥 获取调度信息异常: {str(e)}")
            return None

    async def health_check(self) -> Dict[str, Any]:
        """
        调度服务健康检查

        Returns:
            Dict: 健康检查结果
        """
        try:
            # 执行一个简单的查询来验证服务状态
            test_schedule = await query_scheduler_info("test_system", "1.0.0", "test_table")

            return {
                "service": "scheduler_service",
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "message": "调度服务运行正常"
            }
        except Exception as e:
            return {
                "service": "scheduler_service",
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "message": "调度服务异常"
            }


# 创建全局调度服务实例
scheduler_service = SchedulerService()