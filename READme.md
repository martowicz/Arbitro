# ⚽ Arbitro

**Sports management and analytics system for football referees.**

Arbitro is a Full-Stack web application that automates the retrieval of match assignment data (from the PZPN system) and integrates it with advanced health and performance analytics from Garmin watches. Forget about manual data entry – the system automatically links your heart rate and pace metrics to the correct match half!

🚀 **Project Status:** Containerized Version.  
All services now run in Docker containers for easy setup, portability, and isolation.  

---

## 🔒 Security & Credentials

All sensitive credentials (PZPN24, Garmin) are stored securely in the local database and **encrypted with AES**. Each user keeps their own encryption key locally, ensuring that passwords never leave your machine and remain fully protected.

---

## 🛠️ Tech Stack
* **Backend:** Python 3, FastAPI, SQLite
* **Frontend:** Vue.js 3 (Composition API), Vite, Chart.js
* **Integrations:** Garmin Connect API, Web Scraping (PZPN Extranet)
* **Data Engineering:** Custom ETL pipelines, Time-Series Data Processing
* **Deployment:** Docker & Docker Compose

---

## ⚙️ Prerequisites
To run Arbitro locally, ensure you have installed:  
* [Docker & Docker Compose](https://www.docker.com/)  
* [Git](https://git-scm.com/)  

---

## 📥 Local Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/Arbitro.git
cd Arbitro
```

### 2. Build and start containers
```bash
~/Arbitro$ docker compose up --build
```

This will spin up both backend and frontend services in isolated containers.

---

## 🧩 First-Time User Setup

After the containers are running:

1. Open the frontend in your browser, typically:  
   http://localhost:5173

2. On the first launch, you will be prompted to provide:
   * **Full Name** (Surname & Name)
   * **PZPN24 credentials** (email & password)
   * **Garmin credentials** (email & password)
   * **Your OpenAI API key** (for match performance analysis)

3. Start the **initial synchronization** via the app interface. This will:
   * Fetch your upcoming and past match assignments from PZPN24
   * Retrieve health and performance data from Garmin
   * Link heart rate and pace metrics to the correct match halves

All credentials entered will be **securely encrypted** with AES and stored locally in your database.



## 🧰 Notes
* Your **AES encryption key** is stored locally per user. Losing it means losing access to your encrypted credentials.  
* Database is **local-only**; no data is sent to external servers outside of the integrations.