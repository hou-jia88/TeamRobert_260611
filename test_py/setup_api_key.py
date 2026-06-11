"""
快速配置 DeepSeek API Key 的辅助脚本
"""
import os

def setup_api_key():
    print("=" * 60)
    print("🔧 TeamRobert - DeepSeek API 配置助手")
    print("=" * 60)
    print()
    
    env_file = "../.env"
    
    # 检查是否已存在 .env 文件
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "DEEPSEEK_API_KEY=sk-" in content:
            print("✅ 检测到已配置的 API Key")
            print()
            update = input("是否要更新 API Key？(y/n): ").strip().lower()
            if update != 'y':
                print("\n✨ 配置已完成，可以开始使用了！")
                return
    
    print("\n📝 请按照以下步骤获取 API Key：")
    print("1. 访问: https://platform.deepseek.com")
    print("2. 注册/登录账号")
    print("3. 进入 'API Keys' 页面")
    print("4. 点击 '创建新密钥'")
    print("5. 复制生成的密钥")
    print()
    
    api_key = input("🔑 请粘贴您的 DeepSeek API Key: ").strip()
    
    if not api_key:
        print("\n❌ 未输入 API Key，配置取消")
        return
    
    if not api_key.startswith("sk-"):
        print("\n⚠️  警告: API Key 格式似乎不正确（应该以 sk- 开头）")
        confirm = input("是否继续？(y/n): ").strip().lower()
        if confirm != 'y':
            print("\n❌ 配置取消")
            return
    
    # 写入 .env 文件
    env_content = f"""# DeepSeek API 配置
DEEPSEEK_API_KEY={api_key}
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
"""
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("\n" + "=" * 60)
    print("✅ API Key 配置成功！")
    print("=" * 60)
    print(f"\n📁 配置文件已保存到: {os.path.abspath(env_file)}")
    print("\n🧪 接下来可以运行测试：")
    print("   python test_deepseek.py")
    print("\n🚀 或启动服务：")
    print("   cd backend")
    print("   python main.py")
    print()

if __name__ == "__main__":
    setup_api_key()
