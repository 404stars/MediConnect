import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, case
from database.connection import get_db
from models.usuario import Usuario
from models.sesion import Sesion
from models.usuario_rol import UsuarioRol
from models.rol import Rol
from models.funcionario import Funcionario
from models.cargo import Cargo
from models.profesional_salud import ProfesionalSalud
from models.paciente import Paciente
from models.especialidad import Especialidad
from models.cita import Cita
from models.bloque_hora import BloqueHora
from models.agenda_diaria import AgendaDiaria
from models.profesional_especialidad import ProfesionalEspecialidad
from schemas.admin_schemas import (
    AdminCreateUserSchema, UpdateUserRolesSchema, UserListItemSchema, UserRoleSchema,
    RoleSchema, UsersListResponseSchema, RolesListResponseSchema
)
from schemas.auth_schemas import MessageResponseSchema
from utils.hashing import hash_password
from utils.auth_dependencies import get_current_user_id
from utils.permissions import require_permission, require_admin
from utils.constants import Rol as RolConstantes, EstadoCita
from services.report_service import generar_csv_citas, generar_csv_pacientes_atendidos
from datetime import datetime, date
import io

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/users", response_model=MessageResponseSchema)
def create_user(
    user_data: AdminCreateUserSchema,
    current_user_id: int = Depends(require_permission("manage_users")),
    db: Session = Depends(get_db)
):
    try:
        existing_user = db.query(Usuario).filter(
            (Usuario.rut == user_data.rut) | (Usuario.email == user_data.email)
        ).first()
        
        if existing_user:
            if existing_user.rut == user_data.rut:
                raise HTTPException(status_code=400, detail="Ya existe un usuario con este RUT")
            else:
                raise HTTPException(status_code=400, detail="Ya existe un usuario con este email")

        hashed_password = hash_password(user_data.password)
        new_user = Usuario(
            rut=user_data.rut,
            nombre=user_data.nombre,
            apellido_paterno=user_data.apellido_paterno,
            apellido_materno=user_data.apellido_materno or "",
            email=user_data.email,
            telefono=user_data.telefono,
            hash_password=hashed_password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        if user_data.roles:
            for role_id in user_data.roles:
                role = db.query(Rol).filter(Rol.id_rol == role_id).first()
                if role:
                    user_role = UsuarioRol(id_usuario=new_user.id_usuario, id_rol=role_id)
                    db.add(user_role)
                    
                    if role.nombre in [RolConstantes.MEDICO, RolConstantes.RECEPCIONISTA]:
                        cargo_nombre = "Médico General" if role.nombre == RolConstantes.MEDICO else "Recepcionista"
                        cargo = db.query(Cargo).filter(Cargo.nombre == cargo_nombre).first()
                        
                        if cargo:
                            funcionario = Funcionario(
                                id_usuario=new_user.id_usuario,
                                id_cargo=cargo.id_cargo,
                                fecha_contrato=date.today(),
                                estado='ACTIVO'
                            )
                            db.add(funcionario)
                            db.flush()
                            
                            if role.nombre == RolConstantes.MEDICO:
                                profesional = ProfesionalSalud(
                                    id_funcionario=funcionario.id_funcionario,
                                    registro_profesional=f"REG-{new_user.id_usuario}-{date.today().year}",
                                    fecha_titulo=date.today(),
                                    estado_registro='VIGENTE'
                                )
                                db.add(profesional)
                    
                    elif role.nombre == RolConstantes.PACIENTE:
                        paciente = Paciente(
                            id_usuario=new_user.id_usuario
                        )
                        db.add(paciente)
            
            db.commit()
        else:
            paciente_role = db.query(Rol).filter(Rol.nombre == RolConstantes.PACIENTE).first()
            if paciente_role:
                user_role = UsuarioRol(id_usuario=new_user.id_usuario, id_rol=paciente_role.id_rol)
                db.add(user_role)
                
                paciente = Paciente(
                    id_usuario=new_user.id_usuario
                )
                db.add(paciente)
                db.commit()
        
        return MessageResponseSchema(
            message="Usuario creado exitosamente",
            user_id=new_user.id_usuario
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
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
        user = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        db.query(UsuarioRol).filter(UsuarioRol.id_usuario == user_id).delete()
        
        for role_id in roles_data.roles:
            role = db.query(Rol).filter(Rol.id_rol == role_id).first()
            if role:
                user_role = UsuarioRol(id_usuario=user_id, id_rol=role_id)
                db.add(user_role)
        
        db.commit()
        
        return MessageResponseSchema(message="Roles actualizados exitosamente")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.delete("/users/{user_id}", response_model=MessageResponseSchema)
def delete_user(
    user_id: int,
    current_user_id: int = Depends(require_permission("manage_users")),
    db: Session = Depends(get_db)
):
    try:
        if user_id == current_user_id:
            raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta")
        
        user = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        db.query(UsuarioRol).filter(UsuarioRol.id_usuario == user_id).delete()
        db.query(Sesion).filter(Sesion.id_usuario == user_id).delete()
        db.delete(user)
        db.commit()
        
        return MessageResponseSchema(message="Usuario eliminado exitosamente")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
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
        query = db.query(Cita).join(
            BloqueHora, Cita.id_bloque == BloqueHora.id_bloque
        ).join(
            AgendaDiaria, BloqueHora.id_agenda == AgendaDiaria.id_agenda
        ).join(
            Paciente, Cita.id_paciente == Paciente.id_paciente
        ).join(
            Usuario, Paciente.id_usuario == Usuario.id_usuario
        )
        
        if estado:
            query = query.filter(Cita.estado == estado)
        
        if fecha_desde:
            try:
                fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                query = query.filter(AgendaDiaria.fecha >= fecha_desde_obj)
            except ValueError:
                pass
        
        if fecha_hasta:
            try:
                fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                query = query.filter(AgendaDiaria.fecha <= fecha_hasta_obj)
            except ValueError:
                pass
        
        if rut_paciente:
            query = query.filter(Usuario.rut.contains(rut_paciente.replace('-', '')))
        
        if profesional:
            from sqlalchemy.orm import aliased
            UsuarioProfesional = aliased(Usuario)
            
            query = query.join(
                ProfesionalSalud, AgendaDiaria.id_profesional == ProfesionalSalud.id_profesional
            ).join(
                Funcionario, ProfesionalSalud.id_funcionario == Funcionario.id_funcionario
            ).join(
                UsuarioProfesional, Funcionario.id_usuario == UsuarioProfesional.id_usuario
            ).filter(
                (UsuarioProfesional.nombre.ilike(f'%{profesional}%')) |
                (UsuarioProfesional.apellido_paterno.ilike(f'%{profesional}%')) |
                (UsuarioProfesional.apellido_materno.ilike(f'%{profesional}%'))
            )
        
        if especialidad:
            if not profesional:
                query = query.join(
                    ProfesionalSalud, AgendaDiaria.id_profesional == ProfesionalSalud.id_profesional
                )
            
            query = query.join(
                ProfesionalEspecialidad, ProfesionalSalud.id_profesional == ProfesionalEspecialidad.id_profesional
            ).join(
                Especialidad, ProfesionalEspecialidad.id_especialidad == Especialidad.id_especialidad
            ).filter(
                Especialidad.nombre.ilike(f'%{especialidad}%')
            )
        
        citas = query.order_by(desc(Cita.fecha_solicitud)).all()
        
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
        query = db.query(Cita).join(
            BloqueHora, Cita.id_bloque == BloqueHora.id_bloque
        ).join(
            AgendaDiaria, BloqueHora.id_agenda == AgendaDiaria.id_agenda
        ).join(
            Paciente, Cita.id_paciente == Paciente.id_paciente
        ).join(
            Usuario, Paciente.id_usuario == Usuario.id_usuario
        ).filter(
            Cita.estado == EstadoCita.ATENDIDA
        )

        if fecha_desde:
            try:
                fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                query = query.filter(AgendaDiaria.fecha >= fecha_desde_obj)
            except ValueError:
                pass
        
        if fecha_hasta:
            try:
                fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                query = query.filter(AgendaDiaria.fecha <= fecha_hasta_obj)
            except ValueError:
                pass

        if profesional:
            from sqlalchemy.orm import aliased
            UsuarioProfesional = aliased(Usuario)
            
            query = query.join(
                ProfesionalSalud, AgendaDiaria.id_profesional == ProfesionalSalud.id_profesional
            ).join(
                Funcionario, ProfesionalSalud.id_funcionario == Funcionario.id_funcionario
            ).join(
                UsuarioProfesional, Funcionario.id_usuario == UsuarioProfesional.id_usuario
            ).filter(
                (UsuarioProfesional.nombre.ilike(f'%{profesional}%')) |
                (UsuarioProfesional.apellido_paterno.ilike(f'%{profesional}%')) |
                (UsuarioProfesional.apellido_materno.ilike(f'%{profesional}%'))
            )

        if especialidad:
            if not profesional:
                query = query.join(
                    ProfesionalSalud, AgendaDiaria.id_profesional == ProfesionalSalud.id_profesional
                )
            
            query = query.join(
                ProfesionalEspecialidad, ProfesionalSalud.id_profesional == ProfesionalEspecialidad.id_profesional
            ).join(
                Especialidad, ProfesionalEspecialidad.id_especialidad == Especialidad.id_especialidad
            ).filter(
                Especialidad.nombre.ilike(f'%{especialidad}%')
            )
        
        citas = query.order_by(desc(AgendaDiaria.fecha)).all()
        
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
