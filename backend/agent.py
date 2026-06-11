import re
from datetime import datetime
from sqlalchemy.orm import Session
import sys
import os
import json
import logging
from typing import Dict, Optional
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import Task, Meeting, Document, TeamMember, TeamNote
from backend.llm_client import DeepSeekClient

# 配置日志
def setup_logger():
    """设置对话日志记录器"""
    # 创建 logs 目录
    log_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 日志文件路径（按日期分割）
    log_file = log_dir / f"chat_{datetime.now().strftime('%Y%m%d')}.log"
    
    # 创建 logger
    logger = logging.getLogger('chat_logger')
    logger.setLevel(logging.INFO)
    
    # 避免重复添加 handler
    if not logger.handlers:
        # 文件 handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 控制台 handler（可选）
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

# 初始化 logger
chat_logger = setup_logger()

class ContextCache:
    """上下文缓存管理器 - 减少数据库查询和token消耗"""
    
    def __init__(self):
        self._team_members = None
        self._tasks_summary = None
        self._last_update = None
        self._cache_ttl = 300  # 缓存有效期5分钟
        self._hit_count = 0
        self._miss_count = 0
    
    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        if not self._last_update:
            return True
        return (datetime.now() - self._last_update).total_seconds() > self._cache_ttl
    
    def invalidate(self):
        """使缓存失效（数据变更时调用）"""
        self._team_members = None
        self._tasks_summary = None
        self._last_update = None
    
    def get_team_context(self, db: Session) -> str:
        """获取团队上下文（带缓存）"""
        if not self.is_expired() and self._team_members is not None:
            self._hit_count += 1
            return self._team_members
        
        self._miss_count += 1
        members = db.query(TeamMember).all()
        if not members:
            self._team_members = "暂无团队成员信息"
        else:
            info_lines = ["【团队成员】"]
            for m in members:
                # 查询该成员的任务负载
                member_tasks = db.query(Task).filter(Task.assignee == m.name).all()
                active_tasks = sum(1 for t in member_tasks if t.status in ["进行中", "待办"])
                
                info_lines.append(f"- {m.name}（{m.role}）")
                if m.email:
                    info_lines.append(f"  邮箱：{m.email}")
                info_lines.append(f"  当前活跃任务数：{active_tasks}")
            
            self._team_members = "\n".join(info_lines)
        
        self._last_update = datetime.now()
        return self._team_members
    
    def get_lightweight_summary(self, db: Session) -> dict:
        """获取轻量级摘要（用于通用对话）"""
        if not self.is_expired() and self._tasks_summary is not None:
            self._hit_count += 1
            return self._tasks_summary
        
        self._miss_count += 1
        tasks = db.query(Task).all()
        meetings = db.query(Meeting).all()
        
        self._tasks_summary = {
            "task_count": len(tasks),
            "status_distribution": {
                "completed": sum(1 for t in tasks if t.status == "已完成"),
                "in_progress": sum(1 for t in tasks if t.status == "进行中"),
                "pending": sum(1 for t in tasks if t.status == "待办")
            },
            "meeting_count": len(meetings)
        }
        
        self._last_update = datetime.now()
        return self._tasks_summary
    
    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        total = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total * 100) if total > 0 else 0
        return {
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": f"{hit_rate:.1f}%"
        }

class DatabaseSchema:
    """数据库Schema信息 - 让LLM知道表结构"""
    
    @staticmethod
    def get_table_schema(table_name: str) -> dict:
        """获取指定表的schema信息"""
        schemas = {
            "task": {
                "table": "tasks",
                "fields": {
                    "id": {"type": "Integer", "description": "任务ID"},
                    "title": {"type": "String", "description": "任务标题"},
                    "description": {"type": "Text", "description": "任务描述"},
                    "assignee": {"type": "String", "description": "负责人姓名"},
                    "status": {"type": "String", "description": "状态", "values": ["待办", "进行中", "已完成"]},
                    "priority": {"type": "String", "description": "优先级", "values": ["高", "中", "低"]},
                    "deadline": {"type": "String", "description": "截止时间"},
                    "created_at": {"type": "String", "description": "创建时间"},
                    "updated_at": {"type": "String", "description": "更新时间"}
                },
                "searchable_fields": ["title", "assignee", "status", "priority"],
                "updatable_fields": ["title", "description", "assignee", "status", "priority", "deadline"]
            },
            "meeting": {
                "table": "meetings",
                "fields": {
                    "id": {"type": "Integer", "description": "会议ID"},
                    "title": {"type": "String", "description": "会议主题"},
                    "date": {"type": "String", "description": "日期"},
                    "time": {"type": "String", "description": "时间"},
                    "participants": {"type": "String", "description": "参与者"},
                    "location": {"type": "String", "description": "地点"},
                    "agenda": {"type": "Text", "description": "议程"},
                    "created_at": {"type": "String", "description": "创建时间"}
                },
                "searchable_fields": ["title", "date", "participants"],
                "updatable_fields": ["title", "date", "time", "participants", "location", "agenda"]
            },
            "member": {
                "table": "team_members",
                "fields": {
                    "id": {"type": "Integer", "description": "成员ID"},
                    "name": {"type": "String", "description": "姓名"},
                    "role": {"type": "String", "description": "角色/职位"},
                    "email": {"type": "String", "description": "邮箱地址"},
                    "created_at": {"type": "String", "description": "加入时间"}
                },
                "searchable_fields": ["name", "role"],
                "updatable_fields": ["name", "role", "email"]
            },
            "document": {
                "table": "documents",
                "fields": {
                    "id": {"type": "Integer", "description": "文档ID"},
                    "name": {"type": "String", "description": "文档名称"},
                    "type": {"type": "String", "description": "文档类型"},
                    "url": {"type": "String", "description": "文档URL"},
                    "owner": {"type": "String", "description": "所有者"},
                    "created_at": {"type": "String", "description": "上传时间"}
                },
                "searchable_fields": ["name", "type", "owner"],
                "updatable_fields": ["name", "type", "url"]
            }
        }
        return schemas.get(table_name, {})
    
    @staticmethod
    def get_all_schemas() -> str:
        """获取所有表的schema信息（用于LLM提示词）"""
        result = []
        for table_name in ["task", "meeting", "member", "document"]:
            schema = DatabaseSchema.get_table_schema(table_name)
            if schema:
                result.append(f"\n【{schema['table']}】")
                result.append("可更新字段：")
                for field, info in schema['fields'].items():
                    if field in schema['updatable_fields']:
                        desc = info['description']
                        if 'values' in info:
                            desc += f" (可选值: {', '.join(info['values'])})"
                        result.append(f"  - {field}: {desc}")
        return "\n".join(result)


