USE mediconnect;

START TRANSACTION;


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
INSERT INTO usuario (rut, nombre, apellido_paterno, apellido_materno, email, telefono, hash_password) VALUES
('9.876.543-2', 'admin', 'Sistema', 'MediConnect', 'admin@mediconnect.com', '+56912345678', '$2a$12$X5mzDFBA6qoyX7OeYhznPuj0vSNerKYYNJEx5HkgPm93QQVFOsOeG'), -- admin123
('11.123.456-7', 'Dr. Juan Carlos', 'Bodoque', 'Bodoque', 'j.bodoque@mediconnect.com', '+56987654321', '$2a$12$pBjS5arwbOb3ocW7wgn7Nu2KrOwUcAgddM5qPgYVflIwcxi3aaEA6'), -- doctor123
('15.678.910-1', 'Tulio', 'Triviño', 'Triviño', 't.trivino@mediconnect.com', '+56911222333', '$2a$12$MjFoZCKYHqtGtxHywVCxb.sEgRPf5g.5EAFeJRFwSwMHyRNo.qvHq'), -- recep123
('18.212.313-0', 'Patana', 'Pat', 'Ana', 'patana@gmail.com', '+56922333444', '$2a$12$nsOJvpus2jngCaGgma83neTpo/CzDgj6uVtN4rlgk5naJLp18rbfa'); -- test123

-------------------------
-- ASIGNACIÓN DE ROLES --
-------------------------
-- admin -> Administrador
INSERT INTO usuario_rol (id_usuario, id_rol)
SELECT u.id_usuario, r.id_rol
FROM usuario u
JOIN rol r ON r.nombre='Administrador'
LEFT JOIN usuario_rol ur ON ur.id_usuario=u.id_usuario AND ur.id_rol=r.id_rol
WHERE u.email='admin@mediconnect.com' AND ur.id_usuario IS NULL;

-- Dr. Bodoque -> Médico
INSERT INTO usuario_rol (id_usuario, id_rol)
SELECT u.id_usuario, r.id_rol
FROM usuario u
JOIN rol r ON r.nombre='Médico'
LEFT JOIN usuario_rol ur ON ur.id_usuario=u.id_usuario AND ur.id_rol=r.id_rol
WHERE u.email='j.bodoque@mediconnect.com' AND ur.id_usuario IS NULL;

-- Tulio -> Recepcionista
INSERT INTO usuario_rol (id_usuario, id_rol)
SELECT u.id_usuario, r.id_rol
FROM usuario u
JOIN rol r ON r.nombre='Recepcionista'
LEFT JOIN usuario_rol ur ON ur.id_usuario=u.id_usuario AND ur.id_rol=r.id_rol
WHERE u.email='t.trivino@mediconnect.com' AND ur.id_usuario IS NULL;

-- Patana -> Paciente
INSERT INTO usuario_rol (id_usuario, id_rol)
SELECT u.id_usuario, r.id_rol
FROM usuario u
JOIN rol r ON r.nombre='Paciente'
LEFT JOIN usuario_rol ur ON ur.id_usuario=u.id_usuario AND ur.id_rol=r.id_rol
WHERE u.email='patana@gmail.com' AND ur.id_usuario IS NULL;

----------------------------
-- FUNCIONARIOS DE PRUEBA --
----------------------------
-- admin (cargo 1: asume 'Administrador' si lo tienes; si no, ajusta)
INSERT INTO funcionario (id_usuario, id_cargo, id_comuna, direccion, fecha_contrato)
SELECT u.id_usuario, 1, co.id_comuna, 'Av. Siempre Viva 123, Santiago', '2025-01-01'
FROM usuario u
JOIN comuna co ON co.nombre='Santiago'
LEFT JOIN funcionario f ON f.id_usuario=u.id_usuario
WHERE u.email='admin@mediconnect.com' AND f.id_funcionario IS NULL;

-- Dr. Bodoque (cargo: Médico Especialista)
INSERT INTO funcionario (id_usuario, id_cargo, id_comuna, direccion, fecha_contrato)
SELECT u.id_usuario, c.id_cargo, co.id_comuna, 'Av. Siempre No Viva 123, Santiago', '2025-01-02'
FROM usuario u
JOIN cargo c ON c.nombre='Médico Especialista'
JOIN comuna co ON co.nombre='Santiago'
LEFT JOIN funcionario f ON f.id_usuario=u.id_usuario
WHERE u.email='j.bodoque@mediconnect.com' AND f.id_funcionario IS NULL;

-- Tulio (cargo 10: ajusta al nombre real si aplica)
INSERT INTO funcionario (id_usuario, id_cargo, id_comuna, direccion, fecha_contrato)
SELECT u.id_usuario, 10, co.id_comuna, 'Av. Siempre IVA, Santiago', '2025-01-03'
FROM usuario u
JOIN comuna co ON co.nombre='Santiago'
LEFT JOIN funcionario f ON f.id_usuario=u.id_usuario
WHERE u.email='t.trivino@mediconnect.com' AND f.id_funcionario IS NULL;

