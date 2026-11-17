-- =====================================================================
-- Base de datos: trazabilidad de huella de carbono y embalaje (artesanías)
-- Motor: MySQL 5.7+ / MariaDB 10.2+ (InnoDB, utf8mb4)
-- Basada en el PDCA vigente (flota de 2 unidades, piloto Oaxaca con 1 unidad):
-- Formatos A (embalaje), B (viaje/transporte), C (carga masiva desde el Excel
-- del cliente), inventario, GPS, factores de emisión, consolidación y rutas.
-- =====================================================================

DROP DATABASE IF EXISTS someone_somewhere;
CREATE DATABASE someone_somewhere
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE someone_somewhere;

-- =====================================================================
-- 1. SEGURIDAD (RBAC, hash + sal, MFA TOTP, auditoría)
-- =====================================================================

CREATE TABLE roles (
  id_rol        TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre        VARCHAR(40)  NOT NULL UNIQUE,   -- administrador, almacen, operador, coordinador, lider, artesano
  descripcion   VARCHAR(200) NULL
) ENGINE=InnoDB;

CREATE TABLE permisos (
  id_permiso    SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  codigo        VARCHAR(60)  NOT NULL UNIQUE,   -- ej. 'factores.editar', 'viajes.confirmar_parada'
  descripcion   VARCHAR(200) NULL
) ENGINE=InnoDB;

CREATE TABLE rol_permiso (
  id_rol        TINYINT UNSIGNED  NOT NULL,
  id_permiso    SMALLINT UNSIGNED NOT NULL,
  PRIMARY KEY (id_rol, id_permiso),
  FOREIGN KEY (id_rol)     REFERENCES roles(id_rol)       ON DELETE CASCADE,
  FOREIGN KEY (id_permiso) REFERENCES permisos(id_permiso) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE usuarios (
  id_usuario        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_rol            TINYINT UNSIGNED NOT NULL,
  nombre_completo   VARCHAR(120) NOT NULL,
  correo            VARCHAR(150) NOT NULL UNIQUE,
  password_hash     VARCHAR(255) NOT NULL,      -- argon2id/bcrypt (nunca texto plano)
  password_sal      VARCHAR(64)  NOT NULL,
  mfa_habilitado    BOOLEAN      NOT NULL DEFAULT FALSE,
  mfa_secreto_totp  VARBINARY(128) NULL,        -- cifrado a nivel de aplicación
  intentos_fallidos TINYINT UNSIGNED NOT NULL DEFAULT 0,
  bloqueado_hasta   DATETIME NULL,
  activo            BOOLEAN  NOT NULL DEFAULT TRUE,
  ultimo_acceso     DATETIME NULL,
  creado_en         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_rol) REFERENCES roles(id_rol)
  -- Regla de negocio: el rol 'administrador' exige mfa_habilitado = TRUE (validar en la app)
) ENGINE=InnoDB;

CREATE TABLE auditoria (
  id_auditoria  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_usuario    INT UNSIGNED NULL,
  accion        VARCHAR(20)  NOT NULL,          -- INSERT / UPDATE / DELETE / LOGIN
  tabla         VARCHAR(60)  NOT NULL,
  id_registro   VARCHAR(60)  NULL,
  valor_anterior JSON NULL,
  valor_nuevo    JSON NULL,
  ip_origen     VARCHAR(45) NULL,
  fecha         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_aud_tabla (tabla, id_registro),
  INDEX idx_aud_fecha (fecha),
  FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE SET NULL
) ENGINE=InnoDB;

-- =====================================================================
-- 2. CATÁLOGOS BASE: locaciones, empresas, artesanos, unidades, operadores
-- =====================================================================

CREATE TABLE locaciones (
  id_locacion   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  codigo        VARCHAR(20)  NOT NULL UNIQUE,   -- MX-CMX-001, US-LRD-001
  nombre        VARCHAR(120) NOT NULL,
  tipo          ENUM('taller','hub','frontera','cliente_final') NOT NULL,
  pais          CHAR(2)      NOT NULL,          -- MX, US, CA
  estado        VARCHAR(60)  NULL,              -- Oaxaca, Puebla, Chiapas, CDMX...
  ciudad        VARCHAR(80)  NULL,
  direccion     VARCHAR(255) NULL,              -- dato personal si es taller de artesano
  latitud       DECIMAL(9,6) NULL,
  longitud      DECIMAL(9,6) NULL,
  activa        BOOLEAN NOT NULL DEFAULT TRUE,
  INDEX idx_loc_tipo (tipo, estado)
) ENGINE=InnoDB;

