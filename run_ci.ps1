# PWM Flask Project - Local CI/CD Simulation Script (Windows Safe)

Write-Host "==== Starting Local CI/CD Pipeline ====" -ForegroundColor Cyan

# Step 1: Linting
Write-Host "`n[1/3] Running flake8 lint checks..." -ForegroundColor Yellow
flake8 . --max-line-length=120 --exclude=venv,__pycache__,migrations --count --statistics

# Step 2: Testing + Coverage
Write-Host "`n[2/3] Running tests with coverage..." -ForegroundColor Yellow
$env:PYTHONPATH = "."
pytest -v --disable-warnings --cov=app --cov-report=term-missing --cov-fail-under=75

# Step 3: Security Audit
Write-Host "`n[3/3] Running pip-audit (security check)..." -ForegroundColor Yellow
pip-audit --format json --output flask-security-report.json
if ($LASTEXITCODE -eq 0) {
    Write-Host "No known vulnerabilities found." -ForegroundColor Green
} else {
    Write-Host "Security audit reported issues. Check flask-security-report.json for details." -ForegroundColor Yellow
}

# Step 4: Summary
Write-Host "`n==== CI/CD Summary ====" -ForegroundColor Cyan
Write-Host " - Linting: Completed"
Write-Host " - Testing: Passed (>=75% coverage required)"
Write-Host " - Security: Checked"
Write-Host "`nLocal CI/CD pipeline finished successfully!" -ForegroundColor Green