--------------------------
-- PROFESIONAL DE SALUD --
--------------------------
-- Profesional para Dr. Bodoque
INSERT INTO profesional_salud (id_funcionario, registro_profesional, fecha_titulo)
SELECT f.id_funcionario, 'MED-12345-2020', '2020-03-15'
FROM funcionario f
JOIN usuario u ON u.id_usuario=f.id_usuario
LEFT JOIN profesional_salud ps ON ps.id_funcionario=f.id_funcionario
WHERE u.email='j.bodoque@mediconnect.com' AND ps.id_profesional IS NULL;

-- Especialidades (usa nombres en vez de IDs fijos; ajusta si tus nombres difieren)
INSERT INTO profesional_especialidad (id_profesional, id_especialidad, fecha_certificacion)
SELECT ps.id_profesional, e.id_especialidad, '2020-03-15'
FROM profesional_salud ps
JOIN funcionario f ON f.id_funcionario=ps.id_funcionario
JOIN usuario u ON u.id_usuario=f.id_usuario
JOIN especialidad e ON e.nombre='Medicina General'
LEFT JOIN profesional_especialidad pe ON pe.id_profesional=ps.id_profesional AND pe.id_especialidad=e.id_especialidad
WHERE u.email='j.bodoque@mediconnect.com' AND pe.id_profesional IS NULL;

INSERT INTO profesional_especialidad (id_profesional, id_especialidad, fecha_certificacion)
SELECT ps.id_profesional, e.id_especialidad, '2022-06-20'
FROM profesional_salud ps
JOIN funcionario f ON f.id_funcionario=ps.id_funcionario
JOIN usuario u ON u.id_usuario=f.id_usuario
JOIN especialidad e ON e.nombre='Cardiología'
LEFT JOIN profesional_especialidad pe ON pe.id_profesional=ps.id_profesional AND pe.id_especialidad=e.id_especialidad
WHERE u.email='j.bodoque@mediconnect.com' AND pe.id_profesional IS NULL;

------------------------
-- PACIENTE DE PRUEBA --
------------------------
INSERT INTO paciente (id_usuario, fecha_nacimiento, sexo, id_comuna, direccion, contacto_emergencia, telefono_emergencia, alergias)
SELECT u.id_usuario, '1990-05-15', 'M', co.id_comuna, 'San Miguel 1357, Santiago',
       'Ana Banana (Madre)', '+56933444555', 'Penicilina, Trabajar'
FROM usuario u
JOIN comuna co ON co.nombre='Santiago'
LEFT JOIN paciente p ON p.id_usuario=u.id_usuario
WHERE u.email='patana@gmail.com' AND p.id_paciente IS NULL;

----------------------------------------------------------------
-- **NUEVO**: 2 PROFESIONALES EXTRA POR CADA ESPECIALIDAD EN BD
-- (sin agendas ni bloques; re-ejecutable, evita duplicados)
----------------------------------------------------------------

-- 0) 2 filas por especialidad (idx=1,2)
DROP TEMPORARY TABLE IF EXISTS tmp_espec2;
CREATE TEMPORARY TABLE tmp_espec2 AS
SELECT 
    e.id_especialidad,
    e.nombre AS nombre_especialidad,
    n.idx,
    REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(LOWER(e.nombre),' ',''),
            'á','a'),'é','e'),'í','i'),'ó','o'),'ú','u'),'ñ','n') AS slug
FROM especialidad e
CROSS JOIN (SELECT 1 AS idx UNION ALL SELECT 2) n;

