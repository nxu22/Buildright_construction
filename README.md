# BuildRight Renovations - AI AGENT

This is a full-stack AI chatbot demo built with [React](https://react.dev/) + [FastAPI](https://fastapi.tiangolo.com/), powered by [Claude](https://www.anthropic.com/) and RAG (ChromaDB + sentence-transformers).

## What this is

A full-stack AI AGENT built for a fictional residential renovation company in the Greater Toronto Area. Potential clients land on the page, ask questions about services and pricing, get instant AI-powered answers, and leave their contact details -- at which point the business owner receives a summarized lead email automatically.

Built as a portfolio project to demonstrate conversational AI integration, lead capture, and modern web deployment.

---

## How it works

1. User visits the Netlify frontend and opens the chat widget
2. React sends each message to the FastAPI backend on Railway
3. The backend uses RAG (ChromaDB + sentence-transformers) to retrieve relevant FAQ context, then calls Claude to generate a conversational reply
4. After the first exchange, an inline form collects the user name and email -- the client gets a confirmation email instantly via Resend
5. When the user leaves (close button, tab close, or browser close) a beacon request fires and the owner receives an AI-summarized lead email with the full transcript

---

## Features

- **Conversational AI** -- multi-turn chat powered by Claude (claude-sonnet-4), grounded in a custom renovation FAQ knowledge base via RAG
- **Instant quote estimates** -- kitchen, bathroom, basement, or flooring costs with basic / standard / premium tiers
- **Lead capture** -- inline contact form; client gets a confirmation email, owner gets an AI-summarized lead email
- **Reliable lead delivery** -- navigator.sendBeacon on page exit captures leads even when the user closes the browser tab without clicking the close button
- **Duplicate prevention** -- client-side in-flight lock + server-side 2-minute session dedup so the owner receives exactly one email per conversation
- **Hand-drawn UI** -- Caveat handwritten font, coral/mint/forest-green palette, SVG house and tool sketches

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite, deployed on Netlify |
| Backend | FastAPI (Python), deployed on Railway |
| AI / LLM | Anthropic Claude via LangChain |
| Vector search | ChromaDB + sentence-transformers (all-MiniLM-L6-v2) |
| Email | Resend (custom domain buildrightca.space) |

---

## Local development

First, run the backend server:

```bash
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

Then, in a separate terminal, run the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) with your browser to see the result.

You can start editing the frontend by modifying `frontend/src/App.jsx`. The page auto-updates as you edit the file.

The FastAPI backend lives in `api.py` and the chatbot logic in `faq_chatbot.py`.

## Live Demo

- **Frontend:** [buildrightforconstruction.netlify.app](https://buildrightforconstruction.netlify.app/)
- **Backend API:** [buildrightconstruction-production.up.railway.app](https://buildrightconstruction-production.up.railway.app/)

## Learn More

To learn more about the technologies used:

- [React Documentation](https://react.dev/learn)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [Resend Documentation](https://resend.com/docs)

## Deploy

- Frontend is deployed on [Netlify](https://www.netlify.com/)
- Backend is deployed on [Railway](https://railway.app/)
