from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Enum, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.db.base import Base

class ProcessDefinition(Base):
    __tablename__ = "process_definitions"

    process_id = Column(String(32), primary_key=True)
    process_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    sla_hours_target = Column(Float, nullable=False, default=120.0) # 5 business days
    target_cost = Column(Float, nullable=False, default=300.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    instances = relationship("ProcessInstance", back_populates="definition")

class ProcessInstance(Base):
    __tablename__ = "process_instances"

    case_id = Column(String(64), primary_key=True, index=True)
    process_id = Column(String(32), ForeignKey("process_definitions.process_id"), nullable=False)
    requester_id = Column(String(64), nullable=False)
    department_id = Column(String(32), ForeignKey("departments.department_id"), nullable=False)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    current_status = Column(
        Enum("IN_PROGRESS", "COMPLETED", "CANCELLED", "REJECTED", name="case_statuses"),
        nullable=False,
        default="IN_PROGRESS",
        index=True
    )
    total_duration_hours = Column(Float, nullable=True)
    is_sla_breached = Column(Boolean, nullable=False, default=False)
    predicted_breach_probability = Column(Float, nullable=True)
    variant_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    definition = relationship("ProcessDefinition", back_populates="instances")
    events = relationship("ProcessEventLog", back_populates="instance", cascade="all, delete-orphan", order_by="ProcessEventLog.event_timestamp")

    __table_args__ = (
        Index("idx_case_dept_time", "department_id", "start_time"),
    )

class ProcessEventLog(Base):
    __tablename__ = "process_event_logs"

    event_id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), ForeignKey("process_instances.case_id", ondelete="CASCADE"), nullable=False)
    activity_name = Column(String(100), nullable=False, index=True)
    stage_order = Column(Integer, nullable=False)
    actor_id = Column(String(64), nullable=False)
    department_id = Column(String(32), ForeignKey("departments.department_id"), nullable=False)
    event_timestamp = Column(DateTime, nullable=False, index=True)
    activity_status = Column(
        Enum("STARTED", "COMPLETED", "REJECTED", "REWORK_TRIGGERED", name="activity_statuses"),
        nullable=False,
        default="COMPLETED"
    )
    cost_incurred = Column(Float, nullable=False, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    instance = relationship("ProcessInstance", back_populates="events")

    __table_args__ = (
        Index("idx_case_time", "case_id", "event_timestamp"),
        Index("idx_activity_time", "activity_name", "event_timestamp"),
        Index("idx_dept_time", "department_id", "event_timestamp"),
    )
