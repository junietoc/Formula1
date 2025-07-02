import flet as ft
from database import get_db, create_tables
from services import UserService, BicycleService, StationService, LoanService
from models import User, Bicycle, Station, Loan, UserRoleEnum, UserAffiliationEnum, BikeStatusEnum, LoanStatusEnum
import uuid

class BikeLoanApp:
    def __init__(self):
        self.db = next(get_db())
        self.current_user = None
        
    def main(self, page: ft.Page):
        self.page = page  # Store page reference
        page.title = "Sistema de Préstamo de Bicicletas"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.window_width = 1000
        page.window_height = 700
        page.window_resizable = True
        page.padding = 20
        
        # Initialize database
        create_tables()
        
        # Create sample data if empty
        self.create_sample_data()
        
        # Main navigation
        self.nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.icons.PERSON_ADD,
                    selected_icon=ft.icons.PERSON_ADD,
                    label="Crear Usuario",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.DIRECTIONS_BIKE,
                    selected_icon=ft.icons.DIRECTIONS_BIKE,
                    label="Registrar Préstamo",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.ASSIGNMENT_RETURN,
                    selected_icon=ft.icons.ASSIGNMENT_RETURN,
                    label="Registrar Devolución",
                ),
            ],
            on_change=self.nav_change
        )
        
        # Content area
        self.content_area = ft.Container(
            content=ft.Text("Seleccione una opción del menú", size=20),
            expand=True,
            padding=20
        )
        
        # Layout
        page.add(
            ft.Row(
                [
                    self.nav_rail,
                    ft.VerticalDivider(width=1),
                    self.content_area,
                ],
                expand=True,
            )
        )
        
        # Show initial view
        self.show_create_user_view()
    
    def nav_change(self, e):
        index = e.control.selected_index
        if index == 0:
            self.show_create_user_view()
        elif index == 1:
            self.show_loan_view()
        elif index == 2:
            self.show_return_view()
    
    def show_create_user_view(self):
        page = self.page  # Get reference to the page
        
        # Form fields
        cedula_field = ft.TextField(
            label="Cédula",
            hint_text="Ingrese la cédula",
            width=300
        )
        
        carnet_field = ft.TextField(
            label="Carnet",
            hint_text="Ingrese el carnet",
            width=300
        )
        
        name_field = ft.TextField(
            label="Nombre Completo",
            hint_text="Ingrese el nombre completo",
            width=300
        )
        
        email_field = ft.TextField(
            label="Email",
            hint_text="Ingrese el email",
            width=300
        )
        
        affiliation_dropdown = ft.Dropdown(
            label="Afiliación",
            width=300,
            options=[
                ft.dropdown.Option("estudiante", "Estudiante"),
                ft.dropdown.Option("docente", "Docente"),
                ft.dropdown.Option("administrativo", "Administrativo"),
            ]
        )
        
        role_dropdown = ft.Dropdown(
            label="Rol",
            width=300,
            options=[
                ft.dropdown.Option("usuario", "Usuario"),
                ft.dropdown.Option("operador", "Operador"),
                ft.dropdown.Option("admin", "Administrador"),
            ],
            value="usuario"
        )
        
        result_text = ft.Text("", color=ft.colors.GREEN)
        
        def create_user(e):
            try:
                # Validate required fields
                if not all([cedula_field.value, carnet_field.value, name_field.value, 
                           email_field.value, affiliation_dropdown.value]):
                    result_text.value = "Todos los campos son obligatorios"
                    result_text.color = ft.colors.RED
                    page.update()
                    return
                
                # Check if user already exists
                existing_user = UserService.get_user_by_cedula(self.db, cedula_field.value)
                if existing_user:
                    result_text.value = "Ya existe un usuario con esta cédula"
                    result_text.color = ft.colors.RED
                    page.update()
                    return
                
                existing_user = UserService.get_user_by_carnet(self.db, carnet_field.value)
                if existing_user:
                    result_text.value = "Ya existe un usuario con este carnet"
                    result_text.color = ft.colors.RED
                    page.update()
                    return
                
                # Create user
                user = UserService.create_user(
                    self.db,
                    cedula=cedula_field.value,
                    carnet=carnet_field.value,
                    full_name=name_field.value,
                    email=email_field.value,
                    affiliation=UserAffiliationEnum(affiliation_dropdown.value),
                    role=UserRoleEnum(role_dropdown.value)
                )
                
                result_text.value = f"Usuario creado exitosamente: {user.full_name}"
                result_text.color = ft.colors.GREEN
                
                # Clear fields
                cedula_field.value = ""
                carnet_field.value = ""
                name_field.value = ""
                email_field.value = ""
                affiliation_dropdown.value = None
                role_dropdown.value = "usuario"
                
                page.update()
                
            except Exception as ex:
                result_text.value = f"Error: {str(ex)}"
                result_text.color = ft.colors.RED
                page.update()
        
        create_button = ft.ElevatedButton(
            "Crear Usuario",
            on_click=create_user,
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.BLUE,
            )
        )
        
        self.content_area.content = ft.Column([
            ft.Text("Crear Nuevo Usuario", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            cedula_field,
            carnet_field,
            name_field,
            email_field,
            affiliation_dropdown,
            role_dropdown,
            ft.Container(height=20),
            create_button,
            ft.Container(height=20),
            result_text
        ])
        page.update()
    
    def show_loan_view(self):
        page = self.page  # Get reference to the page
        
        # Form fields
        user_cedula_field = ft.TextField(
            label="Cédula del Usuario",
            hint_text="Ingrese la cédula del usuario",
            width=300
        )
        
        bike_code_field = ft.TextField(
            label="Código de Bicicleta",
            hint_text="Ingrese el código de la bicicleta",
            width=300
        )
        
        station_code_field = ft.TextField(
            label="Código de Estación",
            hint_text="Ingrese el código de la estación",
            width=300
        )
        
        result_text = ft.Text("", color=ft.colors.GREEN)
        
        def register_loan(e):
            try:
                # Validate required fields
                if not all([user_cedula_field.value, bike_code_field.value, station_code_field.value]):
                    result_text.value = "Todos los campos son obligatorios"
                    result_text.color = ft.colors.RED
                    page.update()
                    return
                
                # Get user
                user = UserService.get_user_by_cedula(self.db, user_cedula_field.value)
                if not user:
                    result_text.value = "Usuario no encontrado"
                    result_text.color = ft.colors.RED
                    page.update()
                    return
                
                # Get bicycle
                bicycle = BicycleService.get_bicycle_by_code(self.db, bike_code_field.value)
                if not bicycle:
                    result_text.value = "Bicicleta no encontrada"
                    result_text.color = ft.colors.RED
                    page.update()
                    return
                
                if bicycle.status != BikeStatusEnum.disponible:
                    result_text.value = "La bicicleta no está disponible"
                    result_text.color = ft.colors.RED
                    page.update()
                    return
                
                # Get station
                station = StationService.get_station_by_code(self.db, station_code_field.value)
                if not station:
                    result_text.value = "Estación no encontrada"
                    result_text.color = ft.colors.RED
                    page.update()
                    return
                
                # Create loan
                loan = LoanService.create_loan(
                    self.db,
                    user_id=user.id,
                    bike_id=bicycle.id,
                    station_out_id=station.id
                )
                
                result_text.value = f"Préstamo registrado exitosamente. ID: {loan.id}"
                result_text.color = ft.colors.GREEN
                
                # Clear fields
                user_cedula_field.value = ""
                bike_code_field.value = ""
                station_code_field.value = ""
                
                page.update()
                
            except Exception as ex:
                result_text.value = f"Error: {str(ex)}"
                result_text.color = ft.colors.RED
                page.update()
        
        loan_button = ft.ElevatedButton(
            "Registrar Préstamo",
            on_click=register_loan,
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.GREEN,
            )
        )
        
        self.content_area.content = ft.Column([
            ft.Text("Registrar Préstamo de Bicicleta", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            user_cedula_field,
            bike_code_field,
            station_code_field,
            ft.Container(height=20),
            loan_button,
            ft.Container(height=20),
            result_text
        ])
        page.update()
    
    def show_return_view(self):
        page = self.page  # Get reference to the page
        
        # Form fields
        loan_id_field = ft.TextField(
            label="ID del Préstamo",
            hint_text="Ingrese el ID del préstamo",
            width=300
        )
        
        station_code_field = ft.TextField(
            label="Código de Estación de Devolución",
            hint_text="Ingrese el código de la estación",
            width=300
        )
        
        result_text = ft.Text("", color=ft.colors.GREEN)
        
        def register_return(e):
            try:
                # Validate required fields
                if not all([loan_id_field.value, station_code_field.value]):
                    result_text.value = "Todos los campos son obligatorios"
                    result_text.color = ft.colors.RED
                    page.update()
                    return
                
                # Get loan
                try:
                    loan_id = uuid.UUID(loan_id_field.value)
                except ValueError:
                    result_text.value = "ID de préstamo inválido"
                    result_text.color = ft.colors.RED
                    page.update()
                    return
                
                loan = LoanService.get_loan_by_id(self.db, loan_id)
                if not loan:
                    result_text.value = "Préstamo no encontrado"
                    result_text.color = ft.colors.RED
                    page.update()
                    return
                
                if loan.status != LoanStatusEnum.abierto:
                    result_text.value = "El préstamo no está abierto"
                    result_text.color = ft.colors.RED
                    page.update()
                    return
                
                # Get station
                station = StationService.get_station_by_code(self.db, station_code_field.value)
                if not station:
                    result_text.value = "Estación no encontrada"
                    result_text.color = ft.colors.RED
                    page.update()
                    return
                
                # Return loan
                returned_loan = LoanService.return_loan(
                    self.db,
                    loan_id=loan_id,
                    station_in_id=station.id
                )
                
                result_text.value = f"Devolución registrada exitosamente. Préstamo cerrado."
                result_text.color = ft.colors.GREEN
                
                # Clear fields
                loan_id_field.value = ""
                station_code_field.value = ""
                
                page.update()
                
            except Exception as ex:
                result_text.value = f"Error: {str(ex)}"
                result_text.color = ft.colors.RED
                page.update()
        
        return_button = ft.ElevatedButton(
            "Registrar Devolución",
            on_click=register_return,
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.ORANGE,
            )
        )
        
        self.content_area.content = ft.Column([
            ft.Text("Registrar Devolución de Bicicleta", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            loan_id_field,
            station_code_field,
            ft.Container(height=20),
            return_button,
            ft.Container(height=20),
            result_text
        ])
        page.update()
    
    def create_sample_data(self):
        """Create sample data for testing"""
        # Check if data already exists
        if self.db.query(User).first():
            return
        
        # Create sample stations
        station1 = Station(code="EST001", name="Estación Central")
        station2 = Station(code="EST002", name="Estación Norte")
        station3 = Station(code="EST003", name="Estación Sur")
        
        self.db.add_all([station1, station2, station3])
        self.db.commit()
        
        # Create sample bicycles
        bike1 = Bicycle(serial_number="BIKE001", bike_code="B001", status=BikeStatusEnum.disponible)
        bike2 = Bicycle(serial_number="BIKE002", bike_code="B002", status=BikeStatusEnum.disponible)
        bike3 = Bicycle(serial_number="BIKE003", bike_code="B003", status=BikeStatusEnum.disponible)
        
        self.db.add_all([bike1, bike2, bike3])
        self.db.commit()
        
        # Create sample admin user
        admin_user = User(
            cedula="12345678",
            carnet="ADMIN001",
            full_name="Administrador Sistema",
            email="admin@universidad.edu",
            affiliation=UserAffiliationEnum.administrativo,
            role=UserRoleEnum.admin
        )
        
        self.db.add(admin_user)
        self.db.commit()

if __name__ == "__main__":
    app = BikeLoanApp()
    ft.app(target=app.main) 