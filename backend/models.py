from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import Base

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    assignee = Column(String(100), nullable=False)
    status = Column(String(20), default="待办")
    priority = Column(String(20), default="中")
    deadline = Column(String(50), nullable=True)
    created_at = Column(String(50), default=datetime.now().strftime("%Y-%m-%d %H:%M"))
    updated_at = Column(String(50), default=datetime.now().strftime("%Y-%m-%d %H:%M"))

class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    date = Column(String(50), nullable=False)
    time = Column(String(50), nullable=False)
    participants = Column(String(500), nullable=True)
    location = Column(String(200), nullable=True)
    agenda = Column(Text, nullable=True)
    created_at = Column(String(50), default=datetime.now().strftime("%Y-%m-%d %H:%M"))

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=True)
    url = Column(String(500), nullable=True)
    owner = Column(String(100), nullable=False)
    created_at = Column(String(50), default=datetime.now().strftime("%Y-%m-%d %H:%M"))

class TeamMember(Base):
    __tablename__ = "team_members"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    role = Column(String(100), nullable=True)
    email = Column(String(200), nullable=True)
    created_at = Column(String(50), default=datetime.now().strftime("%Y-%m-%d %H:%M"))

class TeamNote(Base):
    __tablename__ = "team_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    author = Column(String(100), nullable=False)  # 作者姓名
    content = Column(Text, nullable=False)  # 笔记内容
    created_at = Column(DateTime, default=datetime.now)
