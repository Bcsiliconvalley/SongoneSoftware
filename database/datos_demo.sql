-- =====================================================================
-- Datos de DEMOSTRACIÓN para el dashboard (ejecutar DESPUÉS de trazabilidad_huella.sql
-- y solo en una base recién creada: usa ids explícitos).
-- Los usuarios (jc@somewhere.com / 123 y sal@somewhere.com / 456) los crea app.py solo.
-- Todo es ficticio, basado en los ejemplos del PDCA.
-- =====================================================================
USE someone_somewhere;

INSERT INTO locaciones (id_locacion, codigo, nombre, tipo, pais, estado, ciudad, latitud, longitud) VALUES
 (1,'MX-OAX-001','Taller Oaxaca','taller','MX','Oaxaca','Oaxaca de Juárez',17.073200,-96.726600),
 (2,'MX-PUE-001','Taller Puebla','taller','MX','Puebla','Puebla',19.041400,-98.206300),
 (3,'MX-CHP-001','Taller Chiapas','taller','MX','Chiapas','Tuxtla Gutiérrez',16.756900,-93.129200),
 (4,'MX-CMX-001','Hub CDMX','hub','MX','CDMX','Ciudad de México',19.432600,-99.133200),
 (5,'US-LRD-001','Frontera Laredo','frontera','US','Texas','Laredo',27.503600,-99.507500),
 (6,'US-HOU-001','Cliente Houston','cliente_final','US','Texas','Houston',29.760400,-95.369800),
 (7,'CA-TOR-001','Cliente Toronto','cliente_final','CA','Ontario','Toronto',43.651000,-79.347000);

INSERT INTO empresas (id_empresa, nombre, tipo, pais) VALUES
 (1,'Someone Somewhere','propia','MX'),
 (2,'Boutique Texas','cliente','US'),
 (3,'Exportadora Canadá','cliente','CA');

INSERT INTO artesanos (id_artesano, id_locacion, nombre, en_piloto) VALUES
 (1,1,'Taller Hermanos Cruz',TRUE),
 (2,2,'Tejidos Mendoza',FALSE),
 (3,3,'Textiles Tzotzil',FALSE);

-- categorías: 1 = Textiles, 2 = Cerámica
INSERT INTO productos (id_producto, id_artesano, id_categoria, nombre, peso_unitario_kg) VALUES
 (1,1,1,'Blusa Bordada Oaxaca',0.400),
 (2,2,1,'Tapete Lana Puebla',4.500),
 (3,3,1,'Camisa Lino Chiapas',0.500),
 (4,1,2,'Jarrón de barro negro',2.000);

INSERT INTO inventario_productos (id_producto, id_locacion, piezas_disponibles) VALUES
 (1,1,12),(2,2,5),(3,3,0),(4,1,8);

-- materiales: 1 Film stretch, 2 Plástico burbuja, 3 Cartón reciclado, 4 Cartón corrugado,
--             5 Papel kraft, 6 Bolsa compostable, 7 Papel honeycomb
INSERT INTO inventario_materiales (id_material, id_locacion, existencia_kg) VALUES
 (1,4,80),(2,4,40),(3,4,150),(4,4,200),(5,4,120.5),(6,4,60),(7,4,75);

INSERT INTO unidades (id_unidad, codigo, id_tipo_unidad, placas, odometro_km, en_piloto) VALUES
 (1,'ECO-014',1,'ABC-123-A',246212.0,TRUE),
 (2,'ECO-015',1,'DEF-456-B',120350.0,FALSE);

INSERT INTO operadores (id_operador, nombre, telefono, licencia) VALUES
 (1,'Operador Demo','555-000-0001','LIC-DEMO-001');

