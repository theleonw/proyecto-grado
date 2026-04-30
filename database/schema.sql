-- database/schema.sql
CREATE DATABASE IF NOT EXISTS forjadores_fbc CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE forjadores_fbc;

CREATE TABLE roles (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE usuarios (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    rol_id BIGINT UNSIGNED NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    telefono VARCHAR(30) NULL,
    activo TINYINT(1) NOT NULL DEFAULT 1,
    ultimo_login DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_usuarios_roles FOREIGN KEY (rol_id) REFERENCES roles(id)
) ENGINE=InnoDB;

CREATE TABLE acudientes (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    usuario_id BIGINT UNSIGNED NOT NULL UNIQUE,
    documento VARCHAR(30) NOT NULL UNIQUE,
    direccion VARCHAR(180) NULL,
    parentesco_principal VARCHAR(50) NOT NULL,
    ocupacion VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_acudientes_usuarios FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
) ENGINE=InnoDB;

CREATE TABLE categorias (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL UNIQUE,
    edad_min TINYINT UNSIGNED NOT NULL,
    edad_max TINYINT UNSIGNED NOT NULL,
    cupo_maximo SMALLINT UNSIGNED NOT NULL,
    descripcion VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_rango_edad CHECK (edad_min <= edad_max)
) ENGINE=InnoDB;

CREATE TABLE estudiantes (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    acudiente_id BIGINT UNSIGNED NOT NULL,
    categoria_id BIGINT UNSIGNED NOT NULL,
    codigo VARCHAR(30) NOT NULL UNIQUE,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    estado ENUM('PREINSCRITO', 'ACTIVO', 'INACTIVO', 'RETIRADO') NOT NULL DEFAULT 'PREINSCRITO',
    fecha_inscripcion DATE NOT NULL,
    observaciones_medicas TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_estudiantes_acudientes FOREIGN KEY (acudiente_id) REFERENCES acudientes(id),
    CONSTRAINT fk_estudiantes_categorias FOREIGN KEY (categoria_id) REFERENCES categorias(id)
) ENGINE=InnoDB;

CREATE TABLE conceptos_pago (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL UNIQUE,
    descripcion VARCHAR(255) NULL,
    valor DECIMAL(10,2) NOT NULL,
    periodicidad ENUM('UNICO', 'MENSUAL', 'BIMESTRAL', 'TRIMESTRAL', 'SEMESTRAL', 'ANUAL') NOT NULL,
    activo TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE pagos (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    estudiante_id BIGINT UNSIGNED NOT NULL,
    concepto_id BIGINT UNSIGNED NOT NULL,
    registrado_por BIGINT UNSIGNED NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    fecha_emision DATE NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    fecha_pago DATETIME NULL,
    metodo_pago ENUM('EFECTIVO', 'TRANSFERENCIA', 'TARJETA', 'QR') NULL,
    referencia VARCHAR(80) NULL,
    estado ENUM('PENDIENTE', 'PAGADO', 'VENCIDO', 'ANULADO') NOT NULL DEFAULT 'PENDIENTE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_pagos_estudiantes FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id),
    CONSTRAINT fk_pagos_conceptos FOREIGN KEY (concepto_id) REFERENCES conceptos_pago(id),
    CONSTRAINT fk_pagos_usuarios FOREIGN KEY (registrado_por) REFERENCES usuarios(id)
) ENGINE=InnoDB;

CREATE TABLE asistencias (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    estudiante_id BIGINT UNSIGNED NOT NULL,
    fecha DATE NOT NULL,
    asistio TINYINT(1) NOT NULL,
    observacion VARCHAR(255) NULL,
    registrado_por BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_asistencia_estudiante_fecha UNIQUE (estudiante_id, fecha),
    CONSTRAINT fk_asistencias_estudiantes FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id),
    CONSTRAINT fk_asistencias_usuarios FOREIGN KEY (registrado_por) REFERENCES usuarios(id)
) ENGINE=InnoDB;

CREATE TABLE metricas (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    estudiante_id BIGINT UNSIGNED NOT NULL,
    fecha_medicion DATE NOT NULL,
    velocidad DECIMAL(5,2) NULL,
    resistencia DECIMAL(5,2) NULL,
    fuerza DECIMAL(5,2) NULL,
    tecnica DECIMAL(5,2) NULL,
    observaciones VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_metricas_estudiantes FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id)
) ENGINE=InnoDB;

CREATE TABLE evaluaciones (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    estudiante_id BIGINT UNSIGNED NOT NULL,
    evaluador_id BIGINT UNSIGNED NOT NULL,
    fecha DATE NOT NULL,
    disciplina DECIMAL(4,2) NOT NULL,
    trabajo_equipo DECIMAL(4,2) NOT NULL,
    toma_decisiones DECIMAL(4,2) NOT NULL,
    condicion_fisica DECIMAL(4,2) NOT NULL,
    nota_final DECIMAL(4,2) GENERATED ALWAYS AS ((disciplina + trabajo_equipo + toma_decisiones + condicion_fisica) / 4) STORED,
    comentario TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_evaluaciones_estudiantes FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id),
    CONSTRAINT fk_evaluaciones_usuarios FOREIGN KEY (evaluador_id) REFERENCES usuarios(id)
) ENGINE=InnoDB;

CREATE TABLE lista_espera (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    categoria_id BIGINT UNSIGNED NOT NULL,
    acudiente_id BIGINT UNSIGNED NOT NULL,
    nombres_estudiante VARCHAR(100) NOT NULL,
    apellidos_estudiante VARCHAR(100) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    posicion INT UNSIGNED NOT NULL,
    estado ENUM('EN_ESPERA', 'NOTIFICADO', 'INSCRITO', 'RETIRADO') NOT NULL DEFAULT 'EN_ESPERA',
    fecha_solicitud DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_lista_espera_categoria_posicion UNIQUE (categoria_id, posicion),
    CONSTRAINT fk_lista_espera_categorias FOREIGN KEY (categoria_id) REFERENCES categorias(id),
    CONSTRAINT fk_lista_espera_acudientes FOREIGN KEY (acudiente_id) REFERENCES acudientes(id)
) ENGINE=InnoDB;

DELIMITER $$
CREATE TRIGGER trg_activar_estudiante_post_pago
AFTER INSERT ON pagos
FOR EACH ROW
BEGIN
    IF NEW.estado = 'PAGADO' THEN
        UPDATE estudiantes
        SET estado = 'ACTIVO'
        WHERE id = NEW.estudiante_id;
    END IF;
END $$
DELIMITER ;

CREATE OR REPLACE VIEW vw_morosos AS
SELECT
    e.id AS estudiante_id,
    e.codigo,
    CONCAT(e.nombres, ' ', e.apellidos) AS estudiante,
    COUNT(p.id) AS cuotas_pendientes,
    MIN(p.fecha_vencimiento) AS deuda_mas_antigua,
    DATEDIFF(CURDATE(), MIN(p.fecha_vencimiento)) AS dias_mora,
    SUM(p.monto) AS total_adeudado
FROM estudiantes e
INNER JOIN pagos p ON p.estudiante_id = e.id
WHERE p.estado = 'PENDIENTE'
  AND p.fecha_vencimiento < (CURDATE() - INTERVAL 30 DAY)
GROUP BY e.id, e.codigo, e.nombres, e.apellidos;
