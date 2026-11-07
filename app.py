import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import streamlit_authenticator as stauth
import os
import json

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Someone Somewhere - Equipo 1", page_icon="🧵", layout="wide")

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
USERS_FILE = "users.json"

# --- FUNCIÓN PARA MANEJAR USUARIOS (JSON) ---
def cargar_usuarios():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    else:
        default_credentials = {
            "usernames": {
                "jcarlos": {"name": "Juan Carlos", "password": stauth.Hasher.hash("123"), "email": "jc@somewhere.com", "role": "Administrador"},
                "salvador": {"name": "Salvador", "password": stauth.Hasher.hash("456"), "email": "sal@somewhere.com", "role": "Empleado"}
            }
        }
        with open(USERS_FILE, "w") as f:
            json.dump(default_credentials, f)
        return default_credentials

credentials = cargar_usuarios()

# ==========================================
# --- FUNCIONES DE LOS MÓDULOS (SAMPLES) ---
# ==========================================
def modulo_panel_general():
    st.subheader("📊 Panel General")
    st.write("Resumen del rendimiento de sostenibilidad y operativo de la empresa.")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Envíos Monitoreados", "1,245", "+12%")
    col2.metric("Huella Promedio", "4.2 kg CO2", "-5%")
    col3.metric("Empaques Eco", "82%", "+8%")
    col4.metric("Ingresos (Mes)", "$45,200", "+15%")
    st.divider()
    st.markdown("### 📋 Órdenes Recientes de Clientes")
    datos_ordenes = {
        "ID Orden": ["ORD-1024", "ORD-1025", "ORD-1026", "ORD-1027", "ORD-1028"],
        "Cliente": ["Boutique CDMX", "John Doe (Texas)", "Artesanías del Sur", "María López", "Exportadora Canadá"],
        "Producto": ["Huipil Bordado", "Tapete Lana", "Blusa de Seda", "Textil Personalizado", "Camisa Lino"],
        "Fecha": ["2024-05-18", "2024-05-18", "2024-05-17", "2024-05-17", "2024-05-16"],
        "Estado": ["🟡 Pendiente", "🔵 Enviado", "🟢 Entregado", "🟢 Pagado", "🔵 Enviado"],
        "Total": ["$1,500.00", "$2,800.00", "$3,200.00", "$850.00", "$4,500.00"]
    }
    st.dataframe(pd.DataFrame(datos_ordenes), use_container_width=True)

def modulo_facturacion():
    st.subheader("🧾 Facturas y Cotizaciones")
    tab_cot, tab_fac = st.tabs(["📝 Generar Documento", "📋 Historial"])
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
            st.download_button("📥 Descargar archivo", data=f"Cliente: {cliente}\nTotal: {total}", file_name="documento.txt")
    with tab_fac:
        st.markdown("### Historial de Documentos Recientes")
        historial = {"Fecha": ["2023-10-25", "2023-10-26", "2023-10-27"],"Tipo": ["Factura", "Cotización", "Factura"],"Cliente": ["Artesanías del Sur", "Boutique CDMX", "Exportadora Texas"],"Total": ["$15,000.00", "$8,500.00", "$32,000.00"],"Estado": ["🟢 Pagada", "🟡 Pendiente", "🟢 Pagada"]}
        st.dataframe(pd.DataFrame(historial), use_container_width=True)

def modulo_inventario():
    st.subheader("📦 Gestión de Inventario")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Productos", "4")
    col2.metric("Stock Bajo", "1", "-2", delta_color="inverse")
    col3.metric("Valor del Inventario", "$125,000")
    st.divider()
    st.markdown("### Editar Tabla de Inventario")
    inventario_data = {"ID": ["P-001", "P-002", "P-003", "P-004"],"Producto": ["Blusa Bordada Oaxaca", "Tapete Lana Puebla", "Camisa Lino Chiapas", "Caja Biodegradable"],"Categoría": ["Ropa", "Decoración", "Ropa", "Empaque"],"Stock": [12, 5, 0, 150],"Precio ($)": [1200.0, 2500.0, 1800.0, 25.0]}
    st.data_editor(pd.DataFrame(inventario_data), use_container_width=True, num_rows="dynamic")

