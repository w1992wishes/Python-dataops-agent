"""
表管理LangGraph工作流提示词配置
"""

# 表请求解析提示词 - 第一次LLM交互，解析用户输入
TABLE_REQUEST_ANALYSIS_PROMPT = """你是数据架构师，请从用户描述中提取表请求信息：
用户描述: {user_input}

1. operation_type:
- 含"创建/新增/建表"→create；含"修改/更新"→update
2. db_name: 用户明确指定则提取，否则为null
3. table_name: 用户明确指定则提取，否则为null
4. metric_name_zh_list: 提取所有指标中文名称列表
5. table_purpose: 总结表的用途和业务场景

重要说明 - 如何准确识别指标：
指标是业务度量值，通常具有以下特征：
✅ 正确的指标示例：用户活跃度、订单金额、转化率、客单价、留存率、GMV、DAU、MAU
❌ 不是指标的表字段名：用户名、手机号、注册时间、邮箱、订单ID、地址、性别、年龄

判断标准：
- 指标通常是数值型或可量化的业务度量
- 指标名称包含"度"、"率"、"金额"、"数量"、"比值"等业务度量词汇
- 表字段名是基础属性信息，如ID、名称、时间、联系方式等
- 如果是基础属性字段，不要提取为指标

操作类型需精准判断，数据库/表名不凭空推测，指标列表需准确区分真正的业务指标。

{format_instructions}"""


# 表结构生成提示词 - 第二次LLM交互，生成最终表结构
TABLE_STRUCTURE_PROMPT = """你是专业数据架构师，根据以下信息生成规范表结构：
用户需求: {user_input}
表用途: {table_purpose}
操作类型: {operation_type}
已存在表: {existing_info}
关联指标: {metrics_info}
可用业务域:
{domains_text}

请生成包含以下信息的完整TableInfo对象：
- name: 表英文名（小写下划线）
- nameZh: 表中文名
- businessDomainId: 业务域ID（从可用域中选择）
- daName: 数据库名称（如果用户指定则使用，否则用default_db）
- levelType: 表层级类型（SUB/AGG）
- type: 表类型（IAT/IBT）
- tableProp: 表应用类型（NORMAL/TMP/MID）
- particleSize: 数据粒度
- itOwner: "system"
- itGroup: "data_team"
- businessOwner: "待指定"
- businessGroup: "待指定"
- cols: 字段列表，每个字段包含name, nameZh, colProp, dataType, colType

字段说明：
- colProp: DIM(维度)/METRIC(指标)/NORMAL(普通)
- dataType: string/date/float
- colType: 0(普通字段)/2(分区键)
- 如果字段关联指标，在字段信息中注明对应的metric_id

业务规则：
- 如果表已存在且操作类型为create，返回exist状态
- 如果表不存在且操作类型为update，返回not_exist状态
- 成功创建或更新时，返回success状态并生成完整表结构
- 查询操作直接返回已存在的表信息

{format_instructions}"""


