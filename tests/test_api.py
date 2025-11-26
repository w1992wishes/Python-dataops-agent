"""
LangGraph 智能数据开发平台 API 测试
六个核心接口 + 交互式选择版本
支持用户自主选择测试用例
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
        # 增强连接配置，增加超时和重试设置
        timeout = aiohttp.ClientTimeout(total=120, connect=10, sock_read=60)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={"User-Agent": "LangGraph-API-Tester/1.0"}
        )
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
                "user_input": "修改用户表，新增用户名、邮箱、注册时间、手机号字段，表属于用户域",
                "table_name": "user_table"
            }

            logger.info("📡 发送表结构生成请求...")

            # 添加重试机制
            for attempt in range(3):
                try:
                    async with self.session.post(
                        f"{self.base_url}/api/table",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:

                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"表结构生成结果: {json.dumps(data, ensure_ascii=False, indent=2)}")

                            if data.get("success"):
                                table_info = data.get("data", {})
                                result_info = {
                                    "operation_type": data.get("operation_type"),
                                    "table_name": table_info.get("nameZh", "N/A"),
                                    "table_columns": len(table_info.get("cols", [])),
                                    "table_level": table_info.get("levelType", "N/A")
                                }
                                self.log_test("表结构生成", True, result_info)
                                return data
                            else:
                                self.log_test("表结构生成", False, error=data.get("error", "生成失败"))
                                return data
                        else:
                            error_text = await response.text()
                            error_msg = f"HTTP {response.status}: {error_text}"
                            logger.warning(f"⚠️ 尝试 {attempt + 1}/3 失败: {error_msg}")
                            if attempt == 2:  # 最后一次尝试
                                self.log_test("表结构生成", False, error=error_msg)
                            continue

                except aiohttp.ClientConnectorError as e:
                    error_msg = f"连接错误: {str(e)}"
                    logger.warning(f"⚠️ 尝试 {attempt + 1}/3 连接失败: {error_msg}")
                    if attempt == 2:
                        self.log_test("表结构生成", False, error=error_msg)
                    continue
                except aiohttp.ServerDisconnectedError as e:
                    error_msg = f"服务器断开连接: {str(e)}"
                    logger.warning(f"⚠️ 尝试 {attempt + 1}/3 服务器断开: {error_msg}")
                    if attempt == 2:
                        self.log_test("表结构生成", False, error=error_msg + " (服务器可能在处理请求时崩溃)")
                    continue
                except asyncio.TimeoutError as e:
                    error_msg = f"请求超时: {str(e)}"
                    logger.warning(f"⚠️ 尝试 {attempt + 1}/3 超时: {error_msg}")
                    if attempt == 2:
                        self.log_test("表结构生成", False, error=error_msg + " (处理时间过长)")
                    continue

                if attempt < 2:  # 不是最后一次尝试
                    logger.info(f"⏳ 等待 3 秒后重试...")
                    await asyncio.sleep(3)

        except Exception as e:
            self.log_test("表结构生成", False, error=f"未知异常: {str(e)}")

    async def test_etl_development(self):
        """测试ETL脚本开发"""
        try:
            payload = {
                "table_name": "user_table",
                "user_input": "为用户表创建一个ETL脚本，需要将用户注册表和用户行为表关联，计算每个用户的总登录次数和最后登录时间，结果写入用户活跃度汇总表"
            }

            async with self.session.post(
                f"{self.base_url}/api/etl",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    logger.info(f"ETL脚本开发结果: {json.dumps(data, ensure_ascii=False, indent=2)}")

                    if data.get("success"):
                        etl_info = data.get("data", {})
                        result_info = {
                            "operation_type": data.get("operation_type"),
                            "entity_type": data.get("entity_type"),
                            "target_table": etl_info.get("table_name", "N/A"),
                            "has_etl_code": bool(etl_info.get("etl_code")),
                            "changes_count": len(etl_info.get("changes_summary", []))
                        }
                        self.log_test("ETL脚本开发", True, result_info)
                        return data
                    else:
                        self.log_test("ETL脚本开发", False, error=data.get("error", "开发失败"))
                else:
                    error_text = await response.text()
                    self.log_test("ETL脚本开发", False, error=f"HTTP {response.status}: {error_text}")

        except Exception as e:
            self.log_test("ETL脚本开发", False, error=str(e))

    async def test_metric_management(self):
        """测试指标管理"""
        try:
            payload = {
                "user_input": "创建一个新指标叫月度活跃用户数，统计每个月的活跃用户总数，业务域是用户域，需要包含用户ID、活跃日期等字段",
                "metric_name_zh": "月度活跃用户数",
                "um": "test_user"
            }

            async with self.session.post(
                f"{self.base_url}/api/metric",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    logger.info(f"指标管理结果: {json.dumps(data, ensure_ascii=False, indent=2)}")

                    if data.get("success"):
                        metric_info = data.get("data", {})
                        result_info = {
                            "operation_type": data.get("operation_type"),
                            "entity_type": data.get("entity_type"),
                            "metric_name": metric_info.get("nameZh", "N/A") if metric_info else "N/A",
                            "metric_code": metric_info.get("code", "N/A") if metric_info else "N/A",
                            "business_domain": metric_info.get("processDomainId", "N/A") if metric_info else "N/A"
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

    async def test_ddl_query(self):
        """测试DDL查询"""
        try:
            payload = {
                "system_name": "user_management",
                "version_no": "1.0.0",
                "db_name": "warehouse",
                "table_name": "user_table",
                "user_input": "查询用户表的DDL结构"
            }

            logger.info("📡 发送DDL查询请求...")

            # 添加重试机制
            for attempt in range(3):
                try:
                    async with self.session.post(
                        f"{self.base_url}/api/ddl",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:

                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"DDL查询结果: {json.dumps(data, ensure_ascii=False, indent=2)}")

                            if data.get("success"):
                                ddl_info = data.get("data", {})
                                result_info = {
                                    "operation_type": data.get("operation_type", "N/A"),
                                    "entity_type": data.get("entity_type", "N/A"),
                                    "table_name": ddl_info.get("table_name", "N/A") if ddl_info else "N/A",
                                    "db_name": ddl_info.get("db_name", "N/A") if ddl_info else "N/A",
                                    "table_level_type": ddl_info.get("table_level_type", "N/A") if ddl_info else "N/A",
                                    "is_mock_ddl": ddl_info.get("is_mock_ddl", False) if ddl_info else False
                                }
                                self.log_test("DDL查询", True, result_info)
                                return data
                            else:
                                self.log_test("DDL查询", False, error=data.get("error", "查询失败"))
                                return data
                        else:
                            error_text = await response.text()
                            error_msg = f"HTTP {response.status}: {error_text}"
                            logger.warning(f"⚠️ DDL尝试 {attempt + 1}/3 失败: {error_msg}")
                            if attempt == 2:
                                self.log_test("DDL查询", False, error=error_msg)
                            continue

                except aiohttp.ClientConnectorError as e:
                    error_msg = f"连接错误: {str(e)}"
                    logger.warning(f"⚠️ DDL尝试 {attempt + 1}/3 连接失败: {error_msg}")
                    if attempt == 2:
                        self.log_test("DDL查询", False, error=error_msg)
                    continue
                except aiohttp.ServerDisconnectedError as e:
                    error_msg = f"服务器断开连接: {str(e)}"
                    logger.warning(f"⚠️ DDL尝试 {attempt + 1}/3 服务器断开: {error_msg}")
                    if attempt == 2:
                        self.log_test("DDL查询", False, error=error_msg + " (服务器可能在处理请求时崩溃)")
                    continue
                except asyncio.TimeoutError as e:
                    error_msg = f"请求超时: {str(e)}"
                    logger.warning(f"⚠️ DDL尝试 {attempt + 1}/3 超时: {error_msg}")
                    if attempt == 2:
                        self.log_test("DDL查询", False, error=error_msg + " (处理时间过长)")
                    continue

                if attempt < 2:  # 不是最后一次尝试
                    logger.info(f"⏳ DDL等待 3 秒后重试...")
                    await asyncio.sleep(3)

        except Exception as e:
            self.log_test("DDL查询", False, error=f"DDL未知异常: {str(e)}")

    async def test_scheduler_query(self):
        """测试调度信息查询"""
        try:
            payload = {
                "system_name": "user_management",
                "version_no": "1.0.0",
                "db_name": "warehouse",
                "table_name": "user_table",
                "user_input": "查询用户表的调度配置信息"
            }

            logger.info("📡 发送调度查询请求...")

            # 添加重试机制
            for attempt in range(3):
                try:
                    async with self.session.post(
                        f"{self.base_url}/api/scheduler",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:

                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"调度查询结果: {json.dumps(data, ensure_ascii=False, indent=2)}")

                            if data.get("success"):
                                schedule_info = data.get("data", {})
                                result_info = {
                                    "operation_type": data.get("operation_type", "N/A"),
                                    "entity_type": data.get("entity_type", "N/A"),
                                    "schedule_name": schedule_info.get("schedule_name", "N/A") if schedule_info else "N/A",
                                    "schedule_type": schedule_info.get("schedule_type", "N/A") if schedule_info else "N/A",
                                    "schedule_status": schedule_info.get("schedule_status", "N/A") if schedule_info else "N/A",
                                    "cron_expression": schedule_info.get("cron_expression", "N/A") if schedule_info else "N/A",
                                    "is_mock_schedule": schedule_info.get("is_mock_schedule", False) if schedule_info else False
                                }
                                self.log_test("调度信息查询", True, result_info)
                                return data
                            else:
                                self.log_test("调度信息查询", False, error=data.get("error", "查询失败"))
                                return data
                        else:
                            error_text = await response.text()
                            error_msg = f"HTTP {response.status}: {error_text}"
                            logger.warning(f"⚠️ 调度尝试 {attempt + 1}/3 失败: {error_msg}")
                            if attempt == 2:
                                self.log_test("调度信息查询", False, error=error_msg)
                            continue

                except aiohttp.ClientConnectorError as e:
                    error_msg = f"连接错误: {str(e)}"
                    logger.warning(f"⚠️ 调度尝试 {attempt + 1}/3 连接失败: {error_msg}")
                    if attempt == 2:
                        self.log_test("调度信息查询", False, error=error_msg)
                    continue
                except aiohttp.ServerDisconnectedError as e:
                    error_msg = f"服务器断开连接: {str(e)}"
                    logger.warning(f"⚠️ 调度尝试 {attempt + 1}/3 服务器断开: {error_msg}")
                    if attempt == 2:
                        self.log_test("调度信息查询", False, error=error_msg + " (服务器可能在处理请求时崩溃)")
                    continue
                except asyncio.TimeoutError as e:
                    error_msg = f"请求超时: {str(e)}"
                    logger.warning(f"⚠️ 调度尝试 {attempt + 1}/3 超时: {error_msg}")
                    if attempt == 2:
                        self.log_test("调度信息查询", False, error=error_msg + " (处理时间过长)")
                    continue

                if attempt < 2:  # 不是最后一次尝试
                    logger.info(f"⏳ 调度等待 3 秒后重试...")
                    await asyncio.sleep(3)

        except Exception as e:
            self.log_test("调度信息查询", False, error=f"调度未知异常: {str(e)}")

    async def show_test_menu(self):
        """显示测试菜单供用户选择"""
        logger.info("\n" + "=" * 60)
        logger.info("🎯 LangGraph API 测试菜单")
        logger.info("=" * 60)
        logger.info("请选择要运行的测试 (输入数字):")
        logger.info("  1. 健康检查 (GET /health)")
        logger.info("  2. 表结构生成 (POST /api/table)")
        logger.info("  3. ETL脚本开发 (POST /api/etl)")
        logger.info("  4. 指标管理 (POST /api/metric)")
        logger.info("  5. DDL查询 (POST /api/ddl)")
        logger.info("  6. 调度信息查询 (POST /api/scheduler)")
        logger.info("  7. 运行所有测试")
        logger.info("  0. 退出")
        logger.info("=" * 60)

    async def run_selected_test(self, choice: int):
        """运行用户选择的测试"""
        test_functions = {
            1: ("健康检查", self.test_health_check),
            2: ("表结构生成", self.test_table_generation),
            3: ("ETL脚本开发", self.test_etl_development),
            4: ("指标管理", self.test_metric_management),
            5: ("DDL查询", self.test_ddl_query),
            6: ("调度信息查询", self.test_scheduler_query),
        }

        if choice == 0:
            return False
        elif choice == 7:
            await self.run_all_tests()
        elif choice in test_functions:
            test_name, test_func = test_functions[choice]
            logger.info(f"\n🎯 开始测试: {test_name}")
            logger.info("-" * 40)
            await test_func()
            await asyncio.sleep(1)  # 测试间隔

            # 显示当前测试结果
            total_tests = len(self.test_results)
            successful_tests = sum(1 for r in self.test_results if r["success"])
            logger.info(f"\n📊 当前测试结果: {successful_tests}/{total_tests} 通过")
        else:
            logger.error(f"❌ 无效选择: {choice}")

        return True

    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始运行所有测试")
        logger.info("=" * 60)

        start_time = time.time()

        # 运行所有测试
        tests = [
            ("健康检查", self.test_health_check),
            ("表结构生成", self.test_table_generation),
            ("ETL脚本开发", self.test_etl_development),
            ("指标管理", self.test_metric_management),
            ("DDL查询", self.test_ddl_query),
            ("调度信息查询", self.test_scheduler_query)
        ]

        for test_name, test_func in tests:
            logger.info(f"\n🎯 测试: {test_name}")
            logger.info("-" * 40)
            await test_func()
            # 测试间隔
            await asyncio.sleep(1)

        # 统计测试结果
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - successful_tests
        elapsed_time = time.time() - start_time

        logger.info("\n" + "=" * 60)
        logger.info("📊 测试结果统计")
        logger.info("=" * 60)
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
                    "api_version": "3.0.0"
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
                    data = await response.json()
                    logger.info(f"✅ 服务器状态: {data.get('status', 'unknown')}")
                    return True
                else:
                    logger.warning(f"⚠️ 服务器响应状态码: {response.status}")
    except asyncio.TimeoutError:
        logger.error("❌ 服务器连接超时")
    except aiohttp.ClientConnectorError:
        logger.error("❌ 无法连接到服务器 - 服务器可能未启动")
    except Exception as e:
        logger.error(f"❌ 检查服务器时发生异常: {str(e)}")
    return False


async def diagnose_server_issues():
    """诊断服务器问题"""
    logger.info("🔍 开始诊断服务器问题...")

    # 检查端口是否被占用
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8000))
        if result == 0:
            logger.info("✅ 端口8000可访问")
        else:
            logger.error("❌ 端口8000不可访问 - 服务器可能未启动")
        sock.close()
    except Exception as e:
        logger.error(f"❌ 检查端口时出错: {str(e)}")

    # 检查环境变量
    import os
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("SILICONFLOW_API_KEY")
    if api_key:
        logger.info("✅ API密钥已配置")
    else:
        logger.warning("⚠️ 未配置API密钥 - 可能影响Agent功能")

    logger.info("💡 如果服务器崩溃，请检查:")
    logger.info("   1. API密钥是否正确配置")
    logger.info("   2. 网络连接是否正常")
    logger.info("   3. 服务器控制台是否有错误信息")
    logger.info("   4. 尝试重新启动: python main_api.py")


async def main():
    """主测试函数"""
    logger.info("🎯 LangGraph 智能数据开发平台 API 测试程序 - 交互式选择")

    # 检查环境变量
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("SILICONFLOW_API_KEY")
    if not api_key:
        logger.warning("⚠️  未设置 OPENAI_API_KEY 或 SILICONFLOW_API_KEY 环境变量")
        logger.warning("    某些需要 AI 模型的测试可能会失败")

    # 检查 API 服务器
    logger.info("🔍 检查 API 服务器状态...")
    if not await check_api_server():
        logger.error("❌ API 服务器未运行或不可访问")
        await diagnose_server_issues()
        logger.info("🔄 修复问题后重新运行测试")
        return

    logger.info("✅ API 服务器运行正常")

    # 交互式测试选择
    async with APITester() as tester:
        while True:
            await tester.show_test_menu()

            try:
                choice = input("\n请输入选择 (0-7): ").strip()
                if not choice:
                    continue

                choice = int(choice)

                should_continue = await tester.run_selected_test(choice)

                if not should_continue:
                    logger.info("👋 退出测试程序")
                    break

                # 询问是否继续
                if input("\n是否继续测试? (y/n): ").strip().lower() in ['n', 'no', '否', 'quit', 'exit']:
                    break

            except ValueError:
                logger.error("❌ 请输入有效的数字 (0-7)")
            except KeyboardInterrupt:
                logger.info("\n👋 用户中断，退出测试程序")
                break

        # 显示最终统计
        if tester.test_results:
            logger.info("\n" + "=" * 60)
            logger.info("📊 最终测试统计")
            logger.info("=" * 60)
            total_tests = len(tester.test_results)
            successful_tests = sum(1 for r in tester.test_results if r["success"])
            logger.info(f"📋 总测试数: {total_tests}")
            logger.info(f"✅ 成功测试: {successful_tests}")
            logger.info(f"❌ 失败测试: {total_tests - successful_tests}")
            logger.info(f"📈 成功率: {(successful_tests/total_tests*100):.1f}%")

            # 保存测试报告
            await tester.save_test_report()


if __name__ == "__main__":
    asyncio.run(main())