class ConversationState:
    """对话状态管理器 - 支持多轮对话式修改"""
    
    def __init__(self):
        self.active = False  # 是否有活跃的对话流程
        self.operation = None  # 当前操作类型: 'update_task', 'update_meeting', 'batch_update'
        self.target_records = []  # 目标记录列表
        self.pending_updates = {}  # 待更新的字段
        self.context_info = {}  # 上下文信息
        self.step = 0  # 当前步骤
    
    def reset(self):
        """重置对话状态"""
        self.active = False
        self.operation = None
        self.target_records = []
        self.pending_updates = {}
        self.context_info = {}
        self.step = 0
    
    def to_dict(self) -> dict:
        """转换为字典（用于序列化）"""
        return {
            "active": self.active,
            "operation": self.operation,
            "target_count": len(self.target_records),
            "pending_updates": self.pending_updates,
            "step": self.step
        }


class TeamAgent:
    def __init__(self):
        self.name = "TeamRobert助手"
        self.llm = DeepSeekClient()
        self.use_llm = True  # 是否使用大模型
        self.context_cache = ContextCache()  # 初始化缓存
        self.conv_state = ConversationState()  # 对话状态管理器
    
    def _build_minimal_context(self, db: Session, intent: str) -> dict:
        """构建最小化上下文 - 根据意图按需加载"""
        context = {}
        
        if intent in ["create_task", "update_task", "query_tasks", "query_progress"]:
            # 任务相关：只需要任务统计
            context["tasks_summary"] = self.context_cache.get_lightweight_summary(db)
        
        if intent in ["create_task", "assign"]:
            # 分配任务：需要团队成员信息
            context["team_members"] = self.context_cache.get_team_context(db)
        
        if intent in ["query_progress", "analyze"]:
            # 进度分析：需要完整信息
            context["tasks_summary"] = self.context_cache.get_lightweight_summary(db)
            context["team_members"] = self.context_cache.get_team_context(db)
        
        # 其他情况：只给最基础的统计
        if not context:
            context["overview"] = self.context_cache.get_lightweight_summary(db)
        
        return context
    
    def handle_message(self, message: str, db: Session) -> dict:
        """处理用户消息，返回响应"""
        message = message.strip()
        
        # 记录用户输入
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        chat_logger.info(f"👤 用户 | {message}")
        
        if self.use_llm:
            response = self._handle_with_llm(message, db)
        else:
            response = self._handle_with_rules(message, db)
        
        # 记录助手回复
        if response and 'message' in response:
            reply_preview = response['message'][:100] + '...' if len(response['message']) > 100 else response['message']
            chat_logger.info(f"🤖 助手 | {reply_preview}")
        
        return response
    
    def _handle_with_llm(self, message: str, db: Session) -> dict:
        """使用大模型处理消息"""
        # 检查是否有活跃的对话流程
        if self.conv_state.active:
            return self._continue_conversation(message, db)
        
        # 提取意图
        intent_result = self.llm.extract_intent(message)
        intent = intent_result.get("intent", "chat")
        entities = intent_result.get("entities", {})
        
        # 根据意图执行对应操作
        operation_result = None
        
        if intent == "create_task":
            operation_result = self._create_task_llm(entities, db)
            self.context_cache.invalidate()  # 数据变更，清除缓存
        elif intent == "update_task":
            # 启动智能更新对话流程
            operation_result = self._start_smart_update(message, entities, db)
        elif intent == "query_tasks":
            operation_result = self._query_tasks(db)
        elif intent == "create_meeting":
            operation_result = self._create_meeting_llm(entities, db)
            self.context_cache.invalidate()
        elif intent == "query_meetings":
            operation_result = self._query_meetings(db)
        elif intent == "upload_document":
            operation_result = self._upload_document_llm(entities, db)
            self.context_cache.invalidate()
        elif intent == "query_progress":
            operation_result = self._query_progress_llm(db)
        elif intent == "add_member":
            operation_result = self._add_member_llm(entities, db)
            self.context_cache.invalidate()
        elif intent == "create_note":
            operation_result = self._create_note_llm(entities, db)
            self.context_cache.invalidate()
        elif intent == "help":
            return self._handle_help()
        else:
            # 通用对话 - 使用轻量级上下文
            minimal_context = self._build_minimal_context(db, intent)
            response = self.llm.generate_smart_reply(message, minimal_context)
            return {
                "type": "chat",
                "message": response or f"收到您的消息：{message}\n\n您可以尝试说：\n- '创建任务：XXX'\n- '查看任务进度'\n- '安排会议'\n- '上传文档'"
            }
        
        # 如果有操作结果，生成智能回复（使用最小化上下文）
        if operation_result:
            minimal_context = self._build_minimal_context(db, intent)
            smart_reply = self.llm.generate_smart_reply(message, minimal_context, operation_result)
            if smart_reply:
                operation_result["message"] = smart_reply
        
        return operation_result or {
            "type": "chat",
            "message": "已处理您的请求"
        }
    
    def _handle_with_rules(self, message: str, db: Session) -> dict:
        """使用规则引擎处理消息（备用方案）"""
        if any(keyword in message for keyword in ["任务", "分配", "创建"]):
            return self._handle_task(message, db)
        elif any(keyword in message for keyword in ["会议", "安排", "预约"]):
            return self._handle_meeting(message, db)
        elif any(keyword in message for keyword in ["进度", "状态", "查看"]):
            return self._handle_query(message, db)
        elif any(keyword in message for keyword in ["文档", "文件", "上传"]):
            return self._handle_document(message, db)
        elif any(keyword in message for keyword in ["帮助", "help", "说明"]):
            return self._handle_help()
        else:
            return {
                "type": "chat",
                "message": f"收到您的消息：{message}\n\n您可以尝试说：\n- '创建任务：XXX'\n- '查看任务进度'\n- '安排会议'\n- '上传文档'"
            }
    
    def _handle_task(self, message: str, db: Session) -> dict:
        """处理任务相关操作 - 先验证后创建"""
        if any(keyword in message for keyword in ["创建", "新增", "添加"]):
            title_match = re.search(r'[:：]\s*(.+?)(?:，|,|$)', message)
            assignee_match = re.search(r'(?:分配给|给)\s*(.+?)(?:，|,|$)', message)
            deadline_match = re.search(r'(?:截止|到期)[:：]?\s*(.+?)(?:。|$)', message)
            
            title = title_match.group(1) if title_match else None
            assignee = assignee_match.group(1) if assignee_match else "未分配"
            deadline = deadline_match.group(1) if deadline_match else None
            
            # ===== 验证关键信息 =====
            validation_errors = []
            
            # 如果标题为空，使用默认值
            if not title:
                title = "新任务"
            
            # 验证负责人（如果指定了）
            if assignee and assignee != "未分配":
                team_member = db.query(TeamMember).filter(TeamMember.name == assignee).first()
                if not team_member:
                    validation_errors.append(f"⚠️  警告：'{assignee}' 不在团队成员列表中")
                    members = db.query(TeamMember).all()
                    if members:
                        member_names = ', '.join([m.name for m in members])
                        validation_errors.append(f"   当前团队成员：{member_names}")
                        validation_errors.append(f"   请确认是否拼写错误")
            
            # 如果有严重错误，返回错误信息
            critical_errors = [e for e in validation_errors if e.startswith("❌")]
            if critical_errors:
                error_message = "❌ 任务创建失败\n\n" + "\n".join(validation_errors)
                return {
                    "type": "error",
                    "message": error_message
                }
            
            # ===== 创建任务 =====
            try:
                task = Task(
                    title=title,
                    assignee=assignee,
                    deadline=deadline,
                    status="待办"
                )
                db.add(task)
                db.commit()
                db.refresh(task)
                
                self.context_cache.invalidate()  # 清除缓存
                
                # 构建响应消息
                message_response = f"✅ 任务创建成功！\n\n标题：{title}\n负责人：{assignee}\n截止时间：{deadline or '未设置'}\n状态：待办"
                
                # 添加警告信息（如果有）
                warnings = [e for e in validation_errors if e.startswith("⚠️")]
                if warnings:
                    message_response += "\n\n" + "\n".join(warnings)
                
                return {
                    "type": "task_created",
                    "message": message_response,
                    "data": {"id": task.id, "title": title, "assignee": assignee}
                }
                
            except Exception as e:
                db.rollback()
                chat_logger.error(f"任务创建失败: {str(e)}")
                return {
                    "type": "error",
                    "message": f"❌ 任务创建失败\n\n错误信息：{str(e)}"
                }
        
        elif any(keyword in message for keyword in ["查看", "查询", "列表", "所有"]):
            tasks = db.query(Task).all()
            if not tasks:
                return {"type": "task_list", "message": "📋 当前暂无任务"}
            
            task_list = "\n".join([
                f"{i+1}. {t.title} - {t.assignee} [{t.status}] {'⏰'+t.deadline if t.deadline else ''}"
                for i, t in enumerate(tasks[-10:])
            ])
            return {
                "type": "task_list",
                "message": f"📋 当前任务列表（最近10条）：\n\n{task_list}",
                "data": [{"id": t.id, "title": t.title, "assignee": t.assignee, "status": t.status} for t in tasks]
            }
        
        elif any(keyword in message for keyword in ["更新", "修改", "完成", "进度"]):
            id_match = re.search(r'(\d+)', message)
            if id_match:
                task_id = int(id_match.group(1))
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    if "完成" in message:
                        task.status = "已完成"
                    elif "进行中" in message:
                        task.status = "进行中"
                    task.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
                    db.commit()
                    self.context_cache.invalidate()  # 清除缓存
                    return {"type": "task_updated", "message": f"✅ 任务 '{task.title}' 状态已更新为：{task.status}"}
            
            return {"type": "error", "message": "❌ 未找到指定任务，请提供任务编号"}
        
        return {"type": "chat", "message": "💡 您可以：\n- '创建任务：写需求文档，分配给张三，截止：下周五'\n- '查看所有任务'\n- '完成任务 1'"}
    
    def _handle_meeting(self, message: str, db: Session) -> dict:
        """处理会议相关操作"""
        title_match = re.search(r'[:：]\s*(.+?)(?:，|,|$)', message)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2}|\d{1,2}月\d{1,2}日)', message)
        time_match = re.search(r'(\d{1,2}:\d{2}|\d{1,2}点)', message)
        
        title = title_match.group(1) if title_match else "团队会议"
        date = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")
        time = time_match.group(1) if time_match else "14:00"
        
        meeting = Meeting(
            title=title,
            date=date,
            time=time,
            participants="团队成员"
        )
        db.add(meeting)
        db.commit()
        
        self.context_cache.invalidate()  # 清除缓存
        
        return {
            "type": "meeting_created",
            "message": f"📅 会议安排成功！\n\n主题：{title}\n日期：{date}\n时间：{time}\n\n已通知相关人员"
        }
    
    def _handle_query(self, message: str, db: Session) -> dict:
        """处理查询操作（规则引擎备用）"""
        tasks = db.query(Task).all()
        meetings = db.query(Meeting).all()
        
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == "已完成")
        in_progress = sum(1 for t in tasks if t.status == "进行中")
        pending = total - completed - in_progress
        
        # 计算完成率
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        stats = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 团队工作概览
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 整体进度
   完成率：{completion_rate:.1f}% ({completed}/{total})
   
