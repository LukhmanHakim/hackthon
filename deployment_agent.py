"""
deployment_agent.py  —  runs on the CENTRAL laptop
===================================================
1. Polls the FastAPI server (on the main laptop) every POLL_INTERVAL seconds
2. Picks up sessions with status=pending
3. Executes run_deployment.bat locally (git pull + SQL scripts)
4. Posts logs and updates status back to the FastAPI server via HTTP

Usage:
    python deployment_agent.py

Configure SERVER_URL and PROJECTS_ROOT below before running.
"""

import os
import subprocess
import time
import requests

# ── CONFIG ────────────────────────────────────────────────────────────────────
# IP address of the laptop running the FastAPI server (check with ipconfig)
SERVER_URL = "http://192.168.0.4:80001"

# Root folder on THIS (central) laptop where project subfolders live
PROJECTS_ROOT = r"C:\Projects"             # <-- change to your projects folder

# Path to run_deployment.bat on THIS laptop
BAT_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_deployment.bat")

POLL_INTERVAL = 60      # seconds between polls
BAT_TIMEOUT   = 300     # max seconds to wait for a bat execution
# ─────────────────────────────────────────────────────────────────────────────


def api(method: str, path: str, **kwargs):
    url = f"{SERVER_URL}{path}"
    try:
        resp = getattr(requests, method)(url, timeout=10, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"[AGENT] API error {method.upper()} {path}: {e}")
        return None


def post_log(session_id: str, description: str):
    api("post", f"/api/deployments/{session_id}/logs", json={"description": description})


def set_status(session_id: str, status: str):
    api("put", f"/api/deployments/{session_id}", json={"status": status})


def execute_session(session: dict):
    sid     = session["session_id"]
    project = session["project"]
    client  = session["client"]

    print(f"[AGENT] Starting deployment: session={sid} project={project} client={client}")
    set_status(sid, "running")
    post_log(sid, f"[START] Agent picked up deployment — project={project} client={client}")

    project_path = os.path.join(PROJECTS_ROOT, project)

    try:
        result = subprocess.run(
            [BAT_SCRIPT, project_path, project, client],
            capture_output=True,
            text=True,
            timeout=BAT_TIMEOUT,
            shell=False,
        )

        if result.stdout.strip():
            post_log(sid, f"[OUTPUT]\n{result.stdout.strip()}")
        if result.stderr.strip():
            post_log(sid, f"[STDERR]\n{result.stderr.strip()}")

        if result.returncode == 0:
            set_status(sid, "success")
            post_log(sid, "[DONE] Deployment completed successfully")
            print(f"[AGENT] SUCCESS: {sid}")
        else:
            set_status(sid, "failed")
            post_log(sid, f"[FAIL] Bat exited with code {result.returncode}")
            print(f"[AGENT] FAILED: {sid} (exit code {result.returncode})")

    except subprocess.TimeoutExpired:
        set_status(sid, "failed")
        post_log(sid, f"[FAIL] Timed out after {BAT_TIMEOUT}s")
        print(f"[AGENT] TIMEOUT: {sid}")
    except FileNotFoundError:
        set_status(sid, "failed")
        post_log(sid, f"[FAIL] run_deployment.bat not found at: {BAT_SCRIPT}")
        print(f"[AGENT] BAT NOT FOUND: {BAT_SCRIPT}")
    except Exception as exc:
        set_status(sid, "failed")
        post_log(sid, f"[FAIL] Unexpected error: {exc}")
        print(f"[AGENT] ERROR: {sid} — {exc}")


def poll():
    print(f"[AGENT] Polling {SERVER_URL} for pending deployments ...")
    sessions = api("get", "/api/deployments/", params={"status": "pending"})
    if not sessions:
        print("[AGENT] No pending deployments found")
        return
    print(f"[AGENT] Found {len(sessions)} pending session(s)")
    for session in sessions:
        execute_session(session)


def main():
    print("=" * 60)
    print(f"  Deployment Agent")
    print(f"  Server  : {SERVER_URL}")
    print(f"  Projects: {PROJECTS_ROOT}")
    print(f"  Bat     : {BAT_SCRIPT}")
    print(f"  Poll    : every {POLL_INTERVAL}s")
    print("=" * 60)

    # Verify server is reachable before starting loop
    health = api("get", "/health")
    if health:
        print(f"[AGENT] Server reachable — scheduler running: {health.get('scheduler_running')}")
    else:
        print("[AGENT] WARNING: Could not reach server. Will keep retrying ...")

    while True:
        try:
            poll()
        except Exception as exc:
            print(f"[AGENT] Poll error: {exc}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
