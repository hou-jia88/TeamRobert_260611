"""测试任务创建流程"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal
from backend.models import Task, TeamMember
from backend.agent import TeamAgent
from backend.llm_client import DeepSeekClient

def test_task_creation_flow():
    """测试完整的任务创建流程"""
    print("=" * 60)
    print("任务创建流程测试")
    print("=" * 60)
    
    # 1. 初始化
    agent = TeamAgent()
    db = SessionLocal()
    
    try:
        # 2. 检查团队成员
        print("\n👥 当前团队成员:")
        members = db.query(TeamMember).all()
        if not members:
            print("   ⚠️  警告: 数据库中没有团队成员!")
            print("   请先运行: python init_team_members.py")
        else:
            for m in members:
                print(f"   - {m.name} ({m.role})")
        
        # 3. 测试意图提取
        test_messages = [
            "创建任务：完成需求文档，分配给张三，截止：下周五",
            "帮我安排一个代码审查任务给李四",
            "创建一个新任务"
        ]
        
        print("\n🧪 测试意图提取:")
        for msg in test_messages:
            print(f"\n用户输入: {msg}")
            intent_result = agent.llm.extract_intent(msg)
            print(f"  意图: {intent_result.get('intent')}")
            print(f"  实体: {intent_result.get('entities')}")
            
            # 4. 如果意图是创建任务，尝试创建
            if intent_result.get('intent') == 'create_task':
                entities = intent_result.get('entities', {})
                print(f"\n  📝 准备创建任务:")
                print(f"     标题: {entities.get('title')}")
                print(f"     负责人: {entities.get('assignee')}")
                print(f"     截止时间: {entities.get('deadline')}")
                
                # 验证负责人
                assignee = entities.get('assignee', '未分配')
                if assignee and assignee != '未分配':
                    member = db.query(TeamMember).filter(TeamMember.name == assignee).first()
                    if member:
                        print(f"     ✅ 负责人 '{assignee}' 存在于团队中")
                    else:
                        print(f"     ❌ 负责人 '{assignee}' 不在团队中")
                
                # 尝试创建任务
                print(f"\n  🔨 执行任务创建...")
                result = agent._create_task_llm(entities, db)
                print(f"  结果类型: {result.get('type')}")
                print(f"  消息: {result.get('message', '')[:100]}")
                
                if result.get('type') == 'task_created':
                    print(f"  ✅ 任务创建成功!")
                    task_data = result.get('data', {})
                    print(f"     任务ID: {task_data.get('id')}")
                elif result.get('type') == 'error':
                    print(f"  ❌ 任务创建失败")
                    print(f"     错误: {result.get('message')}")
        
        # 5. 检查最终的任务列表
        print("\n📊 最终任务统计:")
        tasks = db.query(Task).all()
        print(f"   总任务数: {len(tasks)}")
        if tasks:
            print("\n   最近创建的任务:")
            for t in tasks[-5:]:
                print(f"   - ID:{t.id} | {t.title} | {t.assignee} | {t.status}")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_task_creation_flow()