📋 任务分布
   ✅ 已完成：{completed}
   🔄 进行中：{in_progress}
   ⏳ 待　办：{pending}
   📝 总　计：{total}

📅 会议安排
   待开会议：{len(meetings)} 个"""
        
        return {"type": "stats", "message": stats}
    
    def _handle_document(self, message: str, db: Session) -> dict:
        """处理文档相关操作"""
        doc_name = "新文档"
        match = re.search(r'[:：]\s*(.+)', message)
        if match:
            doc_name = match.group(1)
        
        doc = Document(
            name=doc_name,
            type="文档",
            owner="当前用户"
        )
        db.add(doc)
        db.commit()
        
        self.context_cache.invalidate()  # 清除缓存
        
        return {
            "type": "document_created",
            "message": f"📄 文档已记录\n\n名称：{doc_name}\n可随时上传实际文件"
        }
    
    def _handle_help(self) -> dict:
        """提供帮助信息"""
        help_text = """🤖 TeamRobert 助手 - 功能说明

📋 **任务管理**
• "创建任务：写需求文档，分配给张三，截止：下周五"
• "查看所有任务"
• "完成任务 1"

📅 **会议协调**
• "安排会议：项目评审，明天下午3点"
• "查看会议安排"

📊 **进度跟踪**
• "查看团队进度"
• "显示工作状态"

