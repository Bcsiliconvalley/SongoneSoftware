import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import streamlit_authenticator as stauth
import os

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Song One Software", page_icon="🧵", layout="wide")

# --- VARIABLE PARA EL NOMBRE DEL LOGO ---
LOGO_FILENAME = "SongOneSoftwarelogo.jpeg"

# --- FUNCIONES DE LOS MÓDULOS (MODULARIZACIÓN) ---

def modulo_calculo_co2():
    st.header("Cálculo de Huella de Carbono en Tiempo Real")
    st.write("Calcula el CO2 desde el taller del artesano hasta el cliente final.")
    
    # Los inputs (controles) van en la barra lateral
    st.sidebar.subheader("Parámetros del Envío")
    origen = st.sidebar.selectbox("Origen (Taller Artesanal):", ["Oaxaca", "Puebla", "Chiapas"])
    destino = st.sidebar.selectbox("Destino (Cliente):", ["México", "EE.UU.", "Canadá"])
    peso = st.sidebar.number_input("Peso del Paquete (kg):", min_value=0.1, value=2.5)
    transporte = st.sidebar.selectbox("Medio de Transporte:", ["Terrestre (Camión)", "Aéreo (Avión)"])

    # Lógica de cálculo
    if transporte == "Terrestre (Camión)":
        factor_emision = 0.05 # kg CO2 por km por kg
        distancia_base = 1500 if destino == "México" else 3000 if destino == "EE.UU." else 5000
    else:
        factor_emision = 0.50 
        distancia_base = 1500 if destino == "México" else 3000 if destino == "EE.UU." else 5000

    total_co2 = distancia_base * peso * factor_emision
    
    # Resultados en el área principal
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Emisiones Totales Estimadas", value=f"{total_co2:.2f} kg CO2")
    with col2:
        st.info(f"Distancia estimada: {distancia_base} km")
        
    st.success("Nota: Debido a que no consolidamos pedidos, priorizamos rutas directas para garantizar la trazabilidad individual de cada artesano.")


def modulo_seguimiento_embalaje():
    st.header("Monitoreo de Embalaje")
    st.write("Rastrea la cantidad de plástico utilizado frente al material biodegradable.")
    
    st.sidebar.subheader("Datos del Embalaje")
    plastico_usado = st.sidebar.slider("Plástico usado (gramos):", 0, 500, 100)
    biodegradable_usado = st.sidebar.slider("Material biodegradable usado (gramos):", 0, 500, 300)
    
    peso_total = plastico_usado + biodegradable_usado
    
    if peso_total > 0:
        porcentaje_eco = (biodegradable_usado / peso_total) * 100
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Porcentaje Ecológico", value=f"{porcentaje_eco:.1f}%")
        with col2:
            st.write("Meta de la empresa: > 80%")
            
        st.subheader("Distribución de Materiales")
        datos_grafico = pd.DataFrame(
            {"Material": ["Plástico", "Biodegradable"], "Gramos": [plastico_usado, biodegradable_usado]}
        )
        st.bar_chart(datos_grafico.set_index("Material"))
        
        if porcentaje_eco < 50:
            st.error("Alerta: El uso de plástico supera al material biodegradable. Se recomienda cambiar de proveedor.")
        else:
            st.success("¡Buen trabajo! El empaque es mayoritariamente sostenible.")


def modulo_optimizacion_rutas():
    st.header("Optimización de Rutas (Envíos Directos)")
    st.write("Sugerencia de la ruta más corta y con menos contaminación **sin consolidar pedidos**.")
    
    # Mapa centrado en México
    m = folium.Map(location=[22.0, -100.0], zoom_start=4)
    
    # Coordenadas de las locaciones
    coords = {
        "Oaxaca": [17.0732, -96.7266],
        "Puebla": [19.0414, -98.2063],
        "Chiapas": [16.7569, -93.1292],
        "EE.UU. (Texas)": [29.7604, -95.3698],
        "Canadá (Toronto)": [43.6510, -79.3470],
        "México (CDMX)": [19.4326, -99.1332]
    }
    
    # Agregar marcadores al mapa
    for loc, coord in coords.items():
        folium.Marker(coord, popup=loc).add_to(m)
        
    # Dibujar una ruta directa de ejemplo (Oaxaca a EE.UU.)
    folium.PolyLine(
        locations=[coords["Oaxaca"], coords["EE.UU. (Texas)"]], 
        color="blue", weight=2.5, tooltip="Envío Directo"
    ).add_to(m)
    
    # Mostrar el mapa en Streamlit
    st_folium(m, width=1000, height=500)


# --- 1. SISTEMA DE LOGIN ---
credentials = {
    "usernames": {
        "jcarlos": {"name": "Juan Carlos", "password": "123"},
        "salvador": {"name": "Salvador", "password": "456"}
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "songone_dashboard",
    "auth_cookie",
    cookie_expiry_days=30
)

# El login se mantiene en el centro de la pantalla
authenticator.login(location='main')

# --- 2. APLICACIÓN PRINCIPAL (DASHBOARD) ---
if st.session_state.get("authentication_status"):
    name = st.session_state.get("name")

    # --- CONFIGURACIÓN DE LA BARRA LATERAL (SIDEBAR) ---
    with st.sidebar:
        if os.path.exists(LOGO_FILENAME):
            st.image(LOGO_FILENAME, use_container_width=True)
        else:
            st.warning("Logo no encontrado")
            
        st.title("Menú Principal")
        st.write(f"Bienvenido, **{name}**")
        st.divider()
        
        # Menú de navegación
        opcion = st.radio(
            "Selecciona un módulo:",
            ("🌍 1. Cálculo de CO2", "📦 2. Seguimiento de Embalaje", "🚚 3. Optimización de Rutas")
        )
        st.divider()
        
        # Botón de cerrar sesión
        authenticator.logout('Cerrar Sesión', location='sidebar')

    # --- ÁREA PRINCIPAL (CONTENIDO DINÁMICO) ---
    st.title("🧵 Song One Software")
    st.subheader("Textiles Carbono Neutral - Trazabilidad y Monitoreo")
    st.divider()

    # Lógica para mostrar el módulo seleccionado
    if opcion == "🌍 1. Cálculo de CO2":
        modulo_calculo_co2()
    elif opcion == "📦 2. Seguimiento de Embalaje":
        modulo_seguimiento_embalaje()
    elif opcion == "🚚 3. Optimización de Rutas":
        modulo_optimizacion_rutas()

elif st.session_state.get("authentication_status") is False:
    st.error('Usuario o contraseña incorrectos')
else:
    st.warning('Por favor, ingresa tu usuario y contraseña')