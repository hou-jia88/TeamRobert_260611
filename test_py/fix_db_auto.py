"""一键修复数据库 - 自动重建并初始化"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import engine, Base, SessionLocal
from sqlalchemy import inspect
from backend.models import Task, Meeting, Document, TeamMember

def fix_database_auto():
    """自动修复数据库（无需确认）"""
    print("=" * 60)
    print("🔧 数据库自动修复工具")
    print("=" * 60)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\n📋 当前数据库中的表: {tables}")
    print("\n⚠️  即将删除所有现有数据并重建表结构...")
    
    # 删除旧表并重建
    print("\n🗑️  删除旧表...")
    Base.metadata.drop_all(bind=engine)
    
    print("🔨 创建新表...")
    Base.metadata.create_all(bind=engine)
    
    # 验证新表结构
    print("\n✅ 新表结构验证:")
    inspector = inspect(engine)
    all_ok = True
    
    for table_name in ['tasks', 'meetings', 'documents', 'team_members']:
        if table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            col_names = [col['name'] for col in columns]
            print(f"   ✅ {table_name}: {len(columns)} 个字段 - {', '.join(col_names)}")
        else:
            print(f"   ❌ {table_name} 表创建失败!")
            all_ok = False
    
    if not all_ok:
        print("\n❌ 数据库修复失败!")
        return False
    
    print("\n" + "=" * 60)
    print("✅ 数据库重建成功!")
    print("=" * 60)
    
    # 自动初始化团队成员
    print("\n👥 正在初始化团队成员...")
    init_team_members()
    
    return True

def init_team_members():
    """初始化默认团队成员"""
    db = SessionLocal()
    try:
        # 检查是否已有成员
        existing = db.query(TeamMember).count()
        if existing > 0:
            print(f"   ℹ️  已有 {existing} 个团队成员，跳过初始化")
            return
        
        # 添加默认团队成员
        default_members = [
            TeamMember(name="张三", role="前端开发", email="zhangsan@team.com"),
            TeamMember(name="李四", role="后端开发", email="lisi@team.com"),
            TeamMember(name="王五", role="产品经理", email="wangwu@team.com"),
            TeamMember(name="赵六", role="UI设计师", email="zhaoliu@team.com"),
            TeamMember(name="邓然", role="测试工程师", email="dengran@team.com"),
        ]
        
        for member in default_members:
            db.add(member)
        
        db.commit()
        print(f"   ✅ 已添加 {len(default_members)} 个默认团队成员")
        
        # 显示成员列表
        members = db.query(TeamMember).all()
        print("\n   团队成员列表:")
        for m in members:
            print(f"      - {m.name} ({m.role})")
            
    except Exception as e:
        print(f"   ❌ 初始化失败: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    success = fix_database_auto()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 全部完成！现在可以测试任务创建了")
        print("=" * 60)
        print("\n💡 下一步:")
        print("   python quick_test_task.py  # 测试任务创建")
        print("   python view_logs.py        # 查看日志")
    else:
        print("\n❌ 修复失败，请检查错误信息")
