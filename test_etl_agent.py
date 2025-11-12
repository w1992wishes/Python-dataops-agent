"""
测试优化后的ETL Agent
"""
import asyncio
import json
from agents.etl_agent import ETLManagementAgent
from agents.base_agent import AgentConfig


async def test_etl_agent():
    """测试ETL管理Agent（三步工作流）"""
    print("🚀 开始测试ETL管理Agent（三步工作流）")
    print("=" * 60)

    # 初始化Agent
    config = AgentConfig(
        name="etl_management",
        version="3.0.0",
        description="ETL管理Agent测试",
        timeout=300,
        model_name="deepseek-ai/DeepSeek-V3.1"
    )

    agent = ETLManagementAgent(config)

    # 测试用例1: 修改现有ETL代码
    print("\n📊 测试用例1: 基于DDL变更修改ETL代码")
    user_input1 = "用户表新增了user_age字段，请修改ETL代码，添加年龄字段的数据处理"
    table_name1 = "user_table"

    result1 = await agent.process(user_input1, table_name=table_name1)
    print("结果:")
    print(json.dumps(result1.model_dump(), ensure_ascii=False, indent=2))

    # 测试用例2: 创建新ETL代码
    print("\n📊 测试用例2: 为新表创建ETL代码")
    user_input2 = "创建新表的ETL代码，需要加载用户数据并进行统计"
    table_name2 = "new_table"

    result2 = await agent.process(user_input2, table_name=table_name2)
    print("结果:")
    print(json.dumps(result2.model_dump(), ensure_ascii=False, indent=2))

    # 测试用例3: 优化ETL代码
    print("\n📊 测试用例3: 优化ETL代码性能")
    user_input3 = "优化ETL代码，提升数据处理性能，添加更多统计指标"
    table_name3 = "policy_renewal"

    result3 = await agent.process(user_input3, table_name=table_name3)
    print("结果:")
    print(json.dumps(result3.model_dump(), ensure_ascii=False, indent=2))

    print("\n" + "=" * 60)
    print("✅ 测试完成")


async def test_etl_workflow_steps():
    """测试ETL工作流各步骤"""
    print("\n🔗 测试ETL工作流各步骤")
    print("=" * 40)

    from tools.etl_tools import get_etl_script, analyze_ddl_changes
    from tools.table_tools import query_table_ddl

    # 测试步骤1: 查询ETL脚本
    print("\n📄 步骤1: 查询ETL脚本")
    etl_info = await get_etl_script("policy_renewal")
    if etl_info:
        print(f"✅ 找到ETL脚本: {etl_info.get('description')}")
        print(f"源表: {etl_info.get('source_table')}")
        print(f"目标表: {etl_info.get('target_table')}")
        print(f"代码长度: {len(etl_info.get('etl_code', ''))} 字符")
    else:
        print("❌ 未找到ETL脚本")

    # 测试步骤2: 分析DDL变更
    print("\n🏗️ 步骤2: 分析DDL变更")
    ddl_analysis = await analyze_ddl_changes("policy_renewal")
    changes = ddl_analysis.get("ddl_changes", [])
    print(f"✅ 检测到 {len(changes)} 个DDL变更:")
    for i, change in enumerate(changes, 1):
        print(f"   {i}. {change.get('description', '未知')}")

    # 测试步骤3: 获取DDL内容
    print("\n📋 步骤3: 获取DDL内容")
    try:
        ddl_content = await query_table_ddl(
            dbName="warehouse",
            id="table_001",  # 假设ID
            levelType="SUB",
            name="policy_renewal"
        )
        print(f"✅ 获取DDL内容成功: {len(ddl_content)} 字符")
        print(f"DDL预览: {ddl_content[:100]}...")
    except Exception as e:
        print(f"⚠️ DDL获取失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_etl_agent())
    asyncio.run(test_etl_workflow_steps())