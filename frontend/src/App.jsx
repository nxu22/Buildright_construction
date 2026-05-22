import { useState } from 'react'
import ChatWidget from './components/ChatWidget'
import './App.css'

const WavyDivider = () => (
  <svg viewBox="0 0 1200 60" preserveAspectRatio="none" className="wavy-divider" aria-hidden="true">
    <path d="M0,30 C150,60 350,0 600,30 C850,60 1050,0 1200,30 L1200,60 L0,60 Z" />
  </svg>
)

const HouseSketch = () => (
  <svg width="140" height="120" viewBox="0 0 140 120" fill="none" className="deco-house" aria-hidden="true">
    <path d="M12,68 L12,108 L128,108 L128,68" stroke="#2D5016" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M4,72 L70,18 L136,72" stroke="#2D5016" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round"/>
    <rect x="54" y="76" width="32" height="32" rx="2" stroke="#E8735A" strokeWidth="3" strokeLinecap="round"/>
    <rect x="28" y="74" width="20" height="18" rx="2" stroke="#7BC8A4" strokeWidth="2.5" strokeLinecap="round"/>
    <line x1="28" x2="48" y1="83" y2="83" stroke="#7BC8A4" strokeWidth="2" strokeLinecap="round"/>
    <line x1="38" y1="74" x2="38" y2="92" stroke="#7BC8A4" strokeWidth="2" strokeLinecap="round"/>
    <path d="M95,74 L112,74 L112,92 L95,92" stroke="#7BC8A4" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M70,18 L70,8" stroke="#2D5016" strokeWidth="3" strokeLinecap="round"/>
    <circle cx="70" cy="5" r="4" fill="#E8735A"/>
  </svg>
)

const HammerSketch = () => (
  <svg width="52" height="52" viewBox="0 0 52 52" fill="none" className="deco-tool" aria-hidden="true">
    <rect x="28" y="8" width="16" height="10" rx="2" stroke="#2D5016" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
    <line x1="28" y1="13" x2="10" y2="40" stroke="#2D5016" strokeWidth="2.5" strokeLinecap="round"/>
    <line x1="8" y1="38" x2="14" y2="44" stroke="#E8735A" strokeWidth="2.5" strokeLinecap="round"/>
  </svg>
)

const RulerSketch = () => (
  <svg width="52" height="52" viewBox="0 0 52 52" fill="none" className="deco-tool" aria-hidden="true">
    <rect x="6" y="20" width="40" height="12" rx="2" stroke="#2D5016" strokeWidth="2.5" strokeLinecap="round"/>
    <line x1="13" y1="20" x2="13" y2="26" stroke="#2D5016" strokeWidth="2" strokeLinecap="round"/>
    <line x1="20" y1="20" x2="20" y2="24" stroke="#2D5016" strokeWidth="2" strokeLinecap="round"/>
    <line x1="27" y1="20" x2="27" y2="26" stroke="#2D5016" strokeWidth="2" strokeLinecap="round"/>
    <line x1="34" y1="20" x2="34" y2="24" stroke="#2D5016" strokeWidth="2" strokeLinecap="round"/>
  </svg>
)

const StarSketch = () => (
  <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden="true">
    <path d="M14,3 L16,11 L24,11 L18,16 L20,24 L14,19 L8,24 L10,16 L4,11 L12,11 Z"
      stroke="#E8735A" strokeWidth="2" strokeLinejoin="round" fill="#E8735A" fillOpacity="0.18"/>
  </svg>
)

const services = [
  { icon: '🪟', label: 'Kitchen Remodels', desc: 'Full gut to cabinet refresh — we do it all.' },
  { icon: '🛁', label: 'Bathrooms', desc: 'Tile work, vanities, the whole spa dream.' },
  { icon: '🪜', label: 'Basements', desc: 'Rec rooms, home offices, hidden dens.' },
  { icon: '🌿', label: 'Flooring & More', desc: 'Hardwood, tile, trim — the finishing touches.' },
]

export default function App() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="app">

      {/* ── Nav ── */}
      <header className="nav">
        <div className="nav-brand">
          <span className="nav-mark">◈</span>
          <span className="nav-name">BuildRight</span>
        </div>
        <span className="nav-tag">GTA's friendliest renovation crew</span>
      </header>

      {/* ── Hero ── */}
      <section className="hero">
        <div className="hero-deco-left">
          <HouseSketch />
        </div>

        <div className="hero-content">
          <p className="hero-eyebrow">Hello, neighbour 👋</p>
          <h1 className="hero-headline">
            We build the rooms<br/>you'll actually want<br/>to live in.
          </h1>
          <p className="hero-sub">
            No scary surprises. Just honest numbers and good work.
          </p>
          <button className="cta-btn" onClick={() => setIsOpen(true)}>
            Curious what it'll cost? Let's chat
          </button>
        </div>

        <div className="hero-deco-right">
          <div className="deco-blob" />
        </div>
      </section>

      <WavyDivider />

      {/* ── Services ── */}
      <section className="services">
        <div className="services-header">
          <HammerSketch />
          <h2 className="section-title">What we're good at</h2>
          <RulerSketch />
        </div>
        <div className="services-grid">
          {services.map(s => (
            <div className="service-card" key={s.label}>
              <span className="service-icon">{s.icon}</span>
              <h3 className="service-name">{s.label}</h3>
              <p className="service-desc">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Trust strip ── */}
      <section className="trust">
        <div className="trust-inner">
          <div className="trust-item">
            <StarSketch />
            <span>Licensed &amp; insured</span>
          </div>
          <div className="trust-divider" />
          <div className="trust-item">
            <StarSketch />
            <span>Free consultations</span>
          </div>
          <div className="trust-divider" />
          <div className="trust-item">
            <StarSketch />
            <span>GTA-based, family-run</span>
          </div>
        </div>
      </section>

      {/* ── CTA section ── */}
      <section className="cta-section">
        <div className="cta-box">
          <h2 className="cta-title">Ready to get started?</h2>
          <p className="cta-body">
            Tell our assistant what you're dreaming about — kitchen, bathroom,
            basement, flooring — and we'll come back with a real number, not a runaround.
          </p>
          <button className="cta-btn cta-btn--dark" onClick={() => setIsOpen(true)}>
            Start the conversation →
          </button>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="footer">
        <span className="nav-mark">◈</span>
        <span>BuildRight Renovations · Greater Toronto Area</span>
      </footer>

      {/* ── Chat FAB ── */}
      {!isOpen && (
        <button className="chat-fab" onClick={() => setIsOpen(true)} aria-label="Open chat">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M20 2H4C2.9 2 2 2.9 2 4v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" fill="currentColor"/>
          </svg>
        </button>
      )}

      {isOpen && <ChatWidget onClose={() => setIsOpen(false)} />}
    </div>
  )
}
