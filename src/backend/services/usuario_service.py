import logging
from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models.usuario import Usuario
from models.usuario_rol import UsuarioRol
from models.rol import Rol
from models.paciente import Paciente
from models.funcionario import Funcionario
from models.cargo import Cargo
from models.profesional_salud import ProfesionalSalud
from utils.hashing import hash_password
from utils.constants import Rol as RolConstantes

logger = logging.getLogger(__name__)


class UsuarioService:
    def __init__(self, db: Session):
        self.db = db
    
    def verificar_usuario_existente(self, rut: str, email: str, excluir_id: Optional[int] = None):
        query = self.db.query(Usuario).filter(
            (Usuario.rut == rut) | (Usuario.email == email)
        )
        
        if excluir_id:
            query = query.filter(Usuario.id_usuario != excluir_id)
        
        existing_user = query.first()
        
        if existing_user:
            if existing_user.rut == rut:
                raise ValueError("Ya existe un usuario con este RUT")
            else:
                raise ValueError("Ya existe un usuario con este email")
        
        return None
    
    def crear_usuario_base(
        self,
        rut: str,
        nombre: str,
        apellido_paterno: str,
        apellido_materno: str,
        email: str,
        telefono: str,
        password: str
    ) -> Usuario:
        hashed_password = hash_password(password)
        
        new_user = Usuario(
            rut=rut,
            nombre=nombre,
            apellido_paterno=apellido_paterno,
            apellido_materno=apellido_materno or "",
            email=email,
            telefono=telefono,
            hash_password=hashed_password
        )
        
        self.db.add(new_user)
        self.db.flush()
        
        return new_user
    
    def asignar_rol_paciente(self, usuario: Usuario):
        paciente_role = self.db.query(Rol).filter(
            Rol.nombre == RolConstantes.PACIENTE
        ).first()
        
        if not paciente_role:
            logger.error("Rol PACIENTE no encontrado en la base de datos")
            raise ValueError("Rol PACIENTE no configurado en el sistema")
        
        user_role = UsuarioRol(
            id_usuario=usuario.id_usuario,
            id_rol=paciente_role.id_rol
        )
        self.db.add(user_role)
        
        paciente = Paciente(id_usuario=usuario.id_usuario)
        self.db.add(paciente)
        
        logger.info(f"Rol PACIENTE asignado al usuario {usuario.id_usuario}")
    
    def asignar_rol_medico(self, usuario: Usuario):
        medico_role = self.db.query(Rol).filter(
            Rol.nombre == RolConstantes.MEDICO
        ).first()
        
        if not medico_role:
            raise ValueError("Rol MEDICO no configurado en el sistema")
        
        user_role = UsuarioRol(
            id_usuario=usuario.id_usuario,
            id_rol=medico_role.id_rol
        )
        self.db.add(user_role)
        
        cargo = self.db.query(Cargo).filter(Cargo.nombre == "Médico General").first()
        
        if not cargo:
            logger.warning("Cargo 'Médico General' no encontrado, creando uno por defecto")
            cargo = Cargo(nombre="Médico General", descripcion="Médico general")
            self.db.add(cargo)
            self.db.flush()
        
        funcionario = Funcionario(
            id_usuario=usuario.id_usuario,
            id_cargo=cargo.id_cargo,
            fecha_contrato=date.today(),
            estado='ACTIVO'
        )
        self.db.add(funcionario)
        self.db.flush()
        
        profesional = ProfesionalSalud(
            id_funcionario=funcionario.id_funcionario,
            registro_profesional=f"REG-{usuario.id_usuario}-{date.today().year}",
            fecha_titulo=date.today(),
            estado_registro='VIGENTE'
        )
        self.db.add(profesional)
        
        logger.info(f"Rol MEDICO asignado al usuario {usuario.id_usuario}")
    
    def asignar_rol_recepcionista(self, usuario: Usuario):
        recep_role = self.db.query(Rol).filter(
            Rol.nombre == RolConstantes.RECEPCIONISTA
        ).first()
        
        if not recep_role:
            raise ValueError("Rol RECEPCIONISTA no configurado en el sistema")
        
        user_role = UsuarioRol(
            id_usuario=usuario.id_usuario,
            id_rol=recep_role.id_rol
        )
        self.db.add(user_role)
        
        cargo = self.db.query(Cargo).filter(Cargo.nombre == "Recepcionista").first()
        
        if not cargo:
            cargo = Cargo(nombre="Recepcionista", descripcion="Recepcionista")
            self.db.add(cargo)
            self.db.flush()
        
        funcionario = Funcionario(
            id_usuario=usuario.id_usuario,
            id_cargo=cargo.id_cargo,
            fecha_contrato=date.today(),
            estado='ACTIVO'
        )
        self.db.add(funcionario)
        
        logger.info(f"Rol RECEPCIONISTA asignado al usuario {usuario.id_usuario}")
    
    def asignar_rol_administrador(self, usuario: Usuario):
        admin_role = self.db.query(Rol).filter(
            Rol.nombre == RolConstantes.ADMINISTRADOR
        ).first()
        
        if not admin_role:
            raise ValueError("Rol ADMINISTRADOR no configurado en el sistema")
        
        user_role = UsuarioRol(
            id_usuario=usuario.id_usuario,
            id_rol=admin_role.id_rol
        )
        self.db.add(user_role)
        
        logger.info(f"Rol ADMINISTRADOR asignado al usuario {usuario.id_usuario}")
    
    def asignar_roles(self, usuario: Usuario, roles_ids: List[int]):
        if not roles_ids:
            self.asignar_rol_paciente(usuario)
            return
        
        for role_id in roles_ids:
            role = self.db.query(Rol).filter(Rol.id_rol == role_id).first()
            
            if not role:
                logger.warning(f"Rol con ID {role_id} no encontrado, saltando")
                continue
            
            if role.nombre == RolConstantes.PACIENTE:
                self.asignar_rol_paciente(usuario)
            elif role.nombre == RolConstantes.MEDICO:
                self.asignar_rol_medico(usuario)
            elif role.nombre == RolConstantes.RECEPCIONISTA:
                self.asignar_rol_recepcionista(usuario)
            elif role.nombre == RolConstantes.ADMINISTRADOR:
                self.asignar_rol_administrador(usuario)
            else:
                user_role = UsuarioRol(
                    id_usuario=usuario.id_usuario,
                    id_rol=role_id
                )
                self.db.add(user_role)
    
    def crear_usuario_completo(
        self,
        rut: str,
        nombre: str,
        apellido_paterno: str,
        apellido_materno: str,
        email: str,
        telefono: str,
        password: str,
        roles_ids: Optional[List[int]] = None
    ) -> Usuario:
        try:
            self.verificar_usuario_existente(rut, email)
            
            usuario = self.crear_usuario_base(
                rut=rut,
                nombre=nombre,
                apellido_paterno=apellido_paterno,
                apellido_materno=apellido_materno,
                email=email,
                telefono=telefono,
                password=password
            )
            
            self.asignar_roles(usuario, roles_ids)
            
            self.db.commit()
            self.db.refresh(usuario)
            
            logger.info(f"Usuario {usuario.id_usuario} creado exitosamente con {len(roles_ids or [])} roles")
            
            return usuario
            
        except (ValueError, IntegrityError) as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al crear usuario: {str(e)}")
            raise
    
    def actualizar_roles_usuario(self, usuario_id: int, nuevos_roles_ids: List[int]):
        usuario = self.db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
        
        if not usuario:
            raise ValueError("Usuario no encontrado")
        
        try:
            self.db.query(UsuarioRol).filter(UsuarioRol.id_usuario == usuario_id).delete()
            
            for role_id in nuevos_roles_ids:
                role = self.db.query(Rol).filter(Rol.id_rol == role_id).first()
                if role:
                    user_role = UsuarioRol(id_usuario=usuario_id, id_rol=role_id)
                    self.db.add(user_role)
            
            self.db.commit()
            logger.info(f"Roles actualizados para usuario {usuario_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al actualizar roles: {str(e)}")
            raise
    
    def eliminar_usuario(self, usuario_id: int, usuario_actual_id: int):
        if usuario_id == usuario_actual_id:
            raise ValueError("No puedes eliminar tu propia cuenta")
        
        usuario = self.db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
        
        if not usuario:
            raise ValueError("Usuario no encontrado")
        
        try:
            self.db.query(UsuarioRol).filter(UsuarioRol.id_usuario == usuario_id).delete()
            
            self.db.delete(usuario)
            self.db.commit()
            
            logger.info(f"Usuario {usuario_id} eliminado exitosamente")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al eliminar usuario: {str(e)}")
            raise
