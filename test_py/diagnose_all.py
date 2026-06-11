"""全面诊断系统状态"""
import sys
import os
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import engine, SessionLocal
from sqlalchemy import inspect
from backend.models import Task, TeamMember

def check_database():
    """检查数据库状态"""
    print("=" * 60)
    print("📊 数据库检查")
    print("=" * 60)
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\n✅ 数据库连接成功")
        print(f"📋 表列表: {tables}\n")
        
        # 检查 team_members 表
        if 'team_members' in tables:
            columns = inspector.get_columns('team_members')
            col_names = [col['name'] for col in columns]
            print(f"✅ team_members 表存在")
            print(f"   字段: {', '.join(col_names)}")
            
            # 检查是否有 created_at 字段
            if 'created_at' not in col_names:
                print(f"   ❌ 缺少 created_at 字段！需要重建数据库")
                return False
            else:
                print(f"   ✅ created_at 字段存在")
                
            # 检查数据
            db = SessionLocal()
            try:
                count = db.query(TeamMember).count()
                print(f"   📈 团队成员数量: {count}")
                if count == 0:
                    print(f"   ⚠️  警告: 没有团队成员数据")
                else:
                    members = db.query(TeamMember).all()
                    print(f"   成员列表:")
                    for m in members:
                        print(f"      - {m.name} ({m.role})")
            finally:
                db.close()
        else:
            print(f"❌ team_members 表不存在！需要重建数据库")
            return False
            
        # 检查 tasks 表
        if 'tasks' in tables:
            columns = inspector.get_columns('tasks')
            col_names = [col['name'] for col in columns]
            print(f"\n✅ tasks 表存在")
            print(f"   字段: {', '.join(col_names)}")
            
            db = SessionLocal()
            try:
                count = db.query(Task).count()
                print(f"   📈 任务数量: {count}")
            finally:
                db.close()
        else:
            print(f"\n❌ tasks 表不存在！需要重建数据库")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {str(e)}")
        return False

def check_backend():
    """检查后端服务"""
    print("\n" + "=" * 60)
    print("🌐 后端服务检查")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8000/", timeout=3)
        if response.status_code == 200:
            print(f"✅ 后端服务正常运行")
            print(f"   响应: {response.json()}")
            return True
        else:
            print(f"❌ 后端服务返回异常状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到后端服务 (http://localhost:8000)")
        print(f"   请确保后端正在运行: python backend/main.py")
        return False
    except Exception as e:
        print(f"❌ 检查后端失败: {str(e)}")
        return False

def test_chat_api():
    """测试聊天API"""
    print("\n" + "=" * 60)
    print("💬 聊天API测试")
    print("=" * 60)
    
    try:
        # 测试简单消息
        print("\n测试 1: 发送帮助请求...")
        response = requests.post(
            "http://localhost:8000/api/chat",
            json={"message": "帮助"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API 响应成功")
            print(f"   类型: {data.get('type')}")
            print(f"   消息预览: {data.get('message', '')[:100]}")
        else:
            print(f"❌ API 返回错误: {response.status_code}")
            print(f"   响应内容: {response.text[:200]}")
            return False
            
        # 测试创建任务
        print("\n测试 2: 尝试创建任务...")
        response = requests.post(
            "http://localhost:8000/api/chat",
            json={"message": "创建任务：测试任务，分配给张三"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 任务创建 API 响应成功")
            print(f"   类型: {data.get('type')}")
            print(f"   消息: {data.get('message', '')[:150]}")
            
            if data.get('type') == 'error':
                print(f"   ⚠️  但返回了错误信息")
                return False
            elif data.get('type') == 'task_created':
                print(f"   ✅ 任务创建成功！")
                return True
        else:
            print(f"❌ 创建任务失败: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ API 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 60)
    print("🔍 TeamRobert 系统全面诊断")
    print("=" * 60)
    
    # 1. 检查数据库
    db_ok = check_database()
    
    # 2. 检查后端
    backend_ok = check_backend()
    
    # 3. 测试API
    api_ok = False
    if backend_ok:
        api_ok = test_chat_api()
    
    # 总结
    print("\n" + "=" * 60)
    print("📋 诊断总结")
    print("=" * 60)
    print(f"数据库状态: {'✅ 正常' if db_ok else '❌ 异常'}")
    print(f"后端服务: {'✅ 运行中' if backend_ok else '❌ 未运行'}")
    print(f"API功能: {'✅ 正常' if api_ok else '❌ 异常'}")
    
    if not db_ok:
        print("\n🔧 建议操作:")
        print("   python fix_db_auto.py  # 重建数据库")
    
    if not backend_ok:
        print("\n🔧 建议操作:")
        print("   cd backend && python main.py  # 启动后端服务")
    
    if db_ok and backend_ok and not api_ok:
        print("\n🔧 建议操作:")
        print("   查看后端控制台输出，检查具体错误")
        print("   python view_logs.py  # 查看日志")
    
    if db_ok and backend_ok and api_ok:
        print("\n🎉 系统一切正常！")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
