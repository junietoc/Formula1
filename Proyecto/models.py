from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

Base = declarative_base()

class UserRoleEnum(enum.Enum):
    usuario = "usuario"
    operador = "operador"
    admin = "admin"

class UserAffiliationEnum(enum.Enum):
    estudiante = "estudiante"
    docente = "docente"
    administrativo = "administrativo"

class BikeStatusEnum(enum.Enum):
    disponible = "disponible"
    prestada = "prestada"
    mantenimiento = "mantenimiento"
    retirada = "retirada"

class LoanStatusEnum(enum.Enum):
    abierto = "abierto"
    cerrado = "cerrado"
    tardio = "tardio"
    perdido = "perdido"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cedula = Column(String(15), unique=True, nullable=False)
    carnet = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False)
    affiliation = Column(Enum(UserAffiliationEnum))
    role = Column(Enum(UserRoleEnum), default=UserRoleEnum.usuario)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    loans = relationship("Loan", back_populates="user")

class Bicycle(Base):
    __tablename__ = "bicycles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    serial_number = Column(String(40), unique=True, nullable=False)
    bike_code = Column(String(10), unique=True, nullable=False)
    status = Column(Enum(BikeStatusEnum), default=BikeStatusEnum.disponible)
    
    # Relationships
    loans = relationship("Loan", back_populates="bike")

class Station(Base):
    __tablename__ = "stations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(80))
    
    # Relationships
    loans_out = relationship("Loan", foreign_keys="Loan.station_out_id", back_populates="station_out")
    loans_in = relationship("Loan", foreign_keys="Loan.station_in_id", back_populates="station_in")

class Loan(Base):
    __tablename__ = "loans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    bike_id = Column(UUID(as_uuid=True), ForeignKey("bicycles.id"), nullable=False)
    station_out_id = Column(UUID(as_uuid=True), ForeignKey("stations.id"), nullable=False)
    time_out = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    station_in_id = Column(UUID(as_uuid=True), ForeignKey("stations.id"))
    time_in = Column(DateTime(timezone=True))
    status = Column(Enum(LoanStatusEnum), default=LoanStatusEnum.abierto)
    
    # Relationships
    user = relationship("User", back_populates="loans")
    bike = relationship("Bicycle", back_populates="loans")
    station_out = relationship("Station", foreign_keys=[station_out_id], back_populates="loans_out")
    station_in = relationship("Station", foreign_keys=[station_in_id], back_populates="loans_in") 