"""
BuildRight Renovations — Chatbot API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime, timezone
import resend
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="BuildRight Renovations Chatbot API")

# CORS — 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 部署后改成你的 Netlify 域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动时初始化一次 chatbot（避免每次请求都重新加载）
from faq_chatbot import BuildRightChatbot

print("正在初始化聊天机器人...")
chatbot = BuildRightChatbot(
    data_path="construction_faq.json"
)
print("初始化完成！")


# ── 数据模型 ──────────────────────────────────────

class Message(BaseModel):
    role: str   # "user" 或 "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []

class LeadRequest(BaseModel):
    name: str
    email: str
    conversation_summary: str

class QuoteRequest(BaseModel):
    project_type: str   # kitchen | bathroom | basement | full_renovation
    sqft: float
    tier: str           # basic | standard | premium


# ── 路由 ──────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "message": "BuildRight Renovations Chatbot API is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/chat")
def chat(req: ChatRequest):
    """主要对话接口"""
    try:
        history = [{"role": m.role, "content": m.content} for m in req.history]
        result = chatbot.chat_with_history(req.message, history)
        return {
            "reply": result["answer"],
            "source_questions": result["source_questions"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/submit-lead")
def submit_lead(req: LeadRequest):
    """Collect lead info and send email notifications via Resend."""
    print(f"New lead: {req.name} | {req.email}")

    api_key = os.getenv("RESEND_API_KEY")
    owner_email = os.getenv("OWNER_EMAIL")
    from_email = os.getenv("FROM_EMAIL", "onboarding@resend.dev")

    if api_key and owner_email:
        try:
            resend.api_key = api_key
            submitted_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

            _send_owner_email(req, owner_email, from_email, submitted_at)
        except Exception as e:
            print(f"Email error: {e}")

    return {"success": True, "message": "Got it! We'll be in touch within one business day."}


@app.post("/quote")
def quote(req: QuoteRequest):
    """Return a rough cost estimate for a renovation project"""
    try:
        result = chatbot.estimate_quote(req.project_type, req.sqft, req.tier)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _send_owner_email(req: LeadRequest, owner_email: str, from_email: str, submitted_at: str):
    resend.Emails.send({
        "from": from_email,
        "to": owner_email,
        "subject": f"New Lead from BuildRight Assistant — {req.name}",
        "html": f"""
<h2>New lead from BuildRight chatbot</h2>
<table>
  <tr><td><b>Name</b></td><td>{req.name}</td></tr>
  <tr><td><b>Email</b></td><td>{req.email}</td></tr>
  <tr><td><b>Submitted</b></td><td>{submitted_at}</td></tr>
</table>
<h3>Conversation summary</h3>
<pre style="background:#f5f5f5;padding:12px;border-radius:6px">{req.conversation_summary}</pre>
""",
    })