INSERT INTO pedidos (id_pedido, codigo, id_empresa, id_artesano, id_locacion_destino, peso_producto_kg, fecha_pedido, fecha_limite_entrega, estado) VALUES
 (1,'PED-00121',2,1,6,20.00,'2026-11-02 10:00:00','2026-11-30','listo_acopio'),
 (2,'PED-00122',3,2,7,22.50,'2026-11-03 11:30:00','2026-12-05','registrado'),
 (3,'PED-00123',2,3,6,18.00,'2026-11-04 09:15:00','2026-11-28','en_hub'),
 (4,'PED-00124',2,1,6,24.00,'2026-11-05 16:00:00','2026-12-01','en_transito'),
 (5,'PED-00125',2,1,6,20.00,'2026-10-20 12:00:00','2026-11-05','entregado');

INSERT INTO pedido_productos (id_pedido, id_producto, cantidad) VALUES
 (1,1,50),(2,2,5),(3,3,36),(4,4,12),(5,1,50);

INSERT INTO pedido_embalaje (id_pedido, id_material, descripcion, peso_kg, origen_registro) VALUES
 (5,3,'Cartón reciclado (5 cajas)',1.500,'app'),
 (5,5,'Papel kraft',0.500,'app'),
 (5,1,'Film stretch',1.000,'app'),
 (1,3,'Cartón reciclado',1.200,'app'),
 (1,5,'Papel kraft',0.800,'app'),
 (2,3,'Cartón reciclado',1.500,'app'),
 (2,6,'Bolsa compostable',0.400,'app'),
 (3,4,'Cartón corrugado',1.600,'app'),
 (3,7,'Papel honeycomb',0.600,'app'),
 (3,2,'Plástico burbuja',0.300,'app'),
 (4,4,'Cartón corrugado',1.800,'app'),
 (4,7,'Papel honeycomb',0.700,'app');

INSERT INTO viajes (id_viaje, codigo, tramo, id_unidad, id_operador, id_locacion_origen, id_locacion_destino,
                    capacidad_kg, carga_kg, num_pedidos, km_planeados, salida_real, llegada_real,
                    odometro_salida, odometro_llegada, costo_total_mxn, num_paradas, hubo_cambio_ruta,
                    hubo_falla, estado) VALUES
 (1,'VJ-2026-0041',2,1,1,4,5,20000,10000,400,1200,'2026-10-24 06:00:00','2026-10-25 05:30:00',
    245000,246212,18700,3,TRUE,TRUE,'finalizado'),
 (2,'VJ-2026-0042',2,2,1,4,5,20000,6000,240,1200,'2026-11-09 06:00:00',NULL,
    120350,NULL,NULL,0,FALSE,FALSE,'en_curso');

INSERT INTO paradas_viaje (id_viaje, tipo, motivo, detectada_por_gps, confirmada, inicio, fin,
                           odometro_inicio, odometro_fin, km_adicionales, litros_adicionales_est) VALUES
 (1,'desvio','Cambio de llanta',TRUE,TRUE,'2026-10-24 15:10:00','2026-10-24 16:00:00',245600,245612,12,4.00);

INSERT INTO envio_tramos (codigo_envio, id_pedido, tramo, id_viaje, id_locacion_origen, id_locacion_destino,
                          peso_total_kg, distancia_km, paradas, costo_asignado_mxn, fecha_salida, fecha_llegada) VALUES
 ('SS-2026-00125',5,2,1,4,5,23.00,1212,3,46.75,'2026-10-24 06:00:00','2026-10-25 05:30:00'),
 ('SS-2026-00124',4,2,2,4,5,26.50,NULL,0,NULL,'2026-11-09 06:00:00',NULL);

-- 1212 km x 35 L/100 km = 424.2 L; x 2.68 = 1,136.86 kg CO2; / 400 pedidos = 2.842 kg
INSERT INTO huella_viaje (id_viaje, id_factor_emision, id_factor_consumo, km_considerados,
                          litros_estimados, litros_reales, co2_kg, co2_kg_por_pedido) VALUES
 (1,1,1,1212,424.20,431.00,1136.86,2.842);

INSERT INTO posiciones_gps (id_unidad, id_viaje, latitud, longitud, hora_gps) VALUES
 (2,2,19.432600,-99.133200,'2026-11-09 06:00:00'),
 (2,2,20.588800,-100.389900,'2026-11-09 09:30:00'),
 (2,2,22.156500,-100.985500,'2026-11-09 13:00:00');
