from datetime import date, time, datetime, timedelta
from fastapi import HTTPException, status


class HorarioValidator:
    HORA_MINIMA = time(7, 0)
    HORA_MAXIMA = time(22, 0)
    DIAS_MAXIMOS_ANTICIPACION = 180
    DURACION_MINIMA_JORNADA = 60
    DURACION_MAXIMA_JORNADA = 720
    
    @staticmethod
    def validar_fecha_no_pasada(fecha: date):
        if fecha < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden crear agendas para fechas pasadas"
            )
    
    @staticmethod
    def validar_rango_anticipacion(fecha: date):
        fecha_actual = date.today()
        fecha_maxima = fecha_actual + timedelta(days=HorarioValidator.DIAS_MAXIMOS_ANTICIPACION)
        
        if fecha > fecha_maxima:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden crear agendas con más de 6 meses de anticipación"
            )
    
    @staticmethod
    def validar_hora_en_rango(hora: time, nombre_campo: str = "hora"):
        if hora < HorarioValidator.HORA_MINIMA or hora > HorarioValidator.HORA_MAXIMA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La {nombre_campo} debe estar entre las 07:00 y las 22:00"
            )
    
    @staticmethod
    def validar_duracion_jornada(hora_inicio: time, hora_fin: time):
        hora_inicio_dt = datetime.combine(date.today(), hora_inicio)
        hora_fin_dt = datetime.combine(date.today(), hora_fin)
        duracion_jornada = (hora_fin_dt - hora_inicio_dt).total_seconds() / 60
        
        if duracion_jornada < HorarioValidator.DURACION_MINIMA_JORNADA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La jornada debe tener al menos 1 hora de duración"
            )
        
        if duracion_jornada > HorarioValidator.DURACION_MAXIMA_JORNADA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La jornada no puede exceder las 12 horas"
            )
    
    @staticmethod
    def validar_horarios_completos(hora_inicio: time, hora_fin: time, fecha: date):
        HorarioValidator.validar_fecha_no_pasada(fecha)
        HorarioValidator.validar_rango_anticipacion(fecha)
        HorarioValidator.validar_hora_en_rango(hora_inicio, "hora de inicio")
        HorarioValidator.validar_hora_en_rango(hora_fin, "hora de fin")
        HorarioValidator.validar_duracion_jornada(hora_inicio, hora_fin)
