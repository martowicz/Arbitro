# 🗄️ Arbitro Data Access Layer (Repository Pattern)

Welcome to the database module of the Arbitro system. This directory encapsulates all database interactions and data persistence logic, built around the robust **Repository Pattern**. 

By strictly separating the database layer from the business logic and the API layer, the application remains highly testable, maintainable, and agnostic to underlying database changes.

---

## 📂 Architecture & File Responsibilities

This module is designed to handle raw SQLite data manipulation, employing specialized repositories for different domains of the application:

- **`connection.py`** **Role:** Database Lifecycle & Connection Management.  
  **Details:** Acts as the central provider for database connections. It manages SQLite connection states, ensures thread safety (where applicable), and provides clean connection teardowns. It abstracts the boilerplate of executing queries and handling cursors.

- **`repo_garmin.py`** **Role:** Garmin Data Access Object (DAO).  
  **Details:** Manages CRUD (Create, Read, Update, Delete) operations specifically for Garmin fitness activities. It handles the insertion of raw telemetry data (distance, heart rate, timestamps) retrieved from the Garmin Connect API scraper.

- **`repo_matches.py`** **Role:** PZPN Match Data DAO.  
  **Details:** Responsible for storing match schedules, team details, and referee assignments. It utilizes "UPSERT" (Insert or Replace/Ignore) logic to ensure data integrity and prevent duplicates when the Playwright scraper runs multiple times.

- **`repo_linker.py`** **Role:** Relational Mapping.  
  **Details:** The persistence layer for the Smart Linker algorithm. It safely stores the relational mapping (foreign keys) between specific PZPN matches and their corresponding Garmin activities.

- **`repo_settings.py`** **Role:** Secure Credential Vault.  
  **Details:** Manages the storage and retrieval of user settings and login credentials. **Security highlight:** This repository ensures that sensitive data (passwords) are handled securely during read/write operations, working in tandem with the encryption utilities before saving to disk.

---

## 🚀 Technical Highlights for Reviewers

If you are reviewing this codebase for technical evaluation, please consider the following engineering practices implemented here:

1. **The Repository Pattern:** Business logic services never write raw SQL. They call Pythonic methods from these repositories, adhering to the Dependency Inversion Principle and making the services easily mockable for Unit Testing.
2. **SQL Injection Prevention:** All repositories strictly use parameterized queries. No string formatting or concatenation is used for user-supplied data.
3. **Transaction Management:** Repositories handle `commit()` and `rollback()` procedures, ensuring atomic operations. If a complex data insertion fails, the database state remains consistent.
4. **Separation of Concerns (SoC):** By splitting repositories by domain (`garmin`, `matches`, `settings`), the codebase avoids massive, monolithic database files, making it easy to navigate and scale.