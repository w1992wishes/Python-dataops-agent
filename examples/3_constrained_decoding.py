"""
方案三：约束解码
在生成过程中实时约束token选择，从根本上保证输出格式正确性
"""

import os
import json
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from typing import Dict, Any, Set, Optional, List
from enum import Enum
from dataclasses import dataclass

# 数据模型
class ProductInfo(BaseModel):
    name: str = Field(description="产品名称")
    price: float = Field(ge=0, description="产品价格")
    currency: str = Field(default="USD", description="货币单位")
    category: str = Field(description="产品类别")
    features: List[str] = Field(description="产品特性")
    in_stock: bool = Field(description="是否有库存")

@dataclass
class GrammarState:
    """语法状态跟踪"""
    position: str  # 当前位置: start, object_start, key_start, key_content, key_end, value_start, etc.
    expected_tokens: Set[str]  # 期望的token集合
    depth: int  # 嵌套深度
    in_string: bool  # 是否在字符串中
    string_delimiter: Optional[str] = None
    current_key: Optional[str] = None  # 当前处理的键
    brace_count: int = 0  # 大括号计数

class JSONGrammarValidator:
    """JSON语法验证器 - 约束解码的核心组件"""

    def __init__(self, schema: Dict[str, Any] = None):
        self.schema = schema or {}
        self.required_keys = set(schema.get("required", []))
        self.allowed_keys = set(schema.get("properties", {}).keys())

    def get_next_allowed_tokens(self, state: GrammarState, text_so_far: str) -> Set[str]:
        """根据当前语法状态获取允许的token集合"""
        allowed = set()

        # 基础字符集合
        basic_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        basic_chars.update(set('., -_'))
        allowed.update(basic_chars)

        # 根据状态约束
        if state.position == "start":
            return {"{"}

        elif state.position == "object_start":
            allowed.update({'"', "}"})

        elif state.position == "key_start":
            return {'"'}

        elif state.position == "key_content":
            allowed.update(set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'))

        elif state.position == "key_end":
            return {':'}

        elif state.position == "value_start":
            # 根据键名和schema确定值类型
            if state.current_key == "name" or state.current_key == "category":
                return {'"'}
            elif state.current_key == "price":
                return set('0123456789')
            elif state.current_key == "in_stock":
                return set('tfn')  # true, false, null
            elif state.current_key == "features":
                return {'['}
            elif state.current_key == "currency":
                return {'"'}
            else:
                return {'"', '0', 't', 'f', 'n', '['}  # string, number, true, false, null, array

        elif state.position == "string_content":
            if state.string_delimiter == '"':
                allowed.update(set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .-_/'))
            allowed.update({'"',})

        elif state.position == "array_content":
            allowed.update(set('"0123456789tfn'))
            allowed.update({']', ','})

        elif state.position == "object_key_separator":
            allowed.update({',', '}'})

        return allowed

    def update_state(self, state: GrammarState, token: str) -> GrammarState:
        """根据新token更新语法状态"""
        new_state = GrammarState(
            position=state.position,
            expected_tokens=state.expected_tokens.copy(),
            depth=state.depth,
            in_string=state.in_string,
            string_delimiter=state.string_delimiter,
            current_key=state.current_key,
            brace_count=state.brace_count
        )

        # 状态转换逻辑
        if token == '{':
            new_state.position = "object_start"
            new_state.depth += 1
            new_state.brace_count += 1
            new_state.in_string = False

        elif token == '}':
            new_state.position = "object_end"
            new_state.depth -= 1
            new_state.brace_count -= 1

        elif token == '"':
            if not new_state.in_string:
                if new_state.position in ["object_start", "object_key_separator"]:
                    new_state.position = "key_start"
                elif new_state.position in ["value_start"]:
                    new_state.position = "string_content"
                new_state.in_string = True
                new_state.string_delimiter = '"'
            else:
                new_state.in_string = False
                new_state.string_delimiter = None
                if new_state.position == "key_content":
                    new_state.position = "key_end"
                elif new_state.position == "string_content":
                    new_state.position = "object_key_separator"

        elif token == ':':
            if new_state.position == "key_end":
                new_state.position = "value_start"

        elif token == ',':
            if new_state.position == "object_key_separator":
                new_state.position = "key_start"
            elif new_state.position == "array_content":
                new_state.position = "array_content"

        elif token == '[':
            if new_state.position == "value_start" and new_state.current_key == "features":
                new_state.position = "array_content"

        elif token == ']':
            if new_state.position == "array_content":
                new_state.position = "object_key_separator"

        elif token.isalnum():
            if new_state.position == "key_start":
                new_state.position = "key_content"
                new_state.current_key = token
            elif new_state.position == "key_content":
                new_state.current_key += token
            elif new_state.position == "string_content":
                # 字符串内容，保持状态
                pass
            elif new_state.position == "value_start" and token in "tfn":
                # true, false, null的开始
                pass

        return new_state

    def validate_partial_json(self, text: str) -> bool:
        """验证部分JSON是否符合语法"""
        try:
            state = GrammarState(
                position="start",
                expected_tokens=set(),
                depth=0,
                in_string=False,
                brace_count=0
            )

            for char in text:
                # 获取当前允许的token
                allowed_tokens = self.get_next_allowed_tokens(state, text)

                # 检查字符是否被允许
                if char not in allowed_tokens:
                    return False

                # 更新状态
                state = self.update_state(state, char)

            # 检查最终状态
            return state.brace_count == 0 and (state.position == "object_end" or state.position == "object_key_separator")

        except Exception:
            return False

class ConstrainedTokenGenerator:
    """约束Token生成器"""

    def __init__(self, llm):
        self.llm = llm
        self.grammar_validator = JSONGrammarValidator()

    def generate_with_constraints(self, prompt: str, max_length: int = 500) -> str:
        """使用约束生成文本"""
        try:
            generated_text = ""
            state = GrammarState(
                position="start",
                expected_tokens=set(),
                depth=0,
                in_string=False,
                brace_count=0
            )

            # 使用简单的约束生成策略
            for step in range(20):  # 限制步数避免无限循环
                # 获取当前允许的token
                allowed_tokens = self.grammar_validator.get_next_allowed_tokens(state, generated_text)

                # 构建约束提示
                constraint_prompt = f"""
{prompt}

当前生成的JSON：{generated_text}

请继续生成，只使用以下字符：{sorted(list(allowed_tokens))}
每个字符都必须符合JSON语法规则。
请只输出接下来的字符，不要解释。
"""

                # 获取下一个字符
                response = self.llm.invoke(constraint_prompt)
                next_char = response.content.strip()[:1]  # 只取第一个字符

                # 验证字符
                if next_char in allowed_tokens:
                    generated_text += next_char
                    state = self.grammar_validator.update_state(state, next_char)

                    # 检查是否完成
                    if state.brace_count == 0 and state.position != "start":
                        break
                else:
                    # 字符不被允许，尝试找到最接近的有效字符
                    closest_char = self._find_closest_valid_char(next_char, allowed_tokens)
                    if closest_char:
                        generated_text += closest_char
                        state = self.grammar_validator.update_state(state, closest_char)

            return generated_text

        except Exception as e:
            print(f"约束生成失败: {str(e)}")
            return ""

    def _find_closest_valid_char(self, char: str, allowed_tokens: Set[str]) -> Optional[str]:
        """找到最接近的有效字符"""
        # 简单的策略：查找包含在允许字符中的字符
        for c in char:
            if c in allowed_tokens:
                return c

        # 默认尝试
        if '"' in allowed_tokens and state.position in ["object_start", "key_start", "value_start"]:
            return '"'
        elif '}' in allowed_tokens:
            return '}'
        elif ':' in allowed_tokens:
            return ':'
        elif ',' in allowed_tokens:
            return ','

        return None

class ConstrainedDecodingSystem:
    """约束解码系统"""

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=os.getenv("SILICONFLOW_API_KEY"),
            model="deepseek-ai/DeepSeek-V3.1",
            base_url="https://api.siliconflow.cn/v1/",
            temperature=0.1
        )
        self.generator = ConstrainedTokenGenerator(self.llm)

    def generate_structured_output(self, prompt: str, schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """生成结构化输出"""
        try:
            # 设置语法验证器
            self.generator.grammar_validator = JSONGrammarValidator(schema)

            # 构建结构化提示
            structured_prompt = f"""
请生成产品信息的JSON格式输出。

要求格式：
{json.dumps(schema, indent=2, ensure_ascii=False)}

用户需求：{prompt}

请严格按照JSON格式输出，确保所有括号、引号都正确匹配。
"""

            # 约束生成
            generated_json = self.generator.generate_with_constraints(structured_prompt)

            # 验证输出
            try:
                parsed_data = json.loads(generated_json)
                return parsed_data
            except json.JSONDecodeError:
                # 如果解析失败，尝试后处理修复
                return self._post_process_json(generated_json)

        except Exception as e:
            print(f"约束解码失败: {str(e)}")
            return None

    def _post_process_json(self, text: str) -> Optional[Dict[str, Any]]:
        """后处理修复JSON"""
        try:
            # 提取JSON部分
            json_match = json.loads(text)
            return json_match
        except:
            # 如果还是失败，使用启发式修复
            return self._heuristic_json_repair(text)

    def _heuristic_json_repair(self, text: str) -> Optional[Dict[str, Any]]:
        """启发式JSON修复"""
        try:
            # 确保以 { 开头，以 } 结尾
            if not text.strip().startswith('{'):
                text = '{' + text.strip()
            if not text.strip().endswith('}'):
                text = text.strip() + '}'

            # 基本验证
            json.loads(text)
            return json.loads(text)
        except:
            return None

def main():
    """主函数演示约束解码"""
    print("🔧 约束解码演示")
    print("="*50)

    # 创建约束解码系统
    system = ConstrainedDecodingSystem()

    # 定义JSON Schema
    product_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "price": {"type": "number"},
            "currency": {"type": "string", "default": "USD"},
            "category": {"type": "string"},
            "features": {"type": "array"},
            "in_stock": {"type": "boolean"}
        },
        "required": ["name", "price", "category"]
    }

    # 测试用例
    test_cases = [
        "iPhone 15 Pro Max，苹果最新旗舰，钛合金设计，售价1199美元，有库存",
        "戴森V15吸尘器，售价4990元，超强吸力，激光探测技术",
        "特斯拉Model Y，电动汽车，续航里程600公里，售价4万美元，库存紧张",
        "小米手环8，智能穿戴设备，售价299元，心率监测，防水功能"
    ]

    for i, test_input in enumerate(test_cases, 1):
        print(f"\n🧪 测试用例 {i}: {test_input}")
        print("-" * 40)

        try:
            # 生成结构化输出
            result = system.generate_structured_output(test_input, product_schema)

            if result:
                print("✅ 约束解码成功:")
                print(f"   产品: {result.get('name', 'N/A')}")
                print(f"   价格: {result.get('price', 'N/A')} {result.get('currency', 'N/A')}")
                print(f"   类别: {result.get('category', 'N/A')}")
                print(f"   特性: {', '.join(result.get('features', []))}")
                print(f"   库存: {'有' if result.get('in_stock') else '无'}")
            else:
                print("❌ 约束解码失败")

        except Exception as e:
            print(f"💥 处理异常: {str(e)}")

        if i < len(test_cases):
            print("\n" + "="*50)

if __name__ == "__main__":
    main()