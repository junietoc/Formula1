from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    Text,
    Integer,
    SmallInteger,
    Date,
    Index,
)
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


# ------------------------
# Nuevas enumeraciones
# ------------------------


class SanctionStatusEnum(enum.Enum):
    activa = "activa"
    expirada = "expirada"
    apelada = "apelada"


class ReservationStatusEnum(enum.Enum):
    activa = "activa"
    cumplida = "cumplida"
    cancelada = "cancelada"
    expirada = "expirada"


class IncidentTypeEnum(enum.Enum):
    accidente = "accidente"
    deterioro = "deterioro"
    uso_indebido = "uso_indebido"
    otro = "otro"


class IncidentSeverityEnum(enum.Enum):
    leve = "leve"
    media = "media"
    grave = "grave"
    maxima = "maxima"


class PrivilegeTypeEnum(enum.Enum):
    extra_tiempo = "extra_tiempo"
    reserva = "reserva"
    otro = "otro"


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
    privilege = Column(Enum(PrivilegeTypeEnum))
    favorite_bike_id = Column(UUID(as_uuid=True), ForeignKey("bicycles.id"))

    # Relationships
    loans = relationship("Loan", back_populates="user", foreign_keys="Loan.user_id")
    favorite_bike = relationship("Bicycle", foreign_keys=[favorite_bike_id])
    privileges = relationship("Privilege", back_populates="user", foreign_keys="Privilege.user_id")
    messages_sent = relationship(
        "Message",
        foreign_keys="Message.sender_id",
        back_populates="sender",
    )
    messages_received = relationship(
        "Message",
        foreign_keys="Message.receiver_id",
        back_populates="receiver",
    )


class Bicycle(Base):
    __tablename__ = "bicycles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    serial_number = Column(String(40), unique=True, nullable=False)
    bike_code = Column(String(10), unique=True, nullable=False)
    status = Column(Enum(BikeStatusEnum), default=BikeStatusEnum.disponible)
    current_station_id = Column(UUID(as_uuid=True), ForeignKey("stations.id"))
    last_service_at = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    loans = relationship("Loan", back_populates="bike")
    current_station = relationship("Station", foreign_keys=[current_station_id])
    maintenance_records = relationship("MaintenanceRecord", back_populates="bike")
    incidents = relationship("Incident", back_populates="bike")

    __table_args__ = (
        Index("ix_bicycles_status", "status"),
        Index("ix_bicycles_current_station_id", "current_station_id"),
    )


class Station(Base):
    __tablename__ = "stations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(80))
    geom = Column(Text)  # Placeholder for PostGIS POINT type
    capacity = Column(SmallInteger)
    reserved_bicycles = Column(SmallInteger)
    active = Column(Boolean, default=True)

    # Relationships
    loans_out = relationship(
        "Loan", foreign_keys="Loan.station_out_id", back_populates="station_out"
    )
    loans_in = relationship("Loan", foreign_keys="Loan.station_in_id", back_populates="station_in")
    inventory_reports = relationship("InventoryReport", back_populates="station")


class Loan(Base):
    __tablename__ = "loans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    bike_id = Column(UUID(as_uuid=True), ForeignKey("bicycles.id"), nullable=False)
    station_out_id = Column(UUID(as_uuid=True), ForeignKey("stations.id"), nullable=False)
    operator_out_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    time_out = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    station_in_id = Column(UUID(as_uuid=True), ForeignKey("stations.id"))
    operator_in_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    time_in = Column(DateTime(timezone=True))
    duration_min = Column(Integer)
    status = Column(Enum(LoanStatusEnum), default=LoanStatusEnum.abierto)

    # Relationships
    user = relationship("User", back_populates="loans", foreign_keys=[user_id])
    bike = relationship("Bicycle", back_populates="loans")
    station_out = relationship("Station", foreign_keys=[station_out_id], back_populates="loans_out")
    station_in = relationship("Station", foreign_keys=[station_in_id], back_populates="loans_in")
    operator_out = relationship("User", foreign_keys=[operator_out_id])
    operator_in = relationship("User", foreign_keys=[operator_in_id])

    __table_args__ = (
        Index("ix_loans_user_id", "user_id"),
        Index("ix_loans_bike_id", "bike_id"),
        Index("ix_loans_status", "status"),
    )


