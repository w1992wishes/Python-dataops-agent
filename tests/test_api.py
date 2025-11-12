"""
LangGraph 智能数据开发平台 API 测试
精简版本 - 测试三个核心接口 + 流式输出
"""
import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APITester:
    """API测试类"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log_test(self, test_name: str, success: bool, response_data: Dict = None, error: str = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data,
            "error": error
        }
        self.test_results.append(result)

        if success:
            logger.info(f"✅ {test_name} - 成功")
        else:
            logger.error(f"❌ {test_name} - 失败: {error}")

    async def test_health_check(self):
        """测试健康检查"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("健康检查", True, data)
                    return data
                else:
                    self.log_test("健康检查", False, error=f"HTTP {response.status}")
        except Exception as e:
            self.log_test("健康检查", False, error=str(e))

    async def test_table_generation(self):
        """测试表结构生成"""
        try:
            payload = {
                "user_input": "创建一个用户表，包含用户ID（主键）、用户名、邮箱、注册时间、手机号字段，表属于用户域"
            }

            async with self.session.post(
                f"{self.base_url}/api/table",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    logger.info(f"--------------------data--------------------{json.dumps(data, ensure_ascii=False, indent=2)}")
                    if data.get("success"):
                        self.log_test("表结构生成", True, data)
                        return data
                    else:
                        self.log_test("表结构生成", False, error=data.get("error", "生成失败"))
                else:
                    error_text = await response.text()
                    self.log_test("表结构生成", False, error=f"HTTP {response.status}: {error_text}")

        except Exception as e:
            self.log_test("表结构生成", False, error=str(e))

    async def test_etl_development(self):
        """测试ETL脚本开发"""
        try:
            payload = {
                "table_name": "policy_renewal",
                "user_input": "为订单表创建一个ETL脚本，需要将用户表和订单表关联，计算每个用户的总消费金额和订单数量，结果写入用户消费汇总表"
            }

            async with self.session.post(
                f"{self.base_url}/api/etl",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:

                if response.status == 200:
                    data = await response.json()

                    if data.get("success"):
                        etl_script = data.get("etl_script", {})
                        logger.info("🎯 [TEST] ETL脚本开发测试:")
                        logger.info(f"   📜 脚本名称: {etl_script.get('name', 'N/A')}")
                        logger.info(f"   🎯 目标表: {etl_script.get('target_table', 'N/A')}")
                        logger.info(f"   📝 源表数量: {len(etl_script.get('source_tables', []))}")

                        self.log_test("ETL脚本开发", True, data)
                        return data
                    else:
                        self.log_test("ETL脚本开发", False, error=data.get("error", "开发失败"))
                else:
                    error_text = await response.text()
                    self.log_test("ETL脚本开发", False, error=f"HTTP {response.status}: {error_text}")

        except Exception as e:
            self.log_test("ETL脚本开发", False, error=str(e))

    async def test_metric_management(self):
        """测试指标管理React Agent"""
        try:
            payload = {
                "user_input": "创建一个新指标叫月度收入，统计每个月的活跃用户总数，业务域是用户域，需要包含用户ID、活跃日期等字段"
            }

            async with self.session.post(
                f"{self.base_url}/api/metric",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    logger.info(f"--------------------data--------------------{data}")

                    if data.get("success"):
                        # 提取关键信息用于日志记录
                        operation_type = data.get("operation_type", "N/A")
                        metric_data = data.get("data", {})

                        # 获取指标信息
                        metric_info = metric_data.get("metric_info") or metric_data.get("existing_metric")
                        metric_name = metric_info.get("nameZh", "N/A") if metric_info else "N/A"

                        # 获取状态和消息
                        status = metric_data.get("status", "N/A")
                        message = metric_data.get("message", "无消息")

                        result_info = {
                            "operation_type": operation_type,
                            "status": status,
                            "message": message,
                            "metric_name": metric_name,
                            "has_metric_info": bool(metric_info)
                        }

                        self.log_test("指标管理", True, result_info)
                        return data
                    else:
                        self.log_test("指标管理", False, error=data.get("error", "处理失败"))
                else:
                    error_text = await response.text()
                    self.log_test("指标管理", False, error=f"HTTP {response.status}: {error_text}")

        except Exception as e:
            self.log_test("指标管理", False, error=str(e))

    async def test_metric_update(self):
        """测试指标更新"""
        try:
            payload = {
                "user_input": "更新月度活跃用户数指标，添加设备类型字段，区分移动端和桌面端用户，并修改业务口径为按设备类型统计月度活跃用户数"
            }

            async with self.session.post(
                f"{self.base_url}/api/metric",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:

                if response.status == 200:
                    data = await response.json()

                    if data.get("success"):
                        metric_info = data.get("metric_info", {})
                        logger.info("🎯 [TEST] 指标更新测试:")
                        logger.info(f"   🔄 指标名称: {metric_info.get('nameZh', 'N/A')}")
                        logger.info(f"   📝 更新后口径: {metric_info.get('businessCaliber', 'N/A')[:50]}{'...' if len(metric_info.get('businessCaliber', '')) > 50 else ''}")

                        self.log_test("指标更新", True, data)
                        return data
                    else:
                        self.log_test("指标更新", False, error=data.get("error", "更新失败"))
                else:
                    error_text = await response.text()
                    self.log_test("指标更新", False, error=f"HTTP {response.status}: {error_text}")

        except Exception as e:
            self.log_test("指标更新", False, error=str(e))

    async def test_metric_streaming(self):
        """测试指标管理流式接口"""
        try:
            payload = {
                "user_input": "创建一个新指标叫月度收入，统计每日活跃用户的总收入，业务域是收入域，需要包含用户ID、收入金额、日期等字段"
            }

            logger.info("🎯 [TEST] 指标管理流式测试开始...")

            async with self.session.post(
                f"{self.base_url}/api/metric/stream",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:

                if response.status == 200:
                    logger.info("✅ 流式连接建立成功")

                    # 处理流式数据
                    chunks_received = []
                    steps_completed = []

                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data_str = line[6:]  # 移除 'data: ' 前缀
                            try:
                                chunk_data = json.loads(data_str)
                                chunks_received.append(chunk_data)

                                step = chunk_data.get("step", "unknown")
                                message = chunk_data.get("message", "")

                                logger.info(f"📡 [STREAM] 步骤: {step}")
                                logger.info(f"💬 [STREAM] 消息: {message}")

                                # 记录关键步骤
                                if step not in steps_completed:
                                    steps_completed.append(step)

                                # 显示步骤特定数据
                                if step == "analyze_request" and "analysis" in chunk_data.get("data", {}):
                                    analysis = chunk_data["data"]["analysis"]
                                    logger.info(f"   🔍 分析结果: {analysis.get('metric_name', 'N/A')} - {analysis.get('operation_type', 'N/A')}")

                                elif step == "query_metric" and "existing_metric" in chunk_data.get("data", {}):
                                    existing = chunk_data["data"]["existing_metric"]
                                    logger.info(f"   📋 找到现有指标: {existing.get('nameZh', 'N/A')}")

                                elif step == "execute_operation" and "final_metric" in chunk_data.get("data", {}):
                                    final = chunk_data["data"]["final_metric"]
                                    if final:
                                        logger.info(f"   ✅ 最终指标: {final.get('nameZh', 'N/A')}")
                                        logger.info(f"   📊 指标编码: {final.get('code', 'N/A')}")
                                        logger.info(f"   🏷️ 业务域: {final.get('processDomainId', 'N/A')}")

                                elif step == "completed":
                                    logger.info("🎉 流式处理完成")

                            except json.JSONDecodeError as e:
                                logger.warning(f"⚠️ 无法解析流式数据: {e}")

                    # 验证流式处理结果
                    expected_steps = ["analyze_request", "query_metric", "execute_operation", "completed"]
                    missing_steps = [step for step in expected_steps if step not in steps_completed]

                    if missing_steps:
                        error_msg = f"缺少步骤: {', '.join(missing_steps)}"
                        self.log_test("指标管理流式", False, error=error_msg)
                    else:
                        success_data = {
                            "chunks_received": len(chunks_received),
                            "steps_completed": steps_completed,
                            "final_chunk": chunks_received[-1] if chunks_received else None
                        }
                        self.log_test("指标管理流式", True, success_data)
                        logger.info(f"📊 流式统计: 收到 {len(chunks_received)} 个数据块，完成 {len(steps_completed)} 个步骤")

                    return {"chunks": chunks_received, "steps": steps_completed}

                else:
                    error_text = await response.text()
                    self.log_test("指标管理流式", False, error=f"HTTP {response.status}: {error_text}")

        except Exception as e:
            self.log_test("指标管理流式", False, error=str(e))

    async def test_metric_query_streaming(self):
        """测试指标查询流式接口"""
        try:
            payload = {
                "user_input": "查询月度活跃用户数指标，获取该指标的详细信息包括业务口径、计算规则和字段定义"
            }

            logger.info("🎯 [TEST] 指标查询流式测试开始...")

            async with self.session.post(
                f"{self.base_url}/api/metric/stream",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:

                if response.status == 200:
                    logger.info("✅ 查询流式连接建立成功")

                    # 处理流式数据
                    chunks_received = []
                    steps_completed = []

                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data_str = line[6:]  # 移除 'data: ' 前缀
                            try:
                                chunk_data = json.loads(data_str)
                                chunks_received.append(chunk_data)

                                step = chunk_data.get("step", "unknown")
                                message = chunk_data.get("message", "")

                                logger.info(f"📡 [QUERY-STREAM] 步骤: {step}")
                                logger.info(f"💬 [QUERY-STREAM] 消息: {message}")

                                # 记录关键步骤
                                if step not in steps_completed:
                                    steps_completed.append(step)

                                # 显示步骤特定数据
                                if step == "analyze_request" and "analysis" in chunk_data.get("data", {}):
                                    analysis = chunk_data["data"]["analysis"]
                                    logger.info(f"   🔍 查询分析: {analysis.get('metric_name', 'N/A')} - {analysis.get('operation_type', 'N/A')}")

                                elif step == "query_metric" and "existing_metric" in chunk_data.get("data", {}):
                                    existing = chunk_data["data"]["existing_metric"]
                                    if existing:
                                        logger.info(f"   📋 查询到指标: {existing.get('nameZh', 'N/A')}")
                                        logger.info(f"   📊 指标编码: {existing.get('code', 'N/A')}")
                                    else:
                                        logger.info(f"   ❌ 未找到指标")

                                elif step == "execute_operation":
                                    final = chunk_data.get("data", {}).get("final_metric")
                                    if final:
                                        logger.info(f"   ✅ 查询结果: {final.get('nameZh', 'N/A')}")
                                    else:
                                        logger.info(f"   ℹ️ 查询完成，无结果")

                            except json.JSONDecodeError as e:
                                logger.warning(f"⚠️ 无法解析查询流式数据: {e}")

                    # 验证查询流式处理结果
                    expected_steps = ["analyze_request", "query_metric", "execute_operation", "completed"]
                    missing_steps = [step for step in expected_steps if step not in steps_completed]

                    if missing_steps:
                        error_msg = f"查询缺少步骤: {', '.join(missing_steps)}"
                        self.log_test("指标查询流式", False, error=error_msg)
                    else:
                        success_data = {
                            "chunks_received": len(chunks_received),
                            "steps_completed": steps_completed,
                            "query_result": "成功" if any("existing_metric" in chunk.get("data", {}) and chunk["data"]["existing_metric"] for chunk in chunks_received) else "未找到"
                        }
                        self.log_test("指标查询流式", True, success_data)
                        logger.info(f"📊 查询流式统计: 收到 {len(chunks_received)} 个数据块，完成 {len(steps_completed)} 个步骤")

                    return {"chunks": chunks_received, "steps": steps_completed}

                else:
                    error_text = await response.text()
                    self.log_test("指标查询流式", False, error=f"HTTP {response.status}: {error_text}")

        except Exception as e:
            self.log_test("指标查询流式", False, error=str(e))

    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始运行 LangGraph API 测试 - 精简版 + 流式输出")
        logger.info("=" * 50)

        start_time = time.time()

        # 基础功能测试
        logger.info("\n📋 基础功能测试")
        await self.test_health_check()

        # 核心功能测试
        logger.info("\n🎯 核心功能测试")
        #await self.test_table_generation()
        await self.test_etl_development()
        # await self.test_metric_management()
        # await self.test_metric_update()

        # 流式接口测试
        # logger.info("\n🌊 流式接口测试")
        # await self.test_metric_streaming()
        #await self.test_metric_query_streaming()

        # 统计测试结果
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - successful_tests
        elapsed_time = time.time() - start_time

        logger.info("\n" + "=" * 50)
        logger.info("📊 测试结果统计")
        logger.info("=" * 50)
        logger.info(f"📋 总测试数: {total_tests}")
        logger.info(f"✅ 成功测试: {successful_tests}")
        logger.info(f"❌ 失败测试: {failed_tests}")
        logger.info(f"📈 成功率: {(successful_tests/total_tests*100):.1f}%")
        logger.info(f"⏱️ 总耗时: {elapsed_time:.2f}秒")

        # 详细失败信息
        failed_results = [r for r in self.test_results if not r["success"]]
        if failed_results:
            logger.info("\n❌ 失败测试详情:")
            for result in failed_results:
                logger.info(f"   • {result['test_name']}: {result['error']}")

        # 保存测试报告
        await self.save_test_report()

        return successful_tests == total_tests

    async def save_test_report(self):
        """保存测试报告"""
        try:
            report = {
                "test_summary": {
                    "total_tests": len(self.test_results),
                    "successful_tests": sum(1 for r in self.test_results if r["success"]),
                    "failed_tests": sum(1 for r in self.test_results if not r["success"]),
                    "success_rate": f"{(sum(1 for r in self.test_results if r['success'])/len(self.test_results)*100):.1f}%",
                    "test_time": datetime.now().isoformat(),
                    "api_version": "3.1.0",  # 添加流式接口支持
                },
                "test_results": self.test_results
            }

            with open("test_report.json", "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            logger.info("📄 测试报告已保存到 test_report.json")

        except Exception as e:
            logger.error(f"❌ 保存测试报告失败: {e}")


async def check_api_server():
    """检查 API 服务器是否运行"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    return True
    except:
        pass
    return False


async def main():
    """主测试函数"""
    logger.info("🎯 LangGraph 智能数据开发平台 API 测试程序 - 精简版 + 流式输出")

    # 检查环境变量
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("SILICONFLOW_API_KEY")
    if not api_key:
        logger.warning("⚠️  未设置 OPENAI_API_KEY 或 SILICONFLOW_API_KEY 环境变量")
        logger.warning("    某些需要 AI 模型的测试可能会失败")

    # 检查 API 服务器
    logger.info("🔍 检查 API 服务器状态...")
    if not await check_api_server():
        logger.error("❌ API 服务器未运行或不可访问")
        logger.info("请先启动 API 服务器: python main_api.py")
        return

    logger.info("✅ API 服务器运行正常")

    # 运行测试
    async with APITester() as tester:
        success = await tester.run_all_tests()

    if success:
        logger.info("\n🎉 所有测试通过！")
    else:
        logger.info("\n⚠️  部分测试失败，请查看详细日志")


if __name__ == "__main__":
    asyncio.run(main())