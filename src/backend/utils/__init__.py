from utils.auth_dependencies import get_current_user, get_current_user_id
from utils.permissions import (
    require_admin,
    require_staff,
    require_any_role,
    require_permission,
    require_roles,
    get_user_roles,
    has_any_role
)
from utils.constants import EstadoCita, Rol, MotivoCancelacionExcluido, ReglasNegocio, Mensajes
from utils.hashing import hash_password, verify_password
from utils.email_utils import (
    enviar_correo_confirmacion,
    enviar_correo_cancelacion,
    enviar_correo_reprogramacion,
    enviar_correo_recuperacion_password,
    enviar_correo_confirmacion_cambio_password
)

__all__ = [
    'get_current_user',
    'get_current_user_id',
    'require_admin',
    'require_staff',
    'require_any_role',
    'require_permission',
    'require_roles',
    'get_user_roles',
    'has_any_role',
    'EstadoCita',
    'Rol',
    'MotivoCancelacionExcluido',
    'ReglasNegocio',
    'Mensajes',
    'hash_password',
    'verify_password',
    'enviar_correo_confirmacion',
    'enviar_correo_cancelacion',
    'enviar_correo_reprogramacion',
    'enviar_correo_recuperacion_password',
    'enviar_correo_confirmacion_cambio_password',
]
