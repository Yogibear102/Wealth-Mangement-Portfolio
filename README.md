# PWM - Personal Wealth Manager (Flask) - All Stories Implementation (Best-effort)

This project implements all user stories listed, with practical and testable implementations for each story.
Notable additions compared to the previous version:
- Story 9: Asset name is editable and users can pick chart colors per asset (color stored and used in dashboard).
- Story 11: Base reporting currency selection + static exchange-rate conversion. Default rates are in `data/exchange_rates.json` and can be updated or replaced with an API integration (instructions included).
- Story 16: Bulk load & pagination: a `scripts/bulk_load.py` creates 10,000 transactions to help stress-test DB; queries use indexing and pagination for lists.
- Story 17: Uptime/health checks: `/health` endpoint plus Dockerfile and deployment notes for high-availability recommendations (HAProxy, Kubernetes, managed cloud) - true 99% SLA requires infra.
- Story 18: Responsive UI tweaks and mobile-first adjustments.
- Story 19: Performance test script `scripts/perf_test.py` that measures response times of dashboard and transaction-list endpoints after bulk load.

## How to run
1. Unzip and cd into project
2. Create venv & install: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
3. Initialize DB and demo data: `python setup_db.py`
4. Optionally generate 10k transactions for performance testing: `python scripts/bulk_load.py --user demo@example.com --count 10000`
5. Run the app: `python app.py` (or `gunicorn app:app`)
6. Run perf tests: `python scripts/perf_test.py`

## Notes on stories that cannot be fully guaranteed by app code
- Story 17 (99% uptime): This is a deployment/infrastructure SLA and cannot be enforced by application code alone. The repo includes Dockerfile, health endpoint, and CI artifact steps; achieving 99% uptime requires deployment to redundant infrastructure (cloud provider, load balancer, multi-zone deployment). See README section 'High Availability' for recommended architecture.

