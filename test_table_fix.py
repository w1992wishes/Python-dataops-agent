#!/usr/bin/env python3
"""
测试 table_agent 修复后的功能
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.table_agent import TableGenerationAgent
from agents.base_agent import AgentConfig

async def test_table_generation():
    """测试表结构生成功能"""
    print("🚀 开始测试表结构生成功能...")

    # 创建 Agent 配置
    config = AgentConfig(
        name="table_generation_test",
        version="3.0.0",
        description="测试表结构生成Agent",
        timeout=300,
        model_name="gpt-3.5-turbo"  # 使用更便宜的模型进行测试
    )

    try:
        # 初始化 Agent
        agent = TableGenerationAgent(config)
        print("✅ Agent 初始化成功")

        # 测试用户输入
        test_input = "创建一个用户表，包含用户ID、用户名、邮箱、注册时间字段，表属于用户域"

        print(f"📝 测试输入: {test_input}")
        print("🔄 正在处理...")

        # 执行 Agent
        result = await agent.process(test_input)

        if result.success:
            print("✅ 表结构生成成功!")

            table_info = result.data.get("table_info", {})
            analysis = result.data.get("analysis", {})

            print(f"📊 表名: {table_info.get('name', 'N/A')}")
            print(f"🏷️ 中文名: {table_info.get('nameZh', 'N/A')}")
            print(f"🔄 操作类型: {analysis.get('operation_type', 'N/A')}")
            print(f"📋 字段数量: {len(table_info.get('cols', []))}")

            # 检查字段的 tableId
            cols = table_info.get('cols', [])
            if cols:
                print("📝 字段详情:")
                for i, col in enumerate(cols[:3], 1):  # 只显示前3个字段
                    table_id = col.get('tableId', 'N/A')
                    print(f"   {i}. {col.get('name', 'N/A')} ({col.get('nameZh', 'N/A')}) - tableId: '{table_id}'")

                    # 检查 tableId 是否为空字符串（新建表的情况）
                    if table_id == "":
                        print(f"      ✅ tableId 正确设置为空字符串")
                    elif table_id is None:
                        print(f"      ⚠️ tableId 为 None")
                    else:
                        print(f"      ℹ️ tableId 有值: {table_id}")

            return True
        else:
            print(f"❌ 表结构生成失败: {result.error}")
            return False

    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🎯 Table Agent 修复验证测试")
    print("=" * 50)

    success = await test_table_generation()

    print("\n" + "=" * 50)
    if success:
        print("🎉 测试通过！Table Agent 修复成功")
    else:
        print("❌ 测试失败！需要进一步检查")

if __name__ == "__main__":
    asyncio.run(main())