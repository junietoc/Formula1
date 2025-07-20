import pytest
from services import UserService
from models import UserRoleEnum, User

@pytest.mark.usefixtures("db_session")
def test_user_role_change_and_permission_enforcement(db_session):
    """
    Valida que el cambio de rol de usuario actualiza los permisos y acceso a funciones administrativas.
    - Crea un usuario regular y verifica que no puede crear usuarios ni ver reportes.
    - Cambia el rol a 'admin' y verifica acceso a funciones restringidas.
    """
    # Crear usuario regular
    user = UserService.create_user(
        db_session,
        cedula="99999999",
        carnet="USER_99999999",
        full_name="Usuario Prueba",
        email="prueba@correo.com",
        affiliation="estudiante",
        role=UserRoleEnum.usuario
    )
    db_session.commit()
    # Verificar permisos iniciales
    assert not UserService.can_create_users(user)
    assert not UserService.can_view_reports(user)
    # Cambiar rol a admin
    user.role = UserRoleEnum.admin
    db_session.commit()
    # Verificar permisos actualizados
    assert UserService.can_create_users(user)
    assert UserService.can_view_reports(user)
