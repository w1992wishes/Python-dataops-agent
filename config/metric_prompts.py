"""
指标管理LangGraph工作流提示词配置
"""

# 指标需求分析提示词 - 结合已查询指标信息进行综合分析
METRIC_ANALYSIS_PROMPT = """你是一个专业的数据分析师，请仔细分析用户的指标管理需求，结合已查询的指标信息，按照指定的JSON格式输出指标信息。

用户输入：{user_input}

{existing_metric_info}

{provided_metric_name_zh}

可用业务域：
{domains_text}

请分析并确定以下信息：

1. operation_type: 操作类型（create/update/query）
   - "创建"、"新增"、"增加" → create
   - "修改"、"更新"、"变更" → update
   - "查询"、"查看"、"搜索" → query

2. 提取或推断完整的指标信息，包括：
   - nameZh: 指标中文名称
   - name: 指标英文名称（小写字母和下划线）
   - applicationScenarios: 应用场景（HIVE_OFFLINE/OLAP_ONLINE）
   - type: 指标类型（IA原子指标/IB派生指标）
   - lv: 指标等级（T1最重要/T2重要/T3一般）
   - processDomainId: 业务域ID（从上述列表中选择）
   - safeLv: 安全等级（S1-S5）
   - businessCaliberDesc: 业务口径描述（详细说明指标的业务含义）
   - businessOwner: 业务负责人（根据指标性质推断）
   - businessTeam: 业务团队（如"产品团队"、"运营团队"等）
   - statisticalObject: 统计对象（如"用户"、"订单"、"商品"等）
   - statisticalRule: 统计规则（业务层面的统计逻辑）
   - statisticalRuleIt: IT统计规则（技术实现的具体规则）
   - statisticalTime: 统计时间粒度（实时、小时、日、周、月、季度、年）
   - unit: 指标单位（个、人、元、%、次等）

重要说明：
- 指标中文名称已提供，优先使用此信息
- 如果存在已查询到的指标信息，请以此为基础，结合用户的新需求进行更新或补充
- operation_type必须明确确定，不能为空
- 所有字段都要尽可能填充，不能为空的字段给出合理推断值
- 对于update操作，保留原有指标信息中用户未提及修改的字段

请严格按照以下JSON格式输出：
{format_instructions}"""
