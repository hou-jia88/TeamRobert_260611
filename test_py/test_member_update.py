"""测试成员字段更新功能"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal
from backend.models import TeamMember
from backend.agent import TeamAgent

def test_member_update():
    """测试成员字段更新"""
    print("=" * 60)
    print("🧪 测试成员字段更新功能")
    print("=" * 60)
    
    agent = TeamAgent()
    db = SessionLocal()
    
    try:
        # 准备测试数据
        print("\n【准备测试数据】")
        
        # 检查是否有邓然
        deng_ran = db.query(TeamMember).filter(TeamMember.name == "邓然").first()
        if not deng_ran:
            deng_ran = TeamMember(name="邓然", role="测试工程师", email="dengran@old.com")
            db.add(deng_ran)
            db.commit()
            print("   ✅ 已创建邓然")
        else:
            print(f"   ✅ 邓然已存在: {deng_ran.role}, {deng_ran.email}")
        
        # 显示当前信息
        print(f"\n【当前信息】")
        print(f"   姓名: {deng_ran.name}")
        print(f"   角色: {deng_ran.role}")
        print(f"   邮箱: {deng_ran.email}")
        
        # 测试场景 1: 更新邮箱
        print("\n" + "=" * 60)
        print("【测试场景 1】把邓然的邮箱改成 dengran@example.com")
        print("=" * 60)
        
        response = agent.handle_message("把邓然的邮箱改成 dengran@example.com", db)
        print(f"\n系统响应:\n{response['message']}\n")
        
        # 如果需要确认
        if response['type'] in ['confirmation', 'clarification']:
            print("💡 系统等待用户确认...")
            response = agent.handle_message("是的", db)
            print(f"\n系统响应:\n{response['message']}\n")
        
        # 显示更新后的信息
        db.refresh(deng_ran)
        print(f"\n【更新后的信息】")
        print(f"   姓名: {deng_ran.name}")
        print(f"   角色: {deng_ran.role}")
        print(f"   邮箱: {deng_ran.email}")
        
        # 测试场景 2: 更新角色
        print("\n" + "=" * 60)
        print("【测试场景 2】把邓然的角色改为高级测试工程师")
        print("=" * 60)
        
        response = agent.handle_message("把邓然的角色改为高级测试工程师", db)
        print(f"\n系统响应:\n{response['message']}\n")
        
        # 如果需要确认
        if response['type'] in ['confirmation', 'clarification']:
            print("💡 系统等待用户确认...")
            response = agent.handle_message("确认", db)
            print(f"\n系统响应:\n{response['message']}\n")
        
        # 显示最终信息
        db.refresh(deng_ran)
        print(f"\n【最终信息】")
        print(f"   姓名: {deng_ran.name}")
        print(f"   角色: {deng_ran.role}")
        print(f"   邮箱: {deng_ran.email}")
        
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
    test_member_update()
