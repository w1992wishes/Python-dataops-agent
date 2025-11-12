"""
测试更新后的ETL API接口
"""
import asyncio
import json
import requests

async def test_etl_api():
    """测试ETL API接口"""
    base_url = "http://localhost:8000"

    print("🚀 开始测试ETL API接口")
    print("=" * 60)

    # 测试用例1: 修改现有ETL代码
    print("\n📊 测试用例1: 修改现有ETL代码")
    request_data1 = {
        "user_input": "用户表新增了user_age字段，请修改ETL代码，添加年龄字段的数据处理",
        "table_name": "user_table"
    }

    try:
        response1 = requests.post(f"{base_url}/api/etl", json=request_data1)
        print(f"状态码: {response1.status_code}")
        if response1.status_code == 200:
            result = response1.json()
            print("响应成功:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"请求失败: {response1.text}")
    except Exception as e:
        print(f"请求异常: {e}")

    # 测试用例2: 创建新ETL代码
    print("\n📊 测试用例2: 创建新ETL代码")
    request_data2 = {
        "user_input": "创建新表的ETL代码，需要加载用户数据并进行统计",
        "table_name": "new_table"
    }

    try:
        response2 = requests.post(f"{base_url}/api/etl", json=request_data2)
        print(f"状态码: {response2.status_code}")
        if response2.status_code == 200:
            result = response2.json()
            print("响应成功:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"请求失败: {response2.text}")
    except Exception as e:
        print(f"请求异常: {e}")

    # 测试用例3: 优化ETL代码
    print("\n📊 测试用例3: 优化ETL代码")
    request_data3 = {
        "user_input": "优化ETL代码，提升数据处理性能，添加更多统计指标",
        "table_name": "policy_renewal"
    }

    try:
        response3 = requests.post(f"{base_url}/api/etl", json=request_data3)
        print(f"状态码: {response3.status_code}")
        if response3.status_code == 200:
            result = response3.json()
            print("响应成功:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"请求失败: {response3.text}")
    except Exception as e:
        print(f"请求异常: {e}")

    print("\n" + "=" * 60)
    print("✅ API测试完成")


def test_api_format():
    """测试API请求格式"""
    print("\n🔗 测试API请求格式")
    print("=" * 40)

    # 展示请求格式
    request_example = {
        "user_input": "用户表新增了user_age字段，请修改ETL代码，添加年龄字段的数据处理",
        "table_name": "user_table"
    }

    print("API请求格式:")
    print("POST /api/etl")
    print("Content-Type: application/json")
    print("")
    print(json.dumps(request_example, ensure_ascii=False, indent=2))

    # 展示预期响应格式
    response_example = {
        "success": True,
        "data": {
            "operation_type": "update",
            "status": "success",
            "message": "ETL代码已根据DDL变更成功修改",
            "table_name": "user_table",
            "etl_code": "INSERT INTO user_table SELECT user_id, user_name, user_age FROM source_table WHERE create_time >= '${bizdate}'",
            "changes_summary": [
                "在SELECT语句中添加了user_age字段",
                "保持了原有的数据加载逻辑"
            ],
            "ddl_changes": [
                {
                    "change_type": "add_column",
                    "column_name": "user_age",
                    "old_value": None,
                    "new_value": "int",
                    "description": "新增用户年龄字段"
                }
            ],
            "execution_time": 15.2,
            "llm_tokens_used": 1250
        },
        "operation_type": "update",
        "timestamp": "2025-01-01T12:00:00Z"
    }

    print("\n预期响应格式:")
    print(json.dumps(response_example, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    # test_etl_api()  # 取消注释以运行实际API测试
    test_api_format()