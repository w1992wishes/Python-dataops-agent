"""
测试表DDL查询服务
"""
import asyncio
import json
from services.table_ddl_service import table_ddl_service


async def test_table_ddl_service():
    """测试表DDL查询服务"""
    print("🚀 开始测试表DDL查询服务")
    print("=" * 60)

    # 测试用例1: 存在的表
    print("\n📊 测试用例1: 查询存在的表")
    result1 = await table_ddl_service.get_table_ddl_with_validation(
        system_name="user_management",
        version_no="1.0.0",
        db_name="test_db",
        table_name="user_table",
        user_input="查询用户表的DDL结构"
    )
    print("结果:", json.dumps(result1, ensure_ascii=False, indent=2))

    # 测试用例2: 不存在的表
    print("\n📊 测试用例2: 查询不存在的表")
    result2 = await table_ddl_service.get_table_ddl_with_validation(
        system_name="test_system",
        version_no="2.0.0",
        db_name="test_db",
        table_name="nonexistent_table",
        user_input="查询不存在的表"
    )
    print("结果:", json.dumps(result2, ensure_ascii=False, indent=2))

    # 测试用例3: 参数验证失败
    print("\n📊 测试用例3: 参数验证失败")
    result3 = await table_ddl_service.get_table_ddl_with_validation(
        system_name="",
        version_no="1.0.0",
        db_name="test_db",
        table_name="user_table",
        user_input="测试参数验证"
    )
    print("结果:", json.dumps(result3, ensure_ascii=False, indent=2))

    print("\n" + "=" * 60)
    print("✅ 测试完成")


async def test_api_format():
    """测试API返回格式"""
    print("\n🔗 测试API格式")
    print("=" * 40)

    # 模拟API请求
    from models.ddl_schemas import TableDDLRequest
    from services.table_ddl_service import table_ddl_service

    request = TableDDLRequest(
        system_name="user_management",
        version_no="1.0.0",
        db_name="test_db",
        table_name="user_table",
        user_input="查询DDL"
    )

    result = await table_ddl_service.get_table_ddl_with_validation(
        request.system_name,
        request.version_no,
        request.db_name,
        request.table_name,
        request.user_input
    )

    # 构建API响应格式
    from models.ddl_schemas import TableDDLResult
    from datetime import datetime

    api_response = TableDDLResult(
        success=result["success"],
        message=result["message"],
        data=result["data"]
    )

    print("API响应格式:")
    print(json.dumps(api_response.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(test_table_ddl_service())
    asyncio.run(test_api_format())