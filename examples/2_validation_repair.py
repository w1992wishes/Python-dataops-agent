"""
方案二：验证与修复框架
通过多层验证和自动修复机制确保输出格式正确性
"""

import os
import json
import re
from pydantic import BaseModel, Field, field_validator
from langchain_openai import ChatOpenAI
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

# 数据模型
class UserProfile(BaseModel):
    name: str = Field(description="用户姓名")
    age: int = Field(ge=0, le=150, description="用户年龄")
    email: str = Field(description="邮箱地址")
    interests: List[str] = Field(description="兴趣爱好")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError(f"邮箱格式无效: {v}")
        return v

class ValidationResult(Enum):
    """验证结果"""
    VALID = "valid"
    INVALID = "invalid"
    REPAIRED = "repaired"

class BaseValidator:
    """基础验证器"""

    def __init__(self, name: str):
        self.name = name

    def validate(self, data: Any) -> Tuple[bool, str, Any]:
        """验证数据，返回(是否有效, 错误信息, 修复后的数据)"""
        raise NotImplementedError

class JSONFormatValidator(BaseValidator):
    """JSON格式验证器"""

    def __init__(self):
        super().__init__("JSONFormatValidator")

    def validate(self, data: Any) -> Tuple[bool, str, Any]:
        try:
            if isinstance(data, str):
                # 清理JSON字符串
                cleaned = self._clean_json_string(data)
                parsed = json.loads(cleaned)
                return True, "JSON格式有效", parsed
            else:
                json.dumps(data)  # 测试序列化
                return True, "JSON格式有效", data
        except json.JSONDecodeError as e:
            return False, f"JSON格式错误: {str(e)}", None
        except Exception as e:
            return False, f"验证异常: {str(e)}", None

    def _clean_json_string(self, text: str) -> str:
        """清理JSON字符串"""
        cleaned = text.strip()

        # 移除常见前缀
        prefixes = [
            "这是您要的JSON：",
            "以下是JSON结果：",
            "```json", "```"
        ]
        for prefix in prefixes:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()

        # 移除常见后缀
        suffixes = [
            "希望对您有帮助！",
            "希望这个信息有用！"
        ]
        for suffix in suffixes:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()

        # 提取JSON部分
        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if json_match:
            return json_match.group(0)

        return cleaned

class PydanticValidator(BaseValidator):
    """Pydantic数据模型验证器"""

    def __init__(self, pydantic_model):
        super().__init__(f"PydanticValidator_{pydantic_model.__name__}")
        self.pydantic_model = pydantic_model

    def validate(self, data: Any) -> Tuple[bool, str, Any]:
        try:
            validated_obj = self.pydantic_model.model_validate(data)
            return True, "数据验证通过", validated_obj
        except Exception as e:
            return False, f"数据验证错误: {str(e)}", None

