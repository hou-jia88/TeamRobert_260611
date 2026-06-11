"""强制修复所有数据库文件"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import engine, Base, SessionLocal
from sqlalchemy import inspect
from backend.models import Task, Meeting, Document, TeamMember
import shutil

def force_rebuild_all_databases():
    """强制重建所有数据库文件"""
    print("=" * 60)
    print("🔧 强制修复所有数据库")
    print("=" * 60)
    
    # 找到所有数据库文件
    db_files = []
    root_db = os.path.join(os.path.dirname(__file__), 'teamrobert.db')
    backend_db = os.path.join(os.path.dirname(__file__), 'backend', 'teamrobert.db')
    
    if os.path.exists(root_db):
        db_files.append(('根目录', root_db))
    if os.path.exists(backend_db):
        db_files.append(('backend目录', backend_db))
    
    print(f"\n📋 找到的数据库文件:")
    for name, path in db_files:
        size = os.path.getsize(path)
        print(f"   - {name}: {path} ({size} bytes)")
    
    # 删除所有数据库文件
    print("\n🗑️  删除所有数据库文件...")
    for name, path in db_files:
        try:
            os.remove(path)
            print(f"   ✅ 已删除: {name}")
        except Exception as e:
            print(f"   ❌ 删除失败 {name}: {e}")
    
    # 重新创建数据库
    print("\n🔨 重新创建数据库表结构...")
    Base.metadata.create_all(bind=engine)
    
    # 验证
    print("\n✅ 验证新表结构:")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"   表列表: {tables}\n")
    
    for table_name in ['tasks', 'meetings', 'documents', 'team_members']:
        if table_name in tables:
            columns = inspector.get_columns(table_name)
            col_names = [col['name'] for col in columns]
            print(f"   ✅ {table_name}: {len(columns)} 个字段")
            if 'created_at' not in col_names:
                print(f"      ⚠️  警告: 缺少 created_at 字段!")
            else:
                print(f"      ✓ created_at 字段存在")
        else:
            print(f"   ❌ {table_name} 表不存在!")
    
    # 初始化团队成员
    print("\n👥 初始化团队成员...")
    init_team_members()
    
    print("\n" + "=" * 60)
    print("🎉 数据库修复完成!")
    print("=" * 60)

def init_team_members():
    """初始化默认团队成员"""
    db = SessionLocal()
    try:
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
    force_rebuild_all_databases()
    print("\n💡 下一步:")
    print("   1. 重启后端服务 (cd backend && python main.py)")
    print("   2. 测试任务创建 (python test_api_error.py)")

