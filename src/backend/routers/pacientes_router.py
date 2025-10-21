import logging
from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from models import (
    Usuario, Paciente, Cita, BloqueHora, AgendaDiaria,
    ProfesionalSalud, Funcionario, Especialidad,
    MotivoCancelacion, ProfesionalEspecialidad
)
from schemas import (
    EspecialidadResponse, MotivoCancelacionResponse, ProfesionalResponse,
    BloqueDisponibleResponse, CitaResponse, SolicitarCitaRequest,
    CancelarCitaRequest, ReprogramarCitaRequest, CitaResponseAdmin
)
from utils import (
    require_staff, require_any_role, get_user_roles,
    get_current_user, EstadoCita, Rol,
    MotivoCancelacionExcluido, Mensajes,
    enviar_correo_cancelacion,
    enviar_correo_reprogramacion
)
from services import CitaService
from services.cita_service import (
    obtener_info_bloque_agenda,
    obtener_nombre_profesional,
    obtener_especialidad_profesional,
    validar_fecha_pasada,
    enviar_correo_seguro,
    obtener_profesional_desde_usuario,
    obtener_paciente_actual,
    buscar_pacientes_por_rut,
    validar_cita_duplicada,
    construir_cita_response_admin
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pacientes", tags=["Pacientes"])

@router.post("/reprogramar-cita/{id_cita}")
async def reprogramar_cita(
    id_cita: int,
    request: ReprogramarCitaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    _: int = Depends(require_any_role([Rol.PACIENTE]))
):
    try:
        paciente = obtener_paciente_actual(db, current_user.id_usuario)
        cita = db.query(Cita).filter(
            Cita.id_cita == id_cita,
            Cita.id_paciente == paciente.id_paciente,
            Cita.estado.in_(EstadoCita.CANCELABLES)
        ).first()
        if not cita:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cita no encontrada o no se puede reprogramar"
            )
        
        bloque_actual, agenda_actual = obtener_info_bloque_agenda(db, cita.id_bloque)
        
        if datetime.combine(agenda_actual.fecha, bloque_actual.hora_inicio) <= datetime.now() + timedelta(hours=2):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden reprogramar citas con menos de 2 horas de anticipación"
            )
        cita.estado = EstadoCita.CANCELADA
        cita.id_motivo_cancelacion = request.id_motivo_cancelacion
        cita.fecha_cancelacion = datetime.utcnow()
        cita.cancelada_por = current_user.id_usuario
        cita.observaciones = request.observaciones
        bloque_actual.disponible = True
        
        nuevo_bloque, nueva_agenda = obtener_info_bloque_agenda(db, request.id_nuevo_bloque)
        
        if validar_cita_duplicada(db, paciente.id_paciente, nueva_agenda.id_profesional, nueva_agenda.fecha, nuevo_bloque.hora_inicio, id_cita):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Mensajes.CITA_DUPLICADA
            )
        
        nueva_cita = Cita(
            id_paciente=paciente.id_paciente,
            id_bloque=request.id_nuevo_bloque,
            fecha_solicitud=datetime.utcnow(),
            estado=EstadoCita.AGENDADA,
            motivo_consulta=cita.motivo_consulta
        )
        db.add(nueva_cita)
        nuevo_bloque.disponible = False
        db.commit()
        
        profesional_nombre = obtener_nombre_profesional(db, nueva_agenda.id_profesional)
        especialidad_nombre = obtener_especialidad_profesional(db, nueva_agenda.id_profesional)
        
        await enviar_correo_seguro(
            enviar_correo_reprogramacion,
            email=current_user.email,
            nombre=current_user.nombre,
            fecha=nueva_agenda.fecha,
            hora=nuevo_bloque.hora_inicio,
            profesional=profesional_nombre,
            especialidad=especialidad_nombre,
            fecha_anterior=agenda_actual.fecha,
            hora_anterior=bloque_actual.hora_inicio
        )
        
        return {
            "message": "Cita reprogramada exitosamente",
            "id_cita": nueva_cita.id_cita,
            "fecha": nueva_agenda.fecha,
            "hora": nuevo_bloque.hora_inicio
        }
    except HTTPException as http_exc:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reprogramar la cita: {str(e)}"
        )

