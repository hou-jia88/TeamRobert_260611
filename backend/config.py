import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# 验证配置
if not DEEPSEEK_API_KEY:
    print("⚠️  警告: 未设置 DEEPSEEK_API_KEY 环境变量")
    print("请在 .env 文件中添加您的 API Key")