📄 **文档管理**
• "上传文档：需求规格说明书"
• "查看文档列表"

💡 **提示**
直接与我说自然语言即可，我会帮您处理！"""
        return {"type": "help", "message": help_text}
    
    # ===== 大模型处理方法 =====
    
    def _create_task_llm(self, entities: dict, db: Session) -> dict:
        """使用大模型提取的信息创建任务 - 先验证后创建"""
        # ===== 第零步：记录接收到的entities =====
        chat_logger.info(f"📥 接收到entities: {json.dumps(entities, ensure_ascii=False)}")
        
        title = entities.get("title", "新任务")
        assignee = entities.get("assignee", "未分配")
        deadline = entities.get("deadline", None)
        
        # 处理空值
        if not title or title.strip() == "":
            title = "新任务"
        if not assignee or assignee.strip() == "":
            assignee = "未分配"
        
        chat_logger.info(f"📝 任务参数 - 标题:{title}, 负责人:{assignee}, 截止:{deadline}")
        
        # ===== 第一步：验证关键信息 =====
        validation_errors = []
        warnings = []
        
        # 如果标题为空或为默认值，使用默认标题
        if not title or title == "新任务":
            title = "新任务"
            warnings.append("⚠️  未检测到任务标题，使用默认标题'新任务'")
        
        # 验证负责人（如果指定了）
        if assignee and assignee != "未分配":
            try:
                # 首先尝试精确匹配
                team_member = db.query(TeamMember).filter(TeamMember.name == assignee).first()
                
                # 如果精确匹配失败，尝试模糊匹配
                if not team_member:
                    all_members = db.query(TeamMember).all()
                    chat_logger.info(f"🔍 精确匹配失败，尝试模糊匹配 '{assignee}'")
                    
                    for member in all_members:
                        # 提取中文字符进行比较
                        chinese_in_assignee = ''.join([c for c in assignee if '\u4e00' <= c <= '\u9fff'])
                        chinese_in_member = member.name  # 假设团队成员名都是中文
                        
                        # 如果assignee中有中文字符，且与成员名匹配
                        if chinese_in_assignee and chinese_in_assignee in chinese_in_member:
                            team_member = member
                            chat_logger.info(f"✅ 模糊匹配成功: '{assignee}' -> '{member.name}'")
                            assignee = member.name  # 使用正确的名字
                            break
                        
                        # 如果assignee是纯拼音或英文，尝试lowercase匹配
                        elif not chinese_in_assignee:
                            if assignee.lower() in member.name.lower() or member.name.lower() in assignee.lower():
                                team_member = member
                                chat_logger.info(f"✅ 拼音匹配成功: '{assignee}' -> '{member.name}'")
                                assignee = member.name
                                break
                
                if not team_member:
                    chat_logger.warning(f"⚠️  负责人 '{assignee}' 不在团队中")
                    # 负责人不在团队中，给出警告但不阻止
                    warning_msg = f"⚠️  警告：'{assignee}' 不在团队成员列表中"
                    warnings.append(warning_msg)
                    
                    members = db.query(TeamMember).all()
                    if members:
                        member_names = ', '.join([m.name for m in members])
                        warning_msg2 = f"   当前团队成员：{member_names}"
                        warnings.append(warning_msg2)
                        warning_msg3 = f"   请确认是否拼写错误，或先将 {assignee} 添加到团队"
                        warnings.append(warning_msg3)
                        
            except Exception as e:
                chat_logger.error(f"❌ 负责人验证异常: {str(e)}")
                import traceback
                chat_logger.error(traceback.format_exc())
                # 即使验证失败，也继续创建任务
                warnings.append(f"⚠️  负责人验证出错，但将继续创建任务")
        else:
            warnings.append("⚠️  未指定负责人，设置为'未分配'")
        
        # 如果有严重错误，返回错误信息，不创建任务
        critical_errors = [e for e in validation_errors if e.startswith("❌")]
        if critical_errors:
            error_message = "❌ 任务创建失败\n\n" + "\n".join(validation_errors)
            error_message += "\n\n💡 请修正以上问题后重试"
            chat_logger.error(f"❌ 任务创建被阻止: {error_message}")
            return {
                "type": "error",
                "message": error_message,
                "validation_errors": validation_errors
            }
        
        # 合并warnings到validation_errors用于显示
        all_messages = warnings + validation_errors
        
        # ===== 第二步：创建任务（使用事务） =====
        try:
            chat_logger.info(f"💾 开始创建任务到数据库...")
            
            task = Task(
                title=title,
                assignee=assignee,
                deadline=deadline,
                status="待办"
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            
            chat_logger.info(f"✅ 任务创建成功，ID: {task.id}")
            
            # ===== 第三步：任务分解（可选，不影响任务创建） =====
            subtasks = []
            decomposition_warning = ""
            
            if len(title) > 10:  # 复杂任务可能需分解
                try:
                    subtasks = self.llm.decompose_task(title)
                except Exception as e:
                    # 分解失败不影响任务创建，只给出警告
                    decomposition_warning = f"\n\n⚠️  任务分解失败：{str(e)}"
                    decomposition_warning += "\n   任务已创建，但未能自动分解为子任务"
            
            # ===== 第四步：构建响应消息 =====
            response_data = {
                "id": task.id,
                "title": title,
                "assignee": assignee,
                "deadline": deadline or "未设置",
                "subtasks": subtasks
            }
            
            message = f"✅ 任务创建成功！\n\n标题：{title}\n负责人：{assignee}\n截止时间：{deadline or '未设置'}\n状态：待办"
            
            # 添加警告信息（如果有）
            if warnings:
                message += "\n\n" + "\n".join(warnings)
            
            # 添加子任务建议
            if subtasks:
                message += f"\n\n💡 建议分解为 {len(subtasks)} 个子任务："
                for i, st in enumerate(subtasks[:3], 1):
                    message += f"\n{i}. {st['title']}"
            
            # 添加分解失败的警告
            if decomposition_warning:
                message += decomposition_warning
            
            return {
                "type": "task_created",
                "message": message,
                "data": response_data
            }
            
        except Exception as e:
            # 如果创建失败，回滚事务
            db.rollback()
            chat_logger.error(f"任务创建失败: {str(e)}")
            return {
                "type": "error",
                "message": f"❌ 任务创建失败\n\n错误信息：{str(e)}\n\n请稍后重试或联系管理员"
            }
    
    def _update_task_llm(self, entities: dict, db: Session) -> dict:
        """使用大模型提取的信息更新任务"""
        task_id = entities.get("task_id")
        status = entities.get("status")
        
        if not task_id:
            return {"type": "error", "message": "❌ 请提供任务编号"}
        
        task = db.query(Task).filter(Task.id == int(task_id)).first()
        if not task:
            return {"type": "error", "message": f"❌ 未找到任务 #{task_id}"}
        
        if status:
            task.status = status
        task.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        db.commit()
        
        return {
            "type": "task_updated",
            "message": f"✅ 任务 '{task.title}' 已更新\n状态：{task.status}"
        }
    
    def _query_tasks(self, db: Session) -> dict:
        """查询任务列表"""
        tasks = db.query(Task).all()
        if not tasks:
            return {"type": "task_list", "message": "📋 当前暂无任务"}
        
        task_list = "\n".join([
            f"{i+1}. {t.title} - {t.assignee} [{t.status}] {'⏰'+t.deadline if t.deadline else ''}"
            for i, t in enumerate(tasks[-10:])
        ])
        return {
            "type": "task_list",
            "message": f"📋 当前任务列表（最近10条）：\n\n{task_list}",
            "data": [{"id": t.id, "title": t.title, "assignee": t.assignee, "status": t.status} for t in tasks]
        }
    
    def _create_meeting_llm(self, entities: dict, db: Session) -> dict:
        """使用大模型提取的信息创建会议"""
        title = entities.get("title", "团队会议")
        date = entities.get("date", datetime.now().strftime("%Y-%m-%d"))
        time = entities.get("time", "14:00")
        participants = entities.get("participants", "团队成员")
        
        meeting = Meeting(
            title=title,
            date=date,
            time=time,
            participants=participants
        )
        db.add(meeting)
        db.commit()
        
        return {
            "type": "meeting_created",
            "message": f"📅 会议安排成功！\n\n主题：{title}\n日期：{date}\n时间：{time}\n参与者：{participants}\n\n已通知相关人员"
        }
    
    def _query_meetings(self, db: Session) -> dict:
        """查询会议列表"""
        meetings = db.query(Meeting).all()
        if not meetings:
            return {"type": "meeting_list", "message": "📅 暂无安排的会议"}
        
        meeting_list = "\n".join([
            f"{i+1}. {m.title} - {m.date} {m.time} ({m.participants})"
            for i, m in enumerate(meetings[-5:])
        ])
        return {
            "type": "meeting_list",
            "message": f"📅  upcoming 会议：\n\n{meeting_list}"
        }
    
    def _upload_document_llm(self, entities: dict, db: Session) -> dict:
        """使用大模型提取的信息记录文档"""
        doc_name = entities.get("name", "新文档")
        doc_type = entities.get("type", "文档")
        
        doc = Document(
            name=doc_name,
            type=doc_type,
            owner="当前用户"
        )
        db.add(doc)
        db.commit()
        
        return {
            "type": "document_created",
            "message": f"📄 文档已记录\n\n名称：{doc_name}\n类型：{doc_type}\n可随时上传实际文件"
        }
    
    def _query_progress_llm(self, db: Session) -> dict:
        """智能查询进度分析"""
        tasks = db.query(Task).all()
        meetings = db.query(Meeting).all()
        
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == "已完成")
        in_progress = sum(1 for t in tasks if t.status == "进行中")
        pending = total - completed - in_progress
        
        # 计算完成率
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        # 基础统计 - 优化格式
        stats = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 团队工作概览
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 整体进度
   完成率：{completion_rate:.1f}% ({completed}/{total})
   
📋 任务分布
   ✅ 已完成：{completed}
   🔄 进行中：{in_progress}
   ⏳ 待　办：{pending}
   📝 总　计：{total}

📅 会议安排
   待开会议：{len(meetings)} 个"""
        
        # 如果有任务，使用大模型进行智能分析
        if tasks:
            tasks_data = [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "assignee": t.assignee,
                    "deadline": t.deadline
                }
                for t in tasks
            ]
            analysis = self.llm.analyze_progress(tasks_data)
            if analysis:
                stats += f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n💡 智能分析与建议\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{analysis}"
        
        return {"type": "stats", "message": stats}
    
    def _add_member_llm(self, entities: dict, db: Session) -> dict:
        """添加团队成员"""
        name = entities.get("name")
        role = entities.get("role", "未指定")
        email = entities.get("email", None)
        
        # 验证必填字段
        if not name or name.strip() == "":
            return {
                "type": "error",
                "message": "❌ 添加成员失败\n\n请提供成员姓名，例如：\n- '添加成员张三'\n- '新增成员李四，角色：前端开发'"
            }
        
        # 检查是否已存在
        existing = db.query(TeamMember).filter(TeamMember.name == name).first()
        if existing:
            return {
                "type": "warning",
                "message": f"⚠️  成员 '{name}' 已存在于团队中\n\n当前信息：\n- 角色：{existing.role or '未设置'}\n- 邮箱：{existing.email or '未设置'}"
            }
        
        # 创建新成员
        try:
            member = TeamMember(
                name=name,
                role=role if role != "未指定" else None,
                email=email
            )
            db.add(member)
            db.commit()
            db.refresh(member)
            
            chat_logger.info(f"✅ 新成员添加成功: {name} ({role})")
            
            return {
                "type": "member_added",
                "message": f"✅ 成员添加成功！\n\n👤 姓名：{name}\n💼 角色：{role if role != '未指定' else '待分配'}\n📧 邮箱：{email or '待补充'}\n\n现在可以给 {name} 分配任务了！"
            }
        except Exception as e:
            db.rollback()
            chat_logger.error(f"成员添加失败: {str(e)}")
            return {
                "type": "error",
                "message": f"❌ 成员添加失败\n\n错误信息：{str(e)}"
            }
    
    def _create_note_llm(self, entities: dict, db: Session) -> dict:
        """使用LLM创建团队笔记 - 必须提供作者姓名"""
        author = entities.get("author", None)
        content = entities.get("content", None)
        
        # 验证必填字段：作者
        if not author or author.strip() == "":
            return {
                "type": "error",
                "message": "❌ 添加笔记失败\n\n请提供您的姓名，例如：\n- '我是张三，添加笔记：今天完成了需求评审'\n- '我是李四，记一下：下周要进行产品演示'\n\n格式：'我是[姓名]，添加笔记：[内容]'"
            }
        
        # 验证必填字段：内容
        if not content or content.strip() == "":
            return {
                "type": "error",
                "message": f"❌ 添加笔记失败\n\n{author}，请提供笔记内容，例如：\n- '我是{author}，添加笔记：今天完成了需求评审会议'\n- '我是{author}，记一下：下周要进行产品演示'"
            }
        
        # 创建新笔记
        try:
            note = TeamNote(
                author=author,
                content=content
            )
            db.add(note)
            db.commit()
            db.refresh(note)
            
            chat_logger.info(f"✅ 新笔记添加成功: {author} - {content[:50]}...")
            
            return {
                "type": "note_created",
                "message": f"✅ 笔记添加成功！\n\n👤 作者：{author}\n📝 内容：{content}\n⏰ 时间：{note.created_at}\n\n所有团队成员都可以看到这条笔记！"
            }
        except Exception as e:
            db.rollback()
            chat_logger.error(f"笔记添加失败: {str(e)}")
            return {
                "type": "error",
                "message": f"❌ 笔记添加失败\n\n错误信息：{str(e)}"
            }
    
    def _start_smart_update(self, message: str, entities: dict, db: Session) -> dict:
        """启动智能更新对话流程"""
        chat_logger.info(f"🔄 启动智能更新流程: {message}")
        
        # 分析用户想要更新什么
        update_intent = self._analyze_update_intent(message, entities)
        
        if not update_intent or 'target_type' not in update_intent:
            return {
                "type": "clarification",
                "message": "💡 请告诉我您想更新什么？\n\n例如：\n- '把张三的任务改成已完成'\n- '把明天的会议改到后天'\n- '更新邓然的角色'"
            }
        
        target_type = update_intent.get('target_type')  # 'task', 'meeting', 'member'
        search_criteria = update_intent.get('criteria', {})
        new_values = update_intent.get('new_values', {})
        
        # 查找目标记录
        targets = self._find_targets(target_type, search_criteria, db)
        
        if not targets:
            return {
                "type": "error",
                "message": f"❌ 未找到匹配的记录\n\n搜索条件：{search_criteria}\n\n请尝试更具体的描述"
            }
        
        # 如果找到多个，让用户确认
        if len(targets) > 1:
            self.conv_state.active = True
            self.conv_state.operation = f"update_{target_type}"
            self.conv_state.target_records = targets
            self.conv_state.pending_updates = new_values
            self.conv_state.step = 1
            
            # 显示找到的记录，让用户选择
            options = []
            for i, t in enumerate(targets[:5]):  # 最多显示5个
                if target_type == 'task':
                    options.append(f"{i+1}. [{t.id}] {t.title} - {t.assignee} [{t.status}]")
                elif target_type == 'meeting':
                    options.append(f"{i+1}. [{t.id}] {t.title} - {t.date} {t.time}")
                elif target_type == 'member':
                    options.append(f"{i+1}. [{t.id}] {t.name} - {t.role}")
            
            return {
                "type": "clarification",
                "message": f"🔍 找到了 {len(targets)} 条匹配记录，请选择要更新的：\n\n" + "\n".join(options) + "\n\n请输入编号（1-5），或说'全部'来批量更新"
            }
        
        # 只找到一个，直接确认
        target = targets[0]
        self.conv_state.active = True
        self.conv_state.operation = f"update_{target_type}"
        self.conv_state.target_records = [target]
        self.conv_state.pending_updates = new_values
        self.conv_state.step = 2
        
        # 显示当前值和将要更新的值
        current_info = self._format_record_info(target, target_type)
        changes_info = self._format_changes(new_values)
        
        return {
            "type": "confirmation",
            "message": f"✅ 找到目标记录：\n\n{current_info}\n\n将要更新：\n{changes_info}\n\n请确认：'是的' 或 '取消'"
        }
    
    def _continue_conversation(self, message: str, db: Session) -> dict:
        """继续多轮对话"""
        chat_logger.info(f"💬 继续对话 (step={self.conv_state.step}): {message}")
        
        operation = self.conv_state.operation
        step = self.conv_state.step
        
        # 处理取消
        if any(kw in message.lower() for kw in ['取消', 'cancel', '不了', '算了']):
            self.conv_state.reset()
            return {
                "type": "cancelled",
                "message": "👌 已取消操作"
            }
        
        if operation == 'update_task':
            return self._handle_task_update_conversation(message, db, step)
        elif operation == 'update_meeting':
            return self._handle_meeting_update_conversation(message, db, step)
        elif operation == 'update_member':
            return self._handle_member_update_conversation(message, db, step)
        else:
            self.conv_state.reset()
            return {
                "type": "error",
                "message": "❌ 对话状态异常，请重新开始"
            }
    
    def _handle_task_update_conversation(self, message: str, db: Session, step: int) -> dict:
        """处理任务更新的对话流程"""
        
        if step == 1:  # 用户需要从多个选项中选择
            # 解析用户的选择
            if '全部' in message or 'all' in message.lower():
                # 批量更新所有
                self.conv_state.step = 3
                return self._execute_batch_update(db)
            
            # 尝试提取数字
            import re
            num_match = re.search(r'(\d+)', message)
            if num_match:
                idx = int(num_match.group(1)) - 1
                if 0 <= idx < len(self.conv_state.target_records):
                    # 用户选择了特定的记录
                    self.conv_state.target_records = [self.conv_state.target_records[idx]]
                    self.conv_state.step = 2
                    
                    target = self.conv_state.target_records[0]
                    current_info = self._format_record_info(target, 'task')
                    changes_info = self._format_changes(self.conv_state.pending_updates)
                    
                    return {
                        "type": "confirmation",
                        "message": f"✅ 已选择：\n\n{current_info}\n\n将要更新：\n{changes_info}\n\n请确认：'是的' 或 '取消'"
                    }
            
            return {
                "type": "clarification",
                "message": "❓ 请输入编号（如 '1'）或说'全部'"
            }
        
        elif step == 2:  # 等待确认
            if any(kw in message for kw in ['是的', '确认', '确定', '好的', 'yes', 'ok']):
                return self._execute_batch_update(db)
            else:
                self.conv_state.reset()
                return {
                    "type": "cancelled",
                    "message": "👌 已取消"
                }
        
        elif step == 3:  # 需要更多更新信息
            # 使用 LLM 解析用户输入的新字段
            parse_result = self._parse_update_fields(message, 'task')
            if parse_result:
                self.conv_state.pending_updates.update(parse_result)
                return self._execute_batch_update(db)
            else:
                return {
                    "type": "clarification",
                    "message": "❓ 请告诉我要更新成什么？例如：\n- '状态改为已完成'\n- '截止日期改到明天'\n- '标题改成XXX'"
                }
        
        return {
            "type": "error",
            "message": "❌ 对话状态异常"
        }
    
    def _handle_meeting_update_conversation(self, message: str, db: Session, step: int) -> dict:
        """处理会议更新的对话流程"""
        # 类似任务更新，简化版本
        if step == 2:  # 等待确认
            if any(kw in message for kw in ['是的', '确认', '确定', '好的']):
                return self._execute_batch_update(db)
            else:
                self.conv_state.reset()
                return {"type": "cancelled", "message": "👌 已取消"}
        
        return {"type": "error", "message": "❌ 会议更新功能开发中"}
    
    def _handle_member_update_conversation(self, message: str, db: Session, step: int) -> dict:
        """处理成员更新的对话流程"""
        if step == 2:  # 等待确认
            if any(kw in message for kw in ['是的', '确认', '确定', '好的']):
                return self._execute_batch_update(db)
            else:
                self.conv_state.reset()
                return {"type": "cancelled", "message": "👌 已取消"}
        
        return {"type": "error", "message": "❌ 成员更新功能开发中"}
    
    def _execute_batch_update(self, db: Session) -> dict:
        """执行批量更新"""
        targets = self.conv_state.target_records
        updates = self.conv_state.pending_updates
        operation = self.conv_state.operation
        
        if not targets:
            self.conv_state.reset()
            return {"type": "error", "message": "❌ 没有目标记录"}
        
        updated_count = 0
        try:
            for target in targets:
                # 更新字段
                for field, value in updates.items():
                    if hasattr(target, field):
                        setattr(target, field, value)
                
                # 更新时间戳
                if hasattr(target, 'updated_at'):
                    target.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                updated_count += 1
            
            db.commit()
            self.context_cache.invalidate()
            
            # 构建成功消息
            target_type = operation.replace('update_', '')
            success_msg = f"✅ 成功更新 {updated_count} 条{self._get_target_name(target_type)}！\n\n"
            
            # 显示更新详情
            for i, target in enumerate(targets[:3]):  # 最多显示3个
                success_msg += f"{i+1}. {self._format_record_info(target, target_type)}\n"
            
            if len(targets) > 3:
                success_msg += f"... 还有 {len(targets) - 3} 条\n"
            
            success_msg += f"\n更新内容：{self._format_changes(updates)}"
            
            self.conv_state.reset()
            
            return {
                "type": "updated",
                "message": success_msg
            }
            
        except Exception as e:
            db.rollback()
            chat_logger.error(f"批量更新失败: {str(e)}")
            self.conv_state.reset()
            return {
                "type": "error",
                "message": f"❌ 更新失败\n\n错误信息：{str(e)}"
            }
    
    # ===== 辅助方法 =====
    
    def _analyze_update_intent(self, message: str, entities: dict) -> dict:
        """分析更新意图 - 使用Schema信息"""
        # 获取所有表的schema信息
        schema_info = DatabaseSchema.get_all_schemas()
        
        system_prompt = f"""你是一个智能助手，分析用户的更新意图。

{schema_info}

请根据用户的自然语言描述，返回JSON格式：
{{
  "target_type": "task" 或 "meeting" 或 "member" 或 "document",
  "criteria": {{搜索条件字段}},
  "new_values": {{要更新的字段和值}}
}}

重要规则：
1. target_type 必须是上述四个类型之一
2. criteria 中的字段必须是 searchable_fields 中的
3. new_values 中的字段必须是 updatable_fields 中的
4. 只返回JSON，不要其他内容

示例：
用户："把张三的任务改成已完成"
返回：{{"target_type": "task", "criteria": {{"assignee": "张三"}}, "new_values": {{"status": "已完成"}}}}

用户："把明天的会议改到后天"
返回：{{"target_type": "meeting", "criteria": {{"date": "明天"}}, "new_values": {{"date": "后天"}}}}

用户："把邓然的邮箱改成dengran@example.com"
返回：{{"target_type": "member", "criteria": {{"name": "邓然"}}, "new_values": {{"email": "dengran@example.com"}}}}

用户："把所有待办任务改为进行中"
返回：{{"target_type": "task", "criteria": {{"status": "待办"}}, "new_values": {{"status": "进行中"}}}}

只返回JSON。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        result = self.llm.chat_completion(messages, temperature=0.3)
        if result:
            try:
                import json
                result = result.strip()
                if result.startswith("```"):
                    result = result.split("\n", 1)[-1]
                if result.endswith("```"):
                    result = result.rsplit("\n", 1)[0]
                parsed = json.loads(result.strip())
                
                # 验证 target_type
                if 'target_type' not in parsed:
                    chat_logger.warning("⚠️  缺少 target_type 字段")
                    return None
                
                # 验证字段是否在schema中
                target_type = parsed['target_type']
                schema = DatabaseSchema.get_table_schema(target_type)
                if schema:
                    # 验证 criteria 字段
                    if 'criteria' in parsed:
                        valid_criteria = {}
                        for field, value in parsed['criteria'].items():
                            if field in schema['searchable_fields']:
                                valid_criteria[field] = value
                            else:
                                chat_logger.warning(f"⚠️  无效搜索字段: {field}，已忽略")
                        parsed['criteria'] = valid_criteria
                    
                    # 验证 new_values 字段
                    if 'new_values' in parsed:
                        valid_updates = {}
                        for field, value in parsed['new_values'].items():
                            if field in schema['updatable_fields']:
                                valid_updates[field] = value
                            else:
                                chat_logger.warning(f"⚠️  无效更新字段: {field}，已忽略")
                        parsed['new_values'] = valid_updates
                
                return parsed
            except Exception as e:
                chat_logger.error(f"解析更新意图失败: {str(e)}")
                pass
        
        # Fallback: 使用简单规则
        return self._rule_based_update_analysis(message)
    
    def _rule_based_update_analysis(self, message: str) -> dict:
        """基于规则的更新意图分析（fallback）"""
        import re
        
        # 检测任务更新
        if '任务' in message:
            criteria = {}
            new_values = {}
            
            # 提取负责人
            assignee_match = re.search(r'(\S+)的任', message)
            if assignee_match:
                criteria['assignee'] = assignee_match.group(1)
            
            # 提取状态
            if '完成' in message:
                new_values['status'] = '已完成'
            elif '进行中' in message:
                new_values['status'] = '进行中'
            elif '待办' in message or '待处理' in message:
                new_values['status'] = '待办'
            
            if criteria and new_values:
                return {
                    "target_type": "task",
                    "criteria": criteria,
                    "new_values": new_values
                }
        
        return None
    
    def _find_targets(self, target_type: str, criteria: dict, db: Session) -> list:
        """查找目标记录"""
        if target_type == 'task':
            query = db.query(Task)
            if 'assignee' in criteria:
                query = query.filter(Task.assignee == criteria['assignee'])
            if 'status' in criteria:
                query = query.filter(Task.status == criteria['status'])
            if 'title' in criteria:
                query = query.filter(Task.title.contains(criteria['title']))
            return query.all()
        
        elif target_type == 'meeting':
            query = db.query(Meeting)
            if 'date' in criteria:
                query = query.filter(Meeting.date == criteria['date'])
            if 'title' in criteria:
                query = query.filter(Meeting.title.contains(criteria['title']))
            return query.all()
        
        elif target_type == 'member':
            query = db.query(TeamMember)
            if 'name' in criteria:
                query = query.filter(TeamMember.name == criteria['name'])
            if 'role' in criteria:
                query = query.filter(TeamMember.role == criteria['role'])
            return query.all()
        
        return []
    
    def _format_record_info(self, record, record_type: str) -> str:
        """格式化记录信息"""
        if record_type == 'task':
            return f"任务 #{record.id}: {record.title}\n   负责人: {record.assignee}\n   状态: {record.status}\n   截止: {record.deadline or '无'}"
        elif record_type == 'meeting':
            return f"会议 #{record.id}: {record.title}\n   时间: {record.date} {record.time}\n   参与者: {record.participants}"
        elif record_type == 'member':
            return f"成员 #{record.id}: {record.name}\n   角色: {record.role or '未设置'}\n   邮箱: {record.email or '未设置'}"
        return str(record)
    
    def _format_changes(self, updates: dict) -> str:
        """格式化更新内容"""
        if not updates:
            return "无更新"
        
        changes = []
        for field, value in updates.items():
            field_names = {
                'status': '状态',
                'deadline': '截止时间',
                'title': '标题',
                'assignee': '负责人',
                'date': '日期',
                'time': '时间',
                'role': '角色',
                'email': '邮箱'
            }
            cn_name = field_names.get(field, field)
            changes.append(f"{cn_name}: {value}")
        
        return "\n".join(changes)
    
    def _parse_update_fields(self, message: str, target_type: str) -> dict:
        """解析用户输入的更新字段 - 使用Schema信息"""
        # 获取目标表的schema
        schema = DatabaseSchema.get_table_schema(target_type)
        if not schema:
            chat_logger.error(f"未知的目标类型: {target_type}")
            return None
        
        # 构建包含schema信息的提示词
        schema_info = f"""【{schema['table']}表结构】
