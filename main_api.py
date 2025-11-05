"""
LangGraph 智能数据开发平台 API
精简版本 - 只包含指标、表结构、ETL三个核心功能 + 流式输出
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging
import json
from datetime import datetime

# 导入Agent管理系统
from agents import get_agent_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ========== 数据模型 ==========

class BaseRequest(BaseModel):
    """基础请求模型"""
    user_input: str = Field(..., description="用户自然语言输入")


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(..., description="请求是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="返回数据")
    error: Optional[str] = Field(None, description="错误信息")
    operation_type: Optional[str] = Field(None, description="操作类型：create/update/query")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class StreamingChunk(BaseModel):
    """流式输出数据块"""
    step: str = Field(..., description="当前步骤")
    data: Optional[Dict[str, Any]] = Field(None, description="步骤数据")
    message: Optional[str] = Field(None, description="步骤消息")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class MetricStreamingRequest(BaseModel):
    """指标流式请求"""
    user_input: str = Field(..., description="用户自然语言输入")


class TableResponse(BaseResponse):
    """表结构响应"""
    pass  # 使用BaseResponse的data字段存储所有数据


class ETLResponse(BaseResponse):
    """ETL脚本响应"""
    pass  # 使用BaseResponse的data字段存储所有数据


class MetricResponse(BaseResponse):
    """指标响应"""
    pass  # 使用BaseResponse的data字段存储所有数据


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(default="healthy")
    version: str = Field(default="3.0.0")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class StreamingChunk(BaseModel):
    """流式输出数据块"""
    step: str = Field(..., description="当前步骤")
    data: Optional[Dict[str, Any]] = Field(None, description="步骤数据")
    message: Optional[str] = Field(None, description="步骤消息")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class MetricStreamingRequest(BaseModel):
    """指标流式请求"""
    user_input: str = Field(..., description="用户自然语言输入")


# ========== FastAPI 应用初始化 ==========

app = FastAPI(
    title="LangGraph 智能数据开发平台 API",
    description="指标管理、表结构生成、ETL脚本开发",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    logger.info("   GET /health - 健康检查")
    logger.info("📖 API文档: http://localhost:8000/docs")

    yield

    # 关闭时执行
    logger.info("🛑 LangGraph API 服务关闭")


# FastAPI 应用初始化
app = FastAPI(
    title="LangGraph 智能数据开发平台 API",
    description="指标管理、表结构生成、ETL脚本开发",
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

logger.info("🚀 LangGraph API 初始化完成 - 精简版")


# ========== 核心接口 ==========

@app.post("/api/table", response_model=TableResponse)
async def create_table(request: BaseRequest):
    """
    通过自然语言生成表结构信息

    输入：描述表需求的自然语言
    输出：包含字段、类型、约束等完整表结构信息
    """
    try:
        logger.info(f"📊 收到表结构生成请求: {request.user_input[:100]}...")

        # 执行表生成Agent
        result = await agent_manager.execute_agent(
            agent_name="table_generation",
            user_input=request.user_input
        )

        if result.success and result.data:
            table_info = result.data.get("table_info", {})
            analysis_data = result.data.get("analysis", {})

            # 获取操作类型
            operation_type = analysis_data.get("operation_type", "create")

            # 统一数据格式
            response_data = {
                "result": "表结构生成成功",
                "table_info": table_info or {}
            }

            if table_info:
                logger.info(f"✅ 表结构生成成功: {table_info.get('nameZh', 'N/A')} ({operation_type})")
            else:
                logger.info(f"✅ 表结构生成成功，但无返回数据 ({operation_type})")

            return TableResponse(
                success=True,
                data=response_data.get("table_info"),
                operation_type=operation_type
            )
        else:
            logger.error(f"❌ 表结构生成失败: {result.error}")
            raise HTTPException(status_code=500, detail=result.error or "表结构生成失败")

    except Exception as e:
        logger.error(f"❌ 表结构生成异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"表结构生成异常: {str(e)}")


@app.post("/api/etl", response_model=ETLResponse)
async def create_etl(request: BaseRequest):
    """
    通过自然语言生成ETL脚本信息

    输入：描述ETL需求的自然语言
    输出：包含源表、目标表、转换逻辑、SQL脚本等ETL信息
    """
    try:
        logger.info(f"📜 收到ETL脚本生成请求: {request.user_input[:100]}...")

        # 执行ETL开发Agent
        result = await agent_manager.execute_agent(
            agent_name="etl_development",
            user_input=request.user_input
        )

        if result.success and result.data:
            etl_script = result.data.get("etl_info", {})
            analysis_data = result.data.get("analysis", {})

            # 获取操作类型
            operation_type = analysis_data.get("operation_type", "create")

            # 统一数据格式
            response_data = {
                "result": "ETL脚本生成成功",
                "etl_info": etl_script or {}
            }

            if etl_script:
                logger.info(f"✅ ETL脚本生成成功: {etl_script.get('name', 'N/A')} ({operation_type})")
            else:
                logger.info(f"✅ ETL脚本生成成功，但无返回数据 ({operation_type})")

            return ETLResponse(
                success=True,
                data=response_data.get("etl_info"),
                operation_type=operation_type
            )
        else:
            logger.error(f"❌ ETL脚本生成失败: {result.error}")
            raise HTTPException(status_code=500, detail=result.error or "ETL脚本生成失败")

    except Exception as e:
        logger.error(f"❌ ETL脚本生成异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ETL脚本生成异常: {str(e)}")


@app.post("/api/metric", response_model=MetricResponse)
async def create_metric(request: BaseRequest):
    """
    通过自然语言生成或更新指标信息

    输入：描述指标需求的自然语言（创建或更新）
    输出：包含指标名称、编码、业务域、业务口径等完整指标元数据
    """
    try:
        logger.info(f"📊 收到指标管理请求: {request.user_input[:100]}...")

        # 执行指标管理Agent
        result = await agent_manager.execute_agent(
            agent_name="metric_management",
            user_input=request.user_input
        )

        if result.success and result.data:
            metric_data = result.data.get("metric")
            analysis_data = result.data.get("analysis", {})

            # 获取操作类型
            operation_type = analysis_data.get("operation_type", "create")

            # 统一数据格式
            response_data = {
                "result": "指标处理成功",
                "metric_info": metric_data or {},
                "analysis": analysis_data,
                "existing_metric": result.data.get("existing_metric")
            }

            if metric_data:
                logger.info(f"✅ 指标处理成功: {metric_data.get('nameZh', 'N/A')} ({operation_type})")
            else:
                logger.info(f"✅ 指标处理成功，但无返回数据 ({operation_type})")

            return MetricResponse(
                success=True,
                data=response_data.get("metric_info"),
                operation_type=operation_type
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

            # 获取指标管理Agent实例
            metric_agent = agent_manager.get_agent_instance("metric_management")
            if not metric_agent:
                # 尝试创建Agent实例
                metric_agent = await agent_manager.create_agent("metric_management")
                if not metric_agent:
                    yield f"data: {json.dumps({'step': 'error', 'error': '指标管理Agent未初始化', 'timestamp': datetime.now().isoformat()})}\n\n"
                    return

            # 流式执行Agent
            async for chunk in metric_agent.process_stream(request.user_input):
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
        reload=True
    )