CREATE TABLE empresas (                          -- clientes (EUA/Canadá) y la empresa dueña
  id_empresa    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre        VARCHAR(150) NOT NULL,
  tipo          ENUM('propia','cliente') NOT NULL DEFAULT 'cliente',
  rfc_tax_id    VARCHAR(30)  NULL,
  pais          CHAR(2)      NOT NULL,
  correo_contacto VARCHAR(150) NULL,
  telefono      VARCHAR(30)  NULL,
  activa        BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

CREATE TABLE artesanos (
  id_artesano   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_usuario    INT UNSIGNED NULL UNIQUE,       -- si tiene acceso al sistema
  id_locacion   INT UNSIGNED NOT NULL,          -- su taller
  nombre        VARCHAR(120) NOT NULL,
  telefono      VARCHAR(30)  NULL,
  en_piloto     BOOLEAN NOT NULL DEFAULT FALSE, -- los 15 artesanos de Oaxaca
  activo        BOOLEAN NOT NULL DEFAULT TRUE,
  FOREIGN KEY (id_usuario)  REFERENCES usuarios(id_usuario) ON DELETE SET NULL,
  FOREIGN KEY (id_locacion) REFERENCES locaciones(id_locacion)
) ENGINE=InnoDB;

CREATE TABLE tipos_unidad (
  id_tipo_unidad TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre         VARCHAR(40) NOT NULL UNIQUE,   -- Tractocamión
  combustible    ENUM('diesel','gasolina','gas','electrico') NOT NULL DEFAULT 'diesel',
  capacidad_kg   INT UNSIGNED NOT NULL          -- 20000
) ENGINE=InnoDB;

CREATE TABLE unidades (
  id_unidad      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  codigo         VARCHAR(20) NOT NULL UNIQUE,   -- ECO-014
  id_tipo_unidad TINYINT UNSIGNED NOT NULL,
  placas         VARCHAR(15) NULL,
  odometro_km    DECIMAL(10,1) NOT NULL DEFAULT 0,
  en_piloto      BOOLEAN NOT NULL DEFAULT FALSE,  -- las 3 unidades del piloto
  activa         BOOLEAN NOT NULL DEFAULT TRUE,
  FOREIGN KEY (id_tipo_unidad) REFERENCES tipos_unidad(id_tipo_unidad)
) ENGINE=InnoDB;

CREATE TABLE rastreadores_gps (                  -- router 4G/LTE por unidad
  id_rastreador  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_unidad      INT UNSIGNED NOT NULL,
  imei           VARCHAR(20) NOT NULL UNIQUE,
  intervalo_seg  SMALLINT UNSIGNED NOT NULL DEFAULT 120,   -- cada 2 minutos
  activo         BOOLEAN NOT NULL DEFAULT TRUE,
  FOREIGN KEY (id_unidad) REFERENCES unidades(id_unidad)
) ENGINE=InnoDB;

CREATE TABLE operadores (                        -- DATOS PERSONALES
  id_operador    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_usuario     INT UNSIGNED NULL UNIQUE,
  nombre         VARCHAR(120) NOT NULL,
  telefono       VARCHAR(30)  NULL,
  licencia       VARCHAR(30)  NULL,
  activo         BOOLEAN NOT NULL DEFAULT TRUE,
  FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE SET NULL
) ENGINE=InnoDB;

-- =====================================================================
-- 3. PRODUCTOS Y EMBALAJE
-- =====================================================================

CREATE TABLE categorias_producto (
  id_categoria   TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre         VARCHAR(60) NOT NULL UNIQUE    -- Textiles, Cerámica
) ENGINE=InnoDB;

CREATE TABLE productos (
  id_producto    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_artesano    INT UNSIGNED NOT NULL,
  id_categoria   TINYINT UNSIGNED NOT NULL,
  nombre         VARCHAR(150) NOT NULL,
  peso_unitario_kg DECIMAL(8,3) NOT NULL,
  activo         BOOLEAN NOT NULL DEFAULT TRUE,
  FOREIGN KEY (id_artesano)  REFERENCES artesanos(id_artesano),
  FOREIGN KEY (id_categoria) REFERENCES categorias_producto(id_categoria)
) ENGINE=InnoDB;

CREATE TABLE materiales_embalaje (
  id_material    SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre         VARCHAR(80) NOT NULL UNIQUE,   -- Papel kraft, Film stretch, Cartón corrugado...
  tipo           ENUM('reciclado','biodegradable','plastico_no_biodegradable') NOT NULL,
  es_alternativa_a SMALLINT UNSIGNED NULL,      -- catálogo de alternativas al plástico
  activo         BOOLEAN NOT NULL DEFAULT TRUE,
  FOREIGN KEY (es_alternativa_a) REFERENCES materiales_embalaje(id_material)
) ENGINE=InnoDB;

CREATE TABLE embalaje_recomendado (              -- ej. Cerámica → cartón corrugado + honeycomb
  id_categoria   TINYINT UNSIGNED  NOT NULL,
  id_material    SMALLINT UNSIGNED NOT NULL,
  PRIMARY KEY (id_categoria, id_material),
  FOREIGN KEY (id_categoria) REFERENCES categorias_producto(id_categoria),
  FOREIGN KEY (id_material)  REFERENCES materiales_embalaje(id_material)
) ENGINE=InnoDB;

-- Inventario del cliente (alimenta catálogo y consolidación)
CREATE TABLE inventario_productos (              -- productos terminados / piezas disponibles
  id_producto    INT UNSIGNED NOT NULL,
  id_locacion    INT UNSIGNED NOT NULL,          -- taller o hub donde está la pieza
  piezas_disponibles INT UNSIGNED NOT NULL DEFAULT 0,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id_producto, id_locacion),
  FOREIGN KEY (id_producto) REFERENCES productos(id_producto),
  FOREIGN KEY (id_locacion) REFERENCES locaciones(id_locacion)
) ENGINE=InnoDB;

