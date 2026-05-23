import { useState, useRef, useEffect, useCallback } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const WELCOME = {
  role: 'assistant',
  content: "Hi! I'm the BuildRight virtual assistant 👋 I can answer questions about our renovation services, timelines, pricing, and more. What can I help you with today?",
}

export default function ChatWidget({ onClose }) {
  const [messages, setMessages] = useState([WELCOME])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [showLead, setShowLead] = useState(false)
  const [leadName, setLeadName] = useState('')
  const [leadEmail, setLeadEmail] = useState('')
  const [leadDone, setLeadDone] = useState(false)
  const [leadInfo, setLeadInfo] = useState(null)

  const bottomRef   = useRef(null)
  const inputRef    = useRef(null)
  const messagesRef = useRef(messages)          // always-current transcript
  const leadInfoRef = useRef(null)              // always-current leadInfo for listeners
  const leadSentRef = useRef(false)             // client-side in-flight lock
  const sessionId   = useRef(crypto.randomUUID()) // stable per widget mount

  // Keep refs in sync with state
  useEffect(() => { messagesRef.current = messages }, [messages])
  useEffect(() => { leadInfoRef.current = leadInfo },  [leadInfo])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping, showLead])

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // ── Core send function ──────────────────────────────
  // useBeacon=true  → navigator.sendBeacon (survives tab/page close)
  // useBeacon=false → fetch (for normal close-button path)
  // Client guard: leadSentRef prevents concurrent/duplicate fires from the
  // same browser regardless of which trigger fires first.
  const sendOwnerEmail = useCallback((useBeacon = false) => {
    const info = leadInfoRef.current
    if (!info) return                 // no lead captured yet — nothing to send
    if (leadSentRef.current) return   // already sent or in-flight — bail
    leadSentRef.current = true        // lock before any async work

    const transcript = messagesRef.current
      .map(m => `${m.role === 'user' ? 'Client' : 'Agent'}: ${m.content}`)
      .join('\n')

    const payload = JSON.stringify({
      name:                 info.name,
      email:                info.email,
      conversation_summary: transcript,
      session_id:           sessionId.current,
    })

    const url = `${API_URL}/submit-lead`

    if (useBeacon) {
      // sendBeacon survives page close; Blob sets Content-Type: application/json
      // which FastAPI parses identically to a regular fetch POST
      navigator.sendBeacon(url, new Blob([payload], { type: 'application/json' }))
    } else {
      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: payload,
      }).catch(() => {}) // best-effort; errors are swallowed intentionally
    }
  }, []) // stable: reads only from refs and module-level constant

  // ── Page-exit listeners ─────────────────────────────
  // visibilitychange fires when user switches tabs or closes the browser.
  // beforeunload fires just before the page unloads.
  // Both use beacon so the request survives the page lifecycle.
  // leadSentRef ensures only the first trigger that fires actually sends.
  useEffect(() => {
    const onHide = () => {
      if (document.visibilityState === 'hidden') sendOwnerEmail(true)
    }
    const onUnload = () => sendOwnerEmail(true)

    document.addEventListener('visibilitychange', onHide)
    window.addEventListener('beforeunload', onUnload)
    return () => {
      document.removeEventListener('visibilitychange', onHide)
      window.removeEventListener('beforeunload', onUnload)
    }
  }, [sendOwnerEmail])

  // ── Chat logic ──────────────────────────────────────
  const send = async () => {
    const text = input.trim()
    if (!text || isTyping) return

    const next = [...messages, { role: 'user', content: text }]
    setMessages(next)
    setInput('')
    setIsTyping(true)

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          history: messages.map(m => ({ role: m.role, content: m.content })),
        }),
      })
      if (!res.ok) throw new Error()
      const data = await res.json()
      const botMsg = { role: 'assistant', content: data.reply }
      setMessages(prev => {
        const updated = [...prev, botMsg]
        const userCount = updated.filter(m => m.role === 'user').length
        if (userCount === 1 && !leadDone) {
          setTimeout(() => setShowLead(true), 600)
        }
        return updated
      })
    } catch {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Sorry, something went wrong. Please try again in a moment.' },
      ])
    } finally {
      setIsTyping(false)
    }
  }

  const onKeyDown = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  const submitLead = async () => {
    if (!leadName.trim() || !leadEmail.trim()) return
    const info = { name: leadName, email: leadEmail }
    setLeadInfo(info)
    setLeadDone(true)
    setShowLead(false)
    try {
      await fetch(`${API_URL}/register-lead`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(info),
      })
    } catch {
      // best-effort
    }
    setMessages(prev => [
      ...prev,
      {
        role: 'assistant',
        content: `Thanks, ${leadName}! We've sent a confirmation to ${leadEmail} and will follow up within one business day. Feel free to keep asking questions!`,
      },
    ])
  }

  // Close button: use fetch (page is still alive), then unmount
  const handleClose = useCallback(() => {
    sendOwnerEmail(false)
    onClose()
  }, [sendOwnerEmail, onClose])

  // ── Render ──────────────────────────────────────────
  return (
    <div className="cw">
      <div className="cw-header">
        <div className="cw-header-left">
          <span className="cw-dot" />
          <span className="cw-title">BuildRight</span>
        </div>
        <button className="cw-close" onClick={handleClose} aria-label="Close">
          ×
        </button>
      </div>

      <div className="cw-body">
        {messages.map((msg, i) => (
          <div key={i} className={`msg-row ${msg.role}`}>
            {msg.role === 'assistant' && <div className="avatar">BR</div>}
            <div className={`bubble ${msg.role}`}>{msg.content}</div>
          </div>
        ))}

        {isTyping && (
          <div className="msg-row assistant">
            <div className="avatar">BR</div>
            <div className="bubble assistant typing">
              <span /><span /><span />
            </div>
          </div>
        )}

        {showLead && !leadDone && (
          <div className="lead-card">
            <p className="lead-title">Let us follow up with you</p>
            <input
              className="lead-input"
              placeholder="Your name"
              value={leadName}
              onChange={e => setLeadName(e.target.value)}
            />
            <input
              className="lead-input"
              placeholder="Your email"
              type="email"
              value={leadEmail}
              onChange={e => setLeadEmail(e.target.value)}
            />
            <div className="lead-btns">
              <button className="lead-submit" onClick={submitLead}>Submit</button>
              <button className="lead-skip" onClick={() => { setShowLead(false); setLeadDone(true) }}>
                Skip
              </button>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="cw-footer">
        <div className="input-row">
          <textarea
            ref={inputRef}
            className="chat-input"
            placeholder="Ask a question…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            rows={1}
            disabled={isTyping}
          />
          <button
            className="send-btn"
            onClick={send}
            disabled={!input.trim() || isTyping}
            aria-label="Send"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" fill="currentColor" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
