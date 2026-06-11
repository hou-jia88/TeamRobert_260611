"""
DeepSeek API 集成测试脚本
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.llm_client import DeepSeekClient
from backend.config import DEEPSEEK_API_KEY

def test_api_connection():
    """测试 API 连接"""
    print("=" * 50)
    print("🧪 DeepSeek API 连接测试")
    print("=" * 50)
    
    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "sk-your-actual-api-key-here":
        print("❌ 错误: 请先在 .env 文件中配置您的 DeepSeek API Key")
        print("\n获取 API Key 的步骤：")
        print("1. 访问 https://platform.deepseek.com")
        print("2. 注册/登录账号")
        print("3. 在 API Keys 页面创建新的密钥")
        print("4. 将密钥复制到 .env 文件中的 DEEPSEEK_API_KEY")
        return False
    
    print(f"✅ API Key 已配置: {DEEPSEEK_API_KEY[:8]}...")
    
    client = DeepSeekClient()
    
    # 测试简单对话
    print("\n📤 发送测试请求...")
    try:
        messages = [
            {"role": "system", "content": "你是一个助手"},
            {"role": "user", "content": "你好"}
        ]
        response = client.chat_completion(messages)
        
        if response:
            print(f"✅ API 调用成功！")
            print(f"💬 回复: {response}")
            return True
        else:
            print("❌ API 返回为空，请检查 API Key 是否正确")
            return False
    except Exception as e:
        print(f"❌ API 调用失败: {str(e)}")
        return False

def test_intent_extraction():
    """测试意图提取功能"""
    print("\n" + "=" * 50)
    print("🧠 意图提取测试")
    print("=" * 50)
    
    client = DeepSeekClient()
    
    test_cases = [
        "给张三安排一个写文档的任务，下周五截止",
        "明天下午3点开个会讨论项目进度",
        "查看所有任务的完成情况",
        "上传需求规格说明书"
    ]
    
    for i, message in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {message}")
        result = client.extract_intent(message)
        print(f"  意图: {result.get('intent')}")
        print(f"  实体: {result.get('entities')}")

def test_task_decomposition():
    """测试任务分解功能"""
    print("\n" + "=" * 50)
    print("🔧 任务分解测试")
    print("=" * 50)
    
    client = DeepSeekClient()
    
    task = "开发一个用户登录系统"
    print(f"\n任务: {task}")
    
    subtasks = client.decompose_task(task)
    
    if subtasks:
        print(f"\n✅ 分解为 {len(subtasks)} 个子任务:")
        for i, st in enumerate(subtasks, 1):
            print(f"{i}. {st['title']}")
            if 'description' in st:
                print(f"   {st['description']}")
    else:
        print("❌ 任务分解失败")

if __name__ == "__main__":
    print("\n🚀 开始 DeepSeek API 集成测试\n")
    
    # 测试1: API 连接
    if test_api_connection():
        # 测试2: 意图提取
        test_intent_extraction()
        
        # 测试3: 任务分解
        test_task_decomposition()
        
        print("\n" + "=" * 50)
        print("✅ 所有测试完成！")
        print("=" * 50)
    else:
        print("\n⚠️  请先配置 API Key 后再运行测试")
