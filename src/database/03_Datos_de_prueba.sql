USE mediconnect;

DELETE FROM cita;
DELETE FROM bloque_hora;
DELETE FROM agenda_diaria;
DELETE FROM paciente;
DELETE FROM profesional_especialidad;
DELETE FROM profesional_salud;
DELETE FROM funcionario;
DELETE FROM usuario_rol;
DELETE FROM usuario;


------------------------
-- USUARIOS DE PRUEBA --
------------------------

-- Se insertan los usuarios base (IDs 1 al 4)
INSERT INTO usuario (rut, nombre, apellido_paterno, apellido_materno, email, telefono, hash_password) VALUES
('9.876.543-2', 'admin', 'Sistema', 'MediConnect', 'admin@mediconnect.com', '+56912345678', '$2a$12$X5mzDFBA6qoyX7OeYhznPuj0vSNerKYYNJEx5HkgPm93QQVFOsOeG'), -- password: admin123
('11.123.456-7', 'Juan Carlos', 'Bodoque', 'Bodoque', 'j.bodoque@mediconnect.com', '+56987654321', '$2a$12$pBjS5arwbOb3ocW7wgn7Nu2KrOwUcAgddM5qPgYVflIwcxi3aaEA6'), -- password: doctor123
('15.678.910-1', 'Tulio', 'Triviño', 'Triviño', 't.trivino@mediconnect.com', '+56911222333', '$2a$12$MjFoZCKYHqtGtxHywVCxb.sEgRPf5g.5EAFeJRFwSwMHyRNo.qvHq'), -- password: recep123
('18.212.313-0', 'Patana', 'Pat', 'Ana', 'patana@gmail.com', '+56922333444', '$2a$12$nsOJvpus2jngCaGgma83neTpo/CzDgj6uVtN4rlgk5naJLp18rbfa'); -- password: test123

-------------------------
-- ASIGNACIÓN DE ROLES --
-------------------------

INSERT INTO usuario_rol (id_usuario, id_rol) VALUES
(1, 1), -- admin -> Administrador
(2, 2), -- Juan Carlos -> Médico
(3, 3), -- Tulio -> Recepcionista
(4, 4); -- Patana -> Paciente

----------------------------
-- FUNCIONARIOS DE PRUEBA --
----------------------------

-- El usuario con ID 1 (admin) es un funcionario
INSERT INTO funcionario (id_usuario, id_cargo, id_comuna, direccion, fecha_contrato) VALUES
(1, 1, 1, 'Av. Siempre Viva 123, Santiago', '2025-01-01');

-- El usuario con ID 2 (médico) es un funcionario
INSERT INTO funcionario (id_usuario, id_cargo, id_comuna, direccion, fecha_contrato) VALUES
(2, 4, 1, 'Av. Siempre No Viva 123, Santiago', '2025-01-02');

-- El usuario con ID 3 (recepcionista) es un funcionario
INSERT INTO funcionario (id_usuario, id_cargo, id_comuna, direccion, fecha_contrato) VALUES
(3, 10, 1, 'Av. Siempre IVA, Santiago', '2025-01-03');

--------------------------
-- PROFESIONAL DE SALUD --
--------------------------

-- El funcionario con ID 2 (Dr. Bodoque)
INSERT INTO profesional_salud (id_funcionario, registro_profesional, fecha_titulo) VALUES
(2, 'MED-12345-2020', '2020-03-15');

-- Asignar especialidades al profesional con ID 1 (Dr. Bodoque)
INSERT INTO profesional_especialidad (id_profesional, id_especialidad, fecha_certificacion) VALUES
(1, 1, '2020-03-15'),  -- Medicina General
(1, 5, '2022-06-20'); --  Se asigna la especialidad Cardiología (ID 5)

------------------------
-- PACIENTE DE PRUEBA --
------------------------

-- El usuario con ID 4 (Patana) es un paciente.
INSERT INTO paciente (id_usuario, fecha_nacimiento, sexo, id_comuna, direccion, contacto_emergencia, telefono_emergencia, alergias) VALUES
(4, '1990-05-15', 'M', 1, 'San Miguel 1357, Santiago', 'Ana Banana (Madre)', '+56933444555', 'Penicilina, Trabajar');

------------------------------
-- AGENDA Y CITAS DE PRUEBA --
------------------------------

-- Crear agenda para el profesional con ID 1 (Dr. Bodoque) para dos días específicos
INSERT INTO agenda_diaria (id_profesional, fecha, hora_inicio, hora_fin, duracion_cita) VALUES
(1, '2025-11-19', '09:00:00', '17:00:00', 30),
(1, '2025-11-20', '09:00:00', '17:00:00', 30);

-- Crear bloques de hora para las agendas creadas (IDs 1 y 2)
INSERT INTO bloque_hora (id_agenda, hora_inicio, hora_fin) VALUES
-- Agenda del 19/11 (ID 1)
(1, '09:00:00', '09:30:00'), (1, '09:30:00', '10:00:00'),
(1, '10:00:00', '10:30:00'), (1, '10:30:00', '11:00:00'),
(1, '11:00:00', '11:30:00'), (1, '11:30:00', '12:00:00'),
(1, '12:00:00', '12:30:00'), (1, '12:30:00', '13:00:00'),
(1, '14:00:00', '14:30:00'), (1, '14:30:00', '15:00:00'),
(1, '15:00:00', '15:30:00'), (1, '15:30:00', '16:00:00'),
(1, '16:00:00', '16:30:00'), (1, '16:30:00', '17:00:00'),
-- Agenda del 20/11 (ID 2)
(2, '09:00:00', '09:30:00'), (2, '09:30:00', '10:00:00'),
(2, '10:00:00', '10:30:00'), (2, '10:30:00', '11:00:00'),
(2, '11:00:00', '11:30:00'), (2, '11:30:00', '12:00:00'),
(2, '12:00:00', '12:30:00'), (2, '12:30:00', '13:00:00'),
(2, '14:00:00', '14:30:00'), (2, '14:30:00', '15:00:00'),
(2, '15:00:00', '15:30:00'), (2, '15:30:00', '16:00:00'),
(2, '16:00:00', '16:30:00'), (2, '16:30:00', '17:00:00');

-- Crear una cita de prueba
-- Se agenda al paciente con ID 1 (Patana) en el bloque de hora con ID 3 (10:00 a 10:30 del 19/11)
INSERT INTO cita (id_paciente, id_bloque, motivo_consulta) VALUES
(1, 3, 'Consulta de control general');

-- El bloque de hora ahora debe estar no disponible.
UPDATE bloque_hora SET disponible = 0 WHERE id_bloque = 3;

SELECT 'DATOS DE PRUEBA INSERTADOS CORRECTAMENTE' AS mensaje;
