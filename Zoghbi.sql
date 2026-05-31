-- ============================================================
-- Esquema de base de datos: IUTEPI SGLA v2.0
-- Sistema de Gestión de Laboratorios y Aulas
-- ============================================================

CREATE DATABASE IF NOT EXISTS `iutepi_sgla`
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_general_ci;

USE `iutepi_sgla`;

-- ============================================================
-- TABLA: usuarios
-- Las contraseñas se almacenan hasheadas con bcrypt
-- ============================================================
CREATE TABLE IF NOT EXISTS `usuarios` (
    `id_usuario`     INT AUTO_INCREMENT PRIMARY KEY,
    `nombre_usuario` VARCHAR(50)  NOT NULL UNIQUE,
    `contrasena`     VARCHAR(255) NOT NULL,
    `rol`            ENUM('Admin', 'Profesor') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ============================================================
-- TABLA: docentes (con UNIQUE en nombre para evitar duplicados)
-- ============================================================
CREATE TABLE IF NOT EXISTS `docentes` (
    `id_docente` INT AUTO_INCREMENT PRIMARY KEY,
    `nombre`     VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ============================================================
-- TABLA: semestres
-- ============================================================
CREATE TABLE IF NOT EXISTS `semestres` (
    `id_semestre` INT AUTO_INCREMENT PRIMARY KEY,
    `nombre`      VARCHAR(50) NOT NULL,
    `periodo`     VARCHAR(20) DEFAULT '',
    `created_at`  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ============================================================
-- TABLA: horarios_semestrales
-- ============================================================
CREATE TABLE IF NOT EXISTS `horarios_semestrales` (
    `id_horario`   INT AUTO_INCREMENT PRIMARY KEY,
    `id_semestre`  INT         NOT NULL,
    `materia`      VARCHAR(100) NOT NULL,
    `profesor`     VARCHAR(100) NOT NULL,
    `dia_semana`   VARCHAR(20) NOT NULL,
    `hora_inicio`  TIME NOT NULL,
    `hora_fin`     TIME NOT NULL,
    FOREIGN KEY (`id_semestre`) REFERENCES `semestres`(`id_semestre`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ============================================================
-- TABLA: laboratorios
-- ============================================================
CREATE TABLE IF NOT EXISTS `laboratorios` (
    `id_lab`     INT AUTO_INCREMENT PRIMARY KEY,
    `nombre_lab` VARCHAR(100) NOT NULL UNIQUE,
    `tipo`       VARCHAR(50) DEFAULT '',
    `capacidad`  INT NOT NULL DEFAULT 0,
    `estatus`    VARCHAR(20) DEFAULT 'Disponible'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ============================================================
-- TABLA: reservas
-- ============================================================
CREATE TABLE IF NOT EXISTS `reservas` (
    `id_reserva`     INT AUTO_INCREMENT PRIMARY KEY,
    `id_docente`     INT NOT NULL,
    `materia`        VARCHAR(100) DEFAULT NULL,
    `carrera`        VARCHAR(100) DEFAULT NULL,
    `num_estudiantes` INT DEFAULT 0,
    `periodo`        VARCHAR(20) DEFAULT NULL,
    `tipo_reserva`   VARCHAR(50) DEFAULT 'Clase Semestral',
    FOREIGN KEY (`id_docente`) REFERENCES `docentes`(`id_docente`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ============================================================
-- TABLA: detalles_horario (con índice de disponibilidad)
-- ============================================================
CREATE TABLE IF NOT EXISTS `detalles_horario` (
    `id_detalle`   INT AUTO_INCREMENT PRIMARY KEY,
    `id_reserva`   INT NOT NULL,
    `id_lab`       INT NOT NULL,
    `dia_semana`   VARCHAR(20) DEFAULT '',
    `fecha`        DATE NOT NULL,
    `hora_inicio`  TIME NOT NULL,
    `hora_fin`     TIME NOT NULL,
    FOREIGN KEY (`id_reserva`) REFERENCES `reservas`(`id_reserva`)
        ON DELETE CASCADE,
    FOREIGN KEY (`id_lab`) REFERENCES `laboratorios`(`id_lab`)
        ON DELETE CASCADE,
    INDEX `idx_disponibilidad` (`id_lab`, `fecha`, `hora_inicio`, `hora_fin`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ============================================================
-- DATOS INICIALES
-- ============================================================

-- Semestres (6 semestres académicos)
INSERT INTO `semestres` (`id_semestre`, `nombre`, `periodo`) VALUES
    (1, '1', ''),
    (2, '2', ''),
    (3, '3', ''),
    (4, '4', ''),
    (5, '5', ''),
    (6, '6', '')
ON DUPLICATE KEY UPDATE `nombre` = VALUES(`nombre`);

-- Laboratorios default
INSERT INTO `laboratorios` (`id_lab`, `nombre_lab`, `tipo`, `capacidad`, `estatus`) VALUES
    (1, 'Laboratorio I',   'Laboratorio', 30, 'Disponible'),
    (2, 'Laboratorio II',  'Laboratorio', 25, 'Disponible'),
    (3, 'Laboratorio III', 'Laboratorio', 30, 'Disponible'),
    (4, 'Laboratorio VI',  'Laboratorio', 25, 'Disponible')
ON DUPLICATE KEY UPDATE `nombre_lab` = VALUES(`nombre_lab`);

-- Nota: El usuario admin se crea desde la aplicación
-- con contraseña hasheada mediante bcrypt.
