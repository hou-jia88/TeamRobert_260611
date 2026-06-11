from openai import OpenAI
import json
from typing import Dict, Optional, List
from backend.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

class DeepSeekClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )
        self.model = DEEPSEEK_MODEL
    
    def chat_completion(self, messages: list, temperature: float = 0.7) -> str:
        """发送聊天请求到 DeepSeek"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"DeepSeek API 调用失败: {str(e)}")
            return None
    
    def extract_intent(self, user_message: str) -> Dict:
        """提取用户意图和关键信息"""
        system_prompt = """你是一个智能团队协作助手，负责理解用户的自然语言指令。
请分析用户消息并返回JSON格式的结果，包含以下字段：
- intent: 意图类型 (create_task/update_task/query_tasks/create_meeting/query_meetings/upload_document/query_progress/add_member/create_note/help/chat)
- entities: 提取的实体信息（根据意图不同而不同）

任务相关实体：title(任务标题), assignee(负责人), deadline(截止时间), status(状态), task_id(任务ID)
会议相关实体：title(会议主题), date(日期), time(时间), participants(参与者)
文档相关实体：name(文档名称), type(文档类型)
成员相关实体：name(成员姓名), role(角色), email(邮箱)
笔记相关实体：author(作者), content(笔记内容)

重要规则：
1. 如果用户提到"创建任务"、"新增任务"、"添加任务"等，intent必须是"create_task"
2. 如果用户提到"添加成员"、"新增成员"、"加入团队"等，intent必须是"add_member"
3. 如果用户提到"修改"、"更新"、"改成"、"变为"等，并且涉及现有记录，intent必须是"update_task"
4. 如果用户提到"添加笔记"、"记笔记"、"写笔记"、"记录"、"备注"等，intent必须是"create_note"
5. 即使用户输入模糊，也要尽量提取信息，没有的字段设为null
6. 只返回纯JSON，不要包含markdown格式或其他文字

示例：
用户："创建一个任务给张三"
返回：{"intent": "create_task", "entities": {"title": "新任务", "assignee": "张三"}}

用户："添加成员况颜娜"
返回：{"intent": "add_member", "entities": {"name": "况颜娜"}}

用户："把张三的任务改成已完成"
返回：{"intent": "update_task", "entities": {"assignee": "张三", "new_status": "已完成"}}

用户："把所有待办任务改为进行中"
返回：{"intent": "update_task", "entities": {"status": "待办", "new_status": "进行中"}}

用户："添加笔记：今天完成了需求评审会议"
返回：{"intent": "create_note", "entities": {"author": "张三", "content": "今天完成了需求评审会议"}}

用户："帮我记一下：下周要进行产品演示"
返回：{"intent": "create_note", "entities": {"content": "下周要进行产品演示"}}

重要提示：
- 如果用户提到"我是XXX"、"我叫XXX"等，必须将XXX提取为author字段
- 如果用户没有提供姓名，author字段设为null