@router.get("/especialidades", response_model=List[EspecialidadResponse])
async def obtener_especialidades(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    _: int = Depends(require_any_role([Rol.PACIENTE, Rol.ADMINISTRADOR]))
):
    especialidades = db.query(Especialidad).all()
    
    return [
        EspecialidadResponse(
            id_especialidad=esp.id_especialidad,
            nombre=esp.nombre,
            descripcion=esp.descripcion
        )
        for esp in especialidades
    ]

@router.get("/motivos-cancelacion", response_model=List[MotivoCancelacionResponse])
async def obtener_motivos_cancelacion(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    _: int = Depends(require_any_role(Rol.TODOS))
):
    motivos = db.query(MotivoCancelacion).filter(
        MotivoCancelacion.activo == True,
        ~MotivoCancelacion.descripcion.in_(MotivoCancelacionExcluido.LISTA)
    ).all()
    
    return [
        MotivoCancelacionResponse(
            id_motivo=motivo.id_motivo,
            descripcion=motivo.descripcion
        )
        for motivo in motivos
    ]

@router.get("/profesionales", response_model=List[ProfesionalResponse])
async def obtener_profesionales(
    id_especialidad: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    _: int = Depends(require_any_role([Rol.PACIENTE, Rol.ADMINISTRADOR]))
):
    query = (db.query(ProfesionalSalud, Usuario)
            .join(Funcionario, ProfesionalSalud.id_funcionario == Funcionario.id_funcionario)
            .join(Usuario, Funcionario.id_usuario == Usuario.id_usuario))
    
    if id_especialidad:
        query = query.join(ProfesionalEspecialidad, 
                        ProfesionalSalud.id_profesional == ProfesionalEspecialidad.id_profesional
                        ).filter(ProfesionalEspecialidad.id_especialidad == id_especialidad)

    resultados = query.all()
    
    profesionales_response = []
    ahora = datetime.now()
    tiempo_minimo = ahora + timedelta(minutes=30)
    
    for prof, usuario in resultados:
        bloques_disponibles = (db.query(BloqueHora)
                             .join(AgendaDiaria, BloqueHora.id_agenda == AgendaDiaria.id_agenda)
                             .filter(
                                 AgendaDiaria.id_profesional == prof.id_profesional,
                                 BloqueHora.disponible == True
                             )
                             .all())
        
        tiene_bloques_futuros = False
        for bloque in bloques_disponibles:
            agenda = db.query(AgendaDiaria).filter(AgendaDiaria.id_agenda == bloque.id_agenda).first()
            if agenda:
                fecha_hora_bloque = datetime.combine(agenda.fecha, bloque.hora_inicio)
                if fecha_hora_bloque >= tiempo_minimo:
                    tiene_bloques_futuros = True
                    break
        
        if not tiene_bloques_futuros:
            continue
        
        especialidades = (db.query(Especialidad.nombre)
                        .join(ProfesionalEspecialidad, Especialidad.id_especialidad == ProfesionalEspecialidad.id_especialidad)
                        .filter(ProfesionalEspecialidad.id_profesional == prof.id_profesional)
                        .all())
        
        profesionales_response.append(ProfesionalResponse(
            id_profesional=prof.id_profesional,
            nombre_completo=f"{usuario.nombre} {usuario.apellido_paterno}",
            registro_profesional=prof.registro_profesional,
            especialidades=[esp[0] for esp in especialidades]
        ))
    
    return profesionales_response

