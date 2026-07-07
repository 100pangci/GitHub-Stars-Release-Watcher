"""Start server, try login, print all info."""
import os
import subprocess
import sys
import time

import httpx

os.environ["APP_PASSWORD"] = "test1234"

# Kill existing
os.system("taskkill /f /im python.exe 2>nul")
time.sleep(2)

# Start server
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
    cwd=os.path.dirname(os.path.abspath(__file__)),
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
)

time.sleep(6)

# Read server output
import threading


def read_output():
    for line in iter(proc.stdout.readline, b""):
        print(f"[SERVER] {line.decode().strip()}")
t = threading.Thread(target=read_output, daemon=True)
t.start()

try:
    # Health check
    r = httpx.get("http://localhost:8000/health")
    print(f"\n[TEST] GET /health: {r.status_code} {r.json()}")

    # Login
    r = httpx.post("http://localhost:8000/login", data={"password": "test1234"})
    print(f"[TEST] POST /login: {r.status_code} {r.json()}")

    # Try wrong password
    r = httpx.post("http://localhost:8000/login", data={"password": "wrong"})
    print(f"[TEST] POST /login (wrong pw): {r.status_code} {r.json()}")

    # Read stored hash directly
    from app.database import SessionLocal
    from app.security import verify_password
    from app.services.settings import get_setting
    db = SessionLocal()
    h = get_setting(db, "app_password_hash", "")
    print(f"[TEST] stored hash: {h[:30] if h else 'EMPTY'}...")
    if h:
        print(f"[TEST] verify test1234: {verify_password('test1234', h)}")
        print(f"[TEST] verify wrong:    {verify_password('wrong', h)}")
    db.close()

finally:
    proc.terminate()
    proc.wait()
    print("\n[DONE]")
