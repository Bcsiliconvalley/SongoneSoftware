import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import LoginError
import os
from urllib.parse import quote

from db import (
    consultar,
    ejecutar,
    cargar_credenciales,
    crear_usuario,
    asegurar_usuarios_demo,
    describir_conexion,
    cookie_key,
    id_usuario_por_correo,
    registrar_embalaje,
    factor_emision_vigente,
    actualizar_factor_emision,
)


ICONOS = {
    "camisa": '<path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23z"/>',
    "panel": '<path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>',
    "factura": '<path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"/><path d="M12 17.5v-11"/>',
    "paquete": '<path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',
    "globo": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    "camion": '<path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M15 18H9"/><path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14"/><circle cx="17" cy="18" r="2"/><circle cx="7" cy="18" r="2"/>',
    "config": '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
    "portapapeles": '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/>',
    "archivo": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    "candado": '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "usuario_mas": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M19 8v6"/><path d="M22 11h-6"/>',
}


def svg_html(nombre, size=20, color="currentColor"):
    """SVG en línea para usar dentro de HTML/markdown."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'style="vertical-align:-0.15em;flex-shrink:0">{ICONOS[nombre]}</svg>'
    )


def encabezado(nombre, texto, nivel=3):
    """Reemplazo de st.subheader / st.title / '### ' con icono SVG."""
    tamanos = {1: 36, 2: 30, 3: 24, 4: 20}
    st.markdown(
        f'<h{nivel} style="display:flex;align-items:center;gap:0.5rem;margin:0;padding:0.5rem 0">'
        f'{svg_html(nombre, tamanos.get(nivel, 20))}<span>{texto}</span></h{nivel}>',
        unsafe_allow_html=True,
    )


def _svg_data_uri(nombre):
    s = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f'{ICONOS[nombre]}</svg>'
    )
    return "data:image/svg+xml;utf8," + quote(s, safe="")


def inyectar_iconos(selector, nombres):
    """
    Pone un icono SVG (como máscara, hereda el color del texto) antes de cada
    elemento que coincida con `selector`, en orden. Sirve para tabs y radios,
    cuyas etiquetas no aceptan HTML.
    """
    reglas = (
        f"{selector}::before {{ content: ''; display: inline-block; flex-shrink: 0; "
        "width: 1.15em; height: 1.15em; margin-right: 10px; align-self: center; "
        "background-color: currentColor; "
        "-webkit-mask-repeat: no-repeat; mask-repeat: no-repeat; "
        "-webkit-mask-position: center; mask-position: center; "
        "-webkit-mask-size: contain; mask-size: contain; }\n"
    )
    for i, nombre in enumerate(nombres, start=1):
        uri = _svg_data_uri(nombre)
        reglas += (
            f"{selector}:nth-of-type({i})::before "
            f'{{ -webkit-mask-image: url("{uri}"); mask-image: url("{uri}"); }}\n'
        )
    st.markdown(f"<style>{reglas}</style>", unsafe_allow_html=True)


SELECTOR_TABS = 'div[role="tablist"] > button[data-baseweb="tab"]'
SELECTOR_MENU = '[data-testid="stSidebar"] div[role="radiogroup"] > label'

# --- Favicon SVG (page_icon acepta una ruta a archivo) ---
FAVICON = "favicon.svg"
if not os.path.exists(FAVICON):
    with open(FAVICON, "w", encoding="utf-8") as f:
        f.write(svg_html("camisa", 64, "#007AFF"))

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Someone Somewhere - Equipo 1", page_icon=FAVICON, layout="wide")

# --- CSS PERSONALIZADO (DARK MODE / BLACK THEME) ---
st.markdown("""
<style>
    /* 1. Fondo principal oscuro */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* 2. Sidebar oscuro */
    [data-testid="stSidebar"] {
        background-color: #161B22 !important;
        border-right: 1px solid #30363D;
    }
    
    /* Ocultar circulos del menú lateral y dar estilo a los botones */
    [data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child { 
        display: none !important; width: 0 !important; margin: 0 !important; 
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label { 
        background-color: transparent; 
        border-radius: 6px; 
        padding: 10px 15px; 
        margin-bottom: 2px; 
        cursor: pointer; 
        border-left: 4px solid transparent; 
        width: 100%; 
        transition: all 0.2s ease; 
        color: #C9D1D9 !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover { 
        background-color: rgba(255, 255, 255, 0.05); 
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] { 
        background-color: rgba(0, 122, 255, 0.15) !important; 
        border-left: 4px solid #007AFF !important; 
        font-weight: bold; 
        color: #FFFFFF !important;
    }

    /* 3. Estilo de la tarjeta de login en la derecha */
    div[data-testid="stVerticalBlock"] > div:has(div.stTabs) {
        background-color: #161B22;
        padding: 2.5rem 2rem;
        border-radius: 12px;
        border: 1px solid #30363D;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
    }

    /* 4. Ajustes de textos y títulos */
    h1, h2, h3, h4, h5, p, span, div {
        color: #FAFAFA;
    }
    
    /* 5. Inputs y Selectbox oscuros */
    div[data-baseweb="input"] input, 
    div[data-baseweb="select"] > div {
        background-color: #0D1117 !important;
        color: #FAFAFA !important;
        border: 1px solid #30363D !important;
    }
    
    /* 6. Pestañas de Login (Tabs) */
    button[data-baseweb="tab"] {
        color: #8B949E !important;
        background-color: transparent !important;
    }
    button[aria-selected="true"] {
        color: #FFFFFF !important;
        border-bottom-color: #007AFF !important;
    }
</style>
""", unsafe_allow_html=True)

# --- VARIABLE PARA EL NOMBRE DEL LOGO ---
LOGO_FILENAME = "SomeoneSomewhereLogo.jpeg"

# --- USUARIOS DESDE MYSQL (el "usuario" para entrar es el correo) ---
try:
    asegurar_usuarios_demo()
    credentials = cargar_credenciales()
except Exception as e:
    st.error(
        "No se pudo conectar con la base de datos. Revisa que MySQL esté encendido, "
        "que hayas importado trazabilidad_huella.sql y los datos de .streamlit/secrets.toml."
    )
    st.code(str(e))
    try:
        st.caption(describir_conexion())
    except Exception as e2:
        st.caption(f"No se pudo leer secrets.toml: {e2}")
    st.stop()

STOCK_BAJO = 5  # piezas; por debajo o igual se considera "stock bajo"


# --- COLOR DE ESTADOS EN TABLAS (las tablas no admiten SVG, se usa color de texto) ---
def color_estado(valor):
    if "Pendiente" in valor:
        return "color: #E3B341; font-weight: 600"
    if "Enviado" in valor:
        return "color: #58A6FF; font-weight: 600"
    if "Entregado" in valor or "Pagad" in valor:
        return "color: #3FB950; font-weight: 600"
    return ""

def estilo_estado(df):
    estilo = df.style
    aplicar = getattr(estilo, "map", None) or estilo.applymap
    return aplicar(color_estado, subset=["Estado"])

def _fmt(valor, formato="{:,.1f}", vacio="—"):
    """Formatea un número que puede venir vacío (NULL) desde la base."""
    return vacio if pd.isna(valor) else formato.format(valor)

# ==========================================
# --- FUNCIONES DE LOS MÓDULOS ---
# ==========================================
def modulo_panel_general():
    encabezado("panel", "Panel General")
    st.write("Resumen del rendimiento de sostenibilidad y operativo de la empresa.")

    k = consultar("""
        SELECT
          (SELECT COUNT(DISTINCT id_pedido) FROM envio_tramos) AS envios,
          (SELECT AVG(co2_kg_por_pedido) FROM huella_viaje) AS huella,
          (SELECT 100 * (1 - SUM(CASE WHEN m.tipo = 'plastico_no_biodegradable' THEN pe.peso_kg ELSE 0 END)
                             / NULLIF(SUM(pe.peso_kg), 0))
             FROM pedido_embalaje pe
             JOIN materiales_embalaje m ON m.id_material = pe.id_material) AS eco,
          (SELECT COUNT(*) FROM pedidos
            WHERE fecha_pedido >= DATE_SUB(CURDATE(), INTERVAL DAYOFMONTH(CURDATE()) - 1 DAY)) AS pedidos_mes
    """).iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Envíos Monitoreados", _fmt(k["envios"], "{:,.0f}"))
    col2.metric("Huella Promedio", _fmt(k["huella"], "{:.2f} kg CO2e / pedido"))
    col3.metric("Empaques sin plástico", _fmt(k["eco"], "{:.0f}%"))
    col4.metric("Pedidos (mes)", _fmt(k["pedidos_mes"], "{:,.0f}"))
    st.divider()

    encabezado("portapapeles", "Órdenes Recientes de Clientes")
    ordenes = consultar("""
        SELECT p.codigo AS `ID Orden`,
               e.nombre AS Cliente,
               (SELECT GROUP_CONCAT(pr.nombre SEPARATOR ', ')
                  FROM pedido_productos pp
                  JOIN productos pr ON pr.id_producto = pp.id_producto
                 WHERE pp.id_pedido = p.id_pedido) AS Producto,
               DATE(p.fecha_pedido) AS Fecha,
               CASE p.estado
                    WHEN 'entregado'   THEN 'Entregado'
                    WHEN 'en_transito' THEN 'Enviado'
                    WHEN 'cancelado'   THEN 'Cancelado'
                    ELSE 'Pendiente'
               END AS Estado,
               p.peso_producto_kg AS `Peso (kg)`
        FROM pedidos p
        JOIN empresas e ON e.id_empresa = p.id_empresa
        ORDER BY p.fecha_pedido DESC
        LIMIT 10
    """)
    if ordenes.empty:
        st.info("Todavía no hay pedidos registrados.")
    else:
        ordenes["Fecha"] = ordenes["Fecha"].astype(str)
        st.dataframe(estilo_estado(ordenes), use_container_width=True)

def modulo_facturacion():
    # Nota: el esquema de trazabilidad no tiene tablas de facturas ni cotizaciones,
    # por eso este módulo sigue siendo demostrativo (no guarda nada en MySQL).
    encabezado("factura", "Facturas y Cotizaciones")
    inyectar_iconos(SELECTOR_TABS, ["archivo", "portapapeles"])
    tab_cot, tab_fac = st.tabs(["Generar Documento", "Historial"])
    with tab_cot:
        col1, col2 = st.columns(2)
        cliente = col1.text_input("Nombre del Cliente / Empresa", "Boutique CDMX")
        documento = col2.selectbox("Tipo de Documento:", ["Cotización", "Factura"])
        producto = st.selectbox("Producto:", ["Huipil Bordado Oaxaca", "Tapete Lana Puebla", "Blusa Seda Chiapas"])
        c1, c2, c3 = st.columns(3)
        cantidad = c1.number_input("Cantidad:", min_value=1, value=2)
        precio_unitario = c2.number_input("Precio Unitario ($):", min_value=0.0, value=1500.0)
        impuesto_pct = c3.number_input("IVA (%):", min_value=0.0, value=16.0)
        subtotal = cantidad * precio_unitario
        impuesto = subtotal * (impuesto_pct / 100)
        total = subtotal + impuesto
        st.divider()
        st.markdown(f"**Subtotal:** ${subtotal:,.2f} | **IVA:** ${impuesto:,.2f} | **Total:** ${total:,.2f}")
        if st.button("Generar Documento"):
            st.success(f"{documento} generada correctamente para {cliente}.")
            st.download_button("Descargar archivo", data=f"Cliente: {cliente}\nTotal: {total}", file_name="documento.txt")
    with tab_fac:
        encabezado("portapapeles", "Historial de Documentos Recientes")
        historial = {"Fecha": ["2023-10-25", "2023-10-26", "2023-10-27"],"Tipo": ["Factura", "Cotización", "Factura"],"Cliente": ["Artesanías del Sur", "Boutique CDMX", "Exportadora Texas"],"Total": ["$15,000.00", "$8,500.00", "$32,000.00"],"Estado": ["Pagada", "Pendiente", "Pagada"]}
        st.dataframe(estilo_estado(pd.DataFrame(historial)), use_container_width=True)

def modulo_inventario():
    encabezado("paquete", "Gestión de Inventario")
    df = consultar("""
        SELECT i.id_producto, i.id_locacion,
               p.nombre AS Producto, c.nombre AS Categoría, l.nombre AS Locación,
               i.piezas_disponibles AS Stock
        FROM inventario_productos i
        JOIN productos p ON p.id_producto = i.id_producto
        JOIN categorias_producto c ON c.id_categoria = p.id_categoria
        JOIN locaciones l ON l.id_locacion = i.id_locacion
        WHERE p.activo = TRUE
        ORDER BY p.nombre
    """)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Productos", f"{len(df)}")
    col2.metric("Stock Bajo", f"{int((df['Stock'] <= STOCK_BAJO).sum()) if not df.empty else 0}",
                help=f"Productos con {STOCK_BAJO} piezas o menos")
    col3.metric("Piezas Disponibles", f"{int(df['Stock'].sum()) if not df.empty else 0:,}")
    st.divider()

    st.markdown("### Editar Stock de Productos")
    if df.empty:
        st.info("No hay productos en inventario.")
    else:
        editado = st.data_editor(
            df,
            use_container_width=True,
            num_rows="fixed",
            key="editor_inventario",
            disabled=["Producto", "Categoría", "Locación"],
            column_config={
                "id_producto": None,
                "id_locacion": None,
                "Stock": st.column_config.NumberColumn("Stock", min_value=0, step=1),
            },
        )
        if st.button("Guardar cambios de stock"):
            cambios = editado[editado["Stock"] != df["Stock"]]
            for _, f in cambios.iterrows():
                ejecutar(
                    "UPDATE inventario_productos SET piezas_disponibles = :s "
                    "WHERE id_producto = :p AND id_locacion = :l",
                    {"s": int(f["Stock"]), "p": int(f["id_producto"]), "l": int(f["id_locacion"])},
                )
            st.success(f"{len(cambios)} registro(s) actualizado(s).")
            st.rerun()

    st.divider()
    st.markdown("### Materiales de Embalaje")
    mats = consultar("""
        SELECT m.nombre AS Material, m.tipo AS Tipo, l.nombre AS Locación,
               i.existencia_kg AS `Existencia (kg)`
        FROM inventario_materiales i
        JOIN materiales_embalaje m ON m.id_material = i.id_material
        JOIN locaciones l ON l.id_locacion = i.id_locacion
        ORDER BY m.nombre
    """)
    st.dataframe(mats, use_container_width=True)

def modulo_calculo_co2():
    encabezado("globo", "Cálculo de Huella de Carbono en Tiempo Real")
    st.caption("Método: alcance 1 por flota propia (GHG Protocol + ISO 14083). "
               "Litros = km × consumo por tipo de unidad; CO₂ = litros × factor del combustible.")

    unidades = consultar("SELECT id_tipo_unidad, nombre, combustible FROM tipos_unidad ORDER BY nombre")
    if unidades.empty:
        st.warning("No hay tipos de unidad registrados.")
        return

    col1, col2 = st.columns(2)
    with col1:
        tipo = st.selectbox("Tipo de unidad:", unidades["nombre"])
        km = st.number_input("Distancia del viaje (km):", min_value=1.0, value=1212.0)
    with col2:
        pedidos = st.number_input("Pedidos en el viaje:", min_value=1, value=400)

    fila = unidades[unidades["nombre"] == tipo].iloc[0]
    fe = factor_emision_vigente(fila["combustible"])
    fc = consultar(
        """
        SELECT litros_por_100km FROM factores_consumo
        WHERE id_tipo_unidad = :t
          AND vigente_desde <= CURDATE()
          AND (vigente_hasta IS NULL OR vigente_hasta >= CURDATE())
        ORDER BY vigente_desde DESC LIMIT 1
        """,
        {"t": int(fila["id_tipo_unidad"])},
    )
    if fe is None or fc.empty:
        st.error("Falta un factor de emisión o de consumo vigente para este tipo de unidad.")
        return

    kg_co2_litro = float(fe["kg_co2_por_litro"])
    l_100km = float(fc.iloc[0]["litros_por_100km"])
    litros = km * l_100km / 100
    co2 = litros * kg_co2_litro

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Combustible estimado", f"{litros:,.1f} L")
    c2.metric("Emisiones Totales Estimadas", f"{co2:,.1f} kg CO2")
    c3.metric("Por pedido", f"{co2 / pedidos:.2f} kg CO2")
    st.info(f"Factores vigentes: {l_100km:g} L/100 km · {kg_co2_litro:g} kg CO₂ por litro de {fila['combustible']}.")

    st.divider()
    encabezado("portapapeles", "Últimos viajes calculados", nivel=4)
    hist = consultar("""
        SELECT v.codigo AS Viaje, v.salida_real AS Salida, h.km_considerados AS Km,
               h.litros_estimados AS `Litros est.`, h.litros_reales AS `Litros ticket`,
               h.co2_kg AS `CO2 (kg)`, h.co2_kg_por_pedido AS `CO2 por pedido`
        FROM huella_viaje h
        JOIN viajes v ON v.id_viaje = h.id_viaje
        ORDER BY v.salida_real DESC
        LIMIT 10
    """)
    if hist.empty:
        st.caption("Aún no hay viajes con huella calculada.")
    else:
        hist["Salida"] = hist["Salida"].astype(str)
        st.dataframe(hist, use_container_width=True)

def modulo_seguimiento_embalaje():
    encabezado("paquete", "Monitoreo de Embalaje")

    # "Ecológico" = todo lo que no es plástico no biodegradable (reciclado + biodegradable).
    g = consultar("""
        SELECT AVG(peso_plastico_kg) AS plastico_prom, AVG(100 - pct_plastico) AS eco_prom
        FROM vw_embalaje_pedido
        WHERE peso_embalaje_kg IS NOT NULL
    """).iloc[0]
    m1, m2 = st.columns(2)
    m1.metric("Plástico promedio por pedido", _fmt(g["plastico_prom"], "{:.2f} kg"),
              help="Línea base 1.25 kg · meta a 12 meses 0.75 kg")
    m2.metric("Embalaje sin plástico (promedio)", _fmt(g["eco_prom"], "{:.1f}%"),
              help="Meta de la empresa: > 80%")
    st.divider()

    pedidos = consultar("SELECT id_pedido, codigo FROM pedidos ORDER BY fecha_pedido DESC LIMIT 200")
    if pedidos.empty:
        st.info("No hay pedidos registrados.")
        return
    codigo = st.selectbox("Pedido:", pedidos["codigo"])
    id_pedido = int(pedidos.loc[pedidos["codigo"] == codigo, "id_pedido"].iloc[0])

    lineas = consultar(
        """
        SELECT m.nombre AS Material, m.tipo AS Tipo, pe.peso_kg AS `Peso (kg)`,
               pe.origen_registro AS Origen, pe.registrado_en AS Registrado
        FROM pedido_embalaje pe
        JOIN materiales_embalaje m ON m.id_material = pe.id_material
        WHERE pe.id_pedido = :p
        ORDER BY pe.registrado_en
        """,
        {"p": id_pedido},
    )
    if lineas.empty:
        st.warning("Este pedido todavía no tiene embalaje registrado (Formato A).")
    else:
        resumen = consultar("SELECT * FROM vw_embalaje_pedido WHERE id_pedido = :p", {"p": id_pedido}).iloc[0]
        pct_eco = 100 - float(resumen["pct_plastico"])
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric("Porcentaje Ecológico", f"{pct_eco:.1f}%")
        col_res2.metric("Peso de embalaje", f"{float(resumen['peso_embalaje_kg']):.2f} kg")
        col_res3.metric("Peso total (producto + embalaje)", f"{float(resumen['peso_total_kg']):.2f} kg")
        lineas["Registrado"] = lineas["Registrado"].astype(str)
        st.dataframe(lineas, use_container_width=True)
        st.bar_chart(lineas.groupby("Tipo")["Peso (kg)"].sum())
        if pct_eco < 50:
            st.error("Alerta: El uso de plástico supera al material sin plástico.")
        else:
            st.success("¡Buen trabajo! El empaque es mayoritariamente sostenible.")

    st.divider()
    encabezado("portapapeles", "Registrar material (Formato A)", nivel=4)
    mats = consultar("SELECT id_material, nombre, tipo FROM materiales_embalaje WHERE activo = TRUE ORDER BY nombre")
    with st.form("form_embalaje", clear_on_submit=True):
        f1, f2 = st.columns(2)
        nombre_mat = f1.selectbox("Material:", mats["nombre"])
        peso = f2.number_input("Peso (kg):", min_value=0.001, value=0.5, step=0.1, format="%.3f")
        desc = st.text_input("Descripción (opcional):")
        if st.form_submit_button("Agregar renglón"):
            id_mat = int(mats.loc[mats["nombre"] == nombre_mat, "id_material"].iloc[0])
            uid = id_usuario_por_correo(st.session_state.get("username"))
            registrar_embalaje(id_pedido, id_mat, desc, peso, uid)
            st.success("Renglón registrado y material descontado del almacén.")
            st.rerun()

def modulo_optimizacion_rutas():
    encabezado("camion", "Optimización de Rutas")
    locs = consultar("""
        SELECT codigo, nombre, tipo, latitud, longitud
        FROM locaciones
        WHERE latitud IS NOT NULL AND longitud IS NOT NULL
    """)
    if locs.empty:
        st.info("No hay locaciones con coordenadas.")
        return

    m = folium.Map(location=[22.0, -100.0], zoom_start=4, tiles="CartoDB dark_matter")
    colores = {"taller": "green", "hub": "blue", "frontera": "orange", "cliente_final": "red"}
    for _, f in locs.iterrows():
        folium.Marker(
            [float(f["latitud"]), float(f["longitud"])],
            popup=f"{f['nombre']} ({f['codigo']})",
            icon=folium.Icon(color=colores.get(f["tipo"], "gray")),
        ).add_to(m)

    viajes = consultar("""
        SELECT v.codigo AS Viaje, u.codigo AS Unidad, v.tramo AS Tramo, v.estado AS Estado,
               v.llenado_pct AS `Llenado %`, v.km_totales AS Km, v.num_pedidos AS Pedidos,
               lo.latitud AS lat_o, lo.longitud AS lon_o, ld.latitud AS lat_d, ld.longitud AS lon_d
        FROM viajes v
        JOIN unidades u ON u.id_unidad = v.id_unidad
        JOIN locaciones lo ON lo.id_locacion = v.id_locacion_origen
        JOIN locaciones ld ON ld.id_locacion = v.id_locacion_destino
        ORDER BY v.id_viaje DESC
        LIMIT 20
    """)
    for _, v in viajes.dropna(subset=["lat_o", "lon_o", "lat_d", "lon_d"]).iterrows():
        folium.PolyLine(
            locations=[[float(v["lat_o"]), float(v["lon_o"])], [float(v["lat_d"]), float(v["lon_d"])]],
            color="#E3B341" if v["Estado"] == "en_curso" else "#007AFF",
            weight=3,
            tooltip=f"{v['Viaje']} ({v['Estado']})",
        ).add_to(m)

    # Última posición GPS de cada unidad
    gps = consultar("""
        SELECT u.codigo, g.latitud, g.longitud, g.hora_gps
        FROM posiciones_gps g
        JOIN unidades u ON u.id_unidad = g.id_unidad
        WHERE g.hora_gps = (SELECT MAX(g2.hora_gps) FROM posiciones_gps g2 WHERE g2.id_unidad = g.id_unidad)
    """)
    for _, p in gps.iterrows():
        folium.CircleMarker(
            [float(p["latitud"]), float(p["longitud"])],
            radius=8, color="#3FB950", fill=True, fill_opacity=0.9,
            tooltip=f"{p['codigo']} · {p['hora_gps']}",
        ).add_to(m)

    st_folium(m, width=1000, height=500)

    if not viajes.empty:
        st.markdown("### Viajes recientes")
        st.dataframe(viajes[["Viaje", "Unidad", "Tramo", "Estado", "Llenado %", "Km", "Pedidos"]],
                     use_container_width=True)

def modulo_configuracion(user_role):
    encabezado("config", "Configuración del Sistema")
    st.text_input("Nombre de la Empresa", value="Someone Somewhere (Equipo 1)", disabled=True)
    st.text_input("Correo de Contacto", value="admin@somewhere.com")
    st.toggle("Recibir alertas de altas emisiones de CO2", value=True)
    st.toggle("Recibir reportes semanales de empaques", value=True)
    if st.button("Guardar Cambios"): st.success("Configuración guardada exitosamente.")

    # Factores de emisión: solo el administrador, con vigencia y registro de cambios
    if user_role == "administrador":
        st.divider()
        encabezado("globo", "Factores de Emisión", nivel=4)
        st.dataframe(consultar("""
            SELECT combustible AS Combustible, kg_co2_por_litro AS `kg CO2 / litro`,
                   vigente_desde AS Desde, vigente_hasta AS Hasta, fuente AS Fuente
            FROM factores_emision ORDER BY vigente_desde DESC
        """).fillna("vigente").astype({"Desde": str, "Hasta": str}), use_container_width=True)

        vig = factor_emision_vigente("diesel")
        actual = float(vig["kg_co2_por_litro"]) if vig is not None else 2.68
        nuevo = st.number_input("Nuevo factor para diésel (kg CO₂ por litro):",
                                min_value=0.0, value=actual, step=0.01, format="%.4f")
        motivo = st.text_input("Motivo del cambio:")
        if st.button("Actualizar factor"):
            uid = id_usuario_por_correo(st.session_state.get("username"))
            if actualizar_factor_emision("diesel", float(nuevo), motivo, uid):
                st.success("Factor actualizado y registrado en el historial.")
                st.rerun()
            else:
                st.info("El valor es igual al vigente; no hubo cambios.")

# --- 1. SISTEMA DE LOGIN Y REGISTRO ---
# Cookie nueva: ignora las sesiones guardadas con los usuarios anteriores (users.json)
authenticator = stauth.Authenticate(credentials, "someone_dashboard_mysql", cookie_key(), cookie_expiry_days=30)

# Si el navegador trae una cookie de sesión de un usuario que ya no existe en la base,
# se ignora (sin borrarla): borrarla desde aquí provocaba recargas en bucle.
_get_cookie_original = authenticator.cookie_controller.get_cookie
def _get_cookie_valida():
    token = _get_cookie_original()
    if token and token.get("username") not in credentials["usernames"]:
        return None
    return token
authenticator.cookie_controller.get_cookie = _get_cookie_valida

authentication_status = st.session_state.get("authentication_status")

if authentication_status is None or authentication_status is False:
    st.write("")
    st.write("")

    col_izq, col_der = st.columns([1.5, 1], gap="large")
    
    with col_izq:
        st.write("")
        st.write("")
        _, centro_logo, _ = st.columns([1, 1.5, 1])
        with centro_logo:
            if os.path.exists(LOGO_FILENAME):
                st.image(LOGO_FILENAME, use_container_width=True)
            else:
                st.info(f"Coloca tu logo aquí con el nombre: {LOGO_FILENAME}")
                
        st.markdown("<h1 style='text-align: center; color: #FFFFFF;'>Someone Somewhere</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #8B949E;'>Equipo 1 - Capacitación</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6E7681;'>Textiles Carbono Neutral<br>Trazabilidad y Monitoreo</p>", unsafe_allow_html=True)

    with col_der:
        st.markdown("### Acceso al Sistema")
        inyectar_iconos(SELECTOR_TABS, ["candado", "usuario_mas"])
        tab_login, tab_registro = st.tabs(["Ingresar", "Registrarse"])
        
        with tab_login:
            try:
                authenticator.login(location='main')
            except LoginError as e:
                st.warning(f"No se pudo iniciar sesión: {e}")
            if authentication_status is False:
                st.error('Usuario o contraseña incorrectos')
            elif authentication_status is None:
                st.warning('Ingresa tu correo y contraseña')

        with tab_registro:
            # El registro público solo crea cuentas de artesano; los demás roles
            # los asigna un administrador directamente en la tabla usuarios.
            with st.form("registro_form"):
                nuevo_nombre = st.text_input("Nombre Completo:")
                nuevo_correo = st.text_input("Correo (será tu usuario):")
                nueva_password = st.text_input("Contraseña:", type="password")
                btn_registro = st.form_submit_button("Crear Cuenta")
                
                if btn_registro:
                    correo = nuevo_correo.strip().lower()
                    if not nuevo_nombre or not correo or not nueva_password:
                        st.error("Llena todos los campos.")
                    elif "@" not in correo:
                        st.error("Escribe un correo válido.")
                    elif correo in credentials['usernames']:
                        st.error("Ese correo ya está registrado.")
                    else:
                        crear_usuario(nuevo_nombre, correo, nueva_password, "artesano")
                        st.success(f"¡Cuenta creada para {nuevo_nombre}! Ya puedes ingresar.")

elif authentication_status:
    name = st.session_state.get("name")
    username = st.session_state.get("username")
    user_role = credentials['usernames'][username].get('role', 'operador')
    rol_visible = user_role.replace("_", " ").title()

    # ==========================================
    # REORGANIZACIÓN DEL MENÚ POR PRIORIDAD
    # Cada opción es (texto, icono SVG)
    # ==========================================
    opciones_menu = [("Panel General", "panel")]

    # Facturación e Inventario justo después del panel (solo para no-artesanos)
    if user_role != "artesano":
        opciones_menu.append(("Facturas y Cotizaciones", "factura"))
        opciones_menu.append(("Gestión de Inventario", "paquete"))

    # Módulos operativos
    opciones_menu.extend([
        ("Cálculo de CO2", "globo"),
        ("Seguimiento de Embalaje", "paquete"),
        ("Optimización de Rutas", "camion"),
    ])

    # Configuración al final
    if user_role != "artesano":
        opciones_menu.append(("Configuración", "config"))

    etiquetas_menu = [texto for texto, _ in opciones_menu]

    with st.sidebar:
        if os.path.exists(LOGO_FILENAME): st.image(LOGO_FILENAME, use_container_width=True)
        else: st.warning("Logo no encontrado")
        st.title("Menú Principal")
        st.write(f"Bienvenido, **{name}**")
        st.write(f"Rol: **{rol_visible}**")
        st.divider()
        opcion = st.radio("Selecciona un módulo:", etiquetas_menu, label_visibility="collapsed")
        st.divider()
        authenticator.logout('Cerrar Sesión', location='sidebar')

    # Iconos SVG del menú lateral (en el mismo orden que las opciones)
    inyectar_iconos(SELECTOR_MENU, [icono for _, icono in opciones_menu])

    encabezado("camisa", "Someone Somewhere", nivel=1)
    st.subheader(f"Equipo 1 - Trazabilidad y Monitoreo ({rol_visible})")
    st.divider()

    # Renderizado de la opción seleccionada
    if opcion == "Panel General": modulo_panel_general()
    elif opcion == "Facturas y Cotizaciones": modulo_facturacion()
    elif opcion == "Gestión de Inventario": modulo_inventario()
    elif opcion == "Cálculo de CO2": modulo_calculo_co2()
    elif opcion == "Seguimiento de Embalaje": modulo_seguimiento_embalaje()
    elif opcion == "Optimización de Rutas": modulo_optimizacion_rutas()
    elif opcion == "Configuración": modulo_configuracion(user_role)
