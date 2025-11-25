"""
表DDL查询服务
直接函数式实现，无需Agent架构
"""
from typing import Dict, Any, Optional
import asyncio
import traceback
from datetime import datetime
from config.logging_config import get_logger

from tools.table_tools import query_table, query_table_ddl


class TableDDLService:
    """表DDL查询服务 - 简单高效的函数式实现"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.query_table_tool = query_table
        self.query_table_ddl_tool = query_table_ddl

    async def get_table_ddl(self, table_name: str) -> Dict[str, Any]:
        """
        获取表DDL的完整流程

        Args:
            system_name: 子系统英文名
            version_no: 版本号
            db_name: 库名
            table_name: 表名
            user_input: 用户输入（虽然用不上，但保留接口兼容性）

        Returns:
            {
                "success": bool,
                "message": str,
                "data": Optional[Dict]  # 包含ddl_content, system_name, version_no, table_id, table_name, db_name, table_level_type
            }
        """
        try:
            self.logger.info(f"🔍 开始查询表DDL:  {table_name}")

            # Step 1: 查询表是否存在
            self.logger.info(f"📊 步骤1: 查询表是否存在 -  {table_name}")
            table_info = await self.query_table_tool(name=table_name)

            if not table_info:
                self.logger.warning(f"⚠️ 表不存在: {table_name}")
                return {
                    "success": False,
                    "message": f"表 '{table_name}' 不存在",
                    "data": None
                }

            self.logger.info(f"✅ 找到表: {table_info.get('nameZh', table_name)} (ID: {table_info.get('id')})")

            # Step 2: 获取DDL内容
            self.logger.info(f"📄 步骤2: 获取DDL内容")
            try:
                ddl_content = await self.query_table_ddl_tool(
                    table_name=table_name
                )

                self.logger.info(f"✅ DDL查询成功")

            except ValueError as e:
                self.logger.error(f"❌ DDL查询参数错误: {str(e)}")
                return {
                    "success": False,
                    "message": f"DDL查询参数错误: {str(e)}",
                    "data": None
                }
            except Exception as e:
                self.logger.error(f"❌ DDL查询失败: {str(e)}")
                self.logger.error(f"❌ DDL查询异常链路: {traceback.format_exc()}")
                return {
                    "success": False,
                    "message": f"获取DDL失败: {str(e)}",
                    "data": None
                }

            # Step 3: 构建标准化结果
            self.logger.info(f"🏗️ 步骤3: 构建标准化结果")
            result_data = {
                "ddl_content": ddl_content,
                "table_id": table_info["id"],
                "table_name": table_name,
                "table_level_type": table_info["levelType"],
                "table_name_zh": table_info.get("nameZh", table_name),
                "ddl_last_modified": datetime.now().isoformat(),
            }

            self.logger.info(f"🎉 表DDL查询完成: {table_name} ({len(result_data['ddl_content'])} 字符)")

            return {
                "success": True,
                "message": f"成功获取表 '{table_name}' 的DDL内容",
                "data": result_data
            }

        except Exception as e:
            self.logger.error(f"💥 表DDL查询服务异常: {str(e)}")
            self.logger.error(f"💥 表DDL查询服务异常链路: {traceback.format_exc()}")
            return {
                "success": False,
                "message": f"服务异常: {str(e)}",
                "data": None
            }

    async def validate_parameters(self, system_name: str, version_no: str,
                                db_name: str, table_name: str, user_input: str) -> Dict[str, Any]:
        """
        验证输入参数

        Returns:
            {
                "valid": bool,
                "message": str,
                "normalized_params": Optional[Dict]
            }
        """
        try:
            # 基础参数验证
            required_params = {
                "system_name": system_name,
                "version_no": version_no,
                "table_name": table_name
            }

            missing_params = [k for k, v in required_params.items() if not v or not v.strip()]

            if missing_params:
                return {
                    "valid": False,
                    "message": f"缺少必填参数: {', '.join(missing_params)}",
                    "normalized_params": None
                }

            # 参数标准化
            normalized_params = {
                "system_name": system_name.strip(),
                "version_no": version_no.strip(),
                "db_name": db_name.strip().lower() if db_name else "",
                "table_name": table_name.strip().lower(),
                "user_input": user_input.strip() if user_input else ""
            }

            # 额外验证
            import re

            # 长度验证
            if len(normalized_params["system_name"]) > 100:
                return {
                    "valid": False,
                    "message": "system_name 长度不能超过100个字符",
                    "normalized_params": None
                }

            if len(normalized_params["table_name"]) > 100:
                return {
                    "valid": False,
                    "message": "table_name 长度不能超过100个字符",
                    "normalized_params": None
                }

            # 格式验证
            system_pattern = r'^[a-zA-Z0-9_-]+$'
            version_pattern = r'^[a-zA-Z0-9_.-]+$'
            name_pattern = r'^[a-zA-Z0-9_-]+$'

            if not re.match(system_pattern, normalized_params["system_name"]):
                return {
                    "valid": False,
                    "message": "system_name只能包含字母、数字、下划线、短横线",
                    "normalized_params": None
                }

            if not re.match(version_pattern, normalized_params["version_no"]):
                return {
                    "valid": False,
                    "message": "version_no只能包含字母、数字、点号、下划线、短横线",
                    "normalized_params": None
                }

            if not re.match(name_pattern, normalized_params["table_name"]):
                return {
                    "valid": False,
                    "message": "table_name只能包含字母、数字、下划线、短横线",
                    "normalized_params": None
                }

            if normalized_params["db_name"] and not re.match(name_pattern, normalized_params["db_name"]):
                return {
                    "valid": False,
                    "message": "db_name只能包含字母、数字、下划线、短横线",
                    "normalized_params": None
                }

            self.logger.info(f"✅ 参数验证通过: {normalized_params['db_name']}.{normalized_params['table_name']}")

            return {
                "valid": True,
                "message": "参数验证通过",
                "normalized_params": normalized_params
            }

        except Exception as e:
            self.logger.error(f"❌ 参数验证异常: {str(e)}")
            return {
                "valid": False,
                "message": f"参数验证异常: {str(e)}",
                "normalized_params": None
            }

    async def get_table_ddl_with_validation(self, system_name: str, version_no: str,
                                         db_name: str, table_name: str, user_input: str) -> Dict[str, Any]:
        """
        带参数验证的表DDL查询

        这是主要的对外接口方法
        """
        # Step 1: 参数验证
        validation_result = await self.validate_parameters(
            system_name, version_no, db_name, table_name, user_input
        )

        if not validation_result["valid"]:
            self.logger.warning(f"⚠️ 参数验证失败: {validation_result['message']}")
            return {
                "success": False,
                "message": validation_result["message"],
                "data": None
            }

        # Step 2: 执行DDL查询
        params = validation_result["normalized_params"]
        ddl_result = await self.get_table_ddl(
            params["table_name"]
        )
        ddl_result['data']['system_name'] = system_name
        ddl_result['data']['version_no'] = version_no
        return ddl_result


# 创建全局实例
table_ddl_service = TableDDLService()