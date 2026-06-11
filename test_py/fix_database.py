"""修复数据库表结构并重新初始化"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import engine, Base
from sqlalchemy import inspect
from backend.models import Task, Meeting, Document, TeamMember

def fix_database():
    """修复数据库表结构"""
    print("=" * 60)
    print("数据库修复工具")
    print("=" * 60)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\n📋 当前数据库中的表: {tables}")
    
    # 删除旧表并重建
    print("\n⚠️  警告: 这将删除所有现有数据!")
    response = input("是否继续? (yes/no): ")
    
    if response.lower() != 'yes':
        print("操作已取消")
        return
    
    print("\n🗑️  删除旧表...")
    Base.metadata.drop_all(bind=engine)
    
    print("🔨 创建新表...")
    Base.metadata.create_all(bind=engine)
    
    # 验证新表结构
    print("\n✅ 新表结构:")
    inspector = inspect(engine)
    for table_name in ['tasks', 'meetings', 'documents', 'team_members']:
        if table_name in inspector.get_table_names():
            print(f"\n📊 {table_name} 表:")
            columns = inspector.get_columns(table_name)
            for col in columns:
                print(f"   - {col['name']}: {col['type']}")
        else:
            print(f"\n❌ {table_name} 表创建失败!")
    
    print("\n" + "=" * 60)
    print("✅ 数据库修复完成!")
    print("💡 请运行 init_team_members.py 初始化团队成员")
    print("=" * 60)

if __name__ == "__main__":
    fix_database()
