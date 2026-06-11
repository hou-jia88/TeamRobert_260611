"""
测试日志记录功能
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal
from backend.agent import TeamAgent

def test_logging():
    """测试日志记录"""
    print("=" * 70)
    print("🧪 测试对话日志功能")
    print("=" * 70)
    
    agent = TeamAgent()
    db = SessionLocal()
    
    try:
        test_messages = [
            "你好",
            "查看团队进度",
            "创建任务：写需求文档，分配给张三",
            "查看所有任务",
        ]
        
        print("\n发送测试消息:\n")
        for i, message in enumerate(test_messages, 1):
            print(f"[{i}] 用户: {message}")
            response = agent.handle_message(message, db)
            
            if response and 'message' in response:
                reply = response['message']
                preview = reply[:50] + '...' if len(reply) > 50 else reply
                print(f"    助手: {preview}\n")
        
        print("=" * 70)
        print("✅ 测试完成！")
        print("=" * 70)
        
        print("\n📝 查看日志:")
        print("   python view_logs.py -v 10")
        print("\n📊 查看统计:")
        print("   python view_logs.py -t")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_logging()
