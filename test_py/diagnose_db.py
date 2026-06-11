"""
数据库诊断工具 - 检查 team_members 表的问题
"""
import sys
import os
import sqlite3

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal, engine, DATABASE_URL
from backend.models import TeamMember, Base
from sqlalchemy import inspect

def diagnose():
    """全面诊断数据库问题"""
    print("=" * 70)
    print("🔍 TeamRobert 数据库诊断工具")
    print("=" * 70)
    
    # 1. 检查数据库文件
    print("\n【1】检查数据库文件")
    db_path = DATABASE_URL.replace("sqlite:///", "")
    print(f"数据库路径: {db_path}")
    
    if os.path.exists(db_path):
        print(f"✅ 数据库文件存在")
        file_size = os.path.getsize(db_path)
        print(f"📊 文件大小: {file_size} bytes ({file_size/1024:.2f} KB)")
    else:
        print(f"❌ 数据库文件不存在！")
        print(f"💡 首次运行时会自动创建数据库")
    
    # 2. 检查表结构
    print("\n【2】检查数据库表结构")
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📁 数据库中的表: {len(tables)} 个")
        for table in tables:
            print(f"  • {table}")
        
        if 'team_members' not in tables:
            print(f"\n⚠️  team_members 表不存在！")
            print(f"💡 需要运行 fix_and_init_members.py 来创建表")
            return False
        else:
            print(f"\n✅ team_members 表存在")
            
    except Exception as e:
        print(f"❌ 检查表结构失败: {e}")
        return False
    
    # 3. 检查 team_members 表结构详情
    print("\n【3】检查 team_members 表结构详情")
    try:
        columns = inspector.get_columns('team_members')
        print(f"📋 字段列表 ({len(columns)} 个):")
        for col in columns:
            default = col.get('default', 'None')
            print(f"  • {col['name']:15} | {str(col['type']):15} | nullable={col['nullable']} | default={default}")
        
        # 检查是否有 created_at 字段
        has_created_at = any(col['name'] == 'created_at' for col in columns)
        if has_created_at:
            print(f"\n✅ created_at 字段存在")
        else:
            print(f"\n⚠️  created_at 字段缺失！")
            print(f"💡 这可能导致数据插入失败")
            
    except Exception as e:
        print(f"❌ 检查表结构详情失败: {e}")
        return False
    
    # 4. 检查现有数据
    print("\n【4】检查现有数据")
    db = SessionLocal()
    try:
        count = db.query(TeamMember).count()
        print(f"📊 当前团队成员数量: {count}")
        
        if count > 0:
            print(f"\n👥 现有成员列表:")
            members = db.query(TeamMember).all()
            for m in members:
                created = getattr(m, 'created_at', 'N/A')
                print(f"  • ID:{m.id} | {m.name:10} | {m.role:15} | {m.email}")
                print(f"    创建时间: {created}")
        else:
            print(f"\n⚠️  表中没有数据")
            print(f"💡 需要运行初始化脚本添加成员")
            
    except Exception as e:
        print(f"❌ 查询数据失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    # 5. 测试插入数据
    print("\n【5】测试插入数据")
    db = SessionLocal()
    try:
        test_member = TeamMember(
            name="测试用户",
            role="测试角色",
            email="test@test.com"
        )
        db.add(test_member)
        db.commit()
        print(f"✅ 测试数据插入成功 (ID: {test_member.id})")
        
        # 删除测试数据
        db.delete(test_member)
        db.commit()
        print(f"✅ 测试数据已清理")
        
    except Exception as e:
        print(f"❌ 测试插入失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()
    
    # 6. SQLite 直接检查
    print("\n【6】SQLite 直接检查")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取表的 SQL 定义
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='team_members'")
        result = cursor.fetchone()
        if result:
            print(f"📋 team_members 表的 SQL 定义:")
            print(f"   {result[0]}")
        
        # 检查行数
        cursor.execute("SELECT COUNT(*) FROM team_members")
        count = cursor.fetchone()[0]
        print(f"\n📊 SQLite 直接查询的行数: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ SQLite 直接检查失败: {e}")
    
    print("\n" + "=" * 70)
    print("✅ 诊断完成！")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    success = diagnose()
    
    if not success:
        print("\n❌ 诊断发现问题，建议运行以下命令修复:")
        print("   python fix_and_init_members.py")
    else:
        print("\n✅ 数据库状态正常！")
        print("\n如果需要重新初始化成员数据，请运行:")
        print("   python fix_and_init_members.py")