可更新字段：
"""
        for field, info in schema['fields'].items():
            if field in schema['updatable_fields']:
                desc = info['description']
                if 'values' in info:
                    desc += f" (可选值: {', '.join(info['values'])})"
                schema_info += f"- {field}: {desc}\n"
        
        system_prompt = f"""你是一个智能助手，分析用户想要更新{target_type}的哪些字段。

{schema_info}

请根据用户的自然语言描述，提取要更新的字段和值。
返回JSON格式：{{"field_name": "new_value"}}

示例：
用户："状态改为已完成"
返回：{{"status": "已完成"}}

用户："截止日期改到明天"
返回：{{"deadline": "明天"}}

用户："邮箱改成zhangsan@example.com"
返回：{{"email": "zhangsan@example.com"}}

用户："角色改为高级测试工程师"
返回：{{"role": "高级测试工程师"}}

只返回JSON，不要其他内容。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        result = self.llm.chat_completion(messages, temperature=0.3)
        if result:
            try:
                import json
                result = result.strip()
                if result.startswith("```"):
                    result = result.split("\n", 1)[-1]
                if result.endswith("```"):
                    result = result.rsplit("\n", 1)[0]
                parsed = json.loads(result.strip())
                
                # 验证字段是否在schema中
                validated = {}
                for field, value in parsed.items():
                    if field in schema['updatable_fields']:
                        validated[field] = value
                    else:
                        chat_logger.warning(f"⚠️  无效字段: {field}，已忽略")
                
                return validated if validated else None
            except Exception as e:
                chat_logger.error(f"解析更新字段失败: {str(e)}")
                pass
        
        return None
    
    def _get_target_name(self, target_type: str) -> str:
        """获取目标的中文名称"""
        names = {
            'task': '任务',
            'meeting': '会议',
            'member': '成员'
        }
        return names.get(target_type, '记录')