def modulo_calculo_co2():
    st.subheader("🌍 Cálculo de Huella de Carbono en Tiempo Real")
    col1, col2 = st.columns(2)
    with col1:
        origen = st.selectbox("Origen (Taller Artesanal):", ["Oaxaca", "Puebla", "Chiapas"])
        peso = st.number_input("Peso del Paquete (kg):", min_value=0.1, value=2.5)
    with col2:
        destino = st.selectbox("Destino (Cliente):", ["México", "EE.UU.", "Canadá"])
        transporte = st.selectbox("Medio de Transporte:", ["Terrestre (Camión)", "Aéreo (Avión)"])
    factor_emision = 0.05 if transporte == "Terrestre (Camión)" else 0.50
    distancia_base = 1500 if destino == "México" else 3000 if destino == "EE.UU." else 5000
    total_co2 = distancia_base * peso * factor_emision
    st.divider()
    col_res1, col_res2 = st.columns(2)
    col_res1.metric(label="Emisiones Totales Estimadas", value=f"{total_co2:.2f} kg CO2")
    col_res2.info(f"Distancia estimada: {distancia_base} km")
    st.success("Nota: Envío directo para garantizar la trazabilidad individual de cada artesano.")

def modulo_seguimiento_embalaje():
    st.subheader("📦 Monitoreo de Embalaje")
    col1, col2 = st.columns(2)
    plastico_usado = col1.slider("Plástico usado (gramos):", 0, 500, 100)
    biodegradable_usado = col2.slider("Material biodegradable usado (gramos):", 0, 500, 300)
    peso_total = plastico_usado + biodegradable_usado
    if peso_total > 0:
        porcentaje_eco = (biodegradable_usado / peso_total) * 100
        st.divider()
        col_res1, col_res2 = st.columns(2)
        col_res1.metric("Porcentaje Ecológico", f"{porcentaje_eco:.1f}%")
        col_res2.write("Meta de la empresa: > 80%")
        st.bar_chart(pd.DataFrame({"Material": ["Plástico", "Biodegradable"], "Gramos": [plastico_usado, biodegradable_usado]}).set_index("Material"))
        if porcentaje_eco < 50: st.error("Alerta: El uso de plástico supera al material biodegradable.")
        else: st.success("¡Buen trabajo! El empaque es mayoritariamente sostenible.")

def modulo_optimizacion_rutas():
    st.subheader("🚚 Optimización de Rutas (Envíos Directos)")
    m = folium.Map(location=[22.0, -100.0], zoom_start=4, tiles="CartoDB dark_matter")
    coords = {"Oaxaca": [17.0732, -96.7266], "Puebla": [19.0414, -98.2063], "Chiapas": [16.7569, -93.1292],"EE.UU. (Texas)": [29.7604, -95.3698], "Canadá (Toronto)": [43.6510, -79.3470], "México (CDMX)": [19.4326, -99.1332]}
    for loc, coord in coords.items(): folium.Marker(coord, popup=loc).add_to(m)
    folium.PolyLine(locations=[coords["Oaxaca"], coords["EE.UU. (Texas)"]], color="#007AFF", weight=3, tooltip="Envío Directo").add_to(m)
    st_folium(m, width=1000, height=500)

def modulo_configuracion():
    st.subheader("⚙️ Configuración del Sistema")
    st.text_input("Nombre de la Empresa", value="Someone Somewhere (Equipo 1)", disabled=True)
    st.text_input("Correo de Contacto", value="admin@somewhere.com")
    st.toggle("Recibir alertas de altas emisiones de CO2", value=True)
    st.toggle("Recibir reportes semanales de empaques", value=True)
    if st.button("Guardar Cambios"): st.success("Configuración guardada exitosamente.")

