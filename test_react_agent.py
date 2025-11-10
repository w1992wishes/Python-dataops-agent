"""
测试指标管理React Agent
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.metric_agent import MetricManagementAgent
from agents.base_agent import AgentConfig


async def test_react_agent():
    """测试React Agent功能"""
    print("🧪 开始测试指标管理React Agent")

    # 配置Agent
    config = AgentConfig(
        name="test_metric_react",
        version="2.0.0",
        description="测试用指标管理React Agent",
        timeout=60,
        model_name="deepseek-ai/DeepSeek-V3.1"
    )

    # 创建Agent实例
    agent = MetricManagementAgent(config)

    # 测试用例列表
    test_cases = [
        "创建一个新指标：日活跃用户数",
        "查询月度收入指标",
        "修改用户数量指标，改为统计周活跃用户",
        "创建转化率指标，这是一个派生指标",
        "查询不存在的指标：测试指标"
    ]

    for i, test_input in enumerate(test_cases, 1):
        print(f"\n🔍 测试用例 {i}: {test_input}")
        print("-" * 50)

        try:
            # 使用普通模式处理
            result = await agent.process(test_input)

            if result.success:
                print(f"✅ 处理成功")
                if "operation_result" in result.data:
                    op_result = result.data["operation_result"]
                    print(f"📊 操作类型: {op_result.get('operation_type', 'N/A')}")
                    print(f"📝 状态: {op_result.get('status', 'N/A')}")
                    print(f"💬 消息: {op_result.get('message', 'N/A')}")

                    if op_result.get('metric_info'):
                        print(f"📋 指标信息: {op_result['metric_info'].get('nameZh', 'N/A')}")
                    if op_result.get('existing_metric'):
                        print(f"📋 已存在指标: {op_result['existing_metric'].get('nameZh', 'N/A')}")

                if "agent_reply" in result.data:
                    print(f"🤖 Agent回复: {result.data['agent_reply'][:200]}...")
            else:
                print(f"❌ 处理失败: {result.error}")

        except Exception as e:
            print(f"💥 测试异常: {e}")

        print("-" * 50)

    print("\n🎉 测试完成")


async def test_stream_mode():
    """测试流式模式"""
    print("🌊 测试流式模式")

    config = AgentConfig(
        name="test_metric_react_stream",
        version="2.0.0",
        description="测试用指标管理React Agent（流式）",
        timeout=60,
        model_name="deepseek-ai/DeepSeek-V3.1"
    )

    agent = MetricManagementAgent(config)

    test_input = "创建一个新指标：订单转化率"
    print(f"🔍 测试输入: {test_input}")

    try:
        async for chunk in agent.process_stream(test_input):
            print(f"📦 {chunk['step']}: {chunk['message']}")
            if chunk['step'] == "completed":
                break
    except Exception as e:
        print(f"💥 流式测试异常: {e}")


if __name__ == "__main__":
    print("🚀 开始测试指标管理React Agent")

    # 测试普通模式
    asyncio.run(test_react_agent())

    print("\n" + "="*60 + "\n")

    # 测试流式模式
    asyncio.run(test_stream_mode())

    print("\n✅ 所有测试完成")