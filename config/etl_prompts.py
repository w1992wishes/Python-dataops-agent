"""
ETL开发LangGraph工作流提示词配置
"""

# ETL代码修改提示词 - 基于DDL变更修改ETL代码
ETL_MODIFICATION_PROMPT = """你是一个资深的ETL开发专家，需要根据DDL变更和用户需求来修改ETL代码。

用户原始需求：{user_input}

目标表名：{table_name}
操作类型：{operation_type}
用户具体需求：{user_requirements}

现有ETL代码：
```sql
{original_etl_code}
```

对表做的变更ddl：
```sql
{ddl_content}
```

请根据以上信息修改ETL代码，要求：

1. **必须处理所有DDL变更**：
   - 如果有新增字段，需要在SELECT语句中添加对应的字段
   - 如果有字段类型变更，需要相应调整数据处理逻辑
   - 如果有字段删除，需要从SELECT语句中移除对应字段

2. **保持ETL代码结构**：
   - 保留原有的INSERT OVERWRITE结构
   - 保持原有的表连接和过滤条件
   - 维护原有的配置参数和变量

3. **优化数据处理**：
   - 确保新字段有正确的数据源映射
   - 处理可能的NULL值和默认值
   - 考虑数据类型转换的兼容性

4. **代码质量**：
   - 保持SQL语法正确
   - 添加适当的注释说明变更内容
   - 确保代码可读性和维护性

请只返回修改后的完整ETL代码，不要包含```sql```标记和额外的解释。

{format_instructions}"""

# ETL代码创建提示词 - 全新创建ETL代码
ETL_CREATION_PROMPT = """你是一个资深的ETL开发专家，需要根据用户需求和DDL结构创建全新的ETL代码。

用户需求：{user_input}
目标表名：{table_name}
用户具体需求：{user_requirements}

目标表DDL结构：
```sql
{ddl_content}
```

请创建完整的Hive ETL脚本，包含以下部分：

1. **配置部分**：
   - Hive参数设置
   - 日期变量定义
   - 必要的SET语句

2. **转换逻辑部分**：
   - INSERT OVERWRITE语句
   - 完整的SELECT查询逻辑
   - 数据处理和转换

3. **特殊要求**：
   - 根据DDL中的所有字段生成SELECT字段列表
   - 添加数据质量检查
   - 处理分区键（如果有）
   - 考虑性能优化

4. **代码规范**：
   - 添加清晰的注释说明
   - 使用标准SQL语法
   - 确保代码格式工整

请返回完整的Hive ETL脚本，不要包含```sql```标记。

{format_instructions}"""