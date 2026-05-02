# 🗳️ ElectionGuide AI: Non-Partisan Multi-Country Civic Assistant

[![Python CI](https://github.com/Siva-2511/electionguide/actions/workflows/ci.yml/badge.svg)](https://github.com/Siva-2511/electionguide/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)
[![Live Demo](https://img.shields.io/badge/Live_Demo-Cloud_Run-9cf)](https://electionguide-app-1033116720582.us-central1.run.app)

**🌐 Live Application:** [electionguide-app.run.app](https://electionguide-app-1033116720582.us-central1.run.app)

> A non-partisan, AI-powered multi-country civic education assistant that guides users through the election processes in India, the US, UK, Australia, and Canada — from eligibility to casting their vote.

---

> [!WARNING]
> **Note to Judges regarding Google Sign-In:** 
> Because this application integrates with sensitive Google Calendar APIs (to add Election Day reminders to your personal calendar), it requires formal verification from Google, which is currently pending.
> 
> You **can** log in with your own Google Account to test the functionality. However, you will encounter a screen stating **"Google hasn’t verified this app"**. 
> 
> **To proceed and test the app:**
> 1. Click **"Advanced"**.
> 2. Click **"Go to electionguide-app (unsafe)"**.
> 
> We have implemented strict security measures and only request the `calendar.events.freebusy` and `calendar.events` scopes necessary for adding election reminders.

---

## 🚀 Key Features

### 🇮🇳 India & 🇺🇸 Multi-Country Support
- **Voter Registration Guide**: Direct links and step-by-step instructions for ECI (India) and Vote.gov (US).
- **Eligibility Checker**: Instant age-based and residency-based validation.
- **Polling Place Locator**: Integrated with the Google Civic Information API for US voters.
- **Election Reminders**: One-click "Add to Google Calendar" for upcoming election dates.

### 🤖 Resilient AI Intelligence
The chatbot is built with a **production-grade resilience architecture** using the Google Gemini API:
- **Dynamic Model Discovery**: The engine automatically crawls available models at runtime, prioritizing the **Gemini 2.5/2.0 Flash family** while maintaining deep fallbacks to 1.5 variants if primary quotas are hit.
- **Fail-Safe Routing**: Implements a multi-layered retry loop with error classification (404, 429, 500) to ensure the bot stays online even during API load spikes.
- **Circuit Breaker Design**: Features per-model health tracking and global circuit breakers to prevent latency cascades during upstream outages.
- **Performance Optimization**: Dual-track caching (Model Discovery Cache + LRU Query Cache) ensures that repeated queries are answered instantly.

---

## 🛠️ Technology Stack

- **Backend**: Python (Flask), Gunicorn (Production Server)
- **Frontend**: Vanilla JS, Modern CSS (Premium UI with Glassmorphism)
- **AI/ML**: Google Gemini (via `google-genai` SDK)
- **Google Services**:
  - **Civic Information API**: Real-time US election data.
  - **Calendar API**: Automated election day scheduling.
  - **Cloud Run**: Highly scalable, serverless deployment.
  - **OAuth 2.0**: Secure user authentication.

---

## 🔐 Engineering Excellence & Security

- **Deterministic vs. AI Split**: Critical civic data (dates, ages) is handled via hardcoded logic; LLMs are used only for conversational guidance to prevent "hallucinations."
- **Precision Safety Wall**: A strict regex-based filter monitors AI output to ensure answers remain neutral, non-partisan, and purely educational.
- **Atomic State Management**: Thread-safe caching prevents data corruption across concurrent Cloud Run worker instances.
- **Hard Timeout Guards**: All AI calls are wrapped in an 8-10s hard timeout using `ThreadPoolExecutor` to protect server health.

---

## 🧪 Testing & Quality Assurance

- **Robust Test Suite**: 58 automated tests covering API contracts, boundary conditions, and intent detection.
- **CI/CD Integration**: Every push is verified via GitHub Actions to ensure 100% logic integrity.
- **Error Observability**: Detailed diagnostic logging tracks model success rates and failover events for production monitoring.

---

Built with ❤️ for the **Hack2Skill & Google for Developers AI Challenge 2026**.
