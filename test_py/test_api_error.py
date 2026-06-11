"""测试API并捕获详细错误"""
import sys
import os
import requests
import json

def test_api_detailed():
    """详细测试API，显示完整错误信息"""
    
    print("=" * 60)
    print("🧪 API 详细测试")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # 测试 1: 根路径
    print("\n【测试 1】根路径 GET /")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
    
    # 测试 2: 简单聊天
    print("\n【测试 2】简单聊天 POST /api/chat")
    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={"message": "帮助"},
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功")
            print(f"类型: {data.get('type')}")
            print(f"消息: {data.get('message', '')[:200]}")
        else:
            print(f"❌ 失败")
            print(f"响应内容: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试 3: 创建任务（关键测试）
    print("\n【测试 3】创建任务 POST /api/chat")
    print("输入: 创建任务：完成合同，分配给邓然，截止：明天")
    
    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={"message": "创建任务：完成合同，分配给邓然，截止：明天"},
            timeout=15
        )
        
        print(f"\n状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API 调用成功")
            print(f"\n返回数据类型: {data.get('type')}")
            print(f"返回消息:")
            print("-" * 60)
            print(data.get('message', '无消息'))
            print("-" * 60)
            
            if 'data' in data:
                print(f"\n附加数据: {json.dumps(data['data'], ensure_ascii=False, indent=2)}")
                
        else:
            print(f"❌ API 返回错误状态码: {response.status_code}")
            print(f"\n响应内容:")
            print("-" * 60)
            print(response.text[:1000])
            print("-" * 60)
            
            # 尝试解析错误详情
            try:
                error_data = response.json()
                print(f"\n错误详情: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
            except:
                pass
            
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时（超过15秒）")
        print("   可能原因: LLM API 调用太慢或卡住")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接错误: {str(e)}")
        print("   请确认后端服务正在运行")
    except Exception as e:
        print(f"❌ 未知错误: {str(e)}")
        import traceback
        print("\n完整堆栈跟踪:")
        traceback.print_exc()
    
    # 测试 4: 获取任务列表
    print("\n【测试 4】获取任务列表 GET /api/tasks")
    try:
        response = requests.get(f"{base_url}/api/tasks", timeout=5)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            tasks = response.json()
            print(f"✅ 成功，共 {len(tasks)} 个任务")
            if tasks:
                print("最近的任务:")
                for t in tasks[:3]:
                    print(f"  - [{t['id']}] {t['title']} ({t['status']})")
        else:
            print(f"❌ 失败: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    print("\n💡 如果看到 500 错误，请检查:")
    print("   1. 后端控制台的错误输出")
    print("   2. 日志文件: logs/chat_*.log")
    print("   3. 运行: python view_logs.py")

if __name__ == "__main__":
    test_api_detailed()
