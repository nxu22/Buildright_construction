import { useState, useRef, useEffect } from 'react'

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
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping, showLead])

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

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
        // Show lead form after the very first exchange (welcome + user + bot = 3 msgs)
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
    const summary = messages
      .slice(-8)
      .map(m => `${m.role === 'user' ? 'Client' : 'Agent'}: ${m.content}`)
      .join('\n')
    try {
      await fetch(`${API_URL}/submit-lead`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: leadName,
          email: leadEmail,
          conversation_summary: summary,
        }),
      })
    } catch {
      // best-effort
    }
    setLeadDone(true)
    setShowLead(false)
    setMessages(prev => [
      ...prev,
      {
        role: 'assistant',
        content: `Thanks, ${leadName}! We've got your details and will follow up at ${leadEmail} within one business day. Looking forward to talking about your project!`,
      },
    ])
  }


  return (
    <div className="cw">
      {/* Header */}
      <div className="cw-header">
        <div className="cw-header-left">
          <span className="cw-dot" />
          <span className="cw-title">BuildRight</span>
        </div>
        <button className="cw-close" onClick={onClose} aria-label="Close">
          ×
        </button>
      </div>

      {/* Messages */}
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

        {/* Lead form inline */}
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

      {/* Input area */}
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
