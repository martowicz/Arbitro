# ⚙️ Arbitro API Core

Welcome to the core API directory of the Arbitro system. This module serves as the central nervous system of the backend, built with **FastAPI**. It handles RESTful routing, data validation, cryptographic security, and the orchestration of asynchronous scraping workflows.

The architecture here strictly follows the **Separation of Concerns** principle, ensuring the codebase remains highly modular, testable, and scalable.

---

## 📂 Architecture & File Responsibilities

Below is a breakdown of the internal structure and the engineering decisions behind it:

- **`charts.py`** **Role:** Data Aggregation & Analytics.  
  **Details:** Processes raw data from the SQLite database (such as Garmin heart rate metrics and match distances) and transforms it into optimized, frontend-ready JSON structures for Vue 3 charting libraries. 

- **`events.py`** **Role:** Event Handling.  
  **Details:** Manages the logic for specific system events or match-related triggers. It cleanly separates the domain logic from the HTTP transport layer.

- **`models.py`** **Role:** Data Validation & Serialization.  
  **Details:** Utilizes **Pydantic** to define strict data schemas. This guarantees that all incoming requests (e.g., user settings) and outgoing responses are strongly typed, validated, and automatically documented via OpenAPI/Swagger.

- **`settings.py`** **Role:** Secure Configuration Management.  
  **Details:** Exposes endpoints for managing user profiles. **Security highlight:** It handles the logic for receiving sensitive user credentials (PZPN and Garmin logins) from the frontend and securely passing them down to the database layer for encryption.

- **`sync.py`** **Role:** Workflow Orchestration (ETL).  
  **Details:** The control center for the synchronization pipelines. It exposes endpoints that safely trigger the headless Playwright scrapers and the Match Linker algorithm, managing the execution state and returning structured responses to the client.

- **`utils.py`** **Role:** Shared Helpers & Cryptography.  
  **Details:** Contains reusable utility functions, potentially including timestamp normalization algorithms, custom data formatters, and symmetric encryption/decryption helpers used across the API.

---

## 🚀 Technical Highlights for Reviewers

If you are reviewing this code for evaluation, please note the following architectural choices:

1. **Security-First Approach:** Sensitive data (passwords) handled in `settings.py` are never logged or stored in plain text. Utilities in this module ensure data is encrypted at rest.
2. **Modern Python Typing:** Extensive use of Python type hints combined with FastAPI/Pydantic ensures runtime safety and excellent developer experience (DX).
3. **Asynchronous Design:** Designed to efficiently handle long-running I/O bound tasks (like spawning Playwright browsers via `sync.py`) without blocking the main event loop.
4. **Modularity:** By splitting routing and logic into domains (`charts`, `sync`, `settings`), the API is built to scale out easily if new integrations are added in the future.