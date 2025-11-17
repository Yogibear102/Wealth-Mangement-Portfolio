# 🧪 PWM Flask Project – Test & QA Documentation

## 📋 Overview
This document describes the **testing strategy**, **test files**, and **coverage goals** for the **PWM Flask Financial Portfolio Manager** project.

The system uses a comprehensive test-driven QA process to validate:
- Core functionality (assets, transactions, exports)
- Data accuracy and integrity
- Performance and scalability
- Security and session handling
- Responsiveness and UI consistency

---

## ⚙️ Test Environment Setup

### 🧰 Prerequisites
- Python **3.11+**
- Virtual environment (`venv`) activated
- All dependencies installed via:

```bash
pip install -r requirements.txt



QA Acceptance Criteria
| Category             | Requirement                                  | Status           |
| -------------------- | -------------------------------------------- | ---------------- |
| System Functionality | CRUD workflows validated                     | ✅                |
| Data Accuracy        | Reports and charts match DB                  | ✅                |
| Authentication       | Login/logout/session verified                | ✅                |
| Performance          | Dashboard loads under 3 seconds @10k records | ✅                |
| Responsiveness       | No layout issues detected                    | ✅                |
| Code Coverage        | ≥75% enforced                                | ✅ (Current: 76%) |



Current Coverage Summary
| File        | Statements | Missed | Coverage  |
| ----------- | ---------- | ------ | --------- |
| `app.py`    | 338        | 88     | **74%**   |
| `models.py` | 31         | 0      | **100%**  |
| **Total**   | **369**    | **88** | **76% ✅** |

