"""检查并确保 team_notes 表存在"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import engine, Base
from sqlalchemy import inspect
from backend.models import TeamNote

def check_and_create_table():
    """检查并创建 team_notes 表"""
    print("=" * 60)
    print("🔍 检查 team_notes 表")
    print("=" * 60)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\n📋 当前数据库中的表: {tables}")
    
    if 'team_notes' in tables:
        print("\n✅ team_notes 表已存在")
        
        # 显示表结构
        columns = inspector.get_columns('team_notes')
        print("\n📊 表结构:")
        for col in columns:
            print(f"   - {col['name']}: {col['type']} (nullable={col['nullable']})")
    else:
        print("\n❌ team_notes 表不存在，正在创建...")
        
        # 只创建 TeamNote 表
        TeamNote.__table__.create(bind=engine)
        
        print("✅ team_notes 表创建成功！")
        
        # 验证
        inspector = inspect(engine)
        if 'team_notes' in inspector.get_table_names():
            print("✅ 验证通过：表已成功创建")
            
            columns = inspector.get_columns('team_notes')
            print("\n📊 表结构:")
            for col in columns:
                print(f"   - {col['name']}: {col['type']} (nullable={col['nullable']})")
        else:
            print("❌ 验证失败：表创建失败")
    
    print("\n" + "=" * 60)
    print("💡 下一步:")
    print("   1. 重启后端服务: cd backend && python main.py")
    print("   2. 测试笔记功能")
    print("=" * 60)

if __name__ == "__main__":
    check_and_create_table()
