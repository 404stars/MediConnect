"""
Constantes globales del sistema MediConnect
Centraliza valores hardcodeados para facilitar mantenimiento y escalabilidad
"""

# ==================== ESTADOS DE CITAS ====================
class EstadoCita:
    """Estados válidos para una cita médica"""
    AGENDADA = 'AGENDADA'
    CONFIRMADA = 'CONFIRMADA'
    EN_ATENCION = 'EN_ATENCION'
    ATENDIDA = 'ATENDIDA'
    CANCELADA = 'CANCELADA'
    NO_ASISTIO = 'NO_ASISTIO'
    
    # Grupos de estados para consultas frecuentes
    ACTIVAS = [AGENDADA, CONFIRMADA, EN_ATENCION]
    CANCELABLES = [AGENDADA, CONFIRMADA]
    FINALIZADAS = [ATENDIDA, CANCELADA, NO_ASISTIO]
    TODAS = [AGENDADA, CONFIRMADA, EN_ATENCION, ATENDIDA, CANCELADA, NO_ASISTIO]


# ==================== ROLES DEL SISTEMA ====================
class Rol:
    """Roles de usuario disponibles en el sistema"""
    PACIENTE = 'Paciente'
    MEDICO = 'Médico'
    ADMINISTRADOR = 'Administrador'
    RECEPCIONISTA = 'Recepcionista'
    
    # Grupos de roles para permisos frecuentes
    STAFF = [ADMINISTRADOR, MEDICO, RECEPCIONISTA]
    PERSONAL_SALUD = [MEDICO, RECEPCIONISTA]
    TODOS = [PACIENTE, MEDICO, ADMINISTRADOR, RECEPCIONISTA]


# ==================== MOTIVOS DE CANCELACIÓN ====================
class MotivoCancelacionExcluido:
    """Motivos de cancelación que no deben mostrarse a pacientes"""
    CANCELACION_MEDICO = "Cancelación por el médico"
    CANCELACION_PACIENTE = "Cancelación por el paciente"
    ENFERMEDAD_MEDICO = "Enfermedad del médico"
    OTROS_MOTIVOS_MEDICOS = "Otros motivos médicos"
    
    # Lista completa para filtrado
    LISTA = [
        CANCELACION_MEDICO,
        CANCELACION_PACIENTE,
        ENFERMEDAD_MEDICO,
        OTROS_MOTIVOS_MEDICOS
    ]


# ==================== LÍMITES Y REGLAS DE NEGOCIO ====================
class ReglasNegocio:
    """Límites y configuraciones del sistema"""
    # Citas
    MAX_CITAS_POR_DIA = 3
    TIEMPO_ANTICIPACION_MINUTOS = 30
    
    # Paginación
    ITEMS_PER_PAGE_DEFAULT = 50
    MAX_ITEMS_PER_PAGE = 100
    
    # RUT
    RUT_MIN_LENGTH = 8
    RUT_MAX_LENGTH = 12


# ==================== MENSAJES DEL SISTEMA ====================
class Mensajes:
    """Mensajes estandarizados del sistema"""
    # Éxito
    CITA_AGENDADA = "Cita agendada exitosamente"
    CITA_CANCELADA = "Cita cancelada exitosamente"
    CITA_REPROGRAMADA = "Cita reprogramada exitosamente"
    
    # Errores de citas
    CITA_NO_ENCONTRADA = "Cita no encontrada"
    CITA_YA_CANCELADA = "Esta cita ya fue cancelada anteriormente"
    CITA_FINALIZADA = "No se puede cancelar una cita que ya finalizó"
    BLOQUE_NO_DISPONIBLE = "Este bloque de hora ya no está disponible"
    BLOQUE_OCUPADO = "Este bloque de hora ya está ocupado por otra cita"
    CITA_DUPLICADA = "Ya tienes una cita agendada con este profesional en la misma fecha y hora"
    LIMITE_CITAS_DIA = "No puedes tener más de {max} citas agendadas en un mismo día"
    
    # Errores de autorización
    ACCESO_DENEGADO = "No tienes permisos para realizar esta acción"
    SOLO_PACIENTES = "Solo los pacientes pueden realizar esta acción"
    
    # Errores de datos
    PACIENTE_NO_ENCONTRADO = "Paciente no encontrado"
    PROFESIONAL_NO_ENCONTRADO = "Profesional de salud no encontrado"
    AGENDA_NO_ENCONTRADA = "Agenda no encontrada"


# ==================== CONFIGURACIÓN DE EMAIL ====================
class ConfigEmail:
    """Configuración relacionada con emails"""
    REMITENTE_NOMBRE = "MediConnect"
    ASUNTO_CONFIRMACION_CITA = "Confirmación de Cita Médica"
    ASUNTO_CANCELACION_CITA = "Cancelación de Cita Médica"
    ASUNTO_REPROGRAMACION_CITA = "Reprogramación de Cita Médica"
    ASUNTO_RECUPERACION_PASSWORD = "Recuperación de Contraseña"
