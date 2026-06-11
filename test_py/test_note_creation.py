"""测试智能体识别自然语言添加笔记功能"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal, engine, Base
from backend.agent import TeamAgent
from backend.llm_client import DeepSeekClient
from backend.models import TeamNote

def test_create_note():
    """测试通过自然语言创建笔记"""
    
    print("=" * 60)
    print("📝 测试智能体添加笔记功能")
    print("=" * 60)
    print()
    
    # 初始化数据库
    Base.metadata.create_all(bind=engine)
    
    # 创建agent实例
    agent = TeamAgent()
    db = SessionLocal()
    
    try:
        # 测试场景1: 标准格式（带作者）
        print("【测试 1】标准格式：我是张三，添加笔记")
        print("-" * 60)
        message1 = "我是张三，添加笔记：今天完成了需求评审会议，讨论了产品架构"
        print(f"用户输入: {message1}")
        
        response1 = agent.handle_message(message1, db)
        print(f"响应类型: {response1.get('type')}")
        print(f"响应消息:\n{response1.get('message', '无消息')}")
        print()
        
        # 测试场景2: 口语化表达（带作者）
        print("【测试 2】口语化表达：我是李四，帮我记一下")
        print("-" * 60)
        message2 = "我是李四，帮我记一下：下周要进行产品演示"
        print(f"用户输入: {message2}")
        
        response2 = agent.handle_message(message2, db)
        print(f"响应类型: {response2.get('type')}")
        print(f"响应消息:\n{response2.get('message', '无消息')}")
        print()
        
        # 测试场景3: 没有提供作者（应该失败）
        print("【测试 3】未提供作者姓名（应该失败）")
        print("-" * 60)
        message3 = "添加笔记：服务器需要在本周五前升级"
        print(f"用户输入: {message3}")
        
        response3 = agent.handle_message(message3, db)
        print(f"响应类型: {response3.get('type')}")
        print(f"响应消息:\n{response3.get('message', '无消息')}")
        print()
        
        # 显示所有笔记
        print("=" * 60)
        print("📋 当前数据库中的所有笔记:")
        print("=" * 60)
        
        notes = db.query(TeamNote).order_by(TeamNote.id.desc()).all()
        
        if not notes:
            print("❌ 暂无笔记")
        else:
            for i, note in enumerate(notes, 1):
                print(f"\n[{i}] ID: {note.id}")
                print(f"    作者: {note.author}")
                print(f"    内容: {note.content}")
                print(f"    时间: {note.created_at}")
        
        print()
        print("=" * 60)
        print("✅ 测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_create_note()
