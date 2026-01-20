from sqlalchemy import Column, Integer, String
from app.models import Base  # Base global declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)

    # "admin" ou "customer"
    role = Column(String(20), nullable=False, default="customer")
