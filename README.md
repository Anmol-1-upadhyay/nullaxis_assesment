# 🤖 Customer Support AI Chatbot

An AI-powered chatbot that classifies user queries as **Technical Support**, **Feature Request**, or **Sales Lead**, then uses a knowledge base or LLM to generate helpful responses and log critical data. Powered by **FastAPI**, **React**, **ChromaDB**, and **Groq's LLaMA-3**.

---

## 🧰 Features

- 🎯 Intent classification via LLM
- 🔍 Vector search over knowledge base (ChromaDB)
- 💬 Response generation using Groq LLM (LLaMA 3 70B)
- 🧠 Lightweight memory for sales info gathering
- 📝 Logging to:
  - `features.txt`
  - `sales_req.txt`
- 🚨 Escalation logic for failed KB matches or complex sales

---

## 🖥️ System Requirements

| Tool/Dependency | Version             |
|-----------------|---------------------|
| OS              | Windows 10+, macOS 12+, Ubuntu 20.04+ |
| Python          | 3.10.13              |
| Node.js         | 18.19.1              |
| npm             | 9.6.7                |
| ChromaDB        | 0.4.21               |
| OpenAI SDK      | 1.25.2               |
| FastAPI         | 0.111.0              |
| Uvicorn         | 0.30.1               |
| React           | 18.2.0               |
| Vite (optional) | 5.2.9                |

RAM: 8 GB minimum (16 GB recommended)  
Disk Space: 2 GB+

---

## 🚀 Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-repo/customer-support-bot.git
cd customer-support-bot
```

2. Backend Setup (FastAPI)
Prerequisites
Python 3.10+

pip available

Installation
bash
Copy
Edit
cd backend
python -m venv venv

# Activate virtual environment
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# Install backend dependencies
pip install -r ../requirements.txt
Environment Variables
Create a .env file inside /backend/:

env
Copy
Edit
GROQ_API_KEY=your_groq_api_key
CHROMA_DB_PATH=./chroma_db
Run Backend
bash
Copy
Edit
uvicorn main:app --reload
API base: http://localhost:8000

Swagger Docs: http://localhost:8000/docs

3. Frontend Setup (React.js)
Prerequisites
Node.js 18+

npm 9+

Installation
bash
Copy
Edit
cd ../frontend
npm install
API Configuration
Create or update src/config.js:

js
Copy
Edit
export const API_BASE_URL = 'http://localhost:8000';
Run Frontend
bash
Copy
Edit
npm start
Access frontend: http://localhost:3000