CREATE TABLE inventario_materiales (             -- existencias de embalaje
  id_material    SMALLINT UNSIGNED NOT NULL,
  id_locacion    INT UNSIGNED NOT NULL,          -- normalmente el almacén CDMX
  existencia_kg  DECIMAL(10,3) NOT NULL DEFAULT 0,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id_material, id_locacion),
  FOREIGN KEY (id_material) REFERENCES materiales_embalaje(id_material),
  FOREIGN KEY (id_locacion) REFERENCES locaciones(id_locacion)
) ENGINE=InnoDB;

CREATE TABLE movimientos_material (              -- entradas/salidas; la salida se genera con el Formato A
  id_movimiento  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_material    SMALLINT UNSIGNED NOT NULL,
  id_locacion    INT UNSIGNED NOT NULL,
  tipo           ENUM('entrada','salida','ajuste') NOT NULL,
  cantidad_kg    DECIMAL(10,3) NOT NULL,
  id_pedido      INT UNSIGNED NULL,
  id_usuario     INT UNSIGNED NULL,
  creado_en      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_material) REFERENCES materiales_embalaje(id_material),
  FOREIGN KEY (id_locacion) REFERENCES locaciones(id_locacion),
  FOREIGN KEY (id_usuario)  REFERENCES usuarios(id_usuario) ON DELETE SET NULL,
  INDEX idx_mov_material (id_material, creado_en)
) ENGINE=InnoDB;

-- =====================================================================
-- 4. PEDIDOS, EMBALAJE (Formato A) Y TRAMOS
-- =====================================================================

CREATE TABLE pedidos (
  id_pedido      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  codigo         VARCHAR(20) NOT NULL UNIQUE,   -- PED-00125
  id_empresa     INT UNSIGNED NOT NULL,         -- cliente
  id_artesano    INT UNSIGNED NOT NULL,
  id_locacion_destino INT UNSIGNED NOT NULL,    -- destino final
  peso_producto_kg DECIMAL(10,2) NOT NULL,      -- p. ej. 20
  fecha_pedido   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  fecha_limite_entrega DATE NOT NULL,           -- ventana de entrega (criterio de consolidación)
  estado         ENUM('registrado','listo_acopio','en_hub','consolidado','en_transito','entregado','cancelado')
                 NOT NULL DEFAULT 'registrado',
  FOREIGN KEY (id_empresa)  REFERENCES empresas(id_empresa),
  FOREIGN KEY (id_artesano) REFERENCES artesanos(id_artesano),
  FOREIGN KEY (id_locacion_destino) REFERENCES locaciones(id_locacion),
  INDEX idx_ped_consol (id_empresa, id_locacion_destino, estado, fecha_limite_entrega)
) ENGINE=InnoDB;

CREATE TABLE pedido_productos (
  id_pedido      INT UNSIGNED NOT NULL,
  id_producto    INT UNSIGNED NOT NULL,
  cantidad       INT UNSIGNED NOT NULL,
  PRIMARY KEY (id_pedido, id_producto),
  FOREIGN KEY (id_pedido)   REFERENCES pedidos(id_pedido) ON DELETE CASCADE,
  FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
) ENGINE=InnoDB;