@router.get("/bloques-disponibles", response_model=List[BloqueDisponibleResponse])
async def obtener_bloques_disponibles(
    id_profesional: Optional[int] = None,
    id_especialidad: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    _: int = Depends(require_any_role(Rol.TODOS))
):
    if not fecha_desde:
        fecha_desde = date.today()
    elif fecha_desde < date.today():
        fecha_desde = date.today()
    
    ahora = datetime.now()
    tiempo_minimo_anticipacion = timedelta(minutes=30)
    
    bloques_ocupados_subq = db.query(Cita.id_bloque).filter(
        Cita.estado.in_(EstadoCita.ACTIVAS)
    ).subquery()
    
    query = db.query(
        BloqueHora,
        AgendaDiaria,
        Usuario,
        Especialidad
    ).join(AgendaDiaria, BloqueHora.id_agenda == AgendaDiaria.id_agenda)\
     .join(ProfesionalSalud, AgendaDiaria.id_profesional == ProfesionalSalud.id_profesional)\
     .join(Funcionario, ProfesionalSalud.id_funcionario == Funcionario.id_funcionario)\
     .join(Usuario, Funcionario.id_usuario == Usuario.id_usuario)\
     .outerjoin(ProfesionalEspecialidad, ProfesionalSalud.id_profesional == ProfesionalEspecialidad.id_profesional)\
     .outerjoin(Especialidad, ProfesionalEspecialidad.id_especialidad == Especialidad.id_especialidad)\
     .filter(
        BloqueHora.disponible == True,
        AgendaDiaria.activa == True,
        AgendaDiaria.fecha >= fecha_desde,
        ~BloqueHora.id_bloque.in_(bloques_ocupados_subq)
    )
    
    if fecha_hasta:
        query = query.filter(AgendaDiaria.fecha <= fecha_hasta)
    
    if id_profesional:
        query = query.filter(AgendaDiaria.id_profesional == id_profesional)
    
    if id_especialidad:
        query = query.filter(Especialidad.id_especialidad == id_especialidad)
    
    resultados = query.order_by(AgendaDiaria.fecha, BloqueHora.hora_inicio).limit(50).all()
    
    bloques_response = []
    for bloque, agenda, usuario, especialidad in resultados:
        fecha_hora_bloque = datetime.combine(agenda.fecha, bloque.hora_inicio)
        if fecha_hora_bloque <= ahora + tiempo_minimo_anticipacion:
            continue
        
        bloques_response.append(BloqueDisponibleResponse(
            id_bloque=bloque.id_bloque,
            fecha=agenda.fecha,
            hora_inicio=bloque.hora_inicio,
            hora_fin=bloque.hora_fin,
            profesional=f"{usuario.nombre} {usuario.apellido_paterno}",
            especialidad=especialidad.nombre if especialidad else "General"
        ))
    
    return bloques_response

@router.post("/solicitar-cita")
async def solicitar_cita(
    request: SolicitarCitaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    _: int = Depends(require_any_role([Rol.PACIENTE]))
):
    paciente = obtener_paciente_actual(db, current_user.id_usuario)
    cita_service = CitaService(db)
    
    return await cita_service.crear_cita_completa(
        id_paciente=paciente.id_paciente,
        id_bloque=request.id_bloque,
        motivo_consulta=request.motivo_consulta,
        email_paciente=current_user.email,
        nombre_paciente=f"{current_user.nombre} {current_user.apellido_paterno}"
    )

@router.get("/mis-citas", response_model=List[CitaResponse])
async def obtener_mis_citas(
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    _: int = Depends(require_any_role([Rol.PACIENTE]))
):
    try:
        paciente = obtener_paciente_actual(db, current_user.id_usuario)
        
        query = db.query(
            Cita,
            BloqueHora,
            AgendaDiaria,
            Usuario,
            Especialidad
        ).join(BloqueHora, Cita.id_bloque == BloqueHora.id_bloque)\
         .join(AgendaDiaria, BloqueHora.id_agenda == AgendaDiaria.id_agenda)\
         .join(ProfesionalSalud, AgendaDiaria.id_profesional == ProfesionalSalud.id_profesional)\
         .join(Funcionario, ProfesionalSalud.id_funcionario == Funcionario.id_funcionario)\
         .join(Usuario, Funcionario.id_usuario == Usuario.id_usuario)\
         .outerjoin(ProfesionalEspecialidad, ProfesionalSalud.id_profesional == ProfesionalEspecialidad.id_profesional)\
         .outerjoin(Especialidad, ProfesionalEspecialidad.id_especialidad == Especialidad.id_especialidad)\
         .filter(Cita.id_paciente == paciente.id_paciente)
        
        if estado:
            query = query.filter(Cita.estado == estado)
        
        resultados = query.all()
        
        citas_response = []
        for cita, bloque, agenda, usuario_prof, especialidad in resultados:
            citas_response.append(CitaResponse(
                id_cita=cita.id_cita,
                fecha=agenda.fecha,
                hora_inicio=bloque.hora_inicio,
                hora_fin=bloque.hora_fin,
                estado=cita.estado,
                profesional=f"{usuario_prof.nombre} {usuario_prof.apellido_paterno}",
                especialidad=especialidad.nombre if especialidad else "Medicina General",
                motivo_consulta=cita.motivo_consulta,
                observaciones=cita.observaciones
            ))
        
        citas_response.sort(key=lambda x: (x.fecha, x.hora_inicio), reverse=True)
        
        return citas_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error general en obtener_mis_citas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener las citas: {str(e)}"
        )

