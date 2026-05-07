"""
Deployment Manager API
======================
FastAPI app with:
  - CRUD endpoints for deployment sessions
  - Deployment log retrieval
  - APScheduler cron job that marks stale running sessions as failed

NOTE: Bat file execution runs on the central laptop via deployment_agent.py.
      The server does NOT execute the bat directly.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from database import engine, SessionLocal
from models import Base, DeploymentSession
from routers import deployment


def cron_job() -> None:
    """Mark sessions stuck in 'running' for over 10 minutes as failed."""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=10)
        stale = (
            db.query(DeploymentSession)
            .filter(
                DeploymentSession.status == "running",
                DeploymentSession.datetime < cutoff,
            )
            .all()
        )
        for session in stale:
            session.status = "failed"
            print(f"[Scheduler] Marked stale session as failed: {session.session_id}")
        if stale:
            db.commit()
    finally:
        db.close()


scheduler = BackgroundScheduler(timezone="UTC")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    scheduler.add_job(cron_job, trigger="interval", minutes=1, id="stale_check_cron")
    scheduler.start()
    print("[Scheduler] Started — checking for stale sessions every 1 minute")

    yield

    scheduler.shutdown(wait=False)
    print("[Scheduler] Stopped")


app = FastAPI(
    title="Deployment Manager API",
    description="CRUD for deployment sessions. Bat execution handled by remote deployment_agent.py on central laptop.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(deployment.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Deployment Manager API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "scheduler_running": scheduler.running}
