# FinVox: AI-Powered SME Financial Advisory System 🎙️📊

**FinVox** is a Conversational Voice & Chat Multi-Agent Platform designed specifically for Small and Medium Enterprises (SMEs) in Sri Lanka. It acts as an intelligent, real-time financial consultant, allowing SME owners to manage cash flow, analyze investments, and make data-driven decisions using natural voice or text interactions.

## 🚀 Key Features

- **Voice & Chat Interface:** Communicate naturally via text or voice (powered by OpenAI Whisper / Deepgram STT and ElevenLabs TTS). Built with support for code-mixed Sri Lankan English.
- **Multi-Agent AI Core:** Powered by LangGraph, coordinating specialized AI agents:
  - 🧠 *Orchestrator Agent:* Routes queries to the appropriate specialist.
  - 📄 *Document Parser Agent:* Extracts structured data from CSV, Excel, and PDF invoices.
  - 📈 *Cash Flow Forecast Agent:* Predicts 30/60/90-day liquidity and cash flow.
  - 🌍 *Market Research Agent:* Fetches real-time market data (Yahoo Finance, CSE, CBSL).
  - 💼 *Investment Advisor Agent:* Recommends allocations for surplus capital.
  - 📑 *Report Generator Agent:* Creates downloadable PDF financial health summaries.
- **Data Intelligence (RAG):** Securely processes uploaded financial documents using Retrieval-Augmented Generation, anchored by a Qdrant Vector Database.
- **Real-Time Responsiveness:** Designed for ultra-low latency voice interactions using WebRTC via LiveKit.

## 🛠️ Technology Stack

- **Frontend:** React.js + Tailwind CSS
- **Backend:** FastAPI (Python)
- **AI Framework:** LangGraph
- **Vector Database:** Qdrant Cloud
- **State Database:** Supabase (PostgreSQL)
- **LLM Routing:** OpenRouter (OpenAI, Anthropic, Groq)
- **Voice Pipeline:** LiveKit, Deepgram, ElevenLabs

## 🎓 Academic Context

This project is developed by **Dinod Imanjith Withanawasam** (Student ID: KD/BSCSD/21/28 | Cardiff Met ID: st20312099) as part of the BSc (Hons) in Software Engineering program.

---
*Empowering Sri Lankan SMEs with accessible, real-time decision intelligence.*
