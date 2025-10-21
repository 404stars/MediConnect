import logging
from datetime import datetime, date
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, case

from database.connection import get_db
from models import (
    Usuario, Sesion, UsuarioRol, Rol, Funcionario, Cargo,
    ProfesionalSalud, Paciente, Especialidad, Cita, BloqueHora,
    AgendaDiaria, ProfesionalEspecialidad
)
from schemas import (
    AdminCreateUserSchema, UpdateUserRolesSchema, UserListItemSchema,
    UserRoleSchema, RoleSchema, UsersListResponseSchema,
    RolesListResponseSchema, MessageResponseSchema
)
from utils import hash_password, require_permission, require_admin, EstadoCita, Rol as RolConstantes
from utils.auth_dependencies import get_current_user_id
from services import (
    generar_csv_citas, generar_csv_pacientes_atendidos,
    UsuarioService, ReportQueryBuilder
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/users", response_model=MessageResponseSchema)
def create_user(
    user_data: AdminCreateUserSchema,
    current_user_id: int = Depends(require_permission("manage_users")),
    db: Session = Depends(get_db)
):
    try:
        usuario_service = UsuarioService(db)
        
        nuevo_usuario = usuario_service.crear_usuario_completo(
            rut=user_data.rut,
            nombre=user_data.nombre,
            apellido_paterno=user_data.apellido_paterno,
            apellido_materno=user_data.apellido_materno,
            email=user_data.email,
            telefono=user_data.telefono,
            password=user_data.password,
            roles_ids=user_data.roles
        )
        
        return MessageResponseSchema(
            message="Usuario creado exitosamente",
            user_id=nuevo_usuario.id_usuario
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/users", response_model=UsersListResponseSchema)
def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user_id: int = Depends(require_permission("view_all_data")),
    db: Session = Depends(get_db)
):
    """
    Optimizado: Usa joinedload para eliminar N+1 queries.
    Antes: 1 + N queries (N = número de usuarios)
    Después: 1 query única con JOIN
    """
    try:
        # Query optimizada con eager loading
        users = db.query(Usuario).options(
            joinedload(Usuario.usuario_roles).joinedload(UsuarioRol.rol)
        ).offset(skip).limit(limit).all()
        
        total = db.query(Usuario).count()
        
        users_list = [
            UserListItemSchema(
                id_usuario=user.id_usuario,
                rut=user.rut,
                nombre=user.nombre,
                apellido_paterno=user.apellido_paterno,
                apellido_materno=user.apellido_materno,
                email=user.email,
                telefono=user.telefono,
                roles=[
                    {"id_rol": ur.rol.id_rol, "nombre": ur.rol.nombre} 
                    for ur in user.usuario_roles
                ]
            )
            for user in users
        ]
        
        return UsersListResponseSchema(users=users_list, total=total)
        
    except Exception as e:
        logger.error(f"Error en get_users: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/roles", response_model=RolesListResponseSchema)
def get_roles(
    current_user_id: int = Depends(require_permission("manage_roles")),
    db: Session = Depends(get_db)
):
    try:
        roles = db.query(Rol).all()
        roles_list = [
            RoleSchema(
                id_rol=role.id_rol,
                nombre=role.nombre,
                descripcion=getattr(role, 'descripcion', None)
            ) for role in roles
        ]
        
        return RolesListResponseSchema(roles=roles_list)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.put("/users/{user_id}/roles", response_model=MessageResponseSchema)
def update_user_roles(
    user_id: int,
    roles_data: UpdateUserRolesSchema,
    current_user_id: int = Depends(require_permission("manage_users")),
    db: Session = Depends(get_db)
):
    try:
        usuario_service = UsuarioService(db)
        usuario_service.actualizar_roles_usuario(user_id, roles_data.roles)
        
        return MessageResponseSchema(message="Roles actualizados exitosamente")
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.delete("/users/{user_id}", response_model=MessageResponseSchema)
def delete_user(
    user_id: int,
    current_user_id: int = Depends(require_permission("manage_users")),
    db: Session = Depends(get_db)
):
    try:
        db.query(Sesion).filter(Sesion.id_usuario == user_id).delete()
        
        usuario_service = UsuarioService(db)
        usuario_service.eliminar_usuario(user_id, current_user_id)
        
        return MessageResponseSchema(message="Usuario eliminado exitosamente")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/reportes/citas-csv")
async def exportar_reporte_citas_csv(
    estado: str = None,
    fecha_desde: str = None,
    fecha_hasta: str = None,
    profesional: str = None,
    especialidad: str = None,
    rut_paciente: str = None,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(require_admin)
):
    try:
        builder = ReportQueryBuilder(db)
        citas = (builder
                 .with_estado(estado)
                 .with_fecha_desde(fecha_desde)
                 .with_fecha_hasta(fecha_hasta)
                 .with_rut_paciente(rut_paciente)
                 .with_profesional(profesional)
                 .with_especialidad(especialidad)
                 .order_by_fecha_desc()
                 .build())
        
        logger.info(f"Total de citas encontradas: {len(citas)}")
        
        csv_content = generar_csv_citas(citas, db)
        
        filename = f"reporte_citas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            io.BytesIO(csv_content.encode('utf-8-sig')),
            media_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
        
    except Exception as e:
        logger.error(f"Error general en exportar CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al generar reporte: {str(e)}")


@router.get("/reportes/estadisticas-utilizacion")
async def obtener_estadisticas_utilizacion(
    fecha_desde: str = None,
    fecha_hasta: str = None,
    especialidad: str = None,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(require_admin)
):
    try:
        from sqlalchemy import func, and_
        
        filtros_fecha = []
        if fecha_desde:
            try:
                fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                filtros_fecha.append(AgendaDiaria.fecha >= fecha_desde_obj)
            except ValueError:
                pass
        
        if fecha_hasta:
            try:
                fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                filtros_fecha.append(AgendaDiaria.fecha <= fecha_hasta_obj)
            except ValueError:
                pass
        
        query_bloques = db.query(func.count(BloqueHora.id_bloque)).join(AgendaDiaria)
        
        if filtros_fecha:
            query_bloques = query_bloques.filter(and_(*filtros_fecha))
        
        if especialidad:
            query_bloques = query_bloques.join(ProfesionalSalud).join(ProfesionalEspecialidad).join(Especialidad).filter(
                Especialidad.nombre == especialidad
            )
        
        total_bloques_disponibles = query_bloques.scalar() or 0
        
        # Optimizado: 1 query con agregación SQL en lugar de 6 queries separadas
        query_citas_base = db.query(Cita).join(BloqueHora).join(AgendaDiaria)
        
        if filtros_fecha:
            query_citas_base = query_citas_base.filter(and_(*filtros_fecha))
        
        if especialidad:
            query_citas_base = query_citas_base.join(ProfesionalSalud).join(ProfesionalEspecialidad).join(Especialidad).filter(
                Especialidad.nombre == especialidad
            )
        
        # Agregación única con CASE para contar por estado
        estadisticas = db.query(
            func.count(Cita.id_cita).label('total'),
            func.sum(case((Cita.estado == EstadoCita.AGENDADA, 1), else_=0)).label('agendadas'),
            func.sum(case((Cita.estado == EstadoCita.CONFIRMADA, 1), else_=0)).label('confirmadas'),
            func.sum(case((Cita.estado == EstadoCita.EN_ATENCION, 1), else_=0)).label('en_atencion'),
            func.sum(case((Cita.estado == EstadoCita.ATENDIDA, 1), else_=0)).label('atendidas'),
            func.sum(case((Cita.estado == EstadoCita.CANCELADA, 1), else_=0)).label('canceladas'),
            func.sum(case((Cita.estado == EstadoCita.NO_ASISTIO, 1), else_=0)).label('no_asistio')
        ).select_from(Cita).join(BloqueHora).join(AgendaDiaria)
        
        if filtros_fecha:
            estadisticas = estadisticas.filter(and_(*filtros_fecha))
        
        if especialidad:
            estadisticas = estadisticas.join(ProfesionalSalud).join(ProfesionalEspecialidad).join(Especialidad).filter(
                Especialidad.nombre == especialidad
            )
        
        stats = estadisticas.first()
        
        total_citas = stats.total or 0
        citas_agendadas = stats.agendadas or 0
        citas_confirmadas = stats.confirmadas or 0
        citas_en_atencion = stats.en_atencion or 0
        citas_atendidas = stats.atendidas or 0
        citas_canceladas = stats.canceladas or 0
        citas_no_asistio = stats.no_asistio or 0
        
        horas_reservadas = citas_agendadas + citas_confirmadas + citas_en_atencion + citas_atendidas
        horas_efectivas = citas_atendidas
        horas_disponibles_sin_usar = total_bloques_disponibles - total_citas
        
        tasa_utilizacion = (horas_efectivas / total_bloques_disponibles * 100) if total_bloques_disponibles > 0 else 0
        tasa_reserva = (horas_reservadas / total_bloques_disponibles * 100) if total_bloques_disponibles > 0 else 0
        tasa_ausentismo = (citas_no_asistio / total_citas * 100) if total_citas > 0 else 0
        tasa_cancelacion = (citas_canceladas / total_citas * 100) if total_citas > 0 else 0
        
        return {
            "periodo": {
                "fecha_desde": fecha_desde or "Inicio",
                "fecha_hasta": fecha_hasta or "Actual",
                "especialidad": especialidad or "Todas"
            },
            "bloques": {
                "total_disponibles": total_bloques_disponibles,
                "sin_usar": horas_disponibles_sin_usar,
                "con_cita": total_citas
            },
            "citas": {
                "total": total_citas,
                "agendadas": citas_agendadas,
                "confirmadas": citas_confirmadas,
                "en_atencion": citas_en_atencion,
                "atendidas": citas_atendidas,
                "canceladas": citas_canceladas,
                "no_asistio": citas_no_asistio
            },
            "metricas": {
                "horas_reservadas": horas_reservadas,
                "horas_efectivas": horas_efectivas,
                "tasa_utilizacion": round(tasa_utilizacion, 2),
                "tasa_reserva": round(tasa_reserva, 2),
                "tasa_ausentismo": round(tasa_ausentismo, 2),
                "tasa_cancelacion": round(tasa_cancelacion, 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")


@router.get("/reportes/pacientes-atendidos-csv")
async def exportar_pacientes_atendidos_csv(
    fecha_desde: str = None,
    fecha_hasta: str = None,
    especialidad: str = None,
    profesional: str = None,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(require_admin)
):
    try:
        builder = ReportQueryBuilder(db)
        citas = (builder
                 .with_estado(EstadoCita.ATENDIDA)
                 .with_fecha_desde(fecha_desde)
                 .with_fecha_hasta(fecha_hasta)
                 .with_profesional(profesional)
                 .with_especialidad(especialidad)
                 .order_by_agenda_fecha_desc()
                 .build())
        
        csv_content = generar_csv_pacientes_atendidos(citas, db)
        
        filename = f"pacientes_atendidos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            io.BytesIO(csv_content.encode('utf-8-sig')),
            media_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
        
    except Exception as e:
        logger.error(f"Error exportando pacientes atendidos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al generar reporte: {str(e)}")
