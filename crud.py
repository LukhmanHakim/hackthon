import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from models import DeploymentSession, DeploymentLog
from schemas import DeploymentSessionCreate, DeploymentSessionUpdate, DeploymentLogCreate


# ── Deployment Session ────────────────────────────────────────────────────────

def create_deployment(db: Session, data: DeploymentSessionCreate) -> DeploymentSession:
    session = DeploymentSession(
        session_id=str(uuid.uuid4()),
        datetime=datetime.utcnow(),
        project=data.project,
        client=data.client,
        status=data.status or "pending",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_all_deployments(db: Session, skip: int = 0, limit: int = 100, status: str | None = None):
    q = db.query(DeploymentSession)
    if status:
        q = q.filter(DeploymentSession.status == status)
    return q.offset(skip).limit(limit).all()


def get_deployment(db: Session, session_id: str) -> DeploymentSession | None:
    return (
        db.query(DeploymentSession)
        .filter(DeploymentSession.session_id == session_id)
        .first()
    )


def update_deployment(
    db: Session, session_id: str, data: DeploymentSessionUpdate
) -> DeploymentSession | None:
    record = get_deployment(db, session_id)
    if not record:
        return None
    if data.project is not None:
        record.project = data.project
    if data.client is not None:
        record.client = data.client
    if data.status is not None:
        record.status = data.status
    db.commit()
    db.refresh(record)
    return record


def delete_deployment(db: Session, session_id: str) -> bool:
    record = get_deployment(db, session_id)
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True


def get_pending_deployments(db: Session):
    return (
        db.query(DeploymentSession)
        .filter(DeploymentSession.status == "pending")
        .all()
    )


# ── Deployment Log ────────────────────────────────────────────────────────────

def add_log(db: Session, session_id: str, description: str) -> DeploymentLog:
    log = DeploymentLog(
        log_id=str(uuid.uuid4()),
        session_id=session_id,
        datetime=datetime.utcnow(),
        description=description,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_logs_by_session(db: Session, session_id: str):
    return (
        db.query(DeploymentLog)
        .filter(DeploymentLog.session_id == session_id)
        .order_by(DeploymentLog.datetime)
        .all()
    )
