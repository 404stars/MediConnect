
USE mediconnect;

-----------------------
-- ROLES DEL SISTEMA --
-----------------------

INSERT IGNORE INTO rol (nombre, descripcion, permisos) VALUES 
('Administrador', 'Acceso completo al sistema, gestión de usuarios y configuración', 'view_own_profile,manage_users,manage_roles,view_all_data,edit_all,delete_all'),
('Médico', 'Profesional de salud con acceso a gestión de pacientes y citas', 'view_own_profile,manage_appointments,view_patients,view_medical_records,edit_patients'),
('Recepcionista', 'Personal de recepción con acceso a gestión de citas y información básica', 'view_own_profile,manage_appointments,view_patients,schedule_appointments'),
('Paciente', 'Usuario paciente con acceso limitado a su información personal', 'view_own_profile,book_appointment,view_own_appointments');

-----------------
-- UBICACIONES --
-----------------

-- Regiones
INSERT INTO region (nombre) VALUES
('Arica y Parinacota'),
('Tarapacá'),
('Antofagasta'),
('Atacama'),
('Coquimbo'),
('Valparaíso'),
('Metropolitana de Santiago'),
('Libertador General Bernardo O''Higgins'),
('Maule'),
('Ñuble'),
('Biobío'),
('La Araucanía'),
('Los Ríos'),
('Los Lagos'),
('Aysén del General Carlos Ibáñez del Campo'),
('Magallanes y de la Antártica Chilena');

-- Comunas 
INSERT INTO comuna (nombre, id_region) VALUES
-- Región Metropolitana
('Santiago', 7),
('Las Condes', 7),
('Providencia', 7),
('Ñuñoa', 7),
('La Florida', 7),
('Maipú', 7),
('Puente Alto', 7),
('San Miguel', 7),
('Quinta Normal', 7),
('Independencia', 7),
-- Valparaíso
('Valparaíso', 6),
('Viña del Mar', 6),
('Quilpué', 6),
('Villa Alemana', 6),
-- Biobío
('Concepción', 11),
('Talcahuano', 11),
('Chillán', 11),
('Los Ángeles', 11),
-- Antofagasta
('Antofagasta', 3),
('Calama', 3);

----------------------------
-- ESPECIALIDADES MÉDICAS --
----------------------------

INSERT INTO especialidad (nombre, descripcion) VALUES
('Medicina General', 'Atención médica general y preventiva'),
('Medicina Familiar', 'Atención integral de la familia en todas las etapas'),
('Pediatría', 'Atención médica especializada en niños y adolescentes'),
('Ginecología y Obstetricia', 'Atención médica especializada en salud femenina y embarazo'),
('Cardiología', 'Atención médica especializada del corazón y sistema cardiovascular'),
('Neurología', 'Atención médica especializada del sistema nervioso'),
('Dermatología', 'Atención médica especializada de la piel'),
('Traumatología', 'Atención médica especializada en lesiones musculoesqueléticas'),
('Psiquiatría', 'Atención médica especializada en salud mental'),
('Oftalmología', 'Atención médica especializada de los ojos'),
('Otorrinolaringología', 'Atención médica especializada de oídos, nariz y garganta'),
('Urología', 'Atención médica especializada del sistema urinario'),
('Gastroenterología', 'Atención médica especializada del sistema digestivo'),
('Endocrinología', 'Atención médica especializada del sistema endocrino'),
('Reumatología', 'Atención médica especializada en enfermedades reumáticas');

------------------------
-- CARGOS DEL SISTEMA --
------------------------

INSERT INTO cargo (nombre, descripcion) VALUES
('Director Médico', 'Máxima autoridad médica del establecimiento'),
('Jefe de Servicio', 'Responsable de un servicio médico específico'),
('Médico Especialista', 'Profesional médico con especialización'),
('Médico General', 'Profesional médico de atención general'),
('Enfermera Jefe', 'Responsable del equipo de enfermería'),
('Enfermera', 'Profesional de enfermería'),
('Matrona', 'Profesional especializada en salud femenina y obstétrica'),
('Kinesiólogo', 'Profesional en kinesiología y rehabilitación'),
('Psicólogo', 'Profesional en salud mental'),
('Recepcionista Médica', 'Personal de recepción especializado en atención médica'),
('Secretaria Médica', 'Personal administrativo de apoyo médico'),
('Auxiliar de Enfermería', 'Personal de apoyo en enfermería'),
('Administrativo', 'Personal de administración general');

----------------------------
-- MOTIVOS DE CANCELACIÓN --
----------------------------

INSERT INTO motivo_cancelacion (descripcion) VALUES
('Cancelación por el paciente'),
('Cancelación por el médico'),
('Emergencia médica'),
('Enfermedad del médico'),
('Falta de disponibilidad del paciente'),
('Problemas técnicos'),
('Fuerza mayor'),
('Reagendamiento solicitado'),
('Otros motivos médicos');

-------------
-- RESUMEN --
-------------

SELECT 'DATOS INICIALES INSERTADOS CORRECTAMENTE' AS mensaje;
SELECT 'RESUMEN DE DATOS INSERTADOS:' AS resumen;
SELECT COUNT(*) AS total_roles FROM rol;
SELECT COUNT(*) AS total_regiones FROM region;
SELECT COUNT(*) AS total_comunas FROM comuna;
SELECT COUNT(*) AS total_especialidades FROM especialidad;
SELECT COUNT(*) AS total_cargos FROM cargo;
SELECT COUNT(*) AS total_motivos_cancelacion FROM motivo_cancelacion;

SELECT '*** SISTEMA LISTO ***' AS estado;