-- Formato A: una ficha por pedido, con renglones de material
CREATE TABLE pedido_embalaje (
  id_pedido_embalaje INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_pedido      INT UNSIGNED NOT NULL,
  id_material    SMALLINT UNSIGNED NOT NULL,
  descripcion    VARCHAR(120) NULL,             -- "Cartón reciclado (5 cajas)"
  peso_kg        DECIMAL(8,3) NOT NULL,
  registrado_por INT UNSIGNED NULL,
  registrado_en  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,   -- fecha y hora automática
  origen_registro ENUM('app','gps','excel') NOT NULL DEFAULT 'app',
  id_importacion INT UNSIGNED NULL,              -- FK al final del script (importaciones se crea después)
  FOREIGN KEY (id_pedido)   REFERENCES pedidos(id_pedido) ON DELETE CASCADE,
  FOREIGN KEY (id_material) REFERENCES materiales_embalaje(id_material),
  FOREIGN KEY (registrado_por) REFERENCES usuarios(id_usuario) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Viajes (Formato B, encabezado)
CREATE TABLE viajes (
  id_viaje       INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  codigo         VARCHAR(20) NOT NULL UNIQUE,   -- VJ-2026-0041
  tramo          TINYINT UNSIGNED NOT NULL,     -- 1 taller→hub, 2 hub→Laredo, 3 Laredo→cliente
  id_unidad      INT UNSIGNED NOT NULL,
  id_operador    INT UNSIGNED NOT NULL,
  id_locacion_origen  INT UNSIGNED NOT NULL,
  id_locacion_destino INT UNSIGNED NOT NULL,
  capacidad_kg   INT UNSIGNED NOT NULL,         -- copia de la capacidad al momento del viaje
  carga_kg       DECIMAL(10,2) NOT NULL DEFAULT 0,
  num_pedidos    INT UNSIGNED  NOT NULL DEFAULT 0,
  km_planeados   DECIMAL(8,1) NULL,
  salida_real    DATETIME NULL,
  llegada_real   DATETIME NULL,
  odometro_salida  DECIMAL(10,1) NULL,
  odometro_llegada DECIMAL(10,1) NULL,
  costo_total_mxn  DECIMAL(12,2) NULL,          -- se reparte entre sus pedidos
  num_paradas    SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  hubo_cambio_ruta BOOLEAN NOT NULL DEFAULT FALSE,
  hubo_falla     BOOLEAN NOT NULL DEFAULT FALSE,
  estado         ENUM('planeado','en_curso','finalizado','cancelado') NOT NULL DEFAULT 'planeado',
  origen_registro ENUM('app','gps','excel') NOT NULL DEFAULT 'gps',   -- KPI: ≥80% automáticos
  id_importacion INT UNSIGNED NULL,
  -- calculados automáticamente
  km_totales  DECIMAL(10,1) GENERATED ALWAYS AS (odometro_llegada - odometro_salida) STORED,
  llenado_pct DECIMAL(5,2)  GENERATED ALWAYS AS (carga_kg / capacidad_kg * 100) STORED,
  FOREIGN KEY (id_unidad)   REFERENCES unidades(id_unidad),
  FOREIGN KEY (id_operador) REFERENCES operadores(id_operador),
  FOREIGN KEY (id_locacion_origen)  REFERENCES locaciones(id_locacion),
  FOREIGN KEY (id_locacion_destino) REFERENCES locaciones(id_locacion),
  INDEX idx_viaje_fecha (salida_real),
  INDEX idx_viaje_unidad (id_unidad, salida_real)
) ENGINE=InnoDB;

CREATE TABLE paradas_viaje (                     -- B: el operador confirma tipo y motivo
  id_parada      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_viaje       INT UNSIGNED NOT NULL,
  tipo           ENUM('descanso','falla','desvio','carga_descarga','otro') NOT NULL,
  motivo         VARCHAR(200) NULL,
  detectada_por_gps BOOLEAN NOT NULL DEFAULT TRUE,
  confirmada     BOOLEAN NOT NULL DEFAULT FALSE,
  inicio         DATETIME NOT NULL,
  fin            DATETIME NULL,
  odometro_inicio DECIMAL(10,1) NULL,
  odometro_fin    DECIMAL(10,1) NULL,
  km_adicionales  DECIMAL(6,1) NOT NULL DEFAULT 0,   -- desvío
  litros_adicionales_est DECIMAL(7,2) NOT NULL DEFAULT 0,
  FOREIGN KEY (id_viaje) REFERENCES viajes(id_viaje) ON DELETE CASCADE,
  INDEX idx_parada_viaje (id_viaje)
) ENGINE=InnoDB;

-- Un registro por pedido y por tramo (SS-2026-00125 = ID_Envio)
CREATE TABLE envio_tramos (
  id_envio_tramo INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  codigo_envio   VARCHAR(20) NOT NULL UNIQUE,   -- SS-2026-00125
  id_pedido      INT UNSIGNED NOT NULL,
  tramo          TINYINT UNSIGNED NOT NULL,
  id_viaje       INT UNSIGNED NULL,             -- NULL hasta asignarse a un viaje
  id_locacion_origen  INT UNSIGNED NOT NULL,
  id_locacion_destino INT UNSIGNED NOT NULL,
  medio_transporte ENUM('terrestre','aereo','maritimo') NOT NULL DEFAULT 'terrestre',
  peso_total_kg  DECIMAL(10,2) NULL,            -- producto + embalaje
  distancia_km   DECIMAL(8,1)  NULL,
  paradas        SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  costo_asignado_mxn DECIMAL(12,2) NULL,
  fecha_salida   DATETIME NULL,
  fecha_llegada  DATETIME NULL,
  origen_registro ENUM('app','gps','excel') NOT NULL DEFAULT 'gps',
  id_importacion INT UNSIGNED NULL,
  UNIQUE KEY uq_pedido_tramo (id_pedido, tramo),
  FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido),
  FOREIGN KEY (id_viaje)  REFERENCES viajes(id_viaje) ON DELETE SET NULL,
  FOREIGN KEY (id_locacion_origen)  REFERENCES locaciones(id_locacion),
  FOREIGN KEY (id_locacion_destino) REFERENCES locaciones(id_locacion),
  INDEX idx_envio_viaje (id_viaje)
) ENGINE=InnoDB;

-- =====================================================================
-- 5. GPS EN TIEMPO REAL (posición cada 2 min; con almacenamiento diferido)
-- =====================================================================

CREATE TABLE posiciones_gps (
  id_posicion    BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_unidad      INT UNSIGNED NOT NULL,
  id_viaje       INT UNSIGNED NULL,
  latitud        DECIMAL(9,6) NOT NULL,
  longitud       DECIMAL(9,6) NOT NULL,
  velocidad_kmh  DECIMAL(5,1) NULL,
  hora_gps       DATETIME NOT NULL,              -- el sistema usa la hora del GPS
  recibido_en    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  envio_diferido BOOLEAN NOT NULL DEFAULT FALSE, -- se guardó sin señal y se envió después
  UNIQUE KEY uq_unidad_hora (id_unidad, hora_gps),   -- evita duplicados al reenviar
  INDEX idx_gps_viaje (id_viaje, hora_gps),
  FOREIGN KEY (id_unidad) REFERENCES unidades(id_unidad),
  FOREIGN KEY (id_viaje)  REFERENCES viajes(id_viaje) ON DELETE SET NULL
) ENGINE=InnoDB;