@router.post("/cancelar-cita/{id_cita}")
async def cancelar_cita(
    id_cita: int,
    request: CancelarCitaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    _: int = Depends(require_any_role([Rol.PACIENTE]))
):
    try:
        paciente = obtener_paciente_actual(db, current_user.id_usuario)
        
        cita = db.query(Cita).join(BloqueHora).join(AgendaDiaria).filter(
            Cita.id_cita == id_cita,
            Cita.id_paciente == paciente.id_paciente,
            Cita.estado.in_(EstadoCita.CANCELABLES)
        ).first()
        
        if not cita:
            cita_existente = db.query(Cita).filter(
                Cita.id_cita == id_cita,
                Cita.id_paciente == paciente.id_paciente
            ).first()
            
            if cita_existente:
                if cita_existente.estado == EstadoCita.CANCELADA:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Esta cita ya fue cancelada anteriormente"
                    )
                elif cita_existente.estado in ['ATENDIDA', 'NO_ASISTIO']:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No se puede cancelar una cita que ya finalizó"
                    )
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cita no encontrada o no pertenece a este paciente"
            )
        
        bloque, agenda = obtener_info_bloque_agenda(db, cita.id_bloque)
        
        validar_fecha_pasada(agenda.fecha, bloque.hora_inicio)
        
        fecha_cita = agenda.fecha
        hora_cita = bloque.hora_inicio
        nombre_profesional = obtener_nombre_profesional(db, agenda.id_profesional)
        
        motivo = db.query(MotivoCancelacion).filter(
            MotivoCancelacion.id_motivo == request.id_motivo_cancelacion
        ).first()
        motivo_texto = motivo.descripcion if motivo else "Motivo no especificado"
        
        cita.estado = 'CANCELADA'
        cita.id_motivo_cancelacion = request.id_motivo_cancelacion
        cita.fecha_cancelacion = datetime.utcnow()
        cita.cancelada_por = current_user.id_usuario
        cita.observaciones = request.observaciones
        
        bloque.disponible = True
        
        db.commit()
        
        usuario_paciente = db.query(Usuario).filter(Usuario.id_usuario == paciente.id_usuario).first()
        if usuario_paciente and usuario_paciente.email:
            await enviar_correo_seguro(
                enviar_correo_cancelacion,
                email=usuario_paciente.email,
                nombre=f"{usuario_paciente.nombre} {usuario_paciente.apellido_paterno}",
                fecha=fecha_cita,
                hora=hora_cita,
                profesional=nombre_profesional,
                motivo_cancelacion=motivo_texto
            )
        
        return {"message": "Cita cancelada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cancelar la cita: {str(e)}"
        )


