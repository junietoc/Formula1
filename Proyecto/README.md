# VeciRun

Aplicación de escritorio minimal-viable para el sistema de préstamo de bicicletas universitario.

## Stack Tecnológico

- **Python 3.11**
- **Flet** (desktop mode)
- **PostgreSQL 16**
- **SQLAlchemy** (ORM)
- **Alembic** (migraciones)

## Arquitectura

Aplicación monolítica con las siguientes capas:
- **Presentación**: Flet UI
- **Lógica de Negocio**: Services
- **Acceso a Datos**: SQLAlchemy + PostgreSQL

## Funcionalidades Implementadas

### 1. Crear Usuario
- Registro de usuarios (estudiantes, docentes, administrativos)
- Roles: usuario, operador, admin
- Validación de cédula única (carnet se genera automáticamente)

### 2. Registrar Préstamo
- Check-out de bicicletas
- Validación de disponibilidad
- Asociación con estación de salida

### 3. Registrar Devolución
- Check-in de bicicletas
- Cierre de préstamos
- Actualización de estado de bicicletas

## Instalación y Configuración

### Prerrequisitos

1. **Python 3.11** instalado
2. **PostgreSQL 16** instalado y ejecutándose
3. **pip** para gestión de dependencias

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd vecirun
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar base de datos**
   
   Crear base de datos PostgreSQL:
   ```sql
   CREATE DATABASE vecirun_db;
   CREATE USER postgres WITH PASSWORD 'password';
   GRANT ALL PRIVILEGES ON DATABASE vecirun_db TO postgres;
   ```

5. **Configurar variables de entorno**
   
   Crear archivo `.env` en la raíz del proyecto:
   ```
   DATABASE_URL=postgresql://postgres:password@localhost:5432/vecirun_db
   ```

6. **Ejecutar migraciones**
   ```bash
   alembic upgrade head
   ```

7. **Ejecutar la aplicación**
   ```bash
   python main.py
   ```

## Estructura del Proyecto

```
vecirun/
├── main.py              # Aplicación principal Flet
├── models.py            # Modelos SQLAlchemy
├── services.py          # Lógica de negocio
├── database.py          # Configuración de base de datos
├── config.py            # Configuración general
├── requirements.txt     # Dependencias Python
├── alembic.ini         # Configuración Alembic
├── alembic/
│   ├── env.py          # Entorno Alembic
│   ├── script.py.mako  # Template de migraciones
│   └── versions/       # Archivos de migración
└── README.md           # Este archivo
```

## Esquema de Base de Datos

### Enums
- `user_role_enum`: usuario, operador, admin
- `user_affiliation_enum`: estudiante, docente, administrativo
- `bike_status_enum`: disponible, prestada, mantenimiento, retirada
- `loan_status_enum`: abierto, cerrado, tardio, perdido

### Tablas
- `users`: Información de usuarios
- `bicycles`: Información de bicicletas
- `stations`: Estaciones de préstamo/devolución
- `loans`: Registro de préstamos

## Uso de la Aplicación

### 0. Pantalla de Inicio
1. Al abrir la aplicación, se muestra la pantalla de inicio
2. Seleccionar rol: "Usuario Regular" o "Administrador"
3. Si se selecciona "Administrador", elegir estación asignada
4. Hacer clic en "Continuar" para confirmar la selección
5. La navegación se actualiza según el rol seleccionado

### 1. Crear Usuario (Solo Administradores)
1. Seleccionar "Crear Usuario" en el menú lateral
2. Completar todos los campos obligatorios
3. Seleccionar afiliación y rol
4. Hacer clic en "Crear Usuario"

### 2. Registrar Préstamo (Solo Administradores)
1. Seleccionar "Registrar Préstamo" en el menú lateral
2. Ingresar cédula del usuario
3. Seleccionar bicicleta disponible de la lista
4. Ingresar código de estación de salida
5. Hacer clic en "Registrar Préstamo"

### 3. Registrar Devolución (Solo Administradores)
1. Seleccionar "Registrar Devolución" en el menú lateral
2. Ingresar cédula del usuario
3. Ingresar código de estación de devolución
4. Hacer clic en "Registrar Devolución"

### 4. Consultar Disponibilidad (Solo Usuarios Regulares)
1. Seleccionar "Disponibilidad" en el menú lateral
2. Ver la cantidad de bicicletas disponibles por estación
3. Usar el botón "Actualizar" para refrescar la información

## Datos de Prueba

La aplicación incluye datos de muestra automáticamente:

### Estaciones
- EST001: Calle 26
- EST002: Salida al Uriel Gutiérrez
- EST003: Calle 53
- EST004: Calle 45
- EST005: Edificio Ciencia y Tecnología

### Bicicletas
- B001: BIKE001 (disponible)
- B002: BIKE002 (disponible)
- B003: BIKE003 (disponible)

### Usuarios del Sistema

#### Usuario Administrador
- Cédula: 12345678
- Carnet: USER_12345678 (generado automáticamente)
- Email: admin@universidad.edu

#### Usuarios Operadores (uno por estación)
- **Operador Calle 26**: Cédula 11111111, Email: operador1@universidad.edu
- **Operador Uriel Gutiérrez**: Cédula 22222222, Email: operador2@universidad.edu
- **Operador Calle 53**: Cédula 33333333, Email: operador3@universidad.edu
- **Operador Calle 45**: Cédula 44444444, Email: operador4@universidad.edu
- **Operador Ciencia y Tecnología**: Cédula 55555555, Email: operador5@universidad.edu

## Comandos Útiles

### Migraciones
```bash
# Crear nueva migración
alembic revision --autogenerate -m "descripción"

# Ejecutar migraciones pendientes
alembic upgrade head

# Revertir última migración
alembic downgrade -1
```

### Base de Datos
```bash
# Crear tablas (sin migraciones)
python -c "from database import create_tables; create_tables()"
```

## Notas de Desarrollo

- La aplicación utiliza UUIDs como claves primarias
- Todas las operaciones incluyen validaciones de negocio
- Los estados de bicicletas se actualizan automáticamente
- La interfaz es responsive y moderna
- Se incluye manejo de errores completo

## Troubleshooting

### Error de Conexión a Base de Datos
- Verificar que PostgreSQL esté ejecutándose
- Confirmar credenciales en `.env`
- Verificar que la base de datos exista

### Error de Migraciones
- Ejecutar `alembic current` para ver estado
- Verificar que la base de datos esté accesible
- Revisar logs de Alembic

### Error de Dependencias
- Actualizar pip: `pip install --upgrade pip`
- Reinstalar dependencias: `pip install -r requirements.txt --force-reinstall` 