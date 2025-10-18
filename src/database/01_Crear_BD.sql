CREATE DATABASE IF NOT EXISTS mediconnect;
USE mediconnect;


----------------------------------
-- Tablas de Usuario y de Roles --
----------------------------------

-- Tabla de roles
CREATE TABLE IF NOT EXISTS rol (
  id_rol        INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  nombre        VARCHAR(40) NOT NULL UNIQUE,
  descripcion   VARCHAR(200) NULL,
  permisos      TEXT NULL
);

-- Tabla general de usuarios
CREATE TABLE IF NOT EXISTS usuario (
  id_usuario        BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  rut               VARCHAR(12)  NOT NULL UNIQUE,
  nombre            VARCHAR(60)  NOT NULL,
  apellido_paterno  VARCHAR(60)  NOT NULL,
  apellido_materno  VARCHAR(60)  NULL,
  email             VARCHAR(120) NOT NULL UNIQUE,
  telefono          VARCHAR(20)  NULL,
  hash_password     VARCHAR(255) NOT NULL,
  estado            ENUM('ACTIVO','BLOQUEADO') NOT NULL DEFAULT 'ACTIVO',
  token_recuperacion VARCHAR(255) NULL,
  expiracion_token  DATETIME NULL,
  creado_en         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabla intermedia entre usuarios y roles
CREATE TABLE IF NOT EXISTS usuario_rol (
  id_usuario BIGINT UNSIGNED NOT NULL,
  id_rol     INT UNSIGNED NOT NULL,
  PRIMARY KEY (id_usuario, id_rol),
  CONSTRAINT fk_ur_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
  CONSTRAINT fk_ur_rol     FOREIGN KEY (id_rol)     REFERENCES rol(id_rol) ON DELETE CASCADE
);


----------------------------
-- Tablas complementarias --
----------------------------

CREATE TABLE IF NOT EXISTS region (
    id_region INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS comuna (
    id_comuna INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    id_region INT UNSIGNED NOT NULL,
    CONSTRAINT fk_comuna_region FOREIGN KEY (id_region) REFERENCES region(id_region),
    UNIQUE KEY uk_comuna_region (nombre, id_region)
);

CREATE TABLE IF NOT EXISTS cargo (
    id_cargo INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(80) NOT NULL UNIQUE,
    descripcion VARCHAR(200) NULL
);

CREATE TABLE IF NOT EXISTS especialidad (
    id_especialidad INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(80) NOT NULL UNIQUE,
    descripcion VARCHAR(200) NULL
);


-----------------------
-- Tablas de Negocio --
-----------------------

-- Tabla de funcionarios
CREATE TABLE IF NOT EXISTS funcionario (
  id_funcionario    BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  id_usuario        BIGINT UNSIGNED NOT NULL UNIQUE,
  id_cargo          INT UNSIGNED NULL,
  id_comuna         INT UNSIGNED NULL,
  direccion         VARCHAR(255) NULL,
  fecha_contrato    DATE NULL,
  estado            ENUM('ACTIVO','INACTIVO','SUSPENDIDO') NOT NULL DEFAULT 'ACTIVO',
  CONSTRAINT fk_func_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
  CONSTRAINT fk_func_cargo   FOREIGN KEY (id_cargo)   REFERENCES cargo(id_cargo),
  CONSTRAINT fk_func_comuna  FOREIGN KEY (id_comuna)  REFERENCES comuna(id_comuna)
);

-- Tabla de profesionales de salud
CREATE TABLE IF NOT EXISTS profesional_salud (
  id_profesional  BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  id_funcionario  BIGINT UNSIGNED NOT NULL UNIQUE,
  registro_profesional VARCHAR(50) NOT NULL UNIQUE,
  fecha_titulo    DATE NULL,
  estado_registro ENUM('VIGENTE','SUSPENDIDO','CADUCADO') NOT NULL DEFAULT 'VIGENTE',
  CONSTRAINT fk_prof_funcionario FOREIGN KEY (id_funcionario) REFERENCES funcionario(id_funcionario) ON DELETE CASCADE
);

-- Tabla intermedia profesionales y especialidades
CREATE TABLE IF NOT EXISTS profesional_especialidad (
  id_profesional  BIGINT UNSIGNED NOT NULL,
  id_especialidad INT UNSIGNED NOT NULL,
  fecha_certificacion DATE NULL,
  PRIMARY KEY (id_profesional, id_especialidad),
  CONSTRAINT fk_pe_profesional   FOREIGN KEY (id_profesional)  REFERENCES profesional_salud(id_profesional) ON DELETE CASCADE,
  CONSTRAINT fk_pe_especialidad  FOREIGN KEY (id_especialidad) REFERENCES especialidad(id_especialidad) ON DELETE CASCADE
);

-- Tabla de pacientes
CREATE TABLE IF NOT EXISTS paciente (
  id_paciente       BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  id_usuario        BIGINT UNSIGNED NOT NULL UNIQUE,
  fecha_nacimiento  DATE NULL,
  sexo              ENUM('M','F','I') NULL,
  id_comuna         INT UNSIGNED NULL,
  direccion         VARCHAR(255) NULL,
  contacto_emergencia VARCHAR(100) NULL,
  telefono_emergencia VARCHAR(20) NULL,
  alergias          TEXT NULL,
  condiciones_medicas TEXT NULL,
  CONSTRAINT fk_pac_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
  CONSTRAINT fk_pac_comuna  FOREIGN KEY (id_comuna)  REFERENCES comuna(id_comuna)
);

-- Tabla de sesiones de usuario
CREATE TABLE IF NOT EXISTS sesion (
  id_sesion     VARCHAR(100) PRIMARY KEY,
  id_usuario    BIGINT UNSIGNED NOT NULL,
  token_jwt     TEXT NOT NULL,
  fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  fecha_expiracion DATETIME NOT NULL,
  activa        BOOLEAN NOT NULL DEFAULT TRUE,
  ip_address    VARCHAR(45) NULL,
  user_agent    TEXT NULL,
  CONSTRAINT fk_sesion_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
  INDEX idx_sesion_usuario (id_usuario),
  INDEX idx_sesion_activa (activa),
  INDEX idx_sesion_expiracion (fecha_expiracion)
);

-- Tabla de auditoría
CREATE TABLE IF NOT EXISTS audit_log (
  id_log        BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  id_usuario    BIGINT UNSIGNED NULL,
  tabla_afectada VARCHAR(50) NOT NULL,
  operacion     ENUM('INSERT','UPDATE','DELETE') NOT NULL,
  datos_anteriores JSON NULL,
  datos_nuevos  JSON NULL,
  fecha_operacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ip_address    VARCHAR(45) NULL,
  CONSTRAINT fk_audit_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE SET NULL,
  INDEX idx_audit_usuario (id_usuario),
  INDEX idx_audit_tabla (tabla_afectada),
  INDEX idx_audit_fecha (fecha_operacion)
);


---------------------------
-- Sistema de Citas Médicas --
---------------------------

-- Tabla de agenda diaria
CREATE TABLE IF NOT EXISTS agenda_diaria (
  id_agenda     BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  id_profesional BIGINT UNSIGNED NOT NULL,
  fecha         DATE NOT NULL,
  hora_inicio   TIME NOT NULL,
  hora_fin      TIME NOT NULL,
  duracion_cita INT UNSIGNED NOT NULL DEFAULT 30, -- minutos
  activa        BOOLEAN NOT NULL DEFAULT TRUE,
  observaciones TEXT NULL,
  CONSTRAINT fk_agenda_profesional FOREIGN KEY (id_profesional) REFERENCES profesional_salud(id_profesional),
  UNIQUE KEY uk_agenda_prof_fecha (id_profesional, fecha),
  INDEX idx_agenda_fecha (fecha),
  INDEX idx_agenda_activa (activa)
);

-- Tabla de bloques de hora
CREATE TABLE IF NOT EXISTS bloque_hora (
  id_bloque     BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  id_agenda     BIGINT UNSIGNED NOT NULL,
  hora_inicio   TIME NOT NULL,
  hora_fin      TIME NOT NULL,
  disponible    BOOLEAN NOT NULL DEFAULT TRUE,
  tipo_bloque   ENUM('CONSULTA','RESERVADO','BLOQUEADO') NOT NULL DEFAULT 'CONSULTA',
  observaciones VARCHAR(255) NULL,
  CONSTRAINT fk_bloque_agenda FOREIGN KEY (id_agenda) REFERENCES agenda_diaria(id_agenda) ON DELETE CASCADE,
  INDEX idx_bloque_agenda (id_agenda),
  INDEX idx_bloque_disponible (disponible),
  INDEX idx_bloque_hora (hora_inicio, hora_fin)
);

-- Tabla de motivos de cancelación
CREATE TABLE IF NOT EXISTS motivo_cancelacion (
  id_motivo INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  descripcion VARCHAR(200) NOT NULL UNIQUE,
  activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- Tabla de citas
CREATE TABLE IF NOT EXISTS cita (
  id_cita       BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  id_paciente   BIGINT UNSIGNED NOT NULL,
  id_bloque     BIGINT UNSIGNED NOT NULL,
  fecha_solicitud DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  estado        ENUM('AGENDADA','CONFIRMADA','EN_ATENCION','ATENDIDA','CANCELADA','NO_ASISTIO') NOT NULL DEFAULT 'AGENDADA',
  motivo_consulta TEXT NULL,
  observaciones TEXT NULL,
  id_motivo_cancelacion INT UNSIGNED NULL,
  fecha_cancelacion DATETIME NULL,
  cancelada_por BIGINT UNSIGNED NULL, -- ID del usuario que canceló la hora
  CONSTRAINT fk_cita_paciente   FOREIGN KEY (id_paciente) REFERENCES paciente(id_paciente),
  CONSTRAINT fk_cita_bloque     FOREIGN KEY (id_bloque)   REFERENCES bloque_hora(id_bloque),
  CONSTRAINT fk_cita_motivo_cancel FOREIGN KEY (id_motivo_cancelacion) REFERENCES motivo_cancelacion(id_motivo),
  CONSTRAINT fk_cita_cancelada_por FOREIGN KEY (cancelada_por) REFERENCES usuario(id_usuario),
  INDEX idx_cita_paciente (id_paciente),
  INDEX idx_cita_bloque (id_bloque),
  INDEX idx_cita_estado (estado),
  INDEX idx_cita_fecha_solicitud (fecha_solicitud)
);


--------------------------------
-- PROCEDIMIENTOS ALMACENADOS --
--------------------------------

DELIMITER $$

-- Procedimiento para agendar una cita
DROP PROCEDURE IF EXISTS agendar_cita$$
CREATE PROCEDURE agendar_cita(
  IN p_id_paciente BIGINT UNSIGNED,
  IN p_id_bloque BIGINT UNSIGNED,
  IN p_motivo_consulta TEXT
)
BEGIN
  DECLARE v_disponible BOOLEAN DEFAULT FALSE;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  START TRANSACTION;

  -- Verificar disponibilidad del bloque
  SELECT disponible INTO v_disponible 
  FROM bloque_hora 
  WHERE id_bloque = p_id_bloque AND disponible = TRUE;

  IF v_disponible THEN
    -- Crear la cita
    INSERT INTO cita (id_paciente, id_bloque, motivo_consulta)
    VALUES (p_id_paciente, p_id_bloque, p_motivo_consulta);
    
    -- Marcar el bloque como no disponible
    UPDATE bloque_hora SET disponible = FALSE WHERE id_bloque = p_id_bloque;
  ELSE
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El bloque de hora no está disponible';
  END IF;

  COMMIT;
END$$

-- Procedimiento para cancelar una cita
DROP PROCEDURE IF EXISTS cancelar_cita$$
CREATE PROCEDURE cancelar_cita(
  IN p_id_cita BIGINT UNSIGNED,
  IN p_id_motivo_cancelacion INT UNSIGNED,
  IN p_cancelada_por BIGINT UNSIGNED
)
BEGIN
  DECLARE v_id_bloque BIGINT UNSIGNED;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  START TRANSACTION;

  -- Obtener el ID del bloque asociado
  SELECT id_bloque INTO v_id_bloque FROM cita WHERE id_cita = p_id_cita;

  IF v_id_bloque IS NOT NULL THEN
    -- Actualizar el estado de la cita
    UPDATE cita 
    SET estado = 'CANCELADA',
        id_motivo_cancelacion = p_id_motivo_cancelacion,
        fecha_cancelacion = NOW(),
        cancelada_por = p_cancelada_por
    WHERE id_cita = p_id_cita;

    -- Liberar el bloque de hora
    UPDATE bloque_hora SET disponible = TRUE WHERE id_bloque = v_id_bloque;
  END IF;

  COMMIT;
END$$
DELIMITER ;


SELECT 'ESTRUCTURA DE BD CREADA EXITOSAMENTE' AS mensaje;
