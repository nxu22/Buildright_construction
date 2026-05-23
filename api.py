"""
BuildRight Renovations — Chatbot API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime, timezone, timedelta
import resend
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="BuildRight Renovations Chatbot API")

# CORS — allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to your Netlify domain after deploy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# initialize chatbot once at startup
from faq_chatbot import BuildRightChatbot

print("Initializing chatbot...")
chatbot = BuildRightChatbot(
    data_path="construction_faq.json"
)
print("Chatbot ready.")


# ── Server-side dedup ────────────────────────────────
# Maps session_id → datetime of last successful send.
# Cleared on restart (acceptable for Railway single-instance).
# If you move to multi-instance, replace with Redis.
_sent_sessions: dict[str, datetime] = {}
_DEDUP_WINDOW = timedelta(minutes=2)

def _prune_and_check(session_id: str) -> bool:
    """
    Prune stale entries, then return True if this session_id was sent
    within the dedup window (meaning: skip this send).
    """
    if not session_id:
        return False  # no session_id → never deduplicate
    now = datetime.now(timezone.utc)
    cutoff = now - _DEDUP_WINDOW
    stale = [k for k, v in _sent_sessions.items() if v < cutoff]
    for k in stale:
        del _sent_sessions[k]
    last = _sent_sessions.get(session_id)
    return last is not None and (now - last) < _DEDUP_WINDOW

# ── Data models ──────────────────────────────────────

class Message(BaseModel):
    role: str   # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []

class LeadRequest(BaseModel):
    name: str
    email: str
    conversation_summary: str
    session_id: str = ""  # empty string = skip dedup (old clients / sendBeacon fallback)

class RegisterLeadRequest(BaseModel):
    name: str
    email: str

class QuoteRequest(BaseModel):
    project_type: str   # kitchen | bathroom | basement | full_renovation
    sqft: float
    tier: str           # basic | standard | premium


# ── Routes ──────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "message": "BuildRight Renovations Chatbot API is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/debug-email")
def debug_email():
    """Temporary: confirm env vars are set without exposing values. DELETE before going public."""
    return {
        "RESEND_API_KEY": "set" if os.getenv("RESEND_API_KEY") else "MISSING",
        "FROM_EMAIL":     os.getenv("FROM_EMAIL") or "MISSING (will fall back to onboarding@resend.dev sandbox — client emails will fail)",
        "OWNER_EMAIL":    "set" if os.getenv("OWNER_EMAIL") else "MISSING",
    }

@app.post("/chat")
def chat(req: ChatRequest):
    """Main chat endpoint"""
    try:
        history = [{"role": m.role, "content": m.content} for m in req.history]
        result = chatbot.chat_with_history(req.message, history)
        return {
            "reply": result["answer"],
            "source_questions": result["source_questions"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/register-lead")
def register_lead(req: RegisterLeadRequest):
    """Send client a confirmation email immediately when they submit their contact info."""
    print(f"Registering lead: {req.name} | {req.email}")

    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("FROM_EMAIL")

    if not api_key:
        raise HTTPException(status_code=500, detail="RESEND_API_KEY is not configured")
    if not from_email:
        raise HTTPException(status_code=500, detail="FROM_EMAIL is not configured — cannot send from sandbox to arbitrary clients")

    resend.api_key = api_key
    result = resend.Emails.send({
        "from": from_email,
        "to": req.email,
        "subject": "Thanks for reaching out — BuildRight Renovations",
        "html": f"""
<h2>Hi {req.name}, thanks for connecting!</h2>
<p>We received your message through the BuildRight virtual assistant.</p>
<p>A member of our team will follow up with you within <b>one business day</b> to discuss your project.</p>
<p>In the meantime, feel free to reply to this email with any additional details about what you have in mind.</p>
<br>
<p>— The BuildRight Team</p>
<p style="color:#888;font-size:12px">BuildRight Renovations &middot; GTA's trusted renovation experts</p>
""",
    })
    print(f"Client email sent: {result}")
    return {"success": True, "resend_id": getattr(result, 'id', str(result))}


@app.post("/submit-lead")
def submit_lead(req: LeadRequest):
    """Send AI-summarized lead email to owner. Deduplicates by session_id."""
    print(f"Lead received: {req.name} | {req.email} | session={req.session_id or 'none'}")

    if _prune_and_check(req.session_id):
        print(f"Dedup: session {req.session_id} already sent within window, skipping")
        return {"success": True, "deduped": True}

    # Record timestamp before sending so a concurrent request arriving
    # while the email is being built also hits the dedup check
    if req.session_id:
        _sent_sessions[req.session_id] = datetime.now(timezone.utc)

    api_key = os.getenv("RESEND_API_KEY")
    owner_email = os.getenv("OWNER_EMAIL")
    from_email = os.getenv("FROM_EMAIL")

    if not api_key:
        raise HTTPException(status_code=500, detail="RESEND_API_KEY is not configured")
    if not owner_email:
        raise HTTPException(status_code=500, detail="OWNER_EMAIL is not configured")
    if not from_email:
        raise HTTPException(status_code=500, detail="FROM_EMAIL is not configured")

    ai_summary = chatbot.summarize_conversation(req.conversation_summary)
    print(f"AI summary generated:\n{ai_summary}")

    submitted_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    resend.api_key = api_key
    result = resend.Emails.send({
        "from": from_email,
        "to": owner_email,
        "subject": f"New Lead from BuildRight Assistant — {req.name}",
        "html": f"""
<h2>New lead from BuildRight chatbot</h2>
<table cellpadding="6">
  <tr><td><b>Name</b></td><td>{req.name}</td></tr>
  <tr><td><b>Email</b></td><td><a href="mailto:{req.email}">{req.email}</a></td></tr>
  <tr><td><b>Submitted</b></td><td>{submitted_at}</td></tr>
</table>
<h3>What the client wants</h3>
<div style="background:#f5f5f5;padding:14px;border-radius:6px;white-space:pre-wrap">{ai_summary}</div>
<h3 style="margin-top:24px;color:#888;font-size:13px">Full transcript</h3>
<pre style="background:#fafafa;padding:12px;border-radius:6px;font-size:12px;color:#555">{req.conversation_summary}</pre>
""",
    })
    print(f"Owner email sent: {result}")
    return {"success": True, "resend_id": getattr(result, 'id', str(result))}


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


