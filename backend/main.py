from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
import uvicorn
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, SessionLocal, Base
from backend.models import Task, Meeting, Document, TeamMember, TeamNote
from backend.agent import TeamAgent

Base.metadata.create_all(bind=engine)

app = FastAPI(title="TeamRobert API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = TeamAgent()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatRequest(BaseModel):
    message: str

class TaskCreate(BaseModel):
    title: str
    assignee: str
    deadline: str = None
    priority: str = "中"

class MeetingCreate(BaseModel):
    title: str
    date: str
    time: str
    participants: str = ""
    location: str = ""

class NoteCreate(BaseModel):
    author: str
    content: str

@app.get("/")
def read_root():
    return {"message": "欢迎使用 TeamRobert API", "version": "1.0.0"}

@app.post("/api/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """智能对话接口"""
    response = agent.handle_message(request.message, db)
    return response

@app.get("/api/tasks", response_model=List[dict])
def get_tasks(db: Session = Depends(get_db)):
    """获取所有任务"""
    tasks = db.query(Task).order_by(Task.created_at.desc()).all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "assignee": t.assignee,
            "status": t.status,
            "priority": t.priority,
            "deadline": t.deadline,
            "created_at": t.created_at
        }
        for t in tasks
    ]

@app.post("/api/tasks")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """创建任务"""
    new_task = Task(
        title=task.title,
        assignee=task.assignee,
        deadline=task.deadline,
        priority=task.priority
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return {"status": "success", "task_id": new_task.id}

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    db.delete(task)
    db.commit()
    return {"status": "success"}

@app.put("/api/tasks/{task_id}")
def update_task_status(task_id: int, status_update: dict, db: Session = Depends(get_db)):
    """更新任务状态"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    new_status = status_update.get("status")
    if new_status:
        task.status = new_status
        task.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        db.commit()
        db.refresh(task)
    
    return {
        "status": "success",
        "task": {
            "id": task.id,
            "title": task.title,
            "status": task.status,
            "updated_at": task.updated_at
        }
    }

@app.get("/api/meetings")
def get_meetings(db: Session = Depends(get_db)):
    """获取所有会议"""
    meetings = db.query(Meeting).order_by(Meeting.date).all()
    return [
        {
            "id": m.id,
            "title": m.title,
            "date": m.date,
            "time": m.time,
            "participants": m.participants,
            "location": m.location
        }
        for m in meetings
    ]

@app.post("/api/meetings")
def create_meeting(meeting: MeetingCreate, db: Session = Depends(get_db)):
    """创建会议"""
    new_meeting = Meeting(
        title=meeting.title,
        date=meeting.date,
        time=meeting.time,
        participants=meeting.participants,
        location=meeting.location
    )
    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)
    return {"status": "success", "meeting_id": new_meeting.id}

@app.delete("/api/meetings/{meeting_id}")
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """删除会议"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")
    db.delete(meeting)
    db.commit()
    return {"status": "success"}

@app.get("/api/documents")
def get_documents(db: Session = Depends(get_db)):
    """获取所有文档"""
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "type": d.type,
            "owner": d.owner,
            "created_at": d.created_at
        }
        for d in docs
    ]

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """获取统计数据"""
    tasks = db.query(Task).all()
    return {
        "total": len(tasks),
        "completed": sum(1 for t in tasks if t.status == "已完成"),
        "in_progress": sum(1 for t in tasks if t.status == "进行中"),
        "pending": sum(1 for t in tasks if t.status == "待办")
    }

@app.get("/api/notes")
def get_notes(db: Session = Depends(get_db)):
    """获取所有团队笔记"""
    notes = db.query(TeamNote).order_by(TeamNote.created_at.desc()).all()
    return [
        {
            "id": n.id,
            "author": n.author,
            "content": n.content,
             "created_at": n.created_at.strftime("%Y-%m-%d %H:%M") if n.created_at else None
        }
        for n in notes
    ]

@app.post("/api/notes")
def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    """创建团队笔记"""
    new_note = TeamNote(
        author=note.author,
        content=note.content
    )
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return {"status": "success", "note_id": new_note.id}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