@router.get(
    "/admin/todas-las-citas",
    response_model=List[CitaResponseAdmin],
    summary="Obtener citas del sistema (Personal autorizado)",
    dependencies=[Depends(require_staff)]
)
async def obtener_todas_las_citas_admin(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, le=500, description="Número máximo de registros a retornar"),
    estado: Optional[str] = Query(None, description="Filtrar por estado de cita"),
    fecha_desde: Optional[date] = Query(None, description="Filtrar desde fecha (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Filtrar hasta fecha (YYYY-MM-DD)"),
    profesional_id: Optional[int] = Query(None, description="Filtrar por ID del profesional"),
    especialidad_id: Optional[int] = Query(None, description="Filtrar por ID de especialidad"),
    paciente_rut: Optional[str] = Query(None, degescription="Filtrar por RUT del paciente (con o sin formato)"),
    active_role: Optional[str] = Query(None, description="Rol activo del usuario en el frontend"),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene las citas según el rol activo del usuario:
    - Administrador/Recepcionista: Todas las citas (o filtradas por profesional_id si se especifica)
    - Médico: Solo sus propias citas (basándose en active_role si se proporciona)
    """
    try:
        user_roles = get_user_roles(db, current_user.id_usuario)
        
        if active_role == "Médico" or (active_role is None and "Médico" in user_roles and "Administrador" not in user_roles and "Recepcionista" not in user_roles):
            profesional_id = obtener_profesional_desde_usuario(db, current_user.id_usuario)
        
        if paciente_rut:
            ids_pacientes_filtrados = buscar_pacientes_por_rut(db, paciente_rut)
            if not ids_pacientes_filtrados:
                logger.info(f"No se encontraron pacientes con RUT: {paciente_rut}")
                return []
        
        from sqlalchemy.orm import aliased
        UsuarioPaciente = aliased(Usuario)
        UsuarioProfesional = aliased(Usuario)
        
        query = db.query(
            Cita,
            BloqueHora,
            AgendaDiaria,
            Paciente,
            UsuarioPaciente,
            ProfesionalSalud,
            UsuarioProfesional,
            Especialidad,
            MotivoCancelacion
        ).join(BloqueHora, Cita.id_bloque == BloqueHora.id_bloque)\
         .join(AgendaDiaria, BloqueHora.id_agenda == AgendaDiaria.id_agenda)\
         .join(Paciente, Cita.id_paciente == Paciente.id_paciente)\
         .join(UsuarioPaciente, Paciente.id_usuario == UsuarioPaciente.id_usuario)\
         .join(ProfesionalSalud, AgendaDiaria.id_profesional == ProfesionalSalud.id_profesional)\
         .join(Funcionario, ProfesionalSalud.id_funcionario == Funcionario.id_funcionario)\
         .join(UsuarioProfesional, Funcionario.id_usuario == UsuarioProfesional.id_usuario)\
         .join(ProfesionalEspecialidad, ProfesionalSalud.id_profesional == ProfesionalEspecialidad.id_profesional)\
         .join(Especialidad, ProfesionalEspecialidad.id_especialidad == Especialidad.id_especialidad)\
         .outerjoin(MotivoCancelacion, Cita.id_motivo_cancelacion == MotivoCancelacion.id_motivo)
        
        if profesional_id:
            query = query.filter(AgendaDiaria.id_profesional == profesional_id)
        
        if fecha_desde:
            query = query.filter(AgendaDiaria.fecha >= fecha_desde)
        if fecha_hasta:
            query = query.filter(AgendaDiaria.fecha <= fecha_hasta)
        
        if estado:
            query = query.filter(Cita.estado == estado)
        
        if paciente_rut and ids_pacientes_filtrados:
            query = query.filter(Cita.id_paciente.in_(ids_pacientes_filtrados))
        
        if especialidad_id:
            query = query.filter(Especialidad.id_especialidad == especialidad_id)
        
        resultados = query.order_by(AgendaDiaria.fecha.desc(), BloqueHora.hora_inicio.desc())\
                          .offset(skip)\
                          .limit(limit)\
                          .all()
        
        citas_response = []
        for cita, bloque, agenda, paciente, usuario_paciente, profesional_salud, usuario_profesional, especialidad, motivo_cancelacion in resultados:
            cita_data = construir_cita_response_admin(
                cita, bloque, agenda, paciente, usuario_paciente,
                profesional_salud, usuario_profesional, especialidad, motivo_cancelacion
            )
            citas_response.append(cita_data)
        
        return citas_response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener las citas: {str(e)}"
        )



@router.post(
    "/admin/cancelar-cita/{id_cita}",
    summary="Cancelar cualquier cita (Personal autorizado)",
    dependencies=[Depends(require_staff)]
)
async def admin_cancelar_cita(
    id_cita: int,
    request: CancelarCitaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Permite a médicos y administradores cancelar citas.
    Los médicos solo pueden cancelar sus propias citas.
    """
    try:
        cita = db.query(Cita).join(BloqueHora).join(AgendaDiaria).filter(
            Cita.id_cita == id_cita,
            Cita.estado.in_(EstadoCita.CANCELABLES)
        ).first()
        
        if not cita:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cita no encontrada o no se puede cancelar"
            )
        
        bloque, agenda = obtener_info_bloque_agenda(db, cita.id_bloque)
        
        user_roles = get_user_roles(db, current_user.id_usuario)
        if "Médico" in user_roles and "Administrador" not in user_roles:
            profesional_id = obtener_profesional_desde_usuario(db, current_user.id_usuario)
            if profesional_id and agenda.id_profesional != profesional_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para cancelar citas de otros profesionales"
                )
        
        cita.estado = 'CANCELADA'
        cita.id_motivo_cancelacion = request.id_motivo_cancelacion
        cita.fecha_cancelacion = datetime.utcnow()
        cita.cancelada_por = current_user.id_usuario
        cita.observaciones = request.observaciones
        
        bloque.disponible = True
        
        db.commit()
        db.refresh(cita)
        
        paciente = db.query(Paciente).filter(Paciente.id_paciente == cita.id_paciente).first()
        if paciente:
            usuario_paciente = db.query(Usuario).filter(Usuario.id_usuario == paciente.id_usuario).first()
            if usuario_paciente and usuario_paciente.email:
                await enviar_correo_seguro(
                    enviar_correo_cancelacion,
                    email=usuario_paciente.email,
                    nombre=usuario_paciente.nombre,
                    fecha=agenda.fecha,
                    hora=bloque.hora_inicio,
                    profesional=obtener_nombre_profesional(db, agenda.id_profesional),
                    motivo_cancelacion=request.observaciones or "Cancelación administrativa"
                )
        
        return {
            "message": "Cita cancelada exitosamente",
            "id_cita": cita.id_cita,
            "nuevo_estado": cita.estado
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cancelar la cita: {str(e)}"
        )


