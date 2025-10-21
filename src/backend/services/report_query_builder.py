from datetime import datetime
from sqlalchemy.orm import Session, aliased
from sqlalchemy import desc
from models.cita import Cita
from models.bloque_hora import BloqueHora
from models.agenda_diaria import AgendaDiaria
from models.paciente import Paciente
from models.usuario import Usuario
from models.profesional_salud import ProfesionalSalud
from models.funcionario import Funcionario
from models.especialidad import Especialidad
from models.profesional_especialidad import ProfesionalEspecialidad


class ReportQueryBuilder:
    def __init__(self, db: Session):
        self.db = db
        self.query = db.query(Cita).join(
            BloqueHora, Cita.id_bloque == BloqueHora.id_bloque
        ).join(
            AgendaDiaria, BloqueHora.id_agenda == AgendaDiaria.id_agenda
        ).join(
            Paciente, Cita.id_paciente == Paciente.id_paciente
        ).join(
            Usuario, Paciente.id_usuario == Usuario.id_usuario
        )
        self._profesional_joined = False
        self._especialidad_joined = False
    
    def with_estado(self, estado: str):
        if estado:
            self.query = self.query.filter(Cita.estado == estado)
        return self
    
    def with_fecha_desde(self, fecha_desde: str):
        if fecha_desde:
            try:
                fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                self.query = self.query.filter(AgendaDiaria.fecha >= fecha_desde_obj)
            except ValueError:
                pass
        return self
    
    def with_fecha_hasta(self, fecha_hasta: str):
        if fecha_hasta:
            try:
                fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                self.query = self.query.filter(AgendaDiaria.fecha <= fecha_hasta_obj)
            except ValueError:
                pass
        return self
    
    def with_rut_paciente(self, rut_paciente: str):
        if rut_paciente:
            self.query = self.query.filter(
                Usuario.rut.contains(rut_paciente.replace('-', ''))
            )
        return self
    
    def _join_profesional(self):
        if not self._profesional_joined:
            UsuarioProfesional = aliased(Usuario)
            self.query = self.query.join(
                ProfesionalSalud, AgendaDiaria.id_profesional == ProfesionalSalud.id_profesional
            ).join(
                Funcionario, ProfesionalSalud.id_funcionario == Funcionario.id_funcionario
            ).join(
                UsuarioProfesional, Funcionario.id_usuario == UsuarioProfesional.id_usuario
            )
            self.UsuarioProfesional = UsuarioProfesional
            self._profesional_joined = True
    
    def with_profesional(self, profesional: str):
        if profesional:
            self._join_profesional()
            self.query = self.query.filter(
                (self.UsuarioProfesional.nombre.ilike(f'%{profesional}%')) |
                (self.UsuarioProfesional.apellido_paterno.ilike(f'%{profesional}%')) |
                (self.UsuarioProfesional.apellido_materno.ilike(f'%{profesional}%'))
            )
        return self
    
    def with_especialidad(self, especialidad: str):
        if especialidad:
            if not self._profesional_joined:
                self._join_profesional()
            
            if not self._especialidad_joined:
                self.query = self.query.join(
                    ProfesionalEspecialidad, ProfesionalSalud.id_profesional == ProfesionalEspecialidad.id_profesional
                ).join(
                    Especialidad, ProfesionalEspecialidad.id_especialidad == Especialidad.id_especialidad
                )
                self._especialidad_joined = True
            
            self.query = self.query.filter(
                Especialidad.nombre.ilike(f'%{especialidad}%')
            )
        return self
    
    def order_by_fecha_desc(self):
        self.query = self.query.order_by(desc(Cita.fecha_solicitud))
        return self
    
    def order_by_agenda_fecha_desc(self):
        self.query = self.query.order_by(desc(AgendaDiaria.fecha))
        return self
    
    def build(self):
        return self.query.all()
