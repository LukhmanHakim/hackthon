from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


# ── Deployment Session ────────────────────────────────────────────────────────

class DeploymentSessionCreate(BaseModel):
    project: str
    client: str
    status: Optional[str] = "pending"


class DeploymentSessionUpdate(BaseModel):
    project: Optional[str] = None
    client: Optional[str] = None
    status: Optional[str] = None


class DeploymentLogResponse(BaseModel):
    log_id: str
    session_id: str
    datetime: datetime
    description: str

    model_config = {"from_attributes": True}


class DeploymentSessionResponse(BaseModel):
    session_id: str
    datetime: datetime
    project: str
    client: str
    status: str

    model_config = {"from_attributes": True}


class DeploymentSessionDetail(DeploymentSessionResponse):
    logs: List[DeploymentLogResponse] = []


# ── Deployment Log ────────────────────────────────────────────────────────────

class DeploymentLogCreate(BaseModel):
    description: str
