CREATE TABLE IF NOT EXISTS treasury_cuentas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL UNIQUE,
    banco VARCHAR(255),
    moneda VARCHAR(16) NOT NULL,
    reserva_minima DECIMAL(18,2) NOT NULL DEFAULT 0,
    activa BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS treasury_saldos_diarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cuenta_id INT NOT NULL,
    fecha DATE NOT NULL,
    saldo_interno DECIMAL(18,2) NOT NULL,
    saldo_extracto DECIMAL(18,2),
    fuente VARCHAR(50) NOT NULL DEFAULT 'archivo',
    cargado_por VARCHAR(255),
    cargado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY ux_treasury_saldo_cuenta_fecha (cuenta_id, fecha),
    CONSTRAINT fk_treasury_saldos_cuenta
        FOREIGN KEY (cuenta_id) REFERENCES treasury_cuentas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS treasury_discrepancias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    saldo_diario_id INT NOT NULL,
    diferencia DECIMAL(18,2) NOT NULL,
    estado VARCHAR(32) NOT NULL DEFAULT 'abierta',
    detectada_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    saldo_diario_abierta_id INT
        GENERATED ALWAYS AS (CASE WHEN estado = 'abierta' THEN saldo_diario_id ELSE NULL END) STORED,
    UNIQUE KEY ux_treasury_discrepancia_abierta (saldo_diario_abierta_id),
    INDEX ix_treasury_discrepancias_saldo (saldo_diario_id),
    CONSTRAINT fk_treasury_discrepancias_saldo
        FOREIGN KEY (saldo_diario_id) REFERENCES treasury_saldos_diarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS treasury_acciones_correctivas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    discrepancia_id INT NOT NULL,
    descripcion TEXT NOT NULL,
    registrado_por VARCHAR(255),
    registrado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_treasury_acciones_discrepancia
        FOREIGN KEY (discrepancia_id) REFERENCES treasury_discrepancias(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS treasury_informes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    periodo_desde DATE NOT NULL,
    periodo_hasta DATE NOT NULL,
    modulos_incluidos JSON NOT NULL,
    formato VARCHAR(50) NOT NULL,
    generado_por VARCHAR(255),
    generado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    nombre_archivo VARCHAR(255),
    contenido LONGBLOB
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS treasury_notas_coordinacion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    autor VARCHAR(255) NOT NULL,
    area VARCHAR(255) NOT NULL,
    mensaje TEXT NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
