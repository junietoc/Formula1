# Funcionalidad de Bicicletas Favoritas

## Descripción

Se ha implementado una nueva funcionalidad que permite a los usuarios elegir una bicicleta favorita entre las que han usado anteriormente en sus préstamos. Esta funcionalidad incluye reglas específicas para garantizar un uso justo y organizado del sistema.

## Reglas Implementadas

### 1. Una sola bicicleta favorita por usuario
- Cada usuario solo puede tener una bicicleta marcada como favorita
- Si el usuario ya tiene una bicicleta favorita y elige otra, la anterior se reemplaza automáticamente

### 2. Solo bicicletas usadas anteriormente
- Los usuarios solo pueden elegir como favorita una bicicleta que hayan usado en préstamos anteriores o en curso
- El sistema verifica el historial de préstamos del usuario antes de permitir la selección

### 3. Exclusividad de bicicletas favoritas
- Una bicicleta que ha sido marcada como favorita por un usuario no puede ser elegida como favorita por otro usuario
- Solo cuando el propietario actual quita la bicicleta de sus favoritos, otro usuario puede elegirla

### 4. Información visible para administradores
- Cuando un administrador registra un préstamo, puede ver qué bicicletas son favoritas de otros usuarios
- Las bicicletas favoritas se muestran con un ícono de corazón y fondo rosado
- Se incluye información del propietario en el tooltip de la bicicleta

### 5. Información en el perfil del usuario
- Los usuarios pueden ver en su dashboard la información de su bicicleta favorita
- Se muestra la estación donde se encuentra actualmente la bicicleta favorita
- Se incluye el estado actual de la bicicleta

## Componentes Implementados

### Servicios (`services.py`)

Se agregó la clase `FavoriteBikeService` con los siguientes métodos:

- `get_user_favorite_bike(db, user_id)`: Obtiene la bicicleta favorita de un usuario
- `get_user_favorite_bike_by_cedula(db, cedula)`: Obtiene la bicicleta favorita por cédula
- `get_bikes_used_by_user(db, user_id)`: Obtiene todas las bicicletas que ha usado un usuario
- `get_bikes_used_by_user_cedula(db, cedula)`: Obtiene bicicletas usadas por cédula
- `set_favorite_bike(db, user_id, bike_id)`: Establece una bicicleta como favorita
- `set_favorite_bike_by_cedula(db, cedula, bike_id)`: Establece favorita por cédula
- `remove_favorite_bike(db, user_id)`: Quita la bicicleta favorita
- `remove_favorite_bike_by_cedula(db, cedula)`: Quita favorita por cédula
- `get_favorite_bike_owner(db, bike_id)`: Obtiene el propietario de una bicicleta favorita
- `is_bike_favorite(db, bike_id)`: Verifica si una bicicleta es favorita de alguien

### Vista de Gestión (`views/favorite_bike.py`)

Nueva vista `FavoriteBikeView` que permite a los usuarios:

- Ver su bicicleta favorita actual
- Ver todas las bicicletas que han usado y pueden elegir como favorita
- Establecer una nueva bicicleta como favorita
- Quitar su bicicleta favorita actual
- Ver información detallada de cada bicicleta (estación, estado, etc.)

### Modificaciones en Vistas Existentes

#### Vista de Préstamos (`views/loan.py`)
- Se agregó información visual para bicicletas favoritas
- Las bicicletas favoritas se muestran con ícono de corazón y fondo rosado
- Se incluye información del propietario en el tooltip

#### Dashboard (`views/dashboard.py`)
- Se agregó información de la bicicleta favorita en el perfil del usuario
- Se muestra la ubicación y estado de la bicicleta favorita
- Se agregó opción en el menú para gestionar bicicletas favoritas

### Navegación (`main.py`)
- Se agregó nueva opción "Mi Favorita" en el menú de usuarios regulares
- Se integró la nueva vista en el sistema de navegación

## Uso de la Funcionalidad

### Para Usuarios Regulares

1. **Acceder a la gestión de favoritas**: En el menú lateral, seleccionar "Mi Favorita"
2. **Ver bicicleta favorita actual**: La vista muestra si el usuario tiene una bicicleta favorita y su información
3. **Elegir nueva bicicleta favorita**: 
   - Ver la lista de bicicletas usadas anteriormente
   - Seleccionar una bicicleta disponible (no favorita de otro usuario)
   - Hacer clic en "Elegir como favorita"
4. **Quitar bicicleta favorita**: Hacer clic en "Quitar Bicicleta Favorita"

### Para Administradores

1. **Ver información de favoritas**: Al registrar préstamos, las bicicletas favoritas se muestran con:
   - Ícono de corazón rojo
   - Fondo rosado
   - Tooltip con información del propietario
2. **Tomar decisiones informadas**: Conocer qué bicicletas son favoritas de usuarios específicos

## Validaciones Implementadas

- **Verificación de uso previo**: Solo se pueden elegir bicicletas que el usuario haya usado
- **Exclusividad**: Una bicicleta no puede ser favorita de múltiples usuarios
- **Existencia de usuario**: Se verifica que el usuario exista antes de realizar operaciones
- **Estado de bicicleta**: Se considera el estado actual de la bicicleta al mostrar información

## Base de Datos

La funcionalidad utiliza el campo `favorite_bike_id` que ya existía en el modelo `User`:

```python
class User(Base):
    # ... otros campos ...
    favorite_bike_id = Column(UUID(as_uuid=True), ForeignKey("bicycles.id"))
    favorite_bike = relationship("Bicycle", foreign_keys=[favorite_bike_id])
```

## Pruebas

Se incluye un script de prueba (`test_favorite_bike.py`) que demuestra:

- Creación de datos de prueba
- Establecimiento de bicicletas favoritas
- Validación de reglas de exclusividad
- Verificación de restricciones de uso previo
- Funcionalidad de quitar bicicletas favoritas

## Consideraciones Técnicas

- **Rendimiento**: Las consultas están optimizadas para evitar N+1 queries
- **Integridad**: Se mantiene la integridad referencial en la base de datos
- **UX**: Interfaz intuitiva con feedback visual claro
- **Escalabilidad**: La implementación permite futuras expansiones de la funcionalidad

## Futuras Mejoras Posibles

- Notificaciones cuando la bicicleta favorita esté disponible
- Historial de bicicletas favoritas
- Estadísticas de uso de bicicletas favoritas
- Integración con sistema de reservas
- Reportes de bicicletas favoritas por estación 