只返回JSON，不要其他内容。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        result = self.chat_completion(messages, temperature=0.3)
        if result:
            try:
                # 清理可能的markdown格式和多余空白
                result = result.strip()
                # 移除 ```json 和 ``` 标记
                if result.startswith("```"):
                    result = result.split("\n", 1)[-1]  # 移除第一行
                if result.endswith("```"):
                    result = result.rsplit("\n", 1)[0]  # 移除最后一行
                result = result.strip()
                
                # 尝试解析JSON
                parsed = json.loads(result)
                
                # 验证返回结构
                if "intent" not in parsed:
                    print(f"⚠️  LLM返回缺少intent字段: {result}")
                    return {"intent": "chat", "entities": {}}
                
                # 确保entities存在
                if "entities" not in parsed:
                    parsed["entities"] = {}
                
                return parsed
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {str(e)}")
                print(f"   原始响应: {result[:200]}")
                # 尝试从文本中提取JSON
                import re
                json_match = re.search(r'\{[^}]+\}', result)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except:
                        pass
                return {"intent": "chat", "entities": {}}
            except Exception as e:
                print(f"❌ 意图提取异常: {str(e)}")
                return {"intent": "chat", "entities": {}}
        
        # API调用失败时的fallback
        print("⚠️  LLM API调用失败，使用规则引擎fallback")
        return self._fallback_intent_extraction(user_message)
    
    def _fallback_intent_extraction(self, user_message: str) -> Dict:
        """规则引擎fallback - 当LLM失败时使用"""
        import re
        
        message_lower = user_message.lower()
        
        # 检测任务创建
        if any(kw in message_lower for kw in ['创建任务', '新增任务', '添加任务', 'create task']):
            title_match = re.search(r'[:：]\s*(.+?)(?:，|,|$)', user_message)
            assignee_match = re.search(r'(?:分配给|给)\s*(.+?)(?:，|,|$)', user_message)
            deadline_match = re.search(r'(?:截止|到期)[:：]?\s*(.+?)(?:。|$)', user_message)
            
            return {
                "intent": "create_task",
                "entities": {
                    "title": title_match.group(1) if title_match else "新任务",
                    "assignee": assignee_match.group(1) if assignee_match else "未分配",
                    "deadline": deadline_match.group(1) if deadline_match else None
                }
            }
        
        # 检测任务查询
        if any(kw in message_lower for kw in ['查看任务', '查询任务', '任务列表', '所有任务']):
            return {"intent": "query_tasks", "entities": {}}
        
        # 检测添加成员
        if any(kw in message_lower for kw in ['添加成员', '新增成员', '加入团队', 'add member']):
            name_match = re.search(r'(?:成员|加|入)\s*(.+?)(?:，|,|$)', user_message)
            return {
                "intent": "add_member",
                "entities": {
                    "name": name_match.group(1) if name_match else "新成员"
                }
            }
        
        # 检测添加笔记
        if any(kw in message_lower for kw in ['添加笔记', '记笔记', '写笔记', '记录', '备注', 'create note', 'add note']):
            content_match = re.search(r'[:：]\s*(.+)$', user_message)
            author_match = re.search(r'(?:我|本人)是(.+?)(?:，|,|$)', user_message)
            
            # 如果没有找到“我是XXX”格式，尝试其他模式
            if not author_match:
                # 尝试匹配“我叫XXX”
                author_match = re.search(r'我叫(.+?)(?:，|,|$)', user_message)
            
            return {
                "intent": "create_note",
                "entities": {
                    "author": author_match.group(1) if author_match else None,
                    "content": content_match.group(1) if content_match else user_message
                }
            }
        
        # 检测会议相关
        if any(kw in message_lower for kw in ['安排会议', '创建会议', '预约会议']):
            return {"intent": "create_meeting", "entities": {}}
        
        # 默认聊天
        return {"intent": "chat", "entities": {}}
    
    def generate_response(self, intent_result: Dict, context: str = "") -> str:
        """根据意图结果生成自然语言回复"""
        system_prompt = """你是一个友好、专业的团队协作助手。
根据操作结果生成简洁、清晰的中文回复。
使用适当的emoji增强可读性。
保持回复简洁明了，重点突出。"""
        
        user_content = f"操作结果：{json.dumps(intent_result, ensure_ascii=False)}\n上下文：{context}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        return self.chat_completion(messages, temperature=0.7)
    
    def analyze_progress(self, tasks_data: list, team_context: str = "", documents_context: str = "") -> str:
        """智能分析团队进度"""
        system_prompt = """你是一位经验丰富的项目管理专家，擅长团队管理和数据分析。

【分析要求】
1. 结合团队背景进行个性化分析
2. 识别潜在风险和改进机会
3. 给出具体可执行的建议
4. 语气专业但亲切，避免生硬

【回复结构】
📊 整体评估：简要总结当前状态
🎯 亮点与关注点：指出做得好的和需要关注的
💡 建议：给出2-3条实用建议
⚠️ 风险提示：如果有延期风险或其他问题

用中文回复，语言自然流畅，像一位贴心的项目经理在和你交流。"""
        
        user_content = f"任务数据：{json.dumps(tasks_data, ensure_ascii=False)}"
        if team_context:
            user_content += f"\n\n团队成员信息：\n{team_context}"
        if documents_context:
            user_content += f"\n\n相关文档：\n{documents_context}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        return self.chat_completion(messages, temperature=0.6)
    
    def decompose_task(self, task_description: str) -> list:
        """智能分解复杂任务"""
        system_prompt = """你是一个经验丰富的项目经理。
将复杂任务分解为具体的子任务列表。
每个子任务应该：
- 具体可执行
- 有明确的交付物
- 合理的工作量

返回JSON数组格式：[{"title": "子任务标题", "description": "详细描述"}]
只返回JSON，不要其他内容。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"任务：{task_description}"}
        ]
        
        result = self.chat_completion(messages, temperature=0.5)
        if result:
            try:
                result = result.strip()
                if result.startswith("```json"):
                    result = result[7:]
                if result.endswith("```"):
                    result = result[:-3]
                return json.loads(result.strip())
            except json.JSONDecodeError:
                return []
        return []
    
    def generate_smart_reply(self, user_message: str, db_context: dict, operation_result: dict = None) -> str:
        """生成智能对话回复 - 核心增强功能"""
        system_prompt = """你是TeamRobert团队的智能协作助手，一个既专业又有人情味的伙伴。

【你的特点】
- 熟悉团队每个成员的专长和工作风格
- 了解项目进展和文档情况
- 说话自然流畅，像真人一样有温度
- 能主动发现潜在问题并给出建议
- 适当使用emoji，但不滥用

【回复原则】
1. 先理解用户的核心需求，再回应
2. 结合数据库中的真实信息，不要编造
3. 如果涉及人员，考虑他们的角色和当前负载
4. 给出建设性的下一步建议
5. 语气亲切专业，避免机械感

【信息使用说明】
- 团队信息：了解谁擅长什么，当前工作量如何
- 任务信息：了解项目进展和优先级
- 文档信息：了解可用的参考资料
- 会议信息：了解团队的时间安排

记住：你是团队的得力助手，不是冷冰冰的机器人！"""
        
        user_content = f"用户问：{user_message}\n\n"
        user_content += f"【当前数据库状态】\n"
        user_content += json.dumps(db_context, ensure_ascii=False, indent=2)
        
        if operation_result:
            user_content += f"\n【操作结果】\n{json.dumps(operation_result, ensure_ascii=False)}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        return self.chat_completion(messages, temperature=0.8)
