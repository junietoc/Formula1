from sqlalchemy.orm import Session
from models import (
    User,
    Bicycle,
    Station,
    Loan,
    UserRoleEnum,
    UserAffiliationEnum,
    BikeStatusEnum,
    LoanStatusEnum,
)
from datetime import datetime
import uuid
from datetime import timezone, timedelta
from sqlalchemy import or_

# Zona horaria de Colombia (UTC-5)
CO_TZ = timezone(timedelta(hours=-5))


class UserService:
    @staticmethod
    def create_user(
        db: Session,
        cedula: str,
        carnet: str,
        full_name: str,
        email: str,
        affiliation: UserAffiliationEnum,
        role: UserRoleEnum = UserRoleEnum.usuario,
    ) -> User:
        """Create a new user (user or operator with admin privileges)"""
        # Generate a unique carnet if empty
        if not carnet or carnet.strip() == "":
            carnet = f"USER_{cedula}"

        user = User(
            cedula=cedula,
            carnet=carnet,
            full_name=full_name,
            email=email,
            affiliation=affiliation,
            role=role,
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
    def create_loan(
        db: Session,
        user_id: uuid.UUID,
        bike_id: uuid.UUID,
        station_out_id: uuid.UUID,
        station_in_id: uuid.UUID | None = None,
    ) -> Loan:
        """Register a loan (bike check-out)"""
        # Create the loan con timestamp en hora local de Colombia
        loan = Loan(
            user_id=user_id,
            bike_id=bike_id,
            station_out_id=station_out_id,
            station_in_id=station_in_id,
            status=LoanStatusEnum.abierto,
            time_out=datetime.now(CO_TZ),
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
        loan.time_in = datetime.now(CO_TZ)
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
        return (
            db.query(Loan)
            .filter(Loan.user_id == user_id, Loan.status == LoanStatusEnum.abierto)
            .all()
        )

    @staticmethod
    def get_loan_by_id(db: Session, loan_id: uuid.UUID) -> Loan:
        """Get loan by ID"""
        return db.query(Loan).filter(Loan.id == loan_id).first()

    @staticmethod
    def get_open_loans_by_user_cedula(db: Session, cedula: str) -> list[Loan]:
        """Get all open loans for a user by cedula"""
        return (
            db.query(Loan)
            .join(User, Loan.user_id == User.id)
            .filter(User.cedula == cedula, Loan.status == LoanStatusEnum.abierto)
            .all()
        )

    @staticmethod
    def get_loan_history_by_cedula(db: Session, cedula: str) -> list[Loan]:
        """Get all loans (open and closed) for a user by cedula, ordered by time_out descending"""
        return (
            db.query(Loan)
            .join(User, Loan.user_id == User.id)
            .filter(User.cedula == cedula)
            .order_by(Loan.time_out.desc())
            .all()
        )

    @staticmethod
    def get_loans_by_user(db: Session, user_id: uuid.UUID) -> list[Loan]:
        """Get all loans for a user by user_id, ordered by time_out descending"""
        return (
            db.query(Loan)
            .filter(Loan.user_id == user_id)
            .order_by(Loan.time_out.desc())
            .all()
        )

    @staticmethod
    def get_all_loans(db: Session) -> list[Loan]:
        """Get all loans ordered by latest time_out first"""
        return db.query(Loan).order_by(Loan.time_out.desc()).all()

    @staticmethod
    def get_loans_by_station_code(db: Session, station_code: str) -> list[Loan]:
        """Get all loans (out or in) associated with a station code, ordered by latest"""
        # Filter loans where either the outgoing or incoming station matches the code
        return (
            db.query(Loan)
            .join(Station, or_(Loan.station_out_id == Station.id, Loan.station_in_id == Station.id))
            .filter(Station.code == station_code)
            .order_by(Loan.time_out.desc())
            .all()
        )


class FavoriteBikeService:
    @staticmethod
    def get_user_favorite_bike(db: Session, user_id: uuid.UUID) -> Bicycle | None:
        """Get the favorite bike for a user"""
        user = db.query(User).filter(User.id == user_id).first()
        return user.favorite_bike if user else None

    @staticmethod
    def get_user_favorite_bike_by_cedula(db: Session, cedula: str) -> Bicycle | None:
        """Get the favorite bike for a user by cedula"""
        user = UserService.get_user_by_cedula(db, cedula)
        return user.favorite_bike if user else None

    @staticmethod
    def get_bikes_used_by_user(db: Session, user_id: uuid.UUID) -> list[Bicycle]:
        """Get all bikes that a user has used in their loan history"""
        loans = LoanService.get_loans_by_user(db, user_id)
        used_bikes = []
        seen_bikes = set()
        
        for loan in loans:
            if loan.bike and loan.bike.id not in seen_bikes:
                used_bikes.append(loan.bike)
                seen_bikes.add(loan.bike.id)
        
        return used_bikes

    @staticmethod
    def get_bikes_used_by_user_cedula(db: Session, cedula: str) -> list[Bicycle]:
        """Get all bikes that a user has used in their loan history by cedula"""
        loans = LoanService.get_loan_history_by_cedula(db, cedula)
        used_bikes = []
        seen_bikes = set()
        
        for loan in loans:
            if loan.bike and loan.bike.id not in seen_bikes:
                used_bikes.append(loan.bike)
                seen_bikes.add(loan.bike.id)
        
        return used_bikes

    @staticmethod
    def set_favorite_bike(db: Session, user_id: uuid.UUID, bike_id: uuid.UUID) -> bool:
        """Set a bike as favorite for a user"""
        # Check if the bike is already someone else's favorite
        existing_favorite = db.query(User).filter(User.favorite_bike_id == bike_id).first()
        if existing_favorite and existing_favorite.id != user_id:
            return False  # Bike is already someone else's favorite
        
        # Check if user has used this bike before
        user_loans = LoanService.get_loans_by_user(db, user_id)
        user_has_used_bike = any(loan.bike_id == bike_id for loan in user_loans)
        
        if not user_has_used_bike:
            return False  # User hasn't used this bike
        
        # Set the favorite bike
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.favorite_bike_id = bike_id
            db.commit()
            db.refresh(user)
            return True
        
        return False

    @staticmethod
    def set_favorite_bike_by_cedula(db: Session, cedula: str, bike_id: uuid.UUID) -> bool:
        """Set a bike as favorite for a user by cedula"""
        user = UserService.get_user_by_cedula(db, cedula)
        if not user:
            return False
        
        return FavoriteBikeService.set_favorite_bike(db, user.id, bike_id)

    @staticmethod
    def remove_favorite_bike(db: Session, user_id: uuid.UUID) -> bool:
        """Remove the favorite bike for a user"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.favorite_bike_id = None
            db.commit()
            db.refresh(user)
            return True
        return False

    @staticmethod
    def remove_favorite_bike_by_cedula(db: Session, cedula: str) -> bool:
        """Remove the favorite bike for a user by cedula"""
        user = UserService.get_user_by_cedula(db, cedula)
        if not user:
            return False
        
        return FavoriteBikeService.remove_favorite_bike(db, user.id)

    @staticmethod
    def get_favorite_bike_owner(db: Session, bike_id: uuid.UUID) -> User | None:
        """Get the user who has this bike as favorite"""
        return db.query(User).filter(User.favorite_bike_id == bike_id).first()

    @staticmethod
    def is_bike_favorite(db: Session, bike_id: uuid.UUID) -> bool:
        """Check if a bike is someone's favorite"""
        return db.query(User).filter(User.favorite_bike_id == bike_id).first() is not None
