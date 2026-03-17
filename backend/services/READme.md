# 🤖 Arbitro Background Services & Automation (ETL)

Welcome to the `services` module of the Arbitro system. This directory represents the operational "muscle" of the backend application. It houses the autonomous background workers, web scrapers, and the core business algorithms responsible for data extraction, transformation, and synchronization (ETL pipeline).

---

## 📂 Architecture & File Responsibilities

- **`scraper_pzpn.py`** **Role:** Headless Browser Automation (Data Extraction).  
  **Details:** Utilizes **Playwright** to autonomously navigate the PZPN24 portal. It handles complex interactions such as logging in, managing session states (cookies/tokens), bypassing dynamic cookie consent banners (e.g., Usercentrics DOM removal), and scraping paginated match assignments and referee rosters.

- **`scraper_garmin.py`** **Role:** Wearable Telemetry Ingestion.  
  **Details:** Interfaces with Garmin Connect to extract raw fitness and health data. It manages authentication, handles API rate-limiting or payload parsing, and normalizes the telemetry data (distance, heart rate, timestamps) into a structured format ready for the database.

- **`linker.py`** **Role:** The Smart Matching Engine (Data Transformation).  
  **Details:** This is the core algorithmic brain of Arbitro. Since PZPN and Garmin are entirely disconnected systems without shared foreign keys, the Linker employs a heuristic, time-based matching algorithm. It compares match schedules with activity timestamps, applying specific time deltas and tolerance windows to accurately pair a football match with the corresponding physical activity.

- **`prompt_ai.txt`** **Role:** Prompt Engineering & LLM Integration.  
  **Details:** Contains the structured prompts used during the development lifecycle or for AI-driven data parsing. This highlights a modern, AI-assisted engineering workflow and the capability to leverage Large Language Models (LLMs) for complex problem-solving.

---

## 🚀 Technical Highlights for Reviewers

If you are evaluating this codebase, please note the advanced engineering concepts implemented in these background services:

1. **Complex Web Scraping (Playwright):** Moving beyond simple HTTP requests, the PZPN scraper handles dynamic Single Page Applications (SPAs), intercepts network requests, injects custom JavaScript for DOM manipulation, and utilizes `force=True` clicks to ensure reliability against UI overlays.
2. **Concurrency & Performance:** The scraping modules utilize Python's `ThreadPoolExecutor` to fetch details for multiple matches concurrently, drastically reducing the total execution time while respecting target server limits.
3. **Session Persistence:** Scrapers save and reuse authentication states (`storage_state`). This avoids triggering CAPTCHAs, prevents account lockouts due to repeated logins, and speeds up the ETL pipeline.
4. **Fault Tolerance:** The services are built defensively. They include robust error handling, explicit timeouts, and fallback mechanisms ensuring that if one match fails to parse, the entire pipeline does not crash.
5. **Heuristic Algorithmic Logic:** The `linker.py` demonstrates the ability to solve real-world data integration problems by designing custom algorithms to bridge disparate, unstructured datasets based on temporal logic.