class PIIValidator(BaseValidator):
    """个人身份信息检测器"""

    def __init__(self):
        super().__init__("PIIValidator")
        self.patterns = {
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "id_number": r'\b\d{8,}\b',
            "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        }

    def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """检测PII信息"""
        detected = []
        for entity_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                detected.append({
                    "type": entity_type,
                    "value": match.group(),
                    "position": match.span()
                })
        return detected

    def mask_pii(self, text: str, mask_char: str = "*") -> str:
        """遮蔽PII信息"""
        masked_text = text
        pii_list = self.detect_pii(text)

        # 按位置倒序排列
        pii_list.sort(key=lambda x: x["position"][0], reverse=True)

        for pii in pii_list:
            start, end = pii["position"]
            masked_value = mask_char * (end - start)
            masked_text = masked_text[:start] + masked_value + masked_text[end:]

        return masked_text

    def validate(self, data: Any) -> Tuple[bool, str, Any]:
        if isinstance(data, str):
            detected_pii = self.detect_pii(data)
            if detected_pii:
                masked_data = self.mask_pii(data)
                return False, f"检测到PII信息: {[p['type'] for p in detected_pii]}", masked_data
        return True, "未检测到PII信息", data

class BaseRepairer:
    """基础修复器"""

    def __init__(self, name: str):
        self.name = name

    def repair(self, data: Any, error_message: str) -> Optional[Any]:
        """修复数据"""
        raise NotImplementedError

class JSONRepairer(BaseRepairer):
    """JSON格式修复器"""

    def __init__(self):
        super().__init__("JSONRepairer")

    def repair(self, data: str, error_message: str) -> Optional[str]:
        try:
            if not isinstance(data, str):
                return None

            repaired = data.strip()

            # 1. 提取JSON部分
            json_match = re.search(r'\{.*\}', repaired, re.DOTALL)
            if json_match:
                repaired = json_match.group(0)

            # 2. 修复引号问题
            repaired = self._fix_quotes(repaired)

            # 3. 修复括号匹配
            repaired = self._fix_brackets(repaired)

            # 4. 修复尾随逗号
            repaired = re.sub(r',\s*}', '}', repaired)
            repaired = re.sub(r',\s*\]', ']', repaired)

            # 验证修复后的JSON
            json.loads(repaired)
            return repaired

        except Exception:
            return None

    def _fix_quotes(self, text: str) -> str:
        """修复引号问题"""
        return re.sub(r"'(.*?)':", r'"\1":', text)

    def _fix_brackets(self, text: str) -> str:
        """修复括号匹配"""
        open_count = text.count('{')
        close_count = text.count('}')

        while open_count > close_count:
            text += '}'
            close_count += 1

        return text

class DefaultValueRepairer(BaseRepairer):
    """默认值修复器"""

    def __init__(self, defaults: Dict[str, Any]):
        super().__init__("DefaultValueRepairer")
        self.defaults = defaults

    def repair(self, data: Dict[str, Any], error_message: str) -> Optional[Dict[str, Any]]:
        if not isinstance(data, dict):
            return None

        repaired = data.copy()
        for key, default_value in self.defaults.items():
            if key not in repaired or repaired[key] is None:
                repaired[key] = default_value

        return repaired

class ValidationGuard:
    """验证与修复守卫"""

    def __init__(self):
        self.validators: List[BaseValidator] = []
        self.repairers: List[BaseRepairer] = []
        self.llm = ChatOpenAI(
            api_key=os.getenv("SILICONFLOW_API_KEY"),
            model="deepseek-ai/DeepSeek-V3.1",
            base_url="https://api.siliconflow.cn/v1/",
            temperature=0.1
        )

    def use_validator(self, validator: BaseValidator):
        """添加验证器"""
        self.validators.append(validator)
        return self

    def use_repairer(self, repairer: BaseRepairer):
        """添加修复器"""
        self.repairers.append(repairer)
        return self

    def validate(self, data: Any) -> Tuple[ValidationResult, Any, str]:
        """验证数据"""
        current_data = data

        # 第一轮验证
        for validator in self.validators:
            is_valid, error_msg, fixed_data = validator.validate(current_data)

            if not is_valid:
                # 尝试修复
                repaired_data = self._attempt_repair(current_data, error_msg)
                if repaired_data is not None:
                    # 重新验证修复后的数据
                    is_valid_after_repair, _, validated_data = self._run_validators(repaired_data)
                    if is_valid_after_repair:
                        return ValidationResult.REPAIRED, validated_data, error_msg

                return ValidationResult.INVALID, current_data, error_msg

            if fixed_data is not None:
                current_data = fixed_data

        return ValidationResult.VALID, current_data, ""

    def _attempt_repair(self, data: Any, error_msg: str) -> Any:
        """尝试修复数据"""
        current_data = data

        for repairer in self.repairers:
            try:
                repaired = repairer.repair(current_data, error_msg)
                if repaired is not None:
                    current_data = repaired
            except Exception:
                continue

        return current_data

    def _run_validators(self, data: Any) -> Tuple[bool, str, Any]:
        """运行所有验证器"""
        current_data = data

        for validator in self.validators:
            is_valid, error_msg, fixed_data = validator.validate(current_data)
            if not is_valid:
                return False, f"{validator.name}: {error_msg}", current_data
            if fixed_data is not None:
                current_data = fixed_data

        return True, "", current_data

    def validate_with_llm_fallback(self, text: str, schema: Dict[str, Any]) -> Tuple[ValidationResult, Any, str]:
        """带LLM备选的验证"""
        # 首先尝试JSON验证
        try:
            parsed_data = json.loads(text)
        except json.JSONDecodeError:
            # JSON解析失败，使用LLM修复
            return self._llm_repair(text, schema)

        # 然后运行其他验证器
        return self.validate(parsed_data)

    def _llm_repair(self, text: str, schema: Dict[str, Any]) -> Tuple[ValidationResult, Any, str]:
        """使用LLM修复JSON"""
        try:
            repair_prompt = f"""
请修复以下文本，使其成为有效的JSON格式，符合指定的Schema：

原始文本：{text}

JSON Schema要求：
{json.dumps(schema, indent=2, ensure_ascii=False)}

请只输出修复后的JSON，不要添加任何解释。
"""

            response = self.llm.invoke(repair_prompt)
            repaired_json = response.content.strip()

            # 解析修复后的JSON
            parsed_data = json.loads(repaired_json)
            return ValidationResult.REPAIRED, parsed_data, ""

        except Exception as e:
            return ValidationResult.INVALID, None, f"LLM修复失败: {str(e)}"

def main():
    """主函数演示验证与修复框架"""
    print("🛡️ 验证与修复框架演示")
    print("="*50)

    # 创建验证守卫
    guard = ValidationGuard()
    guard.use_validator(JSONFormatValidator())
    guard.use_validator(PydanticValidator(UserProfile))
    guard.use_validator(PIIValidator())

    guard.use_repairer(JSONRepairer())
    guard.use_repairer(DefaultValueRepairer({
        "name": "未知用户",
        "age": 0,
        "email": "unknown@example.com",
        "interests": []
    }))

    # 测试用例
    test_cases = [
        # 有效的JSON
        '{"name": "张三", "age": 30, "email": "zhangsan@example.com", "interests": ["编程", "阅读"]}',

        # 格式错误的JSON
        "这是您要的用户信息：{'name': '李四', 'age': 25, 'email': 'lisi@example.com'} 希望对您有帮助！",

        # 包含PII信息的JSON
        '{"name": "王五", "age": 28, "email": "wangwu@example.com", "phone": "138-1234-5678", "id": "123456789012345678"}',

        # 缺少字段的JSON
        '{"name": "赵六"}',

        # 完全错误的文本
        "用户信息：姓名=钱七，年龄未知，邮箱=qianqi@email.com"
    ]

    user_info_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string"},
            "interests": {"type": "array"}
        }
    }

    for i, test_input in enumerate(test_cases, 1):
        print(f"\n🧪 测试用例 {i}")
        print(f"输入: {test_input}")
        print("-" * 40)

        try:
            # 带LLM备选的验证
            result, validated_data, error_msg = guard.validate_with_llm_fallback(test_input, user_info_schema)

            if result == ValidationResult.VALID:
                print("✅ 验证通过 (原生有效)")
                if isinstance(validated_data, dict):
                    print(f"   姓名: {validated_data.get('name', 'N/A')}")
                    print(f"   年龄: {validated_data.get('age', 'N/A')}")
                    print(f"   邮箱: {validated_data.get('email', 'N/A')}")
                    print(f"   兴趣: {validated_data.get('interests', [])}")

            elif result == ValidationResult.REPAIRED:
                print("✅ 验证通过 (已修复)")
                print(f"   修复说明: {error_msg}")
                if isinstance(validated_data, dict):
                    print(f"   姓名: {validated_data.get('name', 'N/A')}")
                    print(f"   年龄: {validated_data.get('age', 'N/A')}")
                    print(f"   邮箱: {validated_data.get('email', 'N/A')}")
                    print(f"   兴趣: {validated_data.get('interests', [])}")

            else:
                print("❌ 验证失败")
                print(f"   错误: {error_msg}")

        except Exception as e:
            print(f"💥 处理异常: {str(e)}")

        if i < len(test_cases):
            print("\n" + "="*50)

if __name__ == "__main__":
    main()