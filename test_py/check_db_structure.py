"""快速检查数据库表结构"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import engine
from sqlalchemy import inspect

def check_tables():
    inspector = inspect(engine)
    
    print("=" * 60)
    print("数据库表结构检查")
    print("=" * 60)
    
    tables = inspector.get_table_names()
    print(f"\n📋 数据库中的表: {tables}\n")
    
    for table_name in ['tasks', 'meetings', 'documents', 'team_members']:
        if table_name in tables:
            print(f"📊 {table_name} 表的列:")
            columns = inspector.get_columns(table_name)
            for col in columns:
                print(f"   - {col['name']}: {col['type']} (nullable={col['nullable']})")
            print()
        else:
            print(f"❌ {table_name} 表不存在\n")

if __name__ == "__main__":
    check_tables()