# --- 1. SISTEMA DE LOGIN Y REGISTRO ---
authenticator = stauth.Authenticate(credentials, "someone_dashboard", "auth_cookie", cookie_expiry_days=30)
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
                st.info(f"💡 Coloca tu logo aquí con el nombre: {LOGO_FILENAME}")
                
        st.markdown("<h1 style='text-align: center; color: #FFFFFF;'>Someone Somewhere</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #8B949E;'>Equipo 1 - Capacitación</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6E7681;'>Textiles Carbono Neutral<br>Trazabilidad y Monitoreo</p>", unsafe_allow_html=True)

    with col_der:
        st.markdown("### Acceso al Sistema")
        tab_login, tab_registro = st.tabs(["🔐 Ingresar", "📝 Registrarse"])
        
        with tab_login:
            authenticator.login(location='main')
            if authentication_status is False:
                st.error('Usuario o contraseña incorrectos')
            elif authentication_status is None:
                st.warning('Ingresa tus credenciales')

        with tab_registro:
            with st.form("registro_form"):
                nuevo_nombre = st.text_input("Nombre Completo:")
                nuevo_usuario = st.text_input("Usuario:")
                nueva_password = st.text_input("Contraseña:", type="password")
                nuevo_rol = st.selectbox("Rol:", ["Artesano", "Empleado", "Administrador"])
                btn_registro = st.form_submit_button("Crear Cuenta")
                
                if btn_registro:
                    if not nuevo_nombre or not nuevo_usuario or not nueva_password:
                        st.error("Llena todos los campos.")
                    elif nuevo_usuario in credentials['usernames']:
                        st.error("Usuario ya en uso.")
                    else:
                        credentials['usernames'][nuevo_usuario] = {"name": nuevo_nombre, "password": stauth.Hasher.hash(nueva_password), "email": "", "role": nuevo_rol}
                        with open(USERS_FILE, "w") as f: json.dump(credentials, f)
                        st.success(f"¡Cuenta creada para {nuevo_nombre}!")

elif authentication_status:
    name = st.session_state.get("name")
    username = st.session_state.get("username")
    user_role = credentials['usernames'][username].get('role', 'Empleado')

    with st.sidebar:
        if os.path.exists(LOGO_FILENAME): st.image(LOGO_FILENAME, use_container_width=True)
        else: st.warning("Logo no encontrado")
        st.title("Menú Principal")
        st.write(f"Bienvenido, **{name}**")
        st.write(f"Rol: **{user_role}**")
        st.divider()
        
        # ==========================================
        # REORGANIZACIÓN DEL MENÚ POR PRIORIDAD
        # ==========================================
        opciones_menu = ["📊 Panel General"]
        
        # Agregamos Facturación e Inventario justo después del panel (solo para no-artesanos)
        if user_role != "Artesano":
            opciones_menu.append("🧾 Facturas y Cotizaciones")
            opciones_menu.append("📦 Gestión de Inventario")
            
        # Agregamos los módulos operativos
        opciones_menu.extend([
            "🌍 Cálculo de CO2", 
            "📦 Seguimiento de Embalaje", 
            "🚚 Optimización de Rutas"
        ])
        
        # Configuración al final
        if user_role != "Artesano":
            opciones_menu.append("⚙️ Configuración")
        
        opcion = st.radio("Selecciona un módulo:", opciones_menu, label_visibility="collapsed")
        st.divider()
        authenticator.logout('Cerrar Sesión', location='sidebar')

    st.title("🧵 Someone Somewhere")
    st.subheader(f"Equipo 1 - Trazabilidad y Monitoreo ({user_role})")
    st.divider()

    # Renderizado de la opción seleccionada
    if opcion == "📊 Panel General": modulo_panel_general()
    elif opcion == "🧾 Facturas y Cotizaciones": modulo_facturacion()
    elif opcion == "📦 Gestión de Inventario": modulo_inventario()
    elif opcion == "🌍 Cálculo de CO2": modulo_calculo_co2()
    elif opcion == "📦 Seguimiento de Embalaje": modulo_seguimiento_embalaje()
    elif opcion == "🚚 Optimización de Rutas": modulo_optimizacion_rutas()
    elif opcion == "⚙️ Configuración": modulo_configuracion()