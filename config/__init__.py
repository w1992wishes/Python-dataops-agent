"""
配置模块
"""
from .metric_prompts import (
    METRIC_ANALYSIS_PROMPT,
)
from .table_prompts import (
    TABLE_ANALYSIS_PROMPT,
)
from .etl_prompts import (
    ETL_MODIFICATION_PROMPT,
    ETL_CREATION_PROMPT,
)

__all__ = [
    "METRIC_ANALYSIS_PROMPT",
    "TABLE_ANALYSIS_PROMPT",
    "ETL_MODIFICATION_PROMPT",
    "ETL_CREATION_PROMPT",
]