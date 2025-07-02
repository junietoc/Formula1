from sqlalchemy.orm import Session
from models import User, Bicycle, Station, Loan, UserRoleEnum, UserAffiliationEnum, BikeStatusEnum, LoanStatusEnum
from datetime import datetime
import uuid

class UserService:
    @staticmethod
    def create_user(db: Session, cedula: str, carnet: str, full_name: str, email: str, 
                   affiliation: UserAffiliationEnum, role: UserRoleEnum = UserRoleEnum.usuario) -> User:
        """Create a new user (user or operator with admin privileges)"""
        user = User(
            cedula=cedula,
            carnet=carnet,
            full_name=full_name,
            email=email,
            affiliation=affiliation,
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_user_by_cedula(db: Session, cedula: str) -> User:
        """Get user by cedula"""
        return db.query(User).filter(User.cedula == cedula).first()
    
    @staticmethod
    def get_user_by_carnet(db: Session, carnet: str) -> User:
        """Get user by carnet"""
        return db.query(User).filter(User.carnet == carnet).first()

class BicycleService:
    @staticmethod
    def get_available_bicycles(db: Session) -> list[Bicycle]:
        """Get all available bicycles"""
        return db.query(Bicycle).filter(Bicycle.status == BikeStatusEnum.disponible).all()
    
    @staticmethod
    def get_bicycle_by_code(db: Session, bike_code: str) -> Bicycle:
        """Get bicycle by bike_code"""
        return db.query(Bicycle).filter(Bicycle.bike_code == bike_code).first()
    
    @staticmethod
    def update_bicycle_status(db: Session, bicycle: Bicycle, status: BikeStatusEnum):
        """Update bicycle status"""
        bicycle.status = status
        db.commit()
        db.refresh(bicycle)

class StationService:
    @staticmethod
    def get_all_stations(db: Session) -> list[Station]:
        """Get all stations"""
        return db.query(Station).all()
    
    @staticmethod
    def get_station_by_code(db: Session, code: str) -> Station:
        """Get station by code"""
        return db.query(Station).filter(Station.code == code).first()

class LoanService:
    @staticmethod
    def create_loan(db: Session, user_id: uuid.UUID, bike_id: uuid.UUID, 
                   station_out_id: uuid.UUID) -> Loan:
        """Register a loan (bike check-out)"""
        # Create the loan
        loan = Loan(
            user_id=user_id,
            bike_id=bike_id,
            station_out_id=station_out_id,
            status=LoanStatusEnum.abierto
        )
        db.add(loan)
        
        # Update bicycle status to 'prestada'
        bicycle = db.query(Bicycle).filter(Bicycle.id == bike_id).first()
        if bicycle:
            bicycle.status = BikeStatusEnum.prestada
        
        db.commit()
        db.refresh(loan)
        return loan
    
    @staticmethod
    def return_loan(db: Session, loan_id: uuid.UUID, station_in_id: uuid.UUID) -> Loan:
        """Register a return (loan close)"""
        loan = db.query(Loan).filter(Loan.id == loan_id).first()
        if not loan:
            raise ValueError("Loan not found")
        
        if loan.status != LoanStatusEnum.abierto:
            raise ValueError("Loan is not open")
        
        # Update loan
        loan.station_in_id = station_in_id
        loan.time_in = datetime.utcnow()
        loan.status = LoanStatusEnum.cerrado
        
        # Update bicycle status back to 'disponible'
        bicycle = db.query(Bicycle).filter(Bicycle.id == loan.bike_id).first()
        if bicycle:
            bicycle.status = BikeStatusEnum.disponible
        
        db.commit()
        db.refresh(loan)
        return loan
    
    @staticmethod
    def get_open_loans_by_user(db: Session, user_id: uuid.UUID) -> list[Loan]:
        """Get all open loans for a user"""
        return db.query(Loan).filter(
            Loan.user_id == user_id,
            Loan.status == LoanStatusEnum.abierto
        ).all()
    
    @staticmethod
    def get_loan_by_id(db: Session, loan_id: uuid.UUID) -> Loan:
        """Get loan by ID"""
        return db.query(Loan).filter(Loan.id == loan_id).first() 