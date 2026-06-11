"""
测试任务创建的验证逻辑
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal
from backend.agent import TeamAgent

def test_task_validation():
    """测试任务创建验证"""
    print("=" * 70)
    print("🧪 测试任务创建验证逻辑")
    print("=" * 70)
    
    agent = TeamAgent()
    db = SessionLocal()
    
    test_cases = [
        {
            "name": "测试1：正常的任务创建",
            "message": "创建任务：写需求文档，分配给张三，截止：下周五",
            "expected": "success"
        },
        {
            "name": "测试2：负责人不在团队中",
            "message": "创建任务：测试任务，分配给不存在的人",
            "expected": "warning"
        },
        {
            "name": "测试3：缺少任务标题",
            "message": "创建任务，分配给张三",
            "expected": "error"
        },
        {
            "name": "测试4：完整信息",
            "message": "创建任务：前端页面开发，分配给李四，截止：2026-06-05",
            "expected": "success"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{test_case['name']}")
        print(f"用户输入: {test_case['message']}")
        
        try:
            response = agent.handle_message(test_case['message'], db)
            
            if response['type'] == 'error':
                print(f"❌ 结果: 创建失败")
                print(f"   错误信息: {response['message'][:200]}")
            elif response['type'] == 'task_created':
                print(f"✅ 结果: 创建成功")
                print(f"   回复: {response['message'][:200]}...")
            else:
                print(f"⚠️  结果: {response['type']}")
                print(f"   回复: {response.get('message', '')[:200]}")
                
        except Exception as e:
            print(f"❌ 异常: {str(e)}")
            import traceback
            traceback.print_exc()
    
    db.close()
    
    print("\n" + "=" * 70)
    print("✅ 测试完成！")
    print("=" * 70)
    print("\n💡 提示：")
    print("   - 如果负责人不在团队中，会显示警告但依然创建任务")
    print("   - 如果缺少必要信息（如标题），会拒绝创建并提示用户")
    print("   - 所有错误都会明确告知用户问题所在")

if __name__ == "__main__":
    test_task_validation()
