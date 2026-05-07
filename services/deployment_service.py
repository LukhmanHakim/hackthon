"""
Deployment execution service.

Flow per session:
  1. Mark status = running, write start log
  2. Call run_deployment.bat <project_path> <project> <client>
  3. Capture stdout/stderr, write to log table
  4. Mark status = success | failed
"""

import os
import subprocess
from sqlalchemy.orm import Session
from models import DeploymentSession
from crud import add_log, get_pending_deployments

BAT_SCRIPT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "run_deployment.bat")
PROJECTS_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "projects")
TIMEOUT_SECONDS = 300


def _run_bat(project_path: str, project: str, client: str) -> tuple[int, str, str]:
    result = subprocess.run(
        [BAT_SCRIPT, project_path, project, client],
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        shell=False,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def execute_deployment(db: Session, session: DeploymentSession) -> None:
    session.status = "running"
    db.commit()
    add_log(db, session.session_id, f"[START] Deployment started — project={session.project} client={session.client}")

    try:
        project_path = os.path.join(PROJECTS_ROOT, session.project)
        returncode, stdout, stderr = _run_bat(project_path, session.project, session.client)

        if stdout:
            add_log(db, session.session_id, f"[OUTPUT] {stdout}")
        if stderr:
            add_log(db, session.session_id, f"[STDERR] {stderr}")

        if returncode == 0:
            session.status = "success"
            add_log(db, session.session_id, "[DONE] Deployment completed successfully")
        else:
            session.status = "failed"
            add_log(db, session.session_id, f"[FAIL] Bat script exited with code {returncode}")

    except subprocess.TimeoutExpired:
        session.status = "failed"
        add_log(db, session.session_id, f"[FAIL] Deployment timed out after {TIMEOUT_SECONDS}s")
    except FileNotFoundError:
        session.status = "failed"
        add_log(db, session.session_id, f"[FAIL] run_deployment.bat not found at: {BAT_SCRIPT}")
    except Exception as exc:
        session.status = "failed"
        add_log(db, session.session_id, f"[FAIL] Unexpected error: {exc}")
    finally:
        db.commit()


def run_pending_deployments(db: Session) -> None:
    pending = get_pending_deployments(db)
    for session in pending:
        execute_deployment(db, session)
