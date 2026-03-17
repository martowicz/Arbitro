# 🛡️ Arbitro Core Infrastructure

Welcome to the `core` module of the Arbitro system. This directory houses the foundational infrastructure and critical application settings, specifically focusing on the cryptographic and security mechanisms that protect user privacy.

By isolating security operations into a dedicated core module, the architecture enforces a strict boundary between general business logic and sensitive data handling.

---

## 📂 Architecture & File Responsibilities

- **`security.py`** **Role:** Cryptographic Engine & Credential Management.  
  **Details:** This file is responsible for the symmetric encryption and decryption of highly sensitive user credentials (such as PZPN24 and Garmin Connect passwords). It provides the necessary utilities to ensure that plain-text passwords are never written to the disk. 

---

## 🚀 Technical Highlights for Reviewers

For engineering reviewers evaluating this codebase, the existence and design of this module highlight several enterprise-grade security practices:

1. **Encryption at Rest:** Before any user credentials reach the database layer (via the `db` repositories), they pass through `security.py` to be securely encrypted. Even if the SQLite database is compromised, the user passwords remain mathematically protected.
2. **In-Memory Decryption:** Passwords are mathematically decrypted on the fly exactly when the automated headless scrapers (Playwright) need to inject them into the login forms. They exist in plain text only in RAM for milliseconds before being garbage-collected.
3. **Strict Separation of Concerns (SoC):** Security algorithms are not tangled up with FastAPI route handlers or raw SQL queries. This makes it incredibly easy to audit the security logic, rotate encryption keys, or upgrade the cryptographic algorithms in the future without breaking the rest of the application.
4. **Zero-Trust Approach:** The system operates under the assumption that the database layer is untrusted, forcing all sensitive data to be sanitized and secured at the core application layer.