# ---------------------------------------------------------------------------
# NUEVAS TABLAS
# ---------------------------------------------------------------------------


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    station_id = Column(UUID(as_uuid=True), ForeignKey("stations.id"))
    bike_id = Column(UUID(as_uuid=True), ForeignKey("bicycles.id"))
    reserved_from = Column(DateTime(timezone=True))
    reserved_until = Column(DateTime(timezone=True))
    status = Column(Enum(ReservationStatusEnum), default=ReservationStatusEnum.activa)

    user = relationship("User")
    station = relationship("Station")
    bike = relationship("Bicycle")


class Evaluation(Base):
    __tablename__ = "evaluations"

    loan_id = Column(
        UUID(as_uuid=True), ForeignKey("loans.id", ondelete="CASCADE"), primary_key=True
    )
    stars = Column(SmallInteger)
    comment = Column(Text)
    evaluator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    loan = relationship("Loan")
    evaluator = relationship("User")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id = Column(UUID(as_uuid=True), ForeignKey("loans.id"))
    bike_id = Column(UUID(as_uuid=True), ForeignKey("bicycles.id"))
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    return_report_id = Column(UUID(as_uuid=True), ForeignKey("return_reports.id"))
    type = Column(Enum(IncidentTypeEnum))
    severity = Column(SmallInteger)  # 1=leve, 2=media, 3=grave, 4=maxima
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)

    loan = relationship("Loan")
    bike = relationship("Bicycle", back_populates="incidents")
    reporter = relationship("User")
    return_report = relationship("ReturnReport", back_populates="incidents")

    __table_args__ = (Index("ix_incidents_bike_id", "bike_id"),)


class Sanction(Base):
    __tablename__ = "sanctions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"))
    operator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(SanctionStatusEnum), default=SanctionStatusEnum.activa)
    appeal_text = Column(Text)
    appeal_response = Column(Text)

    user = relationship("User", foreign_keys=[user_id])
    incident = relationship("Incident")
    operator = relationship("User", foreign_keys=[operator_id])

    __table_args__ = (Index("ix_sanctions_user_id", "user_id"),)


class Privilege(Base):
    __tablename__ = "privileges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    type = Column(Enum(PrivilegeTypeEnum))
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))

    user = relationship("User", foreign_keys=[user_id], back_populates="privileges")
    granter = relationship("User", foreign_keys=[granted_by])


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    receiver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    subject = Column(String(120))
    body = Column(Text)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True))

    sender = relationship("User", foreign_keys=[sender_id], back_populates="messages_sent")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="messages_received")


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bike_id = Column(UUID(as_uuid=True), ForeignKey("bicycles.id"))
    description = Column(Text)
    performed_at = Column(DateTime(timezone=True), server_default=func.now())

    bike = relationship("Bicycle", back_populates="maintenance_records")


class InventoryReport(Base):
    __tablename__ = "inventory_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    station_id = Column(UUID(as_uuid=True), ForeignKey("stations.id"))
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    report_date = Column(Date, nullable=False)
    available_qty = Column(SmallInteger)
    workshop_qty = Column(SmallInteger)
    notes = Column(Text)

    station = relationship("Station", back_populates="inventory_reports")
    reporter = relationship("User")


class ReturnReport(Base):
    __tablename__ = "return_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id = Column(UUID(as_uuid=True), ForeignKey("loans.id"), nullable=False)
    total_incident_days = Column(Integer, default=0)  # Suma total de días de todos los incidentes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    loan = relationship("Loan")
    creator = relationship("User")
    incidents = relationship("Incident", back_populates="return_report")

    __table_args__ = (Index("ix_return_reports_loan_id", "loan_id"),)
