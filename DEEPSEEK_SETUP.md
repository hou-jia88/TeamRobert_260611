# DeepSeek API 接入指南

## 📋 步骤说明

### 1. 获取 DeepSeek API Key

1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com)
2. 注册/登录账号
3. 进入 "API Keys" 页面
4. 点击 "创建新密钥"
5. 复制生成的 API Key（格式类似：`sk-xxxxxxxxxxxxxxxx`）

### 2. 配置 API Key

在项目根目录的 `.env` 文件中填入您的 API Key：

```env
DEEPSEEK_API_KEY=sk-your-actual-api-key-here
```

> ⚠️ **重要**: `.env` 文件已添加到 `.gitignore`，不会上传到代码仓库，请放心填写真实密钥。

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 测试连接

运行测试脚本验证 API 是否正常工作：

```bash
python test_deepseek.py
```

如果看到以下输出，说明配置成功：
```
✅ API Key 已配置: sk-xxxxx...
✅ API 调用成功！
💬 回复: 你好！有什么可以帮助你的吗？
```

### 5. 启动服务

```bash
cd backend
python main.py
```

然后在浏览器打开 `frontend/index.html` 即可使用智能对话功能！

## 🎯 使用示例

配置大模型后，您可以使用更自然的语言：

### 任务管理
```
❌ 之前需要固定格式：
"创建任务：写需求文档，分配给张三，截止：下周五"

✅ 现在可以自然表达：
"给张三安排个写文档的活，下周五要交"
"帮我把任务5标记为已完成"
"开发一个登录功能"（会自动分解子任务）
```

### 会议安排
```
✅ 自然语言：
"明天下午3点开个会讨论项目进度"
"约个会和团队评审一下需求"
```

### 进度查询
```
✅ 智能分析：
"看看我们做得怎么样了"
"为什么项目进度慢了？"（会给出分析报告）
```

## 🔧 高级配置

### 切换模型

在 `.env` 文件中修改：

```env
# 使用不同的模型
DEEPSEEK_MODEL=deepseek-chat        # 默认聊天模型
# DEEPSEEK_MODEL=deepseek-coder     # 代码专用模型
```

### 关闭大模型（回退到规则引擎）

如果需要临时禁用大模型，修改 `backend/agent.py`：

```python
self.use_llm = False  # 改为 False 即可
```

### 自定义 API 地址

如果您使用的是私有部署或其他兼容 OpenAI 的服务：

```env
DEEPSEEK_BASE_URL=https://your-custom-endpoint/v1
```

## 💰 费用说明

DeepSeek API 采用按量付费：
- deepseek-chat: 约 ¥0.01-0.05 / 1000 tokens
- 日常使用每天约 ¥1-5 元

可在 [DeepSeek 控制台](https://platform.deepseek.com/usage) 查看用量和费用。

## ❓ 常见问题

### Q: 提示 "API Key 无效"
A: 检查 `.env` 文件中的 API Key 是否正确复制，确保没有多余空格。

### Q: 响应很慢
A: 首次调用可能需要 2-5 秒，后续会有缓存加速。

### Q: 如何降低成本？
A: 
1. 简单命令使用规则引擎（设置 `use_llm = False`）
2. 复杂场景才启用大模型
3. 定期查看用量报告

### Q: 支持其他大模型吗？
A: 是的，代码基于 OpenAI SDK，可轻松切换到：
- ChatGPT (OpenAI)
- 通义千问 (阿里云)
- 文心一言 (百度)
- 任何兼容 OpenAI 接口的服务

只需修改 `.env` 中的 `DEEPSEEK_BASE_URL` 和 `DEEPSEEK_API_KEY` 即可。

## 🚀 下一步

集成完成后，您可以：
1. ✅ 体验自然语言交互
2. ✅ 尝试智能任务分解
3. ✅ 查看智能进度分析
4. 🔜 添加更多 AI 功能（如会议纪要生成、风险预警等）

有问题欢迎反馈！
