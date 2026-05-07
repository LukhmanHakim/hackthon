import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


class DeploymentSession(Base):
    __tablename__ = "deployment_session"

    session_id = Column(String(36), primary_key=True, default=new_uuid)
    datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    project = Column(String(255), nullable=False)
    client = Column(String(255), nullable=False)
    # pending | running | success | failed
    status = Column(String(50), default="pending", nullable=False)

    logs = relationship(
        "DeploymentLog",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="DeploymentLog.datetime",
    )


class DeploymentLog(Base):
    __tablename__ = "deployment_log"

    log_id = Column(String(36), primary_key=True, default=new_uuid)
    session_id = Column(
        String(36),
        ForeignKey("deployment_session.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    description = Column(Text, nullable=False)

    session = relationship("DeploymentSession", back_populates="logs")
