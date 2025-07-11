import flet as ft
from database import get_db, create_tables
from services import UserService, BicycleService, StationService, LoanService
from models import User, Bicycle, Station, Loan, UserRoleEnum, UserAffiliationEnum, BikeStatusEnum, LoanStatusEnum
import uuid

class VeciRunApp:
    def __init__(self):
        self.db = next(get_db())
        self.current_user = None
        
    def main(self, page: ft.Page):
        self.page = page  # Store page reference
        page.title = "VeciRun"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.window_maximized = True
        page.window_resizable = True
        page.padding = 20
        
        # Initialize database
        create_tables()
        
        # Create sample data if empty
        self.create_sample_data()
        
        # Main navigation (will be updated based on role)
        self.nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            destinations=[],
            on_change=self.nav_change
        )
        
        # Content area
        self.content_area = ft.Container(
            content=ft.Text("Seleccione una opción del menú", size=20),
            expand=True,
            padding=20
        )
        
        # Layout
        self.main_row = ft.Row(
            [
                self.nav_rail,
                ft.VerticalDivider(width=1),
                self.content_area,
            ],
            expand=True,
        )
        page.add(self.main_row)
        
        # Initially hide the navigation rail
        self.nav_rail.visible = False
        
        # Show initial view
        self.show_home_view()
        
        # Initialize role-based navigation
        self.update_navigation_for_role("regular")
    
    def nav_change(self, e):
        # If no destinations, don't handle navigation
        if not e.control.destinations:
            return
            
        index = e.control.selected_index
        if index == 0:
            # Show dashboard instead of home view when signed in
            if hasattr(self, 'current_user_role') and self.current_user_role:
                self.show_dashboard_view()
            else:
                self.show_home_view()
        elif index == 1:
            if hasattr(self, 'current_user_role') and self.current_user_role == "admin":
                self.show_create_user_view()
            else:
                self.show_availability_view()
        elif index == 2:
            if hasattr(self, 'current_user_role') and self.current_user_role == "admin":
                self.show_loan_view()
        elif index == 3:
            if hasattr(self, 'current_user_role') and self.current_user_role == "admin":
                self.show_return_view()
    
    def show_create_user_view(self):
        page = self.page  # Get reference to the page
        
        # Form fields
        cedula_field = ft.TextField(
            label="Cédula",
            hint_text="Ingrese la cédula",
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
                if not all([cedula_field.value, name_field.value, 
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
                
                # Create user
                user = UserService.create_user(
                    self.db,
                    cedula=cedula_field.value,
                    carnet="",  # Empty carnet since it's not required
                    full_name=name_field.value,
                    email=email_field.value,
                    affiliation=UserAffiliationEnum(affiliation_dropdown.value),
                    role=UserRoleEnum(role_dropdown.value)
                )
                
                result_text.value = f"Usuario creado exitosamente: {user.full_name}"
                result_text.color = ft.colors.GREEN
                
                # Clear fields
                cedula_field.value = ""
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
            name_field,
            email_field,
            affiliation_dropdown,
            role_dropdown,
            ft.Container(height=20),
            create_button,
            ft.Container(height=20),
            result_text
        ], scroll=ft.ScrollMode.AUTO)
        page.update()
    
    def show_home_view(self):
        print("show_home_view")
        page = self.page
        
        # Check if user is already signed in
        if hasattr(self, 'current_user_role') and self.current_user_role:
            self.show_dashboard_view()
            return
        
        # Create the controls and store references
        def create_controls():
            # Create role dropdown
            role_dropdown = ft.Dropdown(
                label="Rol de Usuario",
                width=350,
                options=[
                    ft.dropdown.Option("regular", "Usuario Regular"),
                    ft.dropdown.Option("admin", "Administrador"),
                ],
                value="regular",
                border_color=ft.colors.BLUE,
                focused_border_color=ft.colors.BLUE_400
            )
            
            # Create station dropdown
            station_dropdown = ft.Dropdown(
                label="Seleccione una estación",
                width=350,
                options=[
                    ft.dropdown.Option("EST001", "Calle 26"),
                    ft.dropdown.Option("EST002", "Salida al Uriel Gutiérrez"),
                    ft.dropdown.Option("EST003", "Calle 53"),
                    ft.dropdown.Option("EST004", "Calle 45"),
                    ft.dropdown.Option("EST005", "Edificio Ciencia y Tecnología"),
                ],
                visible=False,
                border_color=ft.colors.BLUE,
                focused_border_color=ft.colors.BLUE_400
            )
            
            # Create station container
            station_container = ft.Container(
                content=ft.Column([
                    ft.Text("Estación Asignada", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text("(Requerido para administradores)", size=12, color=ft.colors.GREY_600),
                    ft.Container(height=10),
                    station_dropdown
                ]),
                padding=ft.padding.only(bottom=20),
                visible=False
            )
            
            # Create cedula field for regular users
            cedula_field = ft.TextField(
                label="Cédula",
                hint_text="Ingrese su cédula",
                width=350,
                visible=True  # visible by default for regular users
            )
            
            # Create sign in button
            sign_in_button = ft.ElevatedButton(
                "Iniciar Sesión",
                width=350,
                height=50,
                style=ft.ButtonStyle(
                    color=ft.colors.WHITE,
                    bgcolor=ft.colors.BLUE,
                    shape=ft.RoundedRectangleBorder(radius=10),
                )
            )
            
            # Create status text
            status_text = ft.Text("", visible=False)
            
            # Return controls (added cedula_field)
            return role_dropdown, station_container, station_dropdown, cedula_field, sign_in_button, status_text
        
        # Create controls and get references (added cedula_field)
        role_dropdown, station_container, station_dropdown, cedula_field, sign_in_button, status_text = create_controls()
        
        # Create a beautiful sign-in card
        sign_in_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    # Header with icon
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.DIRECTIONS_BIKE, size=40, color=ft.colors.BLUE),
                            ft.Text("VeciRun", size=32, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE)
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        padding=ft.padding.only(bottom=20)
                    ),
                    
                    # Subtitle
                    ft.Text(
                        "Sistema de Préstamo de Bicicletas Universitario",
                        size=16,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.colors.GREY_600
                    ),
                    
                    ft.Container(height=25),
                    
                    # Role selection with better styling
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Seleccione su rol", size=16, weight=ft.FontWeight.BOLD),
                            ft.Container(height=10),
                            role_dropdown
                        ]),
                        padding=ft.padding.only(bottom=20)
                    ),
                    
                    # NEW: Cedula input for regular users
                    ft.Container(
                        content=cedula_field,
                        padding=ft.padding.only(bottom=20)
                    ),
                    
                    # Station selection (only for admin)
                    station_container,
                    
                    # Sign in button
                    ft.Container(
                        content=sign_in_button,
                        padding=ft.padding.only(top=20)
                    ),
                    
                    # Status message
                    ft.Container(
                        content=status_text,
                        padding=ft.padding.only(top=15)
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=40,
                width=450
            ),
            elevation=8,
            margin=ft.margin.all(20)
        )
        
        def on_role_change(e):
            if role_dropdown.value == "admin":
                station_container.visible = True
                station_dropdown.visible = True
                # Hide cedula input for admin
                cedula_field.visible = False
            else:
                station_container.visible = False
                station_dropdown.visible = False
                station_dropdown.value = None
                # Show cedula input for regular users
                cedula_field.visible = True
            page.update()
        
        role_dropdown.on_change = on_role_change
        
        def sign_in_click(e):
            # Validation for admin role remains the same
            if role_dropdown.value == "admin" and not station_dropdown.value:
                status_text.value = "Por favor seleccione una estación para administradores"
                status_text.color = ft.colors.RED
                status_text.visible = True
                page.update()
                return
            
            # NEW: Validation for regular user login using cedula
            if role_dropdown.value == "regular":
                if not cedula_field.value:
                    status_text.value = "Por favor ingrese su cédula"
                    status_text.color = ft.colors.RED
                    status_text.visible = True
                    page.update()
                    return
                user = UserService.get_user_by_cedula(self.db, cedula_field.value)
                if not user or user.role != UserRoleEnum.usuario:
                    status_text.value = "Usuario no encontrado o rol inválido"
                    status_text.color = ft.colors.RED
                    status_text.visible = True
                    page.update()
                    return
                # Store current user object for later use
                self.current_user = user
            
            # Store selected role and station in app state
            self.current_user_role = role_dropdown.value
            self.current_user_station = station_dropdown.value if role_dropdown.value == "admin" else None
            
            # Show the navigation rail and update navigation based on role
            self.nav_rail.visible = True
            self.update_navigation_for_role(role_dropdown.value)
            # Update the layout to show the navigation rail
            self.page.update()
            
            # Show success message briefly, then switch to dashboard
            status_text.value = "¡Inicio de sesión exitoso!"
            status_text.color = ft.colors.GREEN
            status_text.visible = True
            page.update()
            
            # Switch to dashboard after a brief delay
            page.window_to_front()
            self.show_dashboard_view()
            
            # Clear cedula field after successful navigation
            cedula_field.value = ""
        
        sign_in_button.on_click = sign_in_click
        
        # Main layout with background
        self.content_area.content = ft.Container(
            content=ft.Column([
                ft.Container(height=40),
                ft.Text(
                    "Bienvenido al Sistema VeciRun",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.colors.BLUE_900
                ),
                ft.Container(height=20),
                ft.Text(
                    "Acceda al sistema seleccionando su rol correspondiente",
                    size=18,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.colors.GREY_700
                ),
                ft.Container(height=40),
                ft.Row([sign_in_card], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=40)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[ft.colors.BLUE_50, ft.colors.WHITE]
            ),
            expand=True
        )
        page.update()
    
    def show_dashboard_view(self):
        """Show dashboard after successful sign-in"""
        print("show_dashboard_view called")
        page = self.page
        
        # Get user role and station info
        role = getattr(self, 'current_user_role', 'regular')
        station = getattr(self, 'current_user_station', None)
        print(f"Dashboard view - Role: {role}, Station: {station}")
        
        # Create welcome message
        # Determine personalized greeting
        if getattr(self, 'current_user', None):
            user_name = self.current_user.full_name
            welcome_message = f"¡Bienvenido, {user_name}!"
        else:
            role_name = "Administrador" if role == "admin" else "Usuario Regular"
            welcome_message = f"¡Bienvenido, {role_name}!"

        welcome_text = ft.Text(
            welcome_message,
            size=28,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLUE_900
        )
        
        # Create role-specific content
        print(f"Creating content for role: {role}")
        if role == "admin":
            station_name = next((opt.text for opt in [
                ft.dropdown.Option("EST001", "Calle 26"),
                ft.dropdown.Option("EST002", "Salida al Uriel Gutiérrez"),
                ft.dropdown.Option("EST003", "Calle 53"),
                ft.dropdown.Option("EST004", "Calle 45"),
                ft.dropdown.Option("EST005", "Edificio Ciencia y Tecnología"),
            ] if opt.key == station), "No asignada")
            
            dashboard_content = ft.Column([
                ft.Container(height=30),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.HOME, color=ft.colors.BLUE),
                                title=ft.Text("Página de Inicio", size=18, weight=ft.FontWeight.BOLD),
                                subtitle=ft.Text(f"Estación: {station_name}", size=14),
                            ),
                            ft.Container(height=20),
                            ft.Text(
                                "Bienvenido al sistema VeciRun",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.GREY_700
                            ),
                            ft.Container(height=10),
                            ft.Text(
                                "Utilice el menú lateral para acceder a las diferentes funciones del sistema.",
                                size=14,
                                color=ft.colors.GREY_600
                            ),
                            ft.Container(height=20),
                            ft.Text(
                                "Funciones disponibles:",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.GREY_700
                            ),
                            ft.Container(height=10),
                            ft.Column([
                                ft.Row([
                                    ft.Icon(ft.icons.PERSON_ADD, color=ft.colors.GREEN, size=20),
                                    ft.Text("Crear nuevos usuarios", size=14)
                                ]),
                                ft.Row([
                                    ft.Icon(ft.icons.DIRECTIONS_BIKE, color=ft.colors.ORANGE, size=20),
                                    ft.Text("Registrar préstamos de bicicletas", size=14)
                                ]),
                                ft.Row([
                                    ft.Icon(ft.icons.ASSIGNMENT_RETURN, color=ft.colors.RED, size=20),
                                    ft.Text("Registrar devoluciones", size=14)
                                ])
                            ], spacing=10)
                        ]),
                        padding=20
                    ),
                    elevation=4
                )
            ])
        else:
            dashboard_content = ft.Column([
                ft.Container(height=30),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.PERSON, color=ft.colors.GREEN),
                                title=ft.Text("Panel de Usuario", size=18, weight=ft.FontWeight.BOLD),
                                subtitle=ft.Text("Acceso a información del sistema", size=14),
                            ),
                            ft.Container(height=20),
                            ft.Text(
                                "Como usuario regular, puede:",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.GREY_700
                            ),
                            ft.Container(height=10),
                            ft.Column([
                                ft.Row([
                                    ft.Icon(ft.icons.LOCATION_ON, color=ft.colors.BLUE, size=20),
                                    ft.Text("Consultar disponibilidad de bicicletas", size=14)
                                ]),
                                ft.Row([
                                    ft.Icon(ft.icons.INFO, color=ft.colors.GREY, size=20),
                                    ft.Text("Ver información de estaciones", size=14)
                                ])
                            ], spacing=10)
                        ]),
                        padding=20
                    ),
                    elevation=4
                )
            ])
        
        # Add logout button
        def logout_click(e):
            # Clear user session
            if hasattr(self, 'current_user_role'):
                delattr(self, 'current_user_role')
            if hasattr(self, 'current_user_station'):
                delattr(self, 'current_user_station')
            
            # Reset navigation to initial state and hide it
            self.nav_rail.destinations = []
            self.nav_rail.selected_index = 0
            self.nav_rail.visible = False
            
            # Force page update to clear navigation
            self.page.update()
            
            # Show sign-in view again
            self.show_home_view()
        
        logout_button = ft.ElevatedButton(
            "Cerrar Sesión",
            on_click=logout_click,
            icon=ft.icons.LOGOUT,
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.RED,
            )
        )
        
        self.content_area.content = ft.Column([
            ft.Container(height=20),
            ft.Row([
                welcome_text,
                ft.Container(expand=True),
                logout_button
            ]),
            ft.Container(height=20),
            dashboard_content
        ], scroll=ft.ScrollMode.AUTO)
        page.update()
    
    def update_navigation_for_role(self, role):
        """Update navigation based on user role"""
        if role == "admin":
            # Admin/Operator navigation
            self.nav_rail.destinations = [
                ft.NavigationRailDestination(
                    icon=ft.icons.HOME,
                    selected_icon=ft.icons.HOME,
                    label="Inicio",
                ),
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
            ]
        else:
            # Regular user navigation
            self.nav_rail.destinations = [
                ft.NavigationRailDestination(
                    icon=ft.icons.HOME,
                    selected_icon=ft.icons.HOME,
                    label="Inicio",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.LOCATION_ON,
                    selected_icon=ft.icons.LOCATION_ON,
                    label="Disponibilidad",
                ),
            ]
        
        # Reset selection
        self.nav_rail.selected_index = 0
        self.page.update()
    
    def show_availability_view(self):
        page = self.page
        
        # Get all stations with bike availability
        stations = StationService.get_all_stations(self.db)
        available_bikes = BicycleService.get_available_bicycles(self.db)
        
        # Create availability cards for each station
        availability_cards = []
        
        for station in stations:
            # Count available bikes assigned to this station
            bike_count = sum(
                1 for bike in available_bikes if bike.current_station_id == station.id
            )
            
            card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.LOCATION_ON, color=ft.colors.BLUE),
                            title=ft.Text(station.name, size=16, weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(f"Código: {station.code}", size=12),
                        ),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.icons.DIRECTIONS_BIKE, color=ft.colors.GREEN),
                                ft.Text(f"{bike_count} bicicletas disponibles", 
                                       size=14, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN),
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            padding=10
                        )
                    ]),
                    padding=10
                ),
                elevation=2
            )
            availability_cards.append(card)
        
        # Header
        header_text = ft.Text(
            "Disponibilidad de Bicicletas por Estación",
            size=24,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER
        )
        
        subtitle_text = ft.Text(
            "Consulta la cantidad de bicicletas disponibles en cada estación",
            size=14,
            text_align=ft.TextAlign.CENTER,
            color=ft.colors.GREY_600
        )
        
        # Refresh button
        def refresh_availability(e):
            self.show_availability_view()
        
        refresh_button = ft.ElevatedButton(
            "Actualizar",
            on_click=refresh_availability,
            icon=ft.icons.REFRESH,
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.BLUE,
            )
        )
        
        self.content_area.content = ft.Column([
            ft.Container(height=20),
            header_text,
            ft.Container(height=10),
            subtitle_text,
            ft.Container(height=30),
            ft.Row([refresh_button], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=20),
            ft.GridView(
                runs_count=2,
                max_extent=300,
                child_aspect_ratio=1.0,
                spacing=20,
                run_spacing=20,
                controls=availability_cards
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)
        page.update()
    
    def show_loan_view(self):
        self.refresh_loan_view(self.page)
    
    def refresh_loan_view(self, page):
        # Form fields
        user_cedula_field = ft.TextField(
            label="Cédula del Usuario",
            hint_text="Ingrese la cédula del usuario",
            width=300
        )
        
        # Station dropdown options shared by both dropdowns
        station_options = [
            ft.dropdown.Option("EST001", "EST001 - Calle 26"),
            ft.dropdown.Option("EST002", "EST002 - Salida al Uriel Gutiérrez"),
            ft.dropdown.Option("EST003", "EST003 - Calle 53"),
            ft.dropdown.Option("EST004", "EST004 - Calle 45"),
            ft.dropdown.Option("EST005", "EST005 - Edificio Ciencia y Tecnología"),
        ]
        
        # Dropdown for departure station
        station_out_dropdown = ft.Dropdown(
            label="Estación de Salida",
            width=300,
            options=station_options
        )

        # Cache admin station code if logged as admin/operator
        admin_station_code = (
            self.current_user_station
            if getattr(self, "current_user_role", None) == "admin" and getattr(self, "current_user_station", None)
            else None
        )

        # If admin/operator, lock departure station now (arrival handled later once defined)
        if admin_station_code:
            station_out_dropdown.value = admin_station_code
            station_out_dropdown.disabled = True

        # Dropdown for arrival station
        station_in_dropdown = ft.Dropdown(
            label="Estación de Llegada",
            width=300,
            options=station_options,
            disabled=True
        )

        # If admin/operator, enable arrival dropdown and filter options after it's defined
        if admin_station_code:
            station_in_dropdown.disabled = False
            station_in_dropdown.options = [opt for opt in station_options if opt.key != admin_station_code]

        # Update arrival station options when departure is selected
        def update_station_in(e):
            selected_out = station_out_dropdown.value
            if not selected_out:
                station_in_dropdown.disabled = True
                station_in_dropdown.options = station_options
            else:
                station_in_dropdown.disabled = False
                station_in_dropdown.options = [opt for opt in station_options if opt.key != selected_out]
                # Reset previous selection if now invalid
                if station_in_dropdown.value == selected_out:
                    station_in_dropdown.value = None
            page.update()

        station_out_dropdown.on_change = update_station_in
        
        # Get available bicycles (filter by admin's current station if applicable)
        available_bikes = BicycleService.get_available_bicycles(self.db)
        if getattr(self, 'current_user_role', None) == "admin" and getattr(self, 'current_user_station', None):
            station_obj = StationService.get_station_by_code(self.db, self.current_user_station)
            if station_obj:
                available_bikes = [bike for bike in available_bikes if bike.current_station_id == station_obj.id]
        
        # ---------- Bike selection cards ----------
        selected_bike_code: str | None = None  # var to store selected bike code

        bike_cards: list[ft.Card] = []

        def select_bike(e):
            nonlocal selected_bike_code, bike_cards, page
            selected_bike_code = e.control.data  # bike code stored in container
            # Highlight selected card by elevating and adding border
            for card in bike_cards:
                is_selected = card.data == selected_bike_code
                card.elevation = 8 if is_selected else 2
                # adjust border in inner container
                container = card.content
                container.border = ft.border.all(color=ft.colors.BLUE, width=2) if is_selected else None
            page.update()

        for bike in available_bikes:
            inner_container = ft.Container(
                data=bike.bike_code,
                on_click=select_bike,
                content=ft.Column([
                    ft.Icon(ft.icons.DIRECTIONS_BIKE, size=32, color=ft.colors.BLUE),
                    ft.Text(bike.bike_code, weight=ft.FontWeight.BOLD)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=10,
                alignment=ft.alignment.center,
            )

            card = ft.Card(
                data=bike.bike_code,
                elevation=2,
                content=inner_container,
                width=120,
                height=120,
            )
            bike_cards.append(card)

        bikes_container = ft.GridView(
            runs_count=3,
            max_extent=150,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
            controls=bike_cards
        )
        
        result_text = ft.Text("", color=ft.colors.GREEN)
        
        def register_loan(e):
            try:
                # Validate required fields
                if not all([
                    user_cedula_field.value,
                    selected_bike_code,
                    station_out_dropdown.value,
                    station_in_dropdown.value
                ]):
                    result_text.value = "Todos los campos son obligatorios"
                    result_text.color = ft.colors.RED
                    page.update()
                    return

                # Ensure stations are different
                if station_out_dropdown.value == station_in_dropdown.value:
                    result_text.value = "La estación de llegada debe ser diferente a la de salida"
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
                bicycle = BicycleService.get_bicycle_by_code(self.db, selected_bike_code)
                if not bicycle:
                    result_text.value = "Bicicleta no encontrada"
                    result_text.color = ft.colors.RED
                    page.update()
                    return
                
                # Get stations
                station_out = StationService.get_station_by_code(self.db, station_out_dropdown.value)
                station_in = StationService.get_station_by_code(self.db, station_in_dropdown.value)
                if not station_out or not station_in:
                    result_text.value = "Estación no encontrada"
                    result_text.color = ft.colors.RED
                    page.update()
                    return
                
                # Create loan
                loan = LoanService.create_loan(
                    self.db,
                    user_id=user.id,
                    bike_id=bicycle.id,
                    station_out_id=station_out.id,
                    station_in_id=station_in.id
                )
                
                result_text.value = f"Préstamo registrado exitosamente. ID: {loan.id}"
                result_text.color = ft.colors.GREEN
                
                # Clear fields
                user_cedula_field.value = ""
                selected_bike_code = None
                # reset card elevations
                for card in bike_cards:
                    card.elevation = 2
                    card.content.border = None
                
                # Refresh available bikes
                self.refresh_loan_view(page)
                
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
            ft.Text("Bicicletas Disponibles:", size=16, weight=ft.FontWeight.BOLD),
            bikes_container,
            ft.Container(height=10),
            station_out_dropdown,
            station_in_dropdown,
            ft.Container(height=20),
            loan_button,
            ft.Container(height=20),
            result_text
        ], scroll=ft.ScrollMode.AUTO)
        page.update()
    
    def show_return_view(self):
        page = self.page  # Get reference to the page
        
        # Form fields
        user_cedula_field = ft.TextField(
            label="Cédula del Usuario",
            hint_text="Ingrese la cédula del usuario",
            width=300
        )
        
        station_dropdown = ft.Dropdown(
            label="Estación de Devolución",
            width=300,
            options=[
                ft.dropdown.Option("EST001", "EST001 - Calle 26"),
                ft.dropdown.Option("EST002", "EST002 - Salida al Uriel Gutiérrez"),
                ft.dropdown.Option("EST003", "EST003 - Calle 53"),
                ft.dropdown.Option("EST004", "EST004 - Calle 45"),
                ft.dropdown.Option("EST005", "EST005 - Edificio Ciencia y Tecnología"),
            ]
        )
        
        result_text = ft.Text("", color=ft.colors.GREEN)
        
        def register_return(e):
            try:
                # Validate required fields
                if not all([user_cedula_field.value, station_dropdown.value]):
                    result_text.value = "Todos los campos son obligatorios"
                    result_text.color = ft.colors.RED
                    page.update()
                    return
                
                # Get user's open loans
                open_loans = LoanService.get_open_loans_by_user_cedula(self.db, user_cedula_field.value)
                if not open_loans:
                    result_text.value = "No se encontraron préstamos abiertos para este usuario"
                    result_text.color = ft.colors.RED
                    page.update()
                    return
                
                # If multiple loans, use the most recent one
                loan = open_loans[0]  # Get the first (most recent) open loan
                
                # Get station
                station = StationService.get_station_by_code(self.db, station_dropdown.value)
                if not station:
                    result_text.value = "Estación no encontrada"
                    result_text.color = ft.colors.RED
                    page.update()
                    return
                
                # Return loan
                returned_loan = LoanService.return_loan(
                    self.db,
                    loan_id=loan.id,
                    station_in_id=station.id
                )
                
                result_text.value = f"Devolución registrada exitosamente. Préstamo cerrado."
                result_text.color = ft.colors.GREEN
                
                # Clear fields
                user_cedula_field.value = ""
                station_dropdown.value = None
                
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
            user_cedula_field,
            station_dropdown,
            ft.Container(height=20),
            return_button,
            ft.Container(height=20),
            result_text
        ], scroll=ft.ScrollMode.AUTO)
        page.update()
    
    def create_sample_data(self):
        """Create sample data for testing"""
        # Check if data already exists
        if self.db.query(User).first():
            return
        
        # Create sample stations
        station1 = Station(code="EST001", name="Calle 26")
        station2 = Station(code="EST002", name="Salida al Uriel Gutiérrez")
        station3 = Station(code="EST003", name="Calle 53")
        station4 = Station(code="EST004", name="Calle 45")
        station5 = Station(code="EST005", name="Edificio Ciencia y Tecnología")
        
        self.db.add_all([station1, station2, station3, station4, station5])
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
            carnet="USER_12345678",
            full_name="Administrador Sistema",
            email="admin@universidad.edu",
            affiliation=UserAffiliationEnum.administrativo,
            role=UserRoleEnum.admin
        )
        
        # Create 5 operator users, one for each station
        operator_users = [
            User(
                cedula="11111111",
                carnet="USER_11111111",
                full_name="Operador Calle 26",
                email="operador1@universidad.edu",
                affiliation=UserAffiliationEnum.administrativo,
                role=UserRoleEnum.operador
            ),
            User(
                cedula="22222222",
                carnet="USER_22222222",
                full_name="Operador Uriel Gutiérrez",
                email="operador2@universidad.edu",
                affiliation=UserAffiliationEnum.administrativo,
                role=UserRoleEnum.operador
            ),
            User(
                cedula="33333333",
                carnet="USER_33333333",
                full_name="Operador Calle 53",
                email="operador3@universidad.edu",
                affiliation=UserAffiliationEnum.administrativo,
                role=UserRoleEnum.operador
            ),
            User(
                cedula="44444444",
                carnet="USER_44444444",
                full_name="Operador Calle 45",
                email="operador4@universidad.edu",
                affiliation=UserAffiliationEnum.administrativo,
                role=UserRoleEnum.operador
            ),
            User(
                cedula="55555555",
                carnet="USER_55555555",
                full_name="Operador Ciencia y Tecnología",
                email="operador5@universidad.edu",
                affiliation=UserAffiliationEnum.administrativo,
                role=UserRoleEnum.operador
            )
        ]
        
        self.db.add(admin_user)
        self.db.add_all(operator_users)
        
        # NEW: Create sample regular user
        regular_user = User(
            cedula="88888888",
            carnet="USER_88888888",
            full_name="Usuario Regular",
            email="usuario@universidad.edu",
            affiliation=UserAffiliationEnum.estudiante,
            role=UserRoleEnum.usuario
        )
        
        self.db.add(regular_user)
        self.db.commit()

if __name__ == "__main__":
    app = VeciRunApp()
    ft.app(target=app.main) 