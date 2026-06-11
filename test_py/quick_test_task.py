"""快速测试任务创建流程 - 简化版"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal
from backend.models import Task, TeamMember
from backend.agent import TeamAgent

def quick_test():
    """快速测试"""
    print("🚀 开始快速测试...\n")
    
    agent = TeamAgent()
    db = SessionLocal()
    
    try:
        # 1. 检查团队成员
        members = db.query(TeamMember).all()
        print(f"👥 团队成员数量: {len(members)}")
        if members:
            for m in members:
                print(f"   - {m.name}")
        else:
            print("   ⚠️  没有团队成员，请先运行 init_team_members.py")
        
        # 2. 测试几个典型输入
        test_cases = [
            "创建任务：完成API开发，分配给张三",
            "帮我创建一个新任务",
            "添加一个文档审查任务给李四，截止明天"
        ]
        
        print("\n" + "="*60)
        print("测试用例")
        print("="*60)
        
        for i, msg in enumerate(test_cases, 1):
            print(f"\n【测试 {i}】{msg}")
            print("-" * 60)
            
            # 提取意图
            intent_result = agent.llm.extract_intent(msg)
            print(f"意图: {intent_result.get('intent')}")
            print(f"实体: {intent_result.get('entities')}")
            
            # 如果是创建任务，执行创建
            if intent_result.get('intent') == 'create_task':
                entities = intent_result.get('entities', {})
                result = agent._create_task_llm(entities, db)
                
                print(f"\n结果类型: {result.get('type')}")
                print(f"消息预览: {result.get('message', '')[:150]}")
                
                if result.get('type') == 'task_created':
                    print("✅ 成功")
                elif result.get('type') == 'error':
                    print("❌ 失败")
        
        # 3. 查看最终结果
        print("\n" + "="*60)
        print("最终任务列表")
        print("="*60)
        
        tasks = db.query(Task).order_by(Task.id.desc()).limit(10).all()
        print(f"\n总任务数: {db.query(Task).count()}")
        
        if tasks:
            print("\n最近创建的任务:")
            for t in tasks:
                print(f"  [{t.id}] {t.title} | 负责人:{t.assignee} | 状态:{t.status}")
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)

if __name__ == "__main__":
    quick_test()
