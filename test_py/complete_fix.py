"""完整修复流程 - 数据库 + 代码更新"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import engine, Base, SessionLocal
from sqlalchemy import inspect
from backend.models import Task, Meeting, Document, TeamMember

def complete_fix():
    """完整修复流程"""
    print("=" * 60)
    print("🔧 完整修复流程")
    print("=" * 60)
    
    # 步骤 1: 重建数据库
    print("\n【步骤 1】重建数据库...")
    fix_database()
    
    # 步骤 2: 初始化团队成员
    print("\n【步骤 2】初始化团队成员...")
    init_team_members()
    
    # 步骤 3: 验证修复
    print("\n【步骤 3】验证修复结果...")
    verify_fix()
    
    print("\n" + "=" * 60)
    print("✅ 修复完成！")
    print("=" * 60)
    print("\n💡 下一步:")
    print("   1. 重启后端服务 (停止当前服务，然后运行: cd backend && python main.py)")
    print("   2. 测试添加成员: '添加成员况颜娜'")
    print("   3. 测试创建任务: '创建任务：完成合同，分配给邓然，截止：明天'")

def fix_database():
    """重建数据库"""
    print("   🗑️  删除旧表...")
    Base.metadata.drop_all(bind=engine)
    
    print("   🔨 创建新表...")
    Base.metadata.create_all(bind=engine)
    
    # 验证
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"   ✅ 表列表: {tables}")
    
    for table_name in ['tasks', 'meetings', 'documents', 'team_members']:
        if table_name in tables:
            columns = inspector.get_columns(table_name)
            col_names = [col['name'] for col in columns]
            has_created_at = 'created_at' in col_names
            status = "✓" if has_created_at else "❌"
            print(f"   {status} {table_name}: {len(columns)} 字段 {'(包含 created_at)' if has_created_at else '(缺少 created_at!)'}")
        else:
            print(f"   ❌ {table_name} 表不存在!")

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

def verify_fix():
    """验证修复结果"""
    db = SessionLocal()
    try:
        # 检查团队成员
        members = db.query(TeamMember).all()
        print(f"   ✅ 团队成员数量: {len(members)}")
        
        # 检查是否有邓然
        deng_ran = db.query(TeamMember).filter(TeamMember.name == "邓然").first()
        if deng_ran:
            print(f"   ✅ 邓然存在: ID={deng_ran.id}, 角色={deng_ran.role}")
        else:
            print(f"   ❌ 邓然不存在!")
        
        # 测试查询（验证 created_at 字段）
        all_members = db.query(TeamMember).all()
        print(f"   ✅ 数据库查询正常（created_at 字段存在）")
        
    except Exception as e:
        print(f"   ❌ 验证失败: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    complete_fix()
