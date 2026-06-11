"""
快速测试任务创建功能
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal
from backend.agent import TeamAgent

def test_basic_task_creation():
    """测试基本任务创建"""
    print("=" * 70)
    print("🧪 测试基本任务创建功能")
    print("=" * 70)
    
    agent = TeamAgent()
    db = SessionLocal()
    
    test_cases = [
        "创建任务：测试任务1",
        "创建任务：测试任务2，分配给张三",
        "查看任务",
    ]
    
    for i, message in enumerate(test_cases, 1):
        print(f"\n【测试{i}】{message}")
        try:
            response = agent.handle_message(message, db)
            print(f"✅ 响应类型: {response['type']}")
            print(f"📝 回复: {response['message'][:100]}...")
        except Exception as e:
            print(f"❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()
    
    db.close()
    print("\n" + "=" * 70)
    print("✅ 测试完成")
    print("=" * 70)

if __name__ == "__main__":
    test_basic_task_creation()
