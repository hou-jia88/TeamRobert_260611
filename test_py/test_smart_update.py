"""测试智能对话式修改功能"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal
from backend.models import Task, TeamMember
from backend.agent import TeamAgent

def test_smart_update():
    """测试智能更新功能"""
    print("=" * 60)
    print("🧪 智能对话式修改功能测试")
    print("=" * 60)
    
    agent = TeamAgent()
    db = SessionLocal()
    
    try:
        # 准备测试数据
        print("\n【准备测试数据】")
        
        # 确保有团队成员
        if db.query(TeamMember).count() == 0:
            members = [
                TeamMember(name="张三", role="前端开发"),
                TeamMember(name="李四", role="后端开发"),
                TeamMember(name="邓然", role="测试工程师"),
            ]
            for m in members:
                db.add(m)
            db.commit()
            print("   ✅ 已创建测试成员")
        
        # 创建测试任务
        test_tasks = [
            Task(title="完成API开发", assignee="张三", status="进行中", deadline="明天"),
            Task(title="修复登录bug", assignee="张三", status="待办", deadline="今天"),
            Task(title="编写测试用例", assignee="邓然", status="待办", deadline="后天"),
            Task(title="优化数据库查询", assignee="李四", status="进行中", deadline="下周"),
        ]
        for t in test_tasks:
            db.add(t)
        db.commit()
        print(f"   ✅ 已创建 {len(test_tasks)} 个测试任务")
        
        # 显示当前任务列表
        print("\n【当前任务列表】")
        tasks = db.query(Task).all()
        for t in tasks:
            print(f"   [{t.id}] {t.title} - {t.assignee} [{t.status}]")
        
        # 测试场景 1: 单任务更新（需要确认）
        print("\n" + "=" * 60)
        print("【测试场景 1】把张三的任务改成已完成")
        print("=" * 60)
        
        response = agent.handle_message("把张三的任务改成已完成", db)
        print(f"\n系统响应:\n{response['message']}\n")
        
        # 如果有多个任务，系统会让用户选择
        if response['type'] == 'clarification':
            print("💡 系统检测到多个任务，让用户选择...")
            # 模拟用户选择第一个
            response = agent.handle_message("1", db)
            print(f"\n系统响应:\n{response['message']}\n")
            
            # 系统等待确认
            if response['type'] == 'confirmation':
                print("💡 系统等待用户确认...")
                # 模拟用户确认
                response = agent.handle_message("是的", db)
                print(f"\n系统响应:\n{response['message']}\n")
        
        # 显示更新后的任务
        print("\n【更新后的任务】")
        zhangsan_tasks = db.query(Task).filter(Task.assignee == "张三").all()
        for t in zhangsan_tasks:
            print(f"   [{t.id}] {t.title} - {t.assignee} [{t.status}]")
        
        # 测试场景 2: 批量更新
        print("\n" + "=" * 60)
        print("【测试场景 2】把所有待办任务改为进行中")
        print("=" * 60)
        
        response = agent.handle_message("把所有待办任务改为进行中", db)
        print(f"\n系统响应:\n{response['message']}\n")
        
        # 如果系统要求确认
        if response['type'] == 'confirmation':
            print("💡 系统等待用户确认...")
            response = agent.handle_message("确认", db)
            print(f"\n系统响应:\n{response['message']}\n")
        
        # 显示最终状态
        print("\n【最终任务状态】")
        tasks = db.query(Task).all()
        for t in tasks:
            print(f"   [{t.id}] {t.title} - {t.assignee} [{t.status}]")
        
        print("\n" + "=" * 60)
        print("✅ 测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_smart_update()
