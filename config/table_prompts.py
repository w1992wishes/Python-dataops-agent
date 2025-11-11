"""
表管理LangGraph工作流提示词配置
"""

# 表需求分析提示词 - 直接输出TableAnalysisResult格式
TABLE_ANALYSIS_PROMPT = """你是一个专业的数据架构师，请仔细分析用户的表管理需求，并按照指定的JSON格式输出表信息。

用户输入：{user_input}

请分析并确定以下信息：

1. operation_type: 操作类型（create/update/query）
   - "创建"、"新建"、"生成"、"建立一个" → create
   - "修改"、"更新"、"变更"、"调整" → update
   - "查询"、"查看"、"搜索"、"找一下"、"获取" → query

2. 提取或推断完整的表信息，包括：
   - db_name: 数据库名称（如果用户明确指定）
   - table_name: 表名称（如果用户明确指定）
   - table_name_zh: 表中文名称（根据描述推断）
   - table_purpose: 表的用途和业务场景描述
   - metric_name_zh_list: 从用户描述中识别出所有与指标相关的中文名称列表

重要说明：
- 如果用户没有明确提到数据库名或表名，请根据描述推断可能的名称
- operation_type必须明确确定，不能为空
- table_name_zh和table_purpose要尽可能详细和准确
- metric_name_zh_list要包含所有可能相关的指标词汇

请严格按照以下JSON格式输出：
{format_instructions}"""

# 表创建默认配置
TABLE_CREATION_DEFAULTS = {
    "db_name": "warehouse",
    "table_name": "generated_table",
    "table_name_zh": "生成的表",
    "table_purpose": "基于用户需求生成的表",
    "metric_name_zh_list": []
}

# 表类型说明
TABLE_TYPE_DESCRIPTIONS = """
表操作类型说明：
- create: 创建新表
- update: 修改现有表结构
- query: 查询表信息

表类型说明：
- IAT: 原子指标表（存储直接统计的指标数据）
- IBT: 派生指标表（存储通过计算得出的指标数据）

表层级说明：
- SUB: 明细表（存储最细粒度的数据）
- AGG: 汇总表（存储聚合后的数据）

表应用类型说明：
- NORMAL: 普通表（常规业务表）
- TMP: 临时表（临时存储数据）
- MID: 中间表（ETL过程中的中间结果表）

字段属性说明：
- DIM: 维度字段（用于描述和分析的角度）
- METRIC: 指标字段（用于衡量的数值）
- NORMAL: 普通字段（一般属性字段）

字段数据类型说明：
- string: 字符串类型
- date: 日期类型
- float: 数值类型

字段分类说明：
- 0: 普通字段
- 2: 分区键字段
"""