-- =====================================================================
-- 6. FACTORES DE EMISIÓN Y HUELLA (GHG Protocol + ISO 14083)
-- =====================================================================

CREATE TABLE factores_emision (                  -- editable por el administrador
  id_factor      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  combustible    ENUM('diesel','gasolina','gas','electrico') NOT NULL,
  kg_co2_por_litro DECIMAL(8,4) NOT NULL,         -- 2.68 para diésel
  vigente_desde  DATE NOT NULL,
  vigente_hasta  DATE NULL,
  fuente         VARCHAR(150) NULL,
  creado_por     INT UNSIGNED NULL,
  creado_en      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (creado_por) REFERENCES usuarios(id_usuario) ON DELETE SET NULL,
  INDEX idx_fe_vigencia (combustible, vigente_desde)
) ENGINE=InnoDB;

CREATE TABLE factores_consumo (                  -- litros / 100 km por tipo de unidad
  id_factor_consumo INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_tipo_unidad TINYINT UNSIGNED NOT NULL,
  litros_por_100km DECIMAL(6,2) NOT NULL,         -- 35
  vigente_desde  DATE NOT NULL,
  vigente_hasta  DATE NULL,
  creado_por     INT UNSIGNED NULL,
  creado_en      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_tipo_unidad) REFERENCES tipos_unidad(id_tipo_unidad),
  FOREIGN KEY (creado_por) REFERENCES usuarios(id_usuario) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Registro de cambios (quién y cuándo) de factores
CREATE TABLE factores_historial (
  id_historial   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  tabla_factor   ENUM('factores_emision','factores_consumo') NOT NULL,
  id_factor      INT UNSIGNED NOT NULL,
  valor_anterior DECIMAL(10,4) NULL,
  valor_nuevo    DECIMAL(10,4) NOT NULL,
  cambiado_por   INT UNSIGNED NULL,
  cambiado_en    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  motivo         VARCHAR(200) NULL,
  FOREIGN KEY (cambiado_por) REFERENCES usuarios(id_usuario) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE huella_viaje (                      -- resultado del cálculo por viaje
  id_viaje       INT UNSIGNED PRIMARY KEY,
  id_factor_emision  INT UNSIGNED NOT NULL,
  id_factor_consumo  INT UNSIGNED NOT NULL,
  km_considerados    DECIMAL(10,1) NOT NULL,
  litros_estimados   DECIMAL(10,2) NOT NULL,      -- km × l/100km (+ adicional por desvíos)
  litros_reales      DECIMAL(10,2) NULL,          -- ticket (validación con 20 viajes)
  co2_kg             DECIMAL(12,2) NOT NULL,
  co2_kg_por_pedido  DECIMAL(8,3)  NOT NULL,
  -- error de la estimación vs ticket (criterio de éxito: |error| ≤ 10%)
  error_combustible_pct DECIMAL(7,2) GENERATED ALWAYS AS
      (ROUND((litros_estimados - litros_reales) / NULLIF(litros_reales, 0) * 100, 2)) STORED,
  alcance_ghg        TINYINT UNSIGNED NOT NULL DEFAULT 1,
  calculado_en       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_viaje) REFERENCES viajes(id_viaje) ON DELETE CASCADE,
  FOREIGN KEY (id_factor_emision) REFERENCES factores_emision(id_factor),
  FOREIGN KEY (id_factor_consumo) REFERENCES factores_consumo(id_factor_consumo)
) ENGINE=InnoDB;

-- =====================================================================
-- 7. RUTAS, CONSOLIDACIÓN, ALERTAS Y CORREOS (Fase 2)
-- =====================================================================

CREATE TABLE simulaciones_ruta (
  id_simulacion  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_usuario     INT UNSIGNED NULL,
  id_locacion_origen  INT UNSIGNED NOT NULL,
  id_locacion_destino INT UNSIGNED NOT NULL,
  id_unidad      INT UNSIGNED NULL,
  km_estimados   DECIMAL(8,1) NULL,
  duracion_min   INT UNSIGNED NULL,
  carga_kg       DECIMAL(10,2) NULL,
  llenado_pct    DECIMAL(5,2)  NULL,
  litros_estimados DECIMAL(10,2) NULL,
  co2_kg_estimado DECIMAL(12,2) NULL,
  proveedor_mapas VARCHAR(40) NULL,
  creada_en      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE SET NULL,
  FOREIGN KEY (id_locacion_origen)  REFERENCES locaciones(id_locacion),
  FOREIGN KEY (id_locacion_destino) REFERENCES locaciones(id_locacion),
  FOREIGN KEY (id_unidad) REFERENCES unidades(id_unidad)
) ENGINE=InnoDB;

