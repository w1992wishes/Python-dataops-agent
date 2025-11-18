"""
方案一：模式引导生成
通过优化提示词引导模型输出正确的结构化格式
"""

import os
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
import json
import re

# 数据模型
class UserInfo(BaseModel):
    name: str = Field(description="用户姓名")
    age: int = Field(ge=0, le=150, description="用户年龄")
    email: str = Field(description="邮箱地址")
    interests: list[str] = Field(description="兴趣爱好")

class PromptBasedExtractor:
    """基于模式引导的结构化输出提取器"""

    def __init__(self, model_name: str = "deepseek-ai/DeepSeek-V3.1"):
        self.llm = ChatOpenAI(
            api_key=os.getenv("SILICONFLOW_API_KEY"),
            model=model_name,
            base_url="https://api.siliconflow.cn/v1/",
            temperature=0.1
        )
        self.parser = PydanticOutputParser(pydantic_object=UserInfo)

    def create_basic_prompt(self) -> ChatPromptTemplate:
        """基础提示词"""
        template = """
请从以下文本中提取用户信息，并严格按照JSON格式输出：

用户输入：{user_input}

输出格式要求：
{format_instructions

请严格按照上述格式输出，不要添加任何解释性文字。
        """
        return ChatPromptTemplate.from_template(template)

    def create_enhanced_prompt(self) -> ChatPromptTemplate:
        """增强提示词"""
        template = """
# 任务说明
你是一个专业的信息提取专家。请从用户输入的文本中提取用户信息，
并严格按照指定的JSON格式输出。

# 严格要求
⚠️ 重要：你必须且只能输出JSON格式数据，不允许：
- 任何解释性文字（如"以下是JSON："）
- 格式标记（如```json```）
- 任何前言后语
- 使用单引号代替双引号

# 输出结构
{format_instructions}

# 格式强化示例
✅ 正确输出：
{{"name": "张三", "age": 25, "email": "zhangsan@example.com", "interests": ["编程", "阅读"]}}

❌ 错误输出：
"这是您要的用户信息：{{"name": "张三"}}"
{{'name': '张三', 'age': 25}}  # 使用了单引号
{{"name": "张三"}} 希望对您有帮助！  # 输出后还有其他文字

# 处理原则
1. 如果某个字段在文本中没有提到，请设为null或合理的默认值
2. 邮箱必须符合标准格式
3. 兴趣爱好可以有多个，也可以为空数组

# 用户输入
{user_input}

现在请严格按照上述格式和示例，输出纯JSON格式结果：
        """
        return ChatPromptTemplate.from_template(template)

    def create_few_shot_prompt(self) -> ChatPromptTemplate:
        """少样本学习提示词"""
        template = """
# 任务说明
你是一个专业的信息提取专家。请从用户输入的文本中提取用户信息，
并严格按照指定的JSON格式输出。

# 输出格式要求
{format_instructions}

# 示例学习
示例1：
输入："李四今年30岁，是个软件工程师，邮箱是 lisi@example.com，喜欢编程和旅游"
输出：
{{
    "name": "李四",
    "age": 30,
    "email": "lisi@example.com",
    "interests": ["编程", "旅游"]
}}

示例2：
输入："王芳，25岁，学生，邮箱 wangfang@email.com"
输出：
{{
    "name": "王芳",
    "age": 25,
    "email": "wangfang@email.com",
    "interests": []
}}

示例3：
输入："赵六，没有提供邮箱，喜欢篮球和音乐，年龄未知"
输出：
{{
    "name": "赵六",
    "age": null,
    "email": null,
    "interests": ["篮球", "音乐"]
}}

# 当前任务
输入：{user_input}

请根据以上示例，输出JSON格式结果：
        """
        return ChatPromptTemplate.from_template(template)

    def create_robust_prompt(self) -> ChatPromptTemplate:
        """最稳定的提示词"""
        template = """
# 🔧 任务定义
从用户文本中提取结构化用户信息，严格按照JSON Schema输出。

# ⚠️ 严格格式要求
- 仅输出纯JSON，无任何前后缀
- 使用双引号，不使用单引号
- 数字不使用引号
- 数组使用方括号，布尔值使用小写true/false
- 确保所有括号配对

# 📋 JSON Schema
{format_instructions}

# 📚 详细示例
示例1（完整信息）：
输入："张明，28岁，程序员，邮箱：zhangming.dev@email.com，爱好：编程、阅读、旅行"
输出：
{{
    "name": "张明",
    "age": 28,
    "email": "zhangming.dev@email.com",
    "interests": ["编程", "阅读", "旅行"]
}}

示例2（部分信息）：
输入："李娜，学生，爱好：画画、音乐"
输出：
{{
    "name": "李娜",
    "age": null,
    "email": null,
    "interests": ["画画", "音乐"]
}}

示例3（邮箱格式）：
输入："王伟，wangwei@company.com"
输出：
{{
    "name": "王伟",
    "age": null,
    "email": "wangwei@company.com",
    "interests": []
}}

# 🎯 当前输入
{user_input}

# ✅ 输出要求
现在请严格按照上述格式和示例，输出纯JSON格式结果：
        """
        return ChatPromptTemplate.from_template(template)

    def extract_with_strategy(self, user_input: str, strategy: str = "robust"):
        """使用指定策略提取信息"""
        try:
            # 选择提示词策略
            if strategy == "basic":
                prompt = self.create_basic_prompt()
            elif strategy == "enhanced":
                prompt = self.create_enhanced_prompt()
            elif strategy == "few_shot":
                prompt = self.create_few_shot_prompt()
            else:  # robust
                prompt = self.create_robust_prompt()

            # 创建处理链
            chain = prompt | self.llm | self.parser

            # 执行提取
            result = chain.invoke({
                "user_input": user_input,
                "format_instructions": self.parser.get_format_instructions()
            })

            return result

        except Exception as e:
            print(f"❌ {strategy}策略提取失败: {str(e)}")
            return None

    def manual_parse_fallback(self, raw_output: str):
        """手动解析备选方案"""
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                return UserInfo.model_validate(data)
            else:
                return None
        except Exception:
            return None

def main():
    """主函数演示模式引导生成"""
    print("🚀 模式引导生成演示")
    print("="*50)

    extractor = PromptBasedExtractor()

    # 测试用例
    test_cases = [
        "李四今年30岁，是个软件工程师，邮箱是 lisi@example.com，喜欢编程和旅游",
        "王芳，25岁，学生，邮箱 wangfang@email.com",
        "赵六，没有提供邮箱，喜欢篮球和音乐，年龄未知",
        "孙七，电话138-1234-5678，年龄35岁，爱好：运动、阅读、看电影，邮箱：sunqi@email.com"
    ]

    strategies = ["basic", "enhanced", "few_shot", "robust"]

    for i, test_input in enumerate(test_cases, 1):
        print(f"\n🧪 测试用例 {i}: {test_input}")
        print("-" * 40)

        for strategy in strategies:
            print(f"\n📋 策略: {strategy}")

            try:
                result = extractor.extract_with_strategy(test_input, strategy)

                if result:
                    print("✅ 提取成功:")
                    print(f"   姓名: {result.name}")
                    print(f"   年龄: {result.age}")
                    print(f"   邮箱: {result.email}")
                    print(f"   兴趣: {', '.join(result.interests) if result.interests else '无'}")
                else:
                    print("❌ 提取失败")

            except Exception as e:
                print(f"💥 异常: {str(e)}")

        # 分隔线
        if i < len(test_cases):
            print("\n" + "="*50)

if __name__ == "__main__":
    main()