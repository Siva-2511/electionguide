# 🗳️ ElectionGuide: AI-Powered Civic Assistant

[![Python CI](https://github.com/Siva-2511/electionguide/actions/workflows/ci.yml/badge.svg)](https://github.com/Siva-2511/electionguide/actions/workflows/ci.yml)
[![Live Demo](https://img.shields.io/badge/Live_Demo-Cloud_Run-9cf)](https://electionguide-app-1033116720582.us-central1.run.app)

**🌐 Live Application:** [electionguide-app.run.app](https://electionguide-app-1033116720582.us-central1.run.app)

> ElectionGuide is a non-partisan assistant that helps users navigate election processes in India, the US, and other countries. It uses Google Gemini to provide conversational guidance on registration, eligibility, and voting steps.

---

> [!IMPORTANT]
> **Note to Judges regarding Google Sign-In:** 
> This app uses Google Calendar APIs to add election reminders. Because verification is pending, you will see a **"Google hasn’t verified this app"** screen. 
> **To test:** Click **"Advanced"** and then **"Go to electionguide-app (unsafe)"**.

---

## ✨ Core Features

- **Conversational Guidance**: Ask questions about voter registration, eligibility (18+), and voting methods.
- **Voter Eligibility Checker**: Fast, rule-based validation for India and US voters.
- **Election Reminders**: One-click integration to add election dates to your **Google Calendar**.
- **Polling Place Search**: Integrated US polling location lookups using the **Google Civic API**.
- **Official Resources**: Direct links to **ECI (India)** and **Vote.gov (US)**.

---

## 🤖 AI & Resilience

The chatbot uses **Google Gemini** with a robust integration designed for high availability:
- **Automatic Fallback**: If the primary Gemini model is rate-limited or unavailable, the system automatically switches to the next available healthy model.
- **Smart Caching**: Uses memory-efficient caching to provide instant answers for repeated election queries.
- **Safety Filters**: Implements filters to ensure all AI responses remain non-partisan and focused on civic education.
- **Deterministic Logic**: Critical info (like voting age) is handled by code logic, while Gemini provides conversational context.

---

## 🛠️ Technology Stack

- **Backend**: Python (Flask) on **Google Cloud Run**.
- **AI**: Google Gemini (via `google-genai` SDK).
- **Integrations**: 
  - **Google Civic Information API** (US polling data).
  - **Google Calendar API** (Election reminders).
  - **Google OAuth 2.0** (Secure login).
- **Frontend**: Responsive HTML/CSS with modern glassmorphism design.

---

## 🧪 Quality & Testing

- **Automated Tests**: 58 tests covering intent detection, API contracts, and safety filters.
- **CI/CD**: Verified via GitHub Actions on every push.
- **Observability**: Built-in logging to monitor API health and failover events.

---

Built with ❤️ for the **Hack2Skill & Google for Developers AI Challenge 2026**.
