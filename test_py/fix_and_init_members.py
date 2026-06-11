"""
修复和初始化团队成员数据脚本
此脚本会检查并修复 team_members 表结构，然后添加成员数据
"""
import sys
import os
import sqlite3

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal, engine
from backend.models import TeamMember, Base

def check_and_fix_table():
    """检查并修复 team_members 表结构"""
    print("=" * 60)
    print("🔧 检查 team_members 表结构")
    print("=" * 60)
    
    # 使用 SQLAlchemy 重新创建表
    try:
        print("\n📋 正在重建 team_members 表...")
        TeamMember.__table__.drop(engine, checkfirst=True)
        TeamMember.__table__.create(engine)
        print("✅ 表结构已更新")
        return True
    except Exception as e:
        print(f"❌ 表结构修复失败: {e}")
        return False

def init_team_members():
    """初始化团队成员"""
    db = SessionLocal()
    
    try:
        # 检查是否已有成员
        existing = db.query(TeamMember).count()
        if existing > 0:
            print(f"\n⚠️  数据库中已有 {existing} 个团队成员")
            print("\n现有成员：")
            members = db.query(TeamMember).all()
            for m in members:
                created = getattr(m, 'created_at', '未知')
                print(f"  - {m.name} ({m.role}) [创建于: {created}]")
            
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
        
        # 验证数据是否成功插入
        count = db.query(TeamMember).count()
        print(f"\n✅ 成功添加 {len(members)} 个团队成员")
        print(f"📊 数据库中现有成员数: {count}")
        
        print("\n团队成员列表：")
        for m in members:
            created = getattr(m, 'created_at', '刚刚')
            print(f"  ✓ {m.name} - {m.role}")
            print(f"    邮箱: {m.email}")
            print(f"    创建时间: {created}")
        
        print("\n💡 提示：你可以根据实际团队情况修改此脚本中的成员信息")
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

def verify_database():
    """验证数据库状态"""
    print("\n" + "=" * 60)
    print("🔍 验证数据库状态")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # 检查所有表
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\n📁 数据库中的表: {', '.join(tables)}")
        
        # 检查 team_members 表结构
        if 'team_members' in tables:
            columns = inspector.get_columns('team_members')
            print(f"\n📋 team_members 表结构:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']} (nullable={col['nullable']})")
            
            # 检查数据
            count = db.query(TeamMember).count()
            print(f"\n📊 team_members 表中的数据行数: {count}")
            
            if count > 0:
                print("\n👥 当前团队成员:")
                members = db.query(TeamMember).all()
                for m in members:
                    print(f"  • {m.name} ({m.role})")
        else:
            print("\n⚠️  team_members 表不存在！")
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("\n🚀 TeamRobert 团队成员初始化工具")
    print("=" * 60)
    
    # 第一步：修复表结构
    fix_success = check_and_fix_table()
    
    if fix_success:
        # 第二步：初始化数据
        print("\n" + "=" * 60)
        print("📝 开始初始化团队成员数据")
        print("=" * 60)
        init_team_members()
        
        # 第三步：验证
        verify_database()
        
        print("\n" + "=" * 60)
        print("✅ 完成！")
        print("=" * 60)
    else:
        print("\n❌ 由于表结构修复失败，无法继续初始化")
        print("请检查数据库文件权限或手动删除 teamrobert.db 后重试")