@router.post(
    "/admin/reprogramar-cita/{id_cita}",
    summary="Reprogramar cualquier cita (Personal autorizado)",
    dependencies=[Depends(require_staff)]
)
async def admin_reprogramar_cita(
    id_cita: int,
    request: ReprogramarCitaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Permite a médicos y administradores reprogramar citas.
    Los médicos solo pueden reprogramar sus propias citas.
    """
    try:
        cita = db.query(Cita).filter(
            Cita.id_cita == id_cita,
            Cita.estado.in_(["AGENDADA", "CONFIRMADA"])
        ).first()
        
        if not cita:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cita no encontrada o no se puede reprogramar"
            )
        
        bloque_actual, agenda_actual = obtener_info_bloque_agenda(db, cita.id_bloque)
        
        user_roles = get_user_roles(db, current_user.id_usuario)
        if "Médico" in user_roles and "Administrador" not in user_roles:
            profesional_id = obtener_profesional_desde_usuario(db, current_user.id_usuario)
            if profesional_id and agenda_actual.id_profesional != profesional_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para reprogramar citas de otros profesionales"
                )
        
        cita.estado = 'CANCELADA'
        cita.id_motivo_cancelacion = request.id_motivo_cancelacion
        cita.fecha_cancelacion = datetime.utcnow()
        cita.cancelada_por = current_user.id_usuario
        cita.observaciones = request.observaciones
        bloque_actual.disponible = True
        
        nuevo_bloque, nueva_agenda = obtener_info_bloque_agenda(db, request.id_nuevo_bloque)
        
        if not nuevo_bloque.disponible:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El nuevo bloque seleccionado no está disponible"
            )
        
        if not nueva_agenda.activa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La agenda del nuevo bloque no está disponible"
            )
        
        if validar_cita_duplicada(db, cita.id_paciente, nueva_agenda.id_profesional, nueva_agenda.fecha, nuevo_bloque.hora_inicio, id_cita):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una cita agendada con este profesional en la nueva fecha y hora seleccionada"
            )
        
        nueva_cita = Cita(
            id_paciente=cita.id_paciente,
            id_bloque=nuevo_bloque.id_bloque,
            estado=EstadoCita.AGENDADA,
            motivo_consulta=cita.motivo_consulta,
            fecha_solicitud=datetime.utcnow()
        )
        
        nuevo_bloque.disponible = False
        
        db.add(nueva_cita)
        db.commit()
        db.refresh(nueva_cita)
        
        paciente = db.query(Paciente).filter(Paciente.id_paciente == cita.id_paciente).first()
        if paciente:
            usuario_paciente = db.query(Usuario).filter(Usuario.id_usuario == paciente.id_usuario).first()
            if usuario_paciente and usuario_paciente.email:
                await enviar_correo_seguro(
                    enviar_correo_reprogramacion,
                    email=usuario_paciente.email,
                    nombre=usuario_paciente.nombre,
                    fecha=nueva_agenda.fecha,
                    hora=nuevo_bloque.hora_inicio,
                    profesional=obtener_nombre_profesional(db, nueva_agenda.id_profesional),
                    especialidad=obtener_especialidad_profesional(db, nueva_agenda.id_profesional),
                    fecha_anterior=agenda_actual.fecha,
                    hora_anterior=bloque_actual.hora_inicio
                )
        
        return {
            "message": "Cita reprogramada exitosamente",
            "id_cita_cancelada": id_cita,
            "id_cita_nueva": nueva_cita.id_cita,
            "nueva_fecha": nueva_agenda.fecha,
            "nueva_hora": nuevo_bloque.hora_inicio
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reprogramar la cita: {str(e)}"
        )


@router.put(
    "/admin/marcar-atendida/{id_cita}",
    summary="Marcar cita como atendida (Personal autorizado)",
    dependencies=[Depends(require_staff)]
)
async def admin_marcar_atendida(
    id_cita: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Permite a médicos y administradores marcar una cita como atendida.
    Los médicos solo pueden marcar sus propias citas.
    """
    try:
        cita = db.query(Cita).filter(
            Cita.id_cita == id_cita,
            Cita.estado.in_(EstadoCita.ACTIVAS)
        ).first()
        
        if not cita:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cita no encontrada o no se puede marcar como atendida"
            )
        
        user_roles = get_user_roles(db, current_user.id_usuario)
        if "Médico" in user_roles and "Administrador" not in user_roles:
            _, agenda = obtener_info_bloque_agenda(db, cita.id_bloque)
            profesional_id = obtener_profesional_desde_usuario(db, current_user.id_usuario)
            if profesional_id and agenda.id_profesional != profesional_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para marcar citas de otros profesionales"
                )
        
        cita.estado = 'ATENDIDA'
        
        db.commit()
        db.refresh(cita)
        
        return {
            "message": "Cita marcada como atendida exitosamente",
            "id_cita": cita.id_cita,
            "nuevo_estado": cita.estado
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al marcar la cita como atendida: {str(e)}"
        )


