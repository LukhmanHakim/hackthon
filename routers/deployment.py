from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from schemas import (
    DeploymentSessionCreate,
    DeploymentSessionUpdate,
    DeploymentSessionResponse,
    DeploymentSessionDetail,
    DeploymentLogResponse,
    DeploymentLogCreate,
)
from crud import (
    create_deployment,
    get_all_deployments,
    get_deployment,
    update_deployment,
    delete_deployment,
    get_logs_by_session,
    add_log,
)
from services.deployment_service import execute_deployment

router = APIRouter(prefix="/api/deployments", tags=["Deployment Sessions"])


# ── 1. CREATE ─────────────────────────────────────────────────────────────────
@router.post("/", response_model=DeploymentSessionResponse, status_code=201)
def create(data: DeploymentSessionCreate, db: Session = Depends(get_db)):
    """Create a new deployment session (status defaults to 'pending')."""
    return create_deployment(db, data)


# ── 2. READ ALL ───────────────────────────────────────────────────────────────
@router.get("/", response_model=List[DeploymentSessionResponse])
def list_all(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List deployment sessions. Filter by status: pending | running | success | failed"""
    return get_all_deployments(db, skip, limit, status)


# ── 3. READ ONE (with logs) ───────────────────────────────────────────────────
@router.get("/{session_id}", response_model=DeploymentSessionDetail)
def get_one(session_id: str, db: Session = Depends(get_db)):
    """Get a single deployment session with all its logs."""
    record = get_deployment(db, session_id)
    if not record:
        raise HTTPException(status_code=404, detail="Deployment session not found")
    return record


# ── 4. UPDATE ─────────────────────────────────────────────────────────────────
@router.put("/{session_id}", response_model=DeploymentSessionResponse)
def update(session_id: str, data: DeploymentSessionUpdate, db: Session = Depends(get_db)):
    """Update project, client, or status of a deployment session."""
    record = update_deployment(db, session_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="Deployment session not found")
    return record


# ── 5. DELETE ─────────────────────────────────────────────────────────────────
@router.delete("/{session_id}", status_code=200)
def delete(session_id: str, db: Session = Depends(get_db)):
    """Delete a deployment session and all its logs."""
    if not delete_deployment(db, session_id):
        raise HTTPException(status_code=404, detail="Deployment session not found")
    return {"message": "Deployment session deleted successfully"}


# ── 6. GET LOGS ───────────────────────────────────────────────────────────────
@router.get("/{session_id}/logs", response_model=List[DeploymentLogResponse])
def get_logs(session_id: str, db: Session = Depends(get_db)):
    """Retrieve all logs for a deployment session."""
    if not get_deployment(db, session_id):
        raise HTTPException(status_code=404, detail="Deployment session not found")
    return get_logs_by_session(db, session_id)


# ── 7. POST LOG (called by remote agent) ─────────────────────────────────────
@router.post("/{session_id}/logs", response_model=DeploymentLogResponse, status_code=201)
def post_log(session_id: str, data: DeploymentLogCreate, db: Session = Depends(get_db)):
    """Add a log entry for a session. Used by the remote deployment agent."""
    if not get_deployment(db, session_id):
        raise HTTPException(status_code=404, detail="Deployment session not found")
    return add_log(db, session_id, data.description)


# ── 8. TRIGGER EXECUTION ──────────────────────────────────────────────────────
@router.post("/{session_id}/execute", status_code=202)
def trigger(session_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Manually trigger deployment execution for a session."""
    record = get_deployment(db, session_id)
    if not record:
        raise HTTPException(status_code=404, detail="Deployment session not found")
    if record.status == "running":
        raise HTTPException(status_code=409, detail="Deployment is already running")
    background_tasks.add_task(execute_deployment, db, record)
    return {"message": "Deployment triggered", "session_id": session_id}
