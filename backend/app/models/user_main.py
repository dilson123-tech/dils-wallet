from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import synonym

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # DB real (Postgres): email NOT NULL + UNIQUE
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)

    # DB real: password_hash (bcrypt)
    hashed_password = Column("password_hash", String(255), nullable=False)

    # DB real: type (admin/customer)
    role = Column("type", String(20), nullable=False, default="customer")

    # Compat: código antigo que usa username continua funcionando (aponta pro email)
    username = synonym("email")
