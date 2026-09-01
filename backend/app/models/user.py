from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(String(64), primary_key=True, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(
        Enum("ADMIN", "CONSULTANT", "EXECUTIVE_VIEWER", name="user_roles"),
        nullable=False,
        default="CONSULTANT"
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Department(Base):
    __tablename__ = "departments"

    department_id = Column(String(32), primary_key=True)
    department_name = Column(String(100), nullable=False)
    cost_per_hour = Column(String(32), nullable=False, default="45.00") # stored as numeric/decimal string
    created_at = Column(DateTime, default=datetime.utcnow)