CREATE TABLE simulacion_pedidos (
  id_simulacion  INT UNSIGNED NOT NULL,
  id_pedido      INT UNSIGNED NOT NULL,
  PRIMARY KEY (id_simulacion, id_pedido),
  FOREIGN KEY (id_simulacion) REFERENCES simulaciones_ruta(id_simulacion) ON DELETE CASCADE,
  FOREIGN KEY (id_pedido)     REFERENCES pedidos(id_pedido) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE alertas_consolidacion (
  id_alerta      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_empresa     INT UNSIGNED NOT NULL,          -- criterios: cliente,
  id_locacion_destino INT UNSIGNED NOT NULL,     -- destino,
  peso_acumulado_kg DECIMAL(10,2) NOT NULL,      -- peso,
  fecha_limite_mas_cercana DATE NOT NULL,        -- fecha límite
  num_pedidos    INT UNSIGNED NOT NULL,
  estado         ENUM('abierta','atendida','descartada') NOT NULL DEFAULT 'abierta',
  id_viaje_resultante INT UNSIGNED NULL,
  creada_en      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atendida_por   INT UNSIGNED NULL,
  FOREIGN KEY (id_empresa) REFERENCES empresas(id_empresa),
  FOREIGN KEY (id_locacion_destino) REFERENCES locaciones(id_locacion),
  FOREIGN KEY (id_viaje_resultante) REFERENCES viajes(id_viaje) ON DELETE SET NULL,
  FOREIGN KEY (atendida_por) REFERENCES usuarios(id_usuario) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE alerta_pedidos (
  id_alerta      INT UNSIGNED NOT NULL,
  id_pedido      INT UNSIGNED NOT NULL,
  PRIMARY KEY (id_alerta, id_pedido),
  FOREIGN KEY (id_alerta) REFERENCES alertas_consolidacion(id_alerta) ON DELETE CASCADE,
  FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE correos_cola (
  id_correo      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  destinatario   VARCHAR(150) NOT NULL,
  asunto         VARCHAR(200) NOT NULL,
  cuerpo         MEDIUMTEXT NOT NULL,
  tipo           ENUM('alerta_consolidacion','estado_pedido','reporte_huella','otro') NOT NULL,
  id_referencia  INT UNSIGNED NULL,
  estado         ENUM('pendiente','enviado','error') NOT NULL DEFAULT 'pendiente',
  intentos       TINYINT UNSIGNED NOT NULL DEFAULT 0,
  creado_en      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  enviado_en     DATETIME NULL,
  INDEX idx_correo_estado (estado, creado_en)
) ENGINE=InnoDB;

-- =====================================================================
-- 8. IMPORTACIÓN DE EXCEL DEL CLIENTE (hojas Formato A, B y C)
-- =====================================================================

CREATE TABLE importaciones (
  id_importacion INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_usuario     INT UNSIGNED NULL,
  archivo        VARCHAR(200) NOT NULL,
  formato        ENUM('A','B','C') NOT NULL,     -- hoja del Excel; cada una con sus reglas de validación
  hoja           VARCHAR(60) NULL,
  filas_total    INT UNSIGNED NOT NULL DEFAULT 0,
  filas_ok       INT UNSIGNED NOT NULL DEFAULT 0,
  filas_error    INT UNSIGNED NOT NULL DEFAULT 0,
  estado         ENUM('cargando','validada','aplicada','rechazada') NOT NULL DEFAULT 'cargando',
  creada_en      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE importacion_filas (
  id_fila        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_importacion INT UNSIGNED NOT NULL,
  num_fila       INT UNSIGNED NOT NULL,
  datos_originales JSON NOT NULL,                -- columnas del Formato C tal cual
  valida         BOOLEAN NOT NULL DEFAULT FALSE,
  errores        JSON NULL,
  FOREIGN KEY (id_importacion) REFERENCES importaciones(id_importacion) ON DELETE CASCADE,
  INDEX idx_imp_fila (id_importacion, valida)
) ENGINE=InnoDB;

-- =====================================================================
-- 9. KPIs: línea base, metas y fotos periódicas (Check del PDCA)
-- =====================================================================

CREATE TABLE kpis (
  id_kpi         TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  codigo         VARCHAR(40) NOT NULL UNIQUE,
  nombre         VARCHAR(100) NOT NULL,
  unidad         VARCHAR(20) NOT NULL,
  linea_base     DECIMAL(10,3) NULL,
  linea_base_min DECIMAL(10,3) NULL,             -- el cliente da rangos (ej. 20-40 t CO₂e/año)
  linea_base_max DECIMAL(10,3) NULL,
  meta_12_meses  DECIMAL(10,3) NULL,
  meta_reduccion_pct DECIMAL(5,2) NULL,          -- ej. -15% de emisiones
  meta_anio_2    DECIMAL(10,3) NULL,
  mayor_es_mejor BOOLEAN NOT NULL
) ENGINE=InnoDB;

CREATE TABLE kpi_mediciones (
  id_medicion    BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_kpi         TINYINT UNSIGNED NOT NULL,
  periodo_inicio DATE NOT NULL,
  periodo_fin    DATE NOT NULL,
  alcance        ENUM('piloto','expansion','total') NOT NULL DEFAULT 'piloto',
  valor          DECIMAL(12,3) NOT NULL,
  calculado_en   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_kpi_periodo (id_kpi, periodo_inicio, periodo_fin, alcance),
  FOREIGN KEY (id_kpi) REFERENCES kpis(id_kpi)
) ENGINE=InnoDB;

-- =====================================================================
-- 10. VISTAS (insumo para dashboards)
-- =====================================================================

-- Formato A: totales de embalaje y % de plástico por pedido
CREATE VIEW vw_embalaje_pedido AS
SELECT p.id_pedido, p.codigo,
       p.peso_producto_kg,
       SUM(pe.peso_kg) AS peso_embalaje_kg,
       SUM(CASE WHEN m.tipo = 'plastico_no_biodegradable' THEN pe.peso_kg ELSE 0 END) AS peso_plastico_kg,
       ROUND(100 * SUM(CASE WHEN m.tipo = 'plastico_no_biodegradable' THEN pe.peso_kg ELSE 0 END)
             / NULLIF(SUM(pe.peso_kg), 0), 1) AS pct_plastico,
       p.peso_producto_kg + SUM(pe.peso_kg) AS peso_total_kg
FROM pedidos p
LEFT JOIN pedido_embalaje pe ON pe.id_pedido = p.id_pedido
LEFT JOIN materiales_embalaje m ON m.id_material = pe.id_material
GROUP BY p.id_pedido, p.codigo, p.peso_producto_kg;

-- KPIs del tramo 2: llenado, km y CO2 por pedido
CREATE VIEW vw_kpi_viajes AS
SELECT v.id_viaje, v.codigo, v.tramo, v.salida_real,
       v.llenado_pct, v.km_totales, v.num_pedidos,
       h.litros_estimados, h.co2_kg, h.co2_kg_por_pedido,
       ROUND(v.km_totales / NULLIF(v.num_pedidos, 0), 2) AS km_por_pedido
FROM viajes v
LEFT JOIN huella_viaje h ON h.id_viaje = v.id_viaje
WHERE v.estado = 'finalizado';

-- % de pedidos consolidados (viaje con más de un pedido del mismo cliente/destino)
CREATE VIEW vw_pedidos_consolidados AS
SELECT DATE_FORMAT(v.salida_real, '%Y-%m') AS mes,
       COUNT(DISTINCT et.id_pedido) AS pedidos_total,
       COUNT(DISTINCT CASE WHEN v.num_pedidos > 1 THEN et.id_pedido END) AS pedidos_consolidados,
       ROUND(100 * COUNT(DISTINCT CASE WHEN v.num_pedidos > 1 THEN et.id_pedido END)
             / NULLIF(COUNT(DISTINCT et.id_pedido), 0), 1) AS pct_consolidado
FROM envio_tramos et
JOIN viajes v ON v.id_viaje = et.id_viaje
WHERE et.tramo = 2
GROUP BY mes;

-- Calidad del GPS: lecturas recibidas vs esperadas por viaje (meta ≥ 95%)
CREATE VIEW vw_calidad_gps AS
SELECT v.id_viaje, v.codigo,
       COUNT(g.id_posicion) AS lecturas_recibidas,
       FLOOR(TIMESTAMPDIFF(SECOND, v.salida_real, v.llegada_real) / 120) AS lecturas_esperadas,
       ROUND(100 * COUNT(g.id_posicion)
             / NULLIF(FLOOR(TIMESTAMPDIFF(SECOND, v.salida_real, v.llegada_real) / 120), 0), 1) AS pct_calidad
FROM viajes v
LEFT JOIN posiciones_gps g ON g.id_viaje = v.id_viaje
WHERE v.llegada_real IS NOT NULL
GROUP BY v.id_viaje, v.codigo, v.salida_real, v.llegada_real;

-- Pedidos pendientes de envío (insumo de catálogo y consolidación)
CREATE VIEW vw_pedidos_pendientes AS
SELECT p.id_pedido, p.codigo, p.id_empresa, p.id_locacion_destino,
       p.peso_producto_kg, p.fecha_limite_entrega, p.estado,
       DATEDIFF(p.fecha_limite_entrega, CURRENT_DATE) AS dias_para_limite
FROM pedidos p
WHERE p.estado IN ('registrado','listo_acopio','en_hub');

-- % de registros de transporte automáticos (meta ≥ 80%; fracaso < 50%)
CREATE VIEW vw_registros_automaticos AS
SELECT DATE_FORMAT(salida_real, '%Y-%m') AS mes,
       COUNT(*) AS viajes_total,
       SUM(origen_registro = 'gps') AS viajes_gps,
       ROUND(100 * SUM(origen_registro = 'gps') / COUNT(*), 1) AS pct_automatico
FROM viajes
WHERE salida_real IS NOT NULL
GROUP BY mes;

-- Validación del combustible estimado vs tickets (criterio: error ≤ 10%)
CREATE VIEW vw_validacion_combustible AS
SELECT v.codigo, h.litros_estimados, h.litros_reales, h.error_combustible_pct,
       (ABS(h.error_combustible_pct) <= 10) AS cumple
FROM huella_viaje h
JOIN viajes v ON v.id_viaje = h.id_viaje
WHERE h.litros_reales IS NOT NULL;

-- Llenado del piloto por pedido y por kilo (pocos viajes: ≈3 en 3 meses)
CREATE VIEW vw_llenado_piloto AS
SELECT DATE_FORMAT(v.salida_real, '%Y-%m') AS mes,
       COUNT(*) AS viajes,
       SUM(v.num_pedidos) AS pedidos,
       SUM(v.carga_kg) AS kg_transportados,
       ROUND(100 * SUM(v.carga_kg) / SUM(v.capacidad_kg), 2) AS llenado_ponderado_pct,
       ROUND(SUM(v.km_totales) / NULLIF(SUM(v.num_pedidos), 0), 2) AS km_por_pedido,
       ROUND(SUM(v.km_totales) / NULLIF(SUM(v.carga_kg), 0), 4) AS km_por_kg
FROM viajes v
JOIN unidades u ON u.id_unidad = v.id_unidad
WHERE v.tramo = 2 AND v.estado = 'finalizado' AND u.en_piloto = TRUE
GROUP BY mes;

-- =====================================================================
-- 11. DATOS INICIALES
-- =====================================================================

INSERT INTO roles (nombre, descripcion) VALUES
 ('administrador','Dashboard, factores de emisión y usuarios (MFA obligatorio)'),
 ('lider_proyecto','Aprueba metas, alcance y paso a expansión'),
 ('coordinador_logistico','Consolidación y planeación de viajes'),
 ('jefe_almacen','Captura Formato A en almacén CDMX'),
 ('operador','Confirma tipo de parada y motivo'),
 ('artesano','Consulta sus pedidos');

INSERT INTO tipos_unidad (nombre, combustible, capacidad_kg) VALUES ('Tractocamión','diesel',20000);

INSERT INTO factores_emision (combustible, kg_co2_por_litro, vigente_desde, fuente)
VALUES ('diesel', 2.6800, '2026-11-02', 'Valor inicial del proyecto (editable)');

INSERT INTO factores_consumo (id_tipo_unidad, litros_por_100km, vigente_desde)
VALUES (1, 35.00, '2026-11-02');

INSERT INTO categorias_producto (nombre) VALUES ('Textiles'), ('Cerámica');

INSERT INTO materiales_embalaje (nombre, tipo) VALUES
 ('Film stretch','plastico_no_biodegradable'),
 ('Plástico burbuja','plastico_no_biodegradable'),
 ('Cartón reciclado','reciclado'),
 ('Cartón corrugado','reciclado'),
 ('Papel kraft','biodegradable'),
 ('Bolsa compostable','biodegradable'),
 ('Papel honeycomb','biodegradable');

-- Alternativas al plástico
UPDATE materiales_embalaje SET es_alternativa_a = (SELECT id_material FROM (SELECT id_material FROM materiales_embalaje WHERE nombre='Film stretch') x)
 WHERE nombre IN ('Papel kraft','Bolsa compostable');
UPDATE materiales_embalaje SET es_alternativa_a = (SELECT id_material FROM (SELECT id_material FROM materiales_embalaje WHERE nombre='Plástico burbuja') x)
 WHERE nombre IN ('Cartón corrugado','Papel honeycomb');

INSERT INTO embalaje_recomendado (id_categoria, id_material)
SELECT c.id_categoria, m.id_material FROM categorias_producto c JOIN materiales_embalaje m
 ON (c.nombre='Textiles' AND m.nombre IN ('Papel kraft','Bolsa compostable'))
 OR (c.nombre='Cerámica' AND m.nombre IN ('Cartón corrugado','Papel honeycomb'));

INSERT INTO kpis (codigo, nombre, unidad, linea_base, linea_base_min, linea_base_max,
                  meta_12_meses, meta_reduccion_pct, meta_anio_2, mayor_es_mejor) VALUES
 ('co2e_t_anio','Toneladas de CO₂e al año','t',NULL,20,40,NULL,15,NULL,FALSE),
 ('co2_kg_pedido','kg de CO₂e por pedido','kg',NULL,1.9,3.7,NULL,15,NULL,FALSE),
 ('plastico_kg_pedido','kg de plástico por pedido','kg',1.25,NULL,NULL,0.75,NULL,0.40,FALSE),
 ('llenado_pct','Llenado de unidad','%',50,NULL,NULL,59,NULL,75,TRUE),
 ('consolidado_pct','% de pedidos consolidados','%',20,NULL,NULL,40,NULL,NULL,TRUE),
 ('viajes_largos_anio','Viajes largos CDMX → frontera al año','viajes',27,NULL,NULL,23,NULL,NULL,FALSE),
 ('km_pedido','km por pedido','km',NULL,NULL,NULL,NULL,NULL,NULL,FALSE),
 ('pct_biodegradable','% plástico vs. biodegradable','%',NULL,NULL,NULL,NULL,NULL,NULL,TRUE),
 ('registros_auto_pct','% de registros de transporte automáticos','%',NULL,NULL,NULL,80,NULL,NULL,TRUE);

-- =====================================================================
-- 12. LLAVES FORÁNEAS DIFERIDAS (tablas definidas antes de sus referencias)
-- =====================================================================
ALTER TABLE pedido_embalaje  ADD CONSTRAINT fk_pe_imp  FOREIGN KEY (id_importacion) REFERENCES importaciones(id_importacion) ON DELETE SET NULL;
ALTER TABLE viajes           ADD CONSTRAINT fk_vj_imp  FOREIGN KEY (id_importacion) REFERENCES importaciones(id_importacion) ON DELETE SET NULL;
ALTER TABLE envio_tramos     ADD CONSTRAINT fk_et_imp  FOREIGN KEY (id_importacion) REFERENCES importaciones(id_importacion) ON DELETE SET NULL;
ALTER TABLE movimientos_material ADD CONSTRAINT fk_mm_ped FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido) ON DELETE SET NULL;