-- 1) Datos inventados
DROP TEMPORARY TABLE IF EXISTS tmp_prof_gen;
CREATE TEMPORARY TABLE tmp_prof_gen AS
SELECT
    t.id_especialidad,
    t.nombre_especialidad,
    t.slug,
    t.idx,
    CONCAT('30', LPAD(t.id_especialidad, 6, '0'), t.idx, '-K') AS rut,
    CASE ((t.id_especialidad + t.idx) % 10)
        WHEN 0 THEN 'Dr. Matías'
        WHEN 1 THEN 'Dra. Camila'
        WHEN 2 THEN 'Dr. Felipe'
        WHEN 3 THEN 'Dra. Valentina'
        WHEN 4 THEN 'Dr. Rodrigo'
        WHEN 5 THEN 'Dra. Daniela'
        WHEN 6 THEN 'Dr. Álvaro'
        WHEN 7 THEN 'Dra. Sofía'
        WHEN 8 THEN 'Dr. Pedro'
        ELSE        'Dra. Marcela'
    END AS nombre,
    CASE ((t.id_especialidad + 2*t.idx) % 10)
        WHEN 0 THEN 'Rojas'     WHEN 1 THEN 'González'
        WHEN 2 THEN 'Muñoz'     WHEN 3 THEN 'Pérez'
        WHEN 4 THEN 'Soto'      WHEN 5 THEN 'Silva'
        WHEN 6 THEN 'Contreras' WHEN 7 THEN 'Reyes'
        WHEN 8 THEN 'Morales'   ELSE 'Vega'
    END AS apellido_paterno,
    CASE ((t.id_especialidad + 3*t.idx) % 10)
        WHEN 0 THEN 'Castillo'  WHEN 1 THEN 'Vargas'
        WHEN 2 THEN 'Torres'    WHEN 3 THEN 'Navarro'
        WHEN 4 THEN 'Fuentes'   WHEN 5 THEN 'Lagos'
        WHEN 6 THEN 'Ortega'    WHEN 7 THEN 'Pizarro'
        WHEN 8 THEN 'Arancibia' ELSE 'Gutiérrez'
    END AS apellido_materno,
    CONCAT('dr.', t.slug, t.idx, '@mediconnect.com') AS email,
    CONCAT('+56942', LPAD(t.id_especialidad, 5, '0'), t.idx) AS telefono,
    '$2a$12$pBjS5arwbOb3ocW7wgn7Nu2KrOwUcAgddM5qPgYVflIwcxi3aaEA6' AS hash_password,  -- doctor123
    CONCAT('MED-', LPAD(t.id_especialidad, 5, '0'), '-', 2015 + t.idx) AS registro_profesional,
    DATE(CONCAT(2014 + t.idx, '-12-15')) AS fecha_titulo,
    DATE('2020-06-01') AS fecha_certificacion
FROM tmp_espec2 t;

-- 2) Usuario
INSERT INTO usuario (rut, nombre, apellido_paterno, apellido_materno, email, telefono, hash_password)
SELECT g.rut, g.nombre, g.apellido_paterno, g.apellido_materno, g.email, g.telefono, g.hash_password
FROM tmp_prof_gen g
LEFT JOIN usuario u ON u.email = g.email
WHERE u.id_usuario IS NULL;

-- 3) Rol Médico
INSERT INTO usuario_rol (id_usuario, id_rol)
SELECT u.id_usuario, r.id_rol
FROM usuario u
JOIN tmp_prof_gen g ON g.email = u.email
JOIN rol r ON r.nombre='Médico'
LEFT JOIN usuario_rol ur ON ur.id_usuario=u.id_usuario AND ur.id_rol=r.id_rol
WHERE ur.id_usuario IS NULL;

-- 4) Funcionario (Médico Especialista, Santiago)
INSERT INTO funcionario (id_usuario, id_cargo, id_comuna, direccion, fecha_contrato)
SELECT u.id_usuario, c.id_cargo, co.id_comuna,
       CONCAT('Clínica ', g.nombre_especialidad, ' ', g.apellido_paterno, ' 123, Santiago'),
       DATE('2025-01-15')
FROM usuario u
JOIN tmp_prof_gen g ON g.email = u.email
JOIN cargo c   ON c.nombre='Médico Especialista'
JOIN comuna co ON co.nombre='Santiago'
LEFT JOIN funcionario f ON f.id_usuario=u.id_usuario
WHERE f.id_funcionario IS NULL;

-- 5) Profesional de salud
INSERT INTO profesional_salud (id_funcionario, registro_profesional, fecha_titulo)
SELECT f.id_funcionario, g.registro_profesional, g.fecha_titulo
FROM funcionario f
JOIN usuario u      ON u.id_usuario=f.id_usuario
JOIN tmp_prof_gen g ON g.email=u.email
LEFT JOIN profesional_salud ps ON ps.id_funcionario=f.id_funcionario
WHERE ps.id_profesional IS NULL;

-- 6) Enlace a especialidad
INSERT INTO profesional_especialidad (id_profesional, id_especialidad, fecha_certificacion)
SELECT ps.id_profesional, g.id_especialidad, g.fecha_certificacion
FROM profesional_salud ps
JOIN funcionario f   ON f.id_funcionario=ps.id_funcionario
JOIN usuario u       ON u.id_usuario=f.id_usuario
JOIN tmp_prof_gen g  ON g.email=u.email
LEFT JOIN profesional_especialidad pe
  ON pe.id_profesional=ps.id_profesional AND pe.id_especialidad=g.id_especialidad
WHERE pe.id_profesional IS NULL;

COMMIT;

-- Resumen (creados ahora)
SELECT 
  g.id_especialidad,
  g.nombre_especialidad,
  COUNT(*) AS profesionales_creados_ahora
FROM tmp_prof_gen g
JOIN usuario u ON u.email = g.email
JOIN funcionario f ON f.id_usuario = u.id_usuario
JOIN profesional_salud ps ON ps.id_funcionario = f.id_funcionario
GROUP BY g.id_especialidad, g.nombre_especialidad
ORDER BY g.id_especialidad;

SELECT 'DATOS DE PRUEBA INSERTADOS CORRECTAMENTE' AS mensaje;
