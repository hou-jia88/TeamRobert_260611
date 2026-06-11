"""诊断任务创建和数据库存储问题"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import engine, SessionLocal
from sqlalchemy import inspect
from backend.models import Task, TeamMember

def check_database():
    """检查数据库表结构和数据"""
    inspector = inspect(engine)
    
    print("=" * 60)
    print("数据库诊断报告")
    print("=" * 60)
    
    # 1. 检查表是否存在
    tables = inspector.get_table_names()
    print(f"\n📋 数据库中的表: {tables}")
    
    # 2. 检查 tasks 表结构
    if 'tasks' in tables:
        print("\n✅ tasks 表存在")
        columns = inspector.get_columns('tasks')
        print("\n📊 tasks 表结构:")
        for col in columns:
            print(f"   - {col['name']}: {col['type']} (nullable={col['nullable']})")
    else:
        print("\n❌ tasks 表不存在!")
        return
    
    # 3. 检查 team_members 表结构
    if 'team_members' in tables:
        print("\n✅ team_members 表存在")
        columns = inspector.get_columns('team_members')
        print("\n📊 team_members 表结构:")
        for col in columns:
            print(f"   - {col['name']}: {col['type']} (nullable={col['nullable']})")
    else:
        print("\n❌ team_members 表不存在!")
    
    # 4. 检查当前数据
    db = SessionLocal()
    try:
        tasks_count = db.query(Task).count()
        members_count = db.query(TeamMember).count()
        
        print(f"\n📈 数据统计:")
        print(f"   - 任务数量: {tasks_count}")
        print(f"   - 团队成员数量: {members_count}")
        
        if members_count > 0:
            print("\n👥 团队成员列表:")
            members = db.query(TeamMember).all()
            for m in members:
                print(f"   - {m.name} ({m.role})")
        
        if tasks_count > 0:
            print("\n📝 最近5个任务:")
            tasks = db.query(Task).order_by(Task.id.desc()).limit(5).all()
            for t in tasks:
                print(f"   - ID:{t.id} | {t.title} | 负责人:{t.assignee} | 状态:{t.status}")
                
    finally:
        db.close()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_database()