@router.put(
    "/admin/marcar-no-asistio/{id_cita}",
    summary="Marcar cita como no asistió (Personal autorizado)",
    dependencies=[Depends(require_staff)]
)
async def admin_marcar_no_asistio(
    id_cita: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Permite a médicos y administradores marcar una cita como no asistida.
    Los médicos solo pueden marcar sus propias citas.
    """
    try:
        cita = db.query(Cita).filter(
            Cita.id_cita == id_cita,
            Cita.estado.in_(EstadoCita.CANCELABLES)
        ).first()
        
        if not cita:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cita no encontrada o no se puede marcar como no asistida"
            )
        
        bloque, agenda = obtener_info_bloque_agenda(db, cita.id_bloque)
        
        user_roles = get_user_roles(db, current_user.id_usuario)
        if "Médico" in user_roles and "Administrador" not in user_roles:
            profesional_id = obtener_profesional_desde_usuario(db, current_user.id_usuario)
            if profesional_id and agenda.id_profesional != profesional_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para marcar citas de otros profesionales"
                )
        
        cita.estado = 'NO_ASISTIO'
        bloque.disponible = True
        
        db.commit()
        db.refresh(cita)
        
        return {
            "message": "Cita marcada como no asistió exitosamente",
            "id_cita": cita.id_cita,
            "nuevo_estado": cita.estado
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al marcar la cita como no asistida: {str(e)}"
        )
