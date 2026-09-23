# 🚀 AVEN AI — Render & Supabase Hosting Guide

This guide walks you through deploying **AVEN AI** on **Render** (Free Web Service or Worker) with a **Supabase PostgreSQL** cloud database.

---

## 🗄️ Step 1: Set Up Supabase Database (2 Minutes)

1. Go to **[https://supabase.com](https://supabase.com)** and sign in.
2. Click **New Project**:
   - **Name:** `aven-ai-db`
   - **Database Password:** Choose a strong password and save it.
   - **Region:** Choose the region closest to you (e.g. *US East* or *EU Central*).
3. Once the project is created, click the **Settings (gear icon)** in the sidebar ➔ **Database**.
4. Scroll down to **Connection String** ➔ Select the **URI** tab ➔ Choose **Session Pooler** (or **Direct**).
5. Copy your connection URI, which looks like:
   ```text
   postgresql://postgres.yourprojectref:yourpassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
   *(Make sure to replace `yourpassword` with your actual database password!)*

> 💡 *Note: You don't need to manually run SQL tables! AVEN AI automatically connects and initializes all required tables and indexes on first startup.*

---

## 🌐 Step 2: Deploy to Render (3 Minutes)

### Option A: Deploy as Web Service (Recommended — 100% Free Tier)

1. Go to **[https://render.com](https://render.com)** and sign in with your GitHub account.
2. Click **New +** ➔ **Web Service**.
3. Select your repository: **`royalrahul456/aven-ai`**.
4. Configure the settings:
   - **Name:** `aven-ai-bot`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Instance Type:** `Free`
5. Scroll down to **Environment Variables** and add the following keys:

| Key | Value | Notes |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | `1234567890:ABCdef...` | From @BotFather |
| `DATABASE_URL` | `postgresql://postgres...` | Your Supabase URI from Step 1 |
| `GEMINI_API_KEY` | `AIzaSy...` | Google AI Studio Key |
| `OPENAI_API_KEY` | `gsk_...` | Groq / OpenAI API Key |
| `OPENAI_API_BASE` | `https://api.groq.com/openai/v1` | Groq endpoint (if using Groq) |
| `MISTRAL_API_KEY` | `1usopp...` | Mistral AI API Key |

6. Click **Create Web Service**.

Render will automatically clone the repository, install dependencies, run the database migrations on Supabase, start the health check endpoint on `/health`, and start polling Telegram!

---

### Option B: Deploy as Background Worker

If you have a Render paid plan or prefer a worker without HTTP ports:
1. Click **New +** ➔ **Background Worker**.
2. Connect `royalrahul456/aven-ai`.
3. Set **Start Command** to `python main.py`.
4. Add the same Environment Variables.
5. Click **Create Background Worker**.

---

## 🔍 Step 3: Verification & Diagnostics

1. Open your Telegram app and search for your bot: **`@AvenAi_Bot`**.
2. Send `/start` — the bot should greet you with your active theme and dashboard!
3. Send `/ping` — the diagnostic card will display **Database Latency** directly measuring the round-trip connection to your Supabase PostgreSQL cluster!
4. Send `/image A futuristic cybernetic city` to test the FLUX.1 studio!

---

## 🔄 Updating Your Bot

Whenever you push new code to your GitHub `main` branch (`git push origin main`), Render will **automatically rebuild and redeploy** the latest version with zero downtime!
