"""
初始化团队成员数据脚本
运行此脚本向数据库添加团队成员信息，让大模型更好地了解团队结构
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal
from backend.models import TeamMember

def init_team_members():
    """初始化团队成员"""
    db = SessionLocal()
    
    try:
        # 检查是否已有成员
        existing = db.query(TeamMember).count()
        if existing > 0:
            print(f"⚠️  数据库中已有 {existing} 个团队成员")
            print("\n现有成员：")
            members = db.query(TeamMember).all()
            for m in members:
                print(f"  - {m.name} ({m.role})")
            
            response = input("\n是否要清空并重新初始化？(y/n): ")
            if response.lower() != 'y':
                print("已取消操作")
                return
            
            # 清空现有数据
            db.query(TeamMember).delete()
            db.commit()
            print("✅ 已清空现有成员数据")
        
        # 添加示例团队成员（根据实际情况修改）
        members = [
            TeamMember(name="张三", role="前端开发工程师", email="zhangsan@team.com"),
            TeamMember(name="李四", role="后端开发工程师", email="lisi@team.com"),
            TeamMember(name="王五", role="产品经理", email="wangwu@team.com"),
            TeamMember(name="赵六", role="UI设计师", email="zhaoliu@team.com"),
            TeamMember(name="小明", role="测试工程师", email="xiaoming@team.com"),
        ]
        
        db.add_all(members)
        db.commit()
        
        print(f"\n✅ 成功添加 {len(members)} 个团队成员")
        for m in members:
            print(f"  - {m.name} ({m.role})")
        
        print("\n💡 提示：你可以根据实际团队情况修改此脚本中的成员信息")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_team_members()
