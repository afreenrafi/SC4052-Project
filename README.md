# SC4052-Project

# 🌸 Bloom — Narrative Intelligence-as-a-Service

Bloom is an AI-powered system that recommends Thai series based on **narrative experience** (e.g., mood, tropes, tone) instead of traditional metadata like genre or title.

Users can describe what they want (e.g. *“fluffy school romance”*), and Bloom extracts features using AI and returns recommendations via a hybrid system.

---

## 🚀 Features

- 🤖 AI-powered narrative feature extraction (Gemini)
- 🎯 Hybrid recommendation:
  - Local Thai BL dataset (precision)
  - TMDb API (coverage)
- 💬 Interactive UI with assistant

---

## 🧠 System Flow

---

## 🛠️ Tech Stack

- Frontend: HTML, CSS, JavaScript  
- Backend: FastAPI (Python)  
- AI: Gemini API  
- External Data: TMDb API  

---

## ⚙️ Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Create .env
```bash
TMDB_API_KEY=your_tmdb_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### 3. Run Backend Server
```bash
python -m uvicorn api:app --reload
```

### 4. Open index.html in browser 
