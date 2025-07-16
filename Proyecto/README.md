# 🚴‍♂️ VeciRun – ¡Tu sistema de bicicletas universitarias!

> Una aplicación **minimal-viable** para gestionar el préstamo y devolución de 🚲 en la universidad.

<div align="center">

![VeciRun banner](vecirunbanner.png)

</div>

---

## 📑 Tabla de Contenido

1. [Características Principales](#-características-principales)
2. [Stack Tecnológico](#-stack-tecnológico)
3. [Instalación Rápida](#-instalación-rápida)
4. [Uso de la App](#-uso-de-la-app)
5. [Guías Flash ⚡](#-guías-flash-)
6. [Estructura del Proyecto](#️-estructura-del-proyecto)
7. [Comandos Útiles](#-comandos-útiles)
8. [Contribuir](#-contribuir)
9. [Licencia](#-licencia)

---

## ✨ Características Principales

✅ Registro y gestión de **usuarios** con roles (`usuario`, `operador`, `admin`).

✅ Control de **préstamos** y **devoluciones** en estaciones.

✅ 🎛️ Dashboard para operadores con actualización en tiempo real.

✅ Datos de ejemplo precargados para que pruebes la app en 1 clic.

---

## 🛠️ Stack Tecnológico

| Módulo | Descripción |
| ------ | ----------- |
| 🐍 Python 3.11 | Lenguaje principal |
| 🎨 Flet (modo Desktop) | UI en Flutter para Desktop |
| 🐘 PostgreSQL 16 | Motor de base de datos |
| 🔗 SQLAlchemy | ORM |
| 🪄 Alembic | Migraciones |

---

## 🚀 Instalación Rápida!

¡Ponte a rodar en **2 pasos**! 🏁

```bash
# 1. Clona el repo y entra en él
git clone git@github.com:junietoc/Formula1.git
cd Formula1/Proyecto 

# 2. Ejecútalo todo con un solo comando ✨
python dev_init.py
```

El asistente `dev init` se encarga de:

- Crear y activar un entorno virtual.
- Instalar todas las dependencias.
- Configurar la base de datos y aplicar migraciones.
- Cargar datos de ejemplo para que pruebes la app al instante.


---

### 🛠️ Instalación Manual (opcional)

Prefieres ir paso a paso o no puedes usar `dev init`? Sigue este flujo completo:

```bash
# 1. Clona el repo
$ git clone git@github.com:junietoc/Formula1.git
$ cd Formula1/Proyecto 

# 2. Crea y activa un entorno virtual
$ python -m venv venv
$ source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instala dependencias
$ pip install -r requirements.txt

# 4. Prepara la base de datos (PostgreSQL debe estar corriendo)
$ createdb vecirun_db
$ psql -c "CREATE USER postgres WITH PASSWORD 'password';"
$ psql -c "GRANT ALL PRIVILEGES ON DATABASE vecirun_db TO postgres;"

# 5. Variables de entorno (crea un archivo .env)
$ echo "DATABASE_URL=postgresql://postgres:password@localhost:5432/vecirun_db" > .env

# 6. Migraciones
$ alembic upgrade head

# 7. (Opcional) Carga datos de muestra
$ python dev_init.py

# 8. Arranca la app 🏁
$ python main.py
```

---

## 🎮 Uso de la App

Al abrir la aplicación encontrarás una pantalla de inicio para escoger tu **rol**:

• **Usuario Regular** – consulta rápida de disponibilidad 🚲.

• **Administrador** – panel completo para crear usuarios, registrar préstamos y devoluciones.

La navegación se adapta automáticamente según tu selección. ¡Todo en una sola ventana!

---

## ⚡ Guías Flash ⚡

### 🔹 Usuario Regular – Ver disponibilidad

1. Abre la app y selecciona **Usuario Regular**.
2. Visualiza la lista de estaciones y bicicletas disponibles.
3. Pulsa **Actualizar** para refrescar la información.

### 🔸 Administrador – Préstamo & Devolución

1. Selecciona **Administrador** > elige tu estación > **Continuar**.
2. Ve a **Registrar Préstamo** y rellena los campos.
3. Después, ve a **Registrar Devolución** para cerrar el ciclo.

*(Consulta datos de demo en la sección **Datos de Prueba** más abajo).*  

---

## 📊 Datos de Prueba

Para facilitar las pruebas de registro y devolución, se han precargado los siguientes datos en la base de datos:

### Estaciones
- **EST001**: Calle 26
- **EST002**: Salida al Uriel Gutiérrez
- **EST003**: Calle 53
- **EST004**: Calle 45
- **EST005**: Edificio Ciencia y Tecnología

### Bicicletas
- **Bicicletas**: 40 bicicletas con seriales desde `BIKE001` hasta `BIKE040`.

### Usuarios
- **Administrador**:
  - Cédula: 12345678
  - Carnet: USER_12345678
  - Nombre: Administrador Sistema
  - Email: admin@universidad.edu

- **Operadores**:
  - Cédula: 11111111, Nombre: Operador Calle 26
  - Cédula: 22222222, Nombre: Operador Uriel Gutiérrez
  - Cédula: 33333333, Nombre: Operador Calle 53
  - Cédula: 44444444, Nombre: Operador Calle 45
  - Cédula: 55555555, Nombre: Operador Ciencia y Tecnología

- **Usuarios Regulares**: 20 usuarios con cédulas desde `80000000` hasta `80000019`.

---

## 🗂️ Estructura del Proyecto

```bash
vecirun/
├── main.py             # Aplicación principal Flet
├── models.py           # Modelos SQLAlchemy
├── services.py         # Lógica de negocio
├── database.py         # Configuración DB
├── alembic/            # Migraciones
└── ...
```

---

## 🔧 Comandos Útiles

```bash
# Crear nueva migración
$ alembic revision --autogenerate -m "descripcion"

# Aplicar migraciones pendientes
$ alembic upgrade head

# Revertir última migración
$ alembic downgrade -1
```

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Si encuentras un 🐛 bug o quieres proponer una 💡 mejora:

1. Abre un **Issue** describiendo tu propuesta.
2. Haz un **Fork** del proyecto y crea una rama con tu feature: `git checkout -b feature/mi-mejora`.
3. Envía un **Pull Request** explicando los cambios.

---

## 📄 Licencia

Este proyecto está licenciado bajo los términos de la licencia MIT. Consulta el archivo `LICENSE` para más info.

---

<div align="center">
Hecho con ❤️ por el equipo *VeciRun*.
</div> 
