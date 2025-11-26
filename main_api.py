"""
LangGraph 智能数据开发平台 API
只包含指标、表结构、ETL三个核心功能 + 流式输出
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import json
from datetime import datetime

# 导入Agent管理系统
from agents import get_agent_manager

# 导入表DDL查询服务
from services.table_ddl_service import table_ddl_service
# 导入调度查询服务
from services.scheduler_service import scheduler_service
from models.api import (
    TableDDLRequest, SchedulerRequest,
    HealthResponse, TableRequest, MetricRequest, MetricStreamingRequest, ETLRequest,
    TableResponse, ETLResponse, MetricResponse, BaseResponse
)

# 配置日志
from config.logging_config import get_logger
logger = get_logger(__name__)

import traceback

# ========== 应用生命周期管理 ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 LangGraph API 服务启动")
    logger.info("📋 可用接口:")
    logger.info("   POST /api/table - 表结构生成")
    logger.info("   POST /api/etl - ETL脚本生成")
    logger.info("   POST /api/metric - 指标管理")
    logger.info("   POST /api/ddl - 表DDL查询")
    logger.info("   POST /api/scheduler - 调度信息查询")
    logger.info("   GET /health - 健康检查")
    logger.info("📖 API文档: http://localhost:8000/docs")

    yield

    # 关闭时执行
    logger.info("🛑 LangGraph API 服务关闭")


# FastAPI 应用初始化
app = FastAPI(
    title="LangGraph 智能数据开发平台 API",
    description="指标管理、表结构生成、ETL脚本开发、DDL查询、调度信息查询 - 统一响应格式",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agent管理器
agent_manager = get_agent_manager()

# ========== 核心接口 ==========

@app.post("/api/table", response_model=TableResponse)
async def create_table(request: TableRequest):
    """
    通过自然语言和表名生成/修改表结构信息

    输入：描述表需求的自然语言 + 表名
    输出：包含字段、类型、约束等完整表结构信息
    """
    try:
        logger.info(f"📊 收到表结构生成请求: {request.table_name}")
        logger.info(f"📝 用户需求: {request.user_input[:100]}...")

        # 执行表生成Agent（参考metric_agent，传入table_name参数）
        result = await agent_manager.execute_agent(
            agent_name="table_generation",
            user_input=request.user_input,
            table_name=request.table_name
        )

        if result.success and result.data:
            # 使用与metric_agent相同的数据结构
            operation_result = result.data.get("operation_result", {})
            table_info = result.data.get("table_info", {})
            message = operation_result.get("message", "")

            # 获取操作类型
            operation_type = operation_result.get("operation_type", "create")

            if table_info:
                logger.info(f"✅ 表结构生成成功: {table_info.get('nameZh', 'N/A')} ({operation_type})")
            else:
                logger.info(f"✅ 表结构生成成功，但无返回数据 ({operation_type})")

            return TableResponse(
                success=True,
                data=table_info or {},
                operation_type=operation_type,
                message=message,
                entity_type='SUB',
            )
        else:
            logger.error(f"❌ 表结构生成失败: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=result.error or "表结构生成失败")

    except Exception as e:
        logger.error(f"❌ 表结构生成异常: {str(traceback.format_exc())}")
        raise HTTPException(status_code=500, detail=f"表结构生成异常: {str(e)}")


@app.post("/api/etl", response_model=ETLResponse)
async def create_etl(request: ETLRequest):
    """
    通过自然语言和表名生成/修改ETL脚本

    输入：用户需求描述 + 目标表名
    输出：基于DDL变更的智能ETL代码
    """
    try:
        logger.info(f"📜 收到ETL脚本请求: {request.table_name}")
        logger.info(f"📝 用户需求: {request.user_input[:100]}...")

        # 执行新的ETL管理Agent（三步工作流）
        result = await agent_manager.execute_agent(
            agent_name="etl_management",
            user_input=request.user_input,
            table_name=request.table_name
        )

        if result.success and result.data:
            operation_result = result.data.get("operation_result", {})
            etl_info = result.data.get("etl_info", {})

            # 提取关键信息
            operation_type = operation_result.get("operation_type", "create")
            status = operation_result.get("status", "success")
            message = operation_result.get("message", "")
            modified_etl_code = operation_result.get("modified_etl_code")
            changes_summary = operation_result.get("changes_summary", [])

            logger.info(f"📊 ETL工作流结果: {operation_type} - {status} - {message}")

            # 构建响应数据 - 首先从etl_info开始，然后用指定字段覆盖
            response_data = dict(etl_info) if etl_info else {}

            # 用operation_result中的指定字段覆盖etl_info中的同名字段
            final_result = {
                "table_name": request.table_name,
                "etl_code": modified_etl_code,
                "changes_summary": changes_summary,
            }

            # 合并数据，存在的字段会被覆盖
            response_data.update(final_result)

            if modified_etl_code:
                logger.info(f"✅ ETL处理成功: {request.table_name} ({operation_type})")
                logger.info(f"📄 ETL代码长度: {len(modified_etl_code)} 字符")
                if changes_summary:
                    logger.info(f"📊 变更摘要: {len(changes_summary)} 项变更")
            else:
                logger.info(f"✅ ETL处理完成，但无代码数据返回 ({operation_type} - {status})")

            return ETLResponse(
                success=True,
                data=response_data,
                entity_type='DEV_ETL',
                operation_type=operation_type,
                message=message
            )
        else:
            logger.error(f"❌ ETL处理失败: {result.error}")
            raise HTTPException(status_code=500, detail=result.error or "ETL处理失败")

    except Exception as e:
        logger.error(f"❌ ETL处理异常: {str(e)}")
        logger.error(f"❌ ETL处理异常链路: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"ETL处理异常: {str(e)}")


@app.post("/api/metric", response_model=MetricResponse)
async def create_metric(request: MetricRequest):
    """
    通过自然语言生成或更新指标信息

    输入：描述指标需求的自然语言（创建或更新）
    输出：包含指标名称、编码、业务域、业务口径等完整指标元数据
    """
    try:
        logger.info(f"📊 收到指标管理请求: {request.user_input[:100]}...")
        logger.info(f"👤 用户账号: {request.um}")
        logger.info(f"📊 查询指标: {request.metric_name_zh}")

        # 执行指标管理工作流，权限检查在agent内部进行
        result = await agent_manager.execute_agent(
            agent_name="metric_management",
            user_input=request.user_input,
            um=request.um,
            metric_name_zh=request.metric_name_zh
        )

        if result.success and result.data:
            # 使用LangGraph工作流的数据结构
            operation_result = result.data.get("operation_result", {})

            # 从operation_result中提取信息
            operation_type = operation_result.get("operation_type", "create")
            status = operation_result.get("status", "success")
            message = operation_result.get("message", "")
            metric_info = operation_result.get("metric_info")
            existing_metric = operation_result.get("existing_metric")

            logger.info(f"📊 工作流结果: {operation_type} - {status} - {message}")

            # 根据操作类型和状态确定实际返回的指标信息
            final_metric_info = None
            response_success = True

            if metric_info:
                # 确保metric_info是字典格式
                if hasattr(metric_info, 'model_dump'):
                    final_metric_info = metric_info.model_dump()
                else:
                    final_metric_info = metric_info
            elif existing_metric:
                # 确保existing_metric是字典格式
                if hasattr(existing_metric, 'model_dump'):
                    final_metric_info = existing_metric.model_dump()
                else:
                    final_metric_info = existing_metric

            # 检查是否为权限错误
            if status == "error":
                response_success = False
                if final_metric_info:
                    logger.info(f"🚫 指标处理失败: {final_metric_info.get('nameZh', 'N/A')} - {message}")
                else:
                    logger.info(f"🚫 指标处理失败: {operation_type} - {message}")
            else:
                if final_metric_info:
                    logger.info(f"✅ 指标处理成功: {final_metric_info.get('nameZh', 'N/A')} ({operation_type})")
                else:
                    logger.info(f"✅ 指标处理完成，但无指标数据返回 ({operation_type} - {status})")

            return MetricResponse(
                success=response_success,
                data=final_metric_info,
                operation_type=operation_type,
                entity_type='MR',
                message=message
            )
        else:
            logger.error(f"❌ 指标处理失败: {result.error}")
            raise HTTPException(status_code=500, detail=result.error or "指标处理失败")

    except Exception as e:
        logger.error(f"❌ 指标处理异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"指标处理异常: {str(e)}")


@app.post("/api/metric/stream")
async def create_metric_stream(request: MetricStreamingRequest):
    """
    指标管理的流式接口

    通过流式输出处理指标创建、更新和查询的每个步骤
    """
    async def generate_stream():
        try:
            logger.info(f"📊 收到指标管理流式请求: {request.user_input[:100]}...")
            logger.info(f"👤 用户账号: {request.um}")
            logger.info(f"📊 查询指标: {request.metric_name_zh}")

            # 获取指标管理工作流Agent实例
            metric_agent = agent_manager.get_agent_instance("metric_management")
            if not metric_agent:
                # 尝试创建Agent实例
                metric_agent = await agent_manager.create_agent("metric_management")
                if not metric_agent:
                    yield f"data: {json.dumps({'step': 'error', 'error': '指标管理Agent未初始化', 'timestamp': datetime.now().isoformat()})}\n\n"
                    return

            # 流式执行Agent，权限检查在agent内部进行
            async for chunk in metric_agent.process_stream(request.user_input, um=request.um, metric_name_zh=request.metric_name_zh):
                # 格式化为SSE格式
                chunk_data = {
                    "step": chunk.get("step", "unknown"),
                    "data": chunk.get("data", {}),
                    "message": chunk.get("message", ""),
                    "timestamp": chunk.get("timestamp", datetime.now().isoformat())
                }
                yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"❌ 指标管理流式处理异常: {str(e)}")
            error_chunk = {
                "step": "error",
                "data": {"error": str(e)},
                "message": f"指标管理流式处理异常: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用Nginx缓冲
        }
    )

@app.post("/api/ddl", response_model=BaseResponse)
async def get_table_ddl(request: TableDDLRequest):
    """
    获取表DDL内容

    Args:
        request: 包含system_name, version_no, db_name, table_name, user_input的请求

    Returns:
        BaseResponse: 包含DDL内容的统一响应
    """
    try:
        logger.info(f"🔍 收到表DDL查询请求: {request.db_name}.{request.table_name}")
        logger.info(f"📋 请求来源: {request.system_name} v{request.version_no}")

        # 调用表DDL服务
        result = await table_ddl_service.get_table_ddl_with_validation(
            system_name=request.system_name,
            version_no=request.version_no,
            db_name=request.db_name,
            table_name=request.table_name,
            user_input=request.user_input or ""
        )

        if result["success"]:
            logger.info(f"✅ 表DDL查询成功: {request.table_name}")
            return BaseResponse(
                success=True,
                data=result["data"],
                operation_type="query",
                entity_type="DEV_DDL",
                message=result["message"]
            )
        else:
            logger.warning(f"⚠️ 表DDL查询失败: {result['message']}")
            return BaseResponse(
                success=False,
                data=None,
                operation_type="query",
                entity_type="DDL",
                error=result["message"]
            )

    except Exception as e:
        logger.error(f"💥 表DDL查询API异常: {str(e)}")
        return BaseResponse(
            success=False,
            data=None,
            operation_type="query",
            entity_type="DDL",
            error=f"表DDL查询异常: {str(e)}"
        )


@app.post("/api/scheduler", response_model=BaseResponse)
async def get_scheduler_info(request: SchedulerRequest):
    """
    获取表调度信息

    Args:
        request: 包含system_name, version_no, db_name(可选), table_name, user_input的请求

    Returns:
        BaseResponse: 包含调度信息的统一响应
    """
    try:
        logger.info(f"⏰ 收到调度查询请求: {request.system_name} v{request.version_no}")
        logger.info(f"📋 查询表: {request.db_name}.{request.table_name if request.db_name else request.table_name}")
        if request.user_input:
            logger.info(f"📝 用户需求: {request.user_input[:100]}...")

        # 调用调度服务
        result = await scheduler_service.get_scheduler_info_with_validation(
            system_name=request.system_name,
            version_no=request.version_no,
            db_name=request.db_name,
            table_name=request.table_name,
            user_input=request.user_input or ""
        )

        if result["success"]:
            logger.info(f"✅ 调度查询成功: {request.table_name}")
            return BaseResponse(
                success=True,
                data=result["data"],
                operation_type="query",
                entity_type="SCHEDULER",
                message=result["message"]
            )
        else:
            logger.warning(f"⚠️ 调度查询失败: {result['message']}")
            return BaseResponse(
                success=False,
                data=None,
                operation_type="query",
                entity_type="SCHEDULER",
                error=result["message"]
            )

    except Exception as e:
        logger.error(f"💥 调度查询API异常: {str(e)}")
        return BaseResponse(
            success=False,
            data=None,
            operation_type="query",
            entity_type="SCHEDULER",
            error=f"调度查询异常: {str(e)}"
        )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    try:
        return HealthResponse(status="healthy")
    except Exception as e:
        logger.error(f"健康检查异常: {str(e)}")
        raise HTTPException(status_code=500, detail="健康检查失败")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main_api:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )