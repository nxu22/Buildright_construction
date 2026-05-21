import { useState } from 'react'
import ChatWidget from './components/ChatWidget'
import './App.css'

export default function App() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <span className="brand-mark">◈</span>
          <span className="brand-name">BuildRight</span>
        </div>
        <p className="tagline">Renovation experts in the GTA</p>
      </header>

      <main className="main">
        <h1>Renovate with confidence.</h1>
        <p>Get instant answers about timelines, pricing, and process — or book a free consultation.</p>
        <button className="open-chat-btn" onClick={() => setIsOpen(true)}>
          Start a conversation
        </button>
      </main>

      {!isOpen && (
        <button
          className="chat-fab"
          onClick={() => setIsOpen(true)}
          aria-label="Open chat"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path
              d="M20 2H4C2.9 2 2 2.9 2 4v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"
              fill="currentColor"
            />
          </svg>
        </button>
      )}

      {isOpen && <ChatWidget onClose={() => setIsOpen(false)} />}
    </div>
  )
}
