# 🧪 Arbitro - Testing Architecture (QA & Testing)

This directory contains a comprehensive suite of automated tests for the Arbitro backend. The tests are designed with a focus on maximum isolation, execution speed, and resilience to changes in external systems (Garmin, PZPN).

Current project state: **31 tests** covering core business logic, security, and the API layer.

## 🎯 Testing Philosophy
The testing architecture in this project is built upon the following principles:
1. **Full Isolation:** Tests never modify the production database. We utilize in-memory databases generated on the fly.
2. **I/O Independence:** External scraping services and file systems are fully mocked. This guarantees that tests execute in fractions of a second and do not depend on external network conditions.
3. **API Contract Testing:** Input/output validation based on Pydantic models protects the system from invalid payloads (HTTP 422 Unprocessable Entity).

---

## 🛠 Testing Techniques and Patterns

Proven engineering patterns were applied during the implementation of this test environment:

### 1. In-Memory Database & Test Fixtures (`pytest.fixture`)
* Configured a global `conftest.py` file to manage the database lifecycle.
* Utilized the **Setup & Teardown** pattern (via `yield` and `tmp_path`) to generate a clean, isolated SQLite table structure before each test. This guarantees the prevention of State Leaks between tests.

### 2. Advanced Mocking (`unittest.mock`)
* **Patching (`@patch`):** Intercepting calls to external modules at the API router level to decouple the business logic layer from disk/network operations.
* **MagicMock:** Simulating complex object structures and behaviors without relying on physical data.
* **Side Effects (`side_effect`):** Intentionally forcing exceptions (e.g., simulating external server crashes or I/O errors) to verify `try...except` blocks and error handling.

### 3. API & Integration Testing (FastAPI `TestClient`)
* **HTTP Contract Verification:** Testing the correctness of status codes (200 OK, 400 Bad Request, 404 Not Found, 405 Method Not Allowed, 422 Unprocessable Entity).
* **Background Tasks Testing:** Verifying the delegation of tasks to the background by FastAPI, while simultaneously intercepting (mocking) the actual process to prevent tests from hanging on long-running scraping operations.

### 4. Statefulness & Partial Updates Preservation
* Designed tests to verify **Non-Destructive Partial Updates**. These tests simulate the passage of time and ensure that POST/PATCH requests updating single fields do not overwrite or wipe out existing data in the database.

### 5. Pure Functions & Unit Testing
* Refactored the core logic of the "Linker" (matching trainings with referee matches) into the **Pure Function** pattern. This allowed for lightning-fast unit testing of the time-window algorithm, bypassing SQL queries entirely.

---

## 📂 Test Modules Structure

To maintain readability and adhere to the Single Responsibility Principle, tests are divided by domain:

* `conftest.py` - Global configuration and in-memory database injection.
* `test_security.py` - Tests for encryption and decryption mechanisms, ensuring sensitive user data (passwords, API keys) is securely processed before database insertion.
* `test_linker.py` - Unit tests for the core linking algorithm, validating the time-window logic (-15 to +90 minutes) for matching Garmin activities with PZPN matches.
* `test_api_settings.py` - Tests for application settings, data encryption, partial updates, and rejection of invalid JSON payloads.
* `test_api_events.py` - Tests for timeline endpoints, chronological sorting, and edge cases handling (e.g., missing statistical data).
* `test_api_charts.py` - Integration tests for the Chart.js dataset generation module.
* `test_api_sync.py` - Verification of the mechanisms delegating asynchronous scraping tasks.

---

## 🚀 How to Run the Tests

The test environment is based on the `pytest` framework. To run the tests, navigate to the main backend directory (ensure your virtual environment is active) and run:

Run all tests with a detailed log:
```bash
pytest tests/ -v