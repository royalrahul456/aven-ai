# ⚡ AVEN AI — Premium Telegram AI Platform

**Telegram Bot:** `@AvenAi_Bot`  
**Version:** `1.1.0`

**AVEN AI** is a production-ready, highly modular, and feature-packed Telegram AI bot built using **Python 3.11+**, **aiogram 3.x**, and **SQLite**. It offers a Telegram-native interface with custom inline keyboards, real-time model switching, FLUX.1 AI image studio, deep reasoning tools, full coding assistance suite, live web search with citations, 6 aesthetic themes with custom typography, persistent memory, and resilient fallback routing.

---

## 🌟 Key Features

* 🤖 **Multi-Model Support:** Switch effortlessly between Google Gemini (`Aven Flash`), Groq / OpenAI (`Aven Pro`, `Aven Ultra`), Mistral AI (`Aven Mistral`), Live Web AI (`Aven Web`), and Smart Routing (`Aven Auto`).
* 🎨 **FLUX.1 Image Studio:** Generate ultra-high-resolution 1024x1024 artwork directly in Telegram with automatic AI prompt enrichment and style presets (Realism, 3D Render, Anime).
* 🧠 **Smart Auto Router:** Intelligently analyzes user query intent (programming, logic proof, live events, or quick conversation) and routes to the best active model with automatic fallback.
* 🌐 **Real-time Web Search:** Searches DuckDuckGo / Google News, summarizes live web facts, and cites sources directly in Telegram.
* 💻 **Complete Coding Suite:** Code generation (`/code`), bug debugging (`/debug`), step-by-step breakdown (`/explaincode`), performance tuning (`/optimize`), security & style audit (`/review`), and cross-language translation (`/convert`).
* 🎭 **Theme & Typography Engine:** Choose between 6 visual styles: `⚡ AVEN PRO`, `🌑 OBSIDIAN`, `💎 CYBERPUNK`, `🔮 VIOLET NEON`, `☀️ SOLAR GOLD`, and `🪐 STELLAR`.
* 🛡️ **Bulletproof Formatting:** Telegram HTML/Markdown conversion with smart code-block preserving message splitting (`<=4096` chars) and auto-file upload for large outputs.
* 🗄️ **Persistent Storage:** Async SQLite database tracking per-user preferences, custom instructions, temperature, sliding multi-turn conversation memory, and usage analytics.
* 🔒 **Enterprise-Grade Security:** Rate limiting middleware, sanitized error handling, and zero credential leaks.

---

## 📂 Project Architecture

```text
Aven AI/
├── bot/
│   ├── handlers/
│   │   ├── start.py          # /start, /about, main navigation
│   │   ├── help.py           # /help categorized directory
│   │   ├── chat.py           # /chat, /ask, multi-turn conversation
│   │   ├── image.py          # /image, /imagine, /draw FLUX.1 studio
│   │   ├── models.py         # /models selector UI & info cards
│   │   ├── tools.py          # /think, /explain, /summarize, /rewrite, /translate
│   │   ├── code.py           # /code, /debug, /explaincode, /optimize, /review, /convert
│   │   ├── settings.py       # /settings, /theme, /temperature, /instructions, /reset
│   │   ├── special.py        # /web, /auto, /status, /ping
│   │   └── __init__.py       # Master router
│   ├── keyboards/
│   │   ├── main.py           # Main menus, help keyboards, back buttons
│   │   ├── models.py         # Model selector grids & preview cards
│   │   ├── settings.py       # Settings, theme picker, temperature slider
│   │   └── tools.py          # Language selectors & code action bars
│   ├── middlewares/
│   │   ├── throttling.py     # Anti-spam token bucket rate limiting
│   │   ├── user_session.py   # User persistence & session injector
│   │   └── error_handler.py  # Global error interceptor
│   └── states/
│       └── form_states.py    # FSM states for multi-step prompts
│
├── providers/
│   ├── base.py               # Abstract AIProvider & error classes
│   ├── gemini.py             # Google Gemini API client
│   ├── mistral.py            # Mistral AI API client
│   ├── openai_compatible.py  # OpenAI & Groq compatible endpoints
│   ├── image.py              # FLUX.1 image generator & AI prompt enricher
│   ├── web.py                # Web search scraper & citation synthesis
│   ├── auto.py               # Smart Intent Classifier & Fallback router
│   └── registry.py           # Central provider registry & status resolver
│
├── database/
│   ├── schema.sql            # SQLite database schema
│   ├── db.py                 # Async SQLite connection manager
│   └── repository.py         # Async CRUD repository
│
├── utils/
│   ├── fonts.py              # Unicode mathematical typography engine
│   ├── formatting.py         # HTML/Markdown conversion & escaping
│   ├── splitter.py           # Code-block preserving chunk splitter
│   ├── logger.py             # Structured safe logger
│   └── themes.py             # Theme palettes and formatting helpers
│
├── config.py                 # Pydantic configuration & model metadata
├── main.py                   # Bot entrypoint with auto-reconnection
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
└── README.md
```

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
* Python 3.11 or higher
* Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
* At least one AI API Key (Groq, Google Gemini, Mistral, Anthropic, or OpenAI)

### 2. Clone & Setup Environment
```bash
git clone https://github.com/royalrahul456/aven-ai.git
cd aven-ai

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure `.env`
Copy `.env.example` to `.env` and configure your keys:
```bash
cp .env.example .env
```

Edit `.env`:
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# AI Provider Keys:
GEMINI_API_KEY=AIzaSy...
OPENAI_API_KEY=gsk_...
OPENAI_API_BASE=https://api.groq.com/openai/v1
MISTRAL_API_KEY=...
```

### 4. Run the Bot
```bash
python main.py
```

The bot will initialize the SQLite database (`data/aven_ai.db`), register official command menus on Telegram, and start polling with auto-reconnect resilience!

---

## 📋 Command Reference

| Command | Category | Description |
| :--- | :--- | :--- |
| `/start` | 🚀 Core | Open AVEN AI dashboard and main menu |
| `/help` | 🚀 Core | Interactive command directory |
| `/chat <msg>` | 🚀 Core | Chat with multi-turn memory |
| `/ask <prompt>` | 🚀 Core | Ask a quick question |
| `/image <prompt>`| 🎨 Art | Generate high-res FLUX.1 artwork |
| `/imagine <prompt>`| 🎨 Art | Generate AI images with style presets |
| `/models` | 🚀 Core | Open model selector UI |
| `/think <query>` | 🧠 AI Tools | Deep step-by-step reasoning |
| `/explain <topic>` | 🧠 AI Tools | Structured explanation with examples |
| `/summarize <text>` | 🧠 AI Tools | Key points and bullet summary |
| `/rewrite <text>` | 🧠 AI Tools | Improve clarity, tone, and grammar |
| `/translate <text>` | 🧠 AI Tools | Multi-language translation |
| `/code <task>` | 💻 Code | Generate clean, documented code |
| `/debug <code>` | 💻 Code | Identify bugs and provide fixes |
| `/explaincode <code>` | 💻 Code | Line-by-line code explanation |
| `/optimize <code>` | 💻 Code | Performance and memory optimization |
| `/review <code>` | 💻 Code | Security, architecture & style audit |
| `/convert <code>` | 💻 Code | Convert code to another language |
| `/settings` | ⚙️ Settings | View active preferences |
| `/theme` | ⚙️ Settings | Change UI & typography theme |
| `/temperature` | ⚙️ Settings | Adjust AI creativity (0.2 - 1.2) |
| `/instructions` | ⚙️ Settings | Set custom system instructions |
| `/reset` | ⚙️ Settings | Reset preferences to defaults |
| `/web <query>` | 🌐 Special | Live web search with citations |
| `/auto` | 🌐 Special | Enable Smart Auto Router |
| `/status` | 🌐 Special | Show system status and metrics |
| `/ping` | 🌐 Special | Test gateway and database latency |
| `/about` | 🌐 Special | About AVEN AI platform |

---

## 📄 License
MIT License. Built for **AVEN AI** (`@AvenAi_Bot`).
