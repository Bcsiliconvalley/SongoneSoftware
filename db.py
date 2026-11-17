"""
Conexión a MySQL/MariaDB (base someone_somewhere) y funciones de acceso.

Configuración (en este orden de prioridad):
  1) .streamlit/secrets.toml  ->  [mysql] host, port, user, password, database
  2) variables de entorno     ->  DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
  3) valores por defecto      ->  localhost:3306, root, sin contraseña (XAMPP)
"""
import os
import secrets as pysecrets
import tomllib
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# ---------------------------------------------------------------------
# Conexión
# ---------------------------------------------------------------------
def _leer_toml():
    """Lee .streamlit/secrets.toml junto a este archivo (tolera BOM de Windows)."""
    ruta = Path(__file__).resolve().parent / ".streamlit" / "secrets.toml"
    if not ruta.exists():
        return None
    datos = ruta.read_bytes()
    if datos.startswith(b"\xef\xbb\xbf"):  # BOM que agrega el Bloc de notas / PowerShell 5
        datos = datos[3:]
    # Si el archivo está mal escrito, tomllib lanza el error y se muestra en la app.
    return tomllib.loads(datos.decode("utf-8"))


def _secrets_archivo():
    datos = _leer_toml()
    return datos.get("mysql") if datos else None


def _config_con_fuente():
    c = _secrets_archivo()
    if c:
        return dict(c), "archivo .streamlit/secrets.toml"
    try:
        return dict(st.secrets["mysql"]), "st.secrets"
    except Exception:
        pass
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "3306"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "someone_somewhere"),
    }, "valores por defecto (no se encontró secrets.toml)"


def _config():
    return _config_con_fuente()[0]


@st.cache_resource
def _clave_aleatoria():
    return pysecrets.token_hex(32)


def cookie_key():
    """
    Clave con la que se firma la cookie de sesión.
    Se toma de [auth] cookie_key en secrets.toml; si no existe se genera una aleatoria
    por arranque (las sesiones guardadas dejan de valer al reiniciar la app).
    """
    clave = None
    datos = _leer_toml()
    if datos:
        clave = (datos.get("auth") or {}).get("cookie_key")
    if not clave:
        try:
            clave = st.secrets["auth"]["cookie_key"]
        except Exception:
            clave = None
    return clave or _clave_aleatoria()


def describir_conexion():
    """Texto de diagnóstico (sin mostrar la contraseña)."""
    c, fuente = _config_con_fuente()
    return (f"Configuración leída de: {fuente} · host={c.get('host')} · puerto={c.get('port')} · "
            f"usuario={c.get('user')} · contraseña={'sí' if c.get('password') else 'NO'} · "
            f"base={c.get('database')}")


@st.cache_resource
def get_engine():
    c = _config()
    url = URL.create(
        "mysql+pymysql",
        username=c.get("user", "root"),
        password=c.get("password", ""),
        host=c.get("host", "localhost"),
        port=int(c.get("port", 3306)),
        database=c.get("database", "someone_somewhere"),
        query={"charset": "utf8mb4"},
    )
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600)


def consultar(sql, params=None) -> pd.DataFrame:
    """SELECT -> DataFrame. Usa parámetros nombrados (:nombre), nunca f-strings."""
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def ejecutar(sql, params=None):
    """INSERT/UPDATE/DELETE en una transacción."""
    with get_engine().begin() as conn:
        return conn.execute(text(sql), params or {})


# ---------------------------------------------------------------------
# Usuarios (tabla usuarios + roles). El "usuario" para iniciar sesión es el correo.
# ---------------------------------------------------------------------
def cargar_credenciales():
    """Arma el diccionario que espera streamlit_authenticator."""
    df = consultar(
        """
        SELECT u.correo, u.nombre_completo, u.password_hash, r.nombre AS rol
        FROM usuarios u
        JOIN roles r ON r.id_rol = u.id_rol
        WHERE u.activo = TRUE
        """
    )
    usuarios = {
        f["correo"]: {
            "name": f["nombre_completo"],
            "password": f["password_hash"],
            "email": f["correo"],
            "role": f["rol"],
        }
        for _, f in df.iterrows()
    }
    return {"usernames": usuarios}


def crear_usuario(nombre, correo, password_plano, rol="artesano"):
    hash_ = stauth.Hasher.hash(password_plano)
    sal = hash_[:29]  # bcrypt guarda la sal dentro del hash: $2b$12$<22 caracteres>
    ejecutar(
        """
        INSERT INTO usuarios (id_rol, nombre_completo, correo, password_hash, password_sal)
        VALUES ((SELECT id_rol FROM roles WHERE nombre = :rol), :nombre, :correo, :hash, :sal)
        """,
        {"rol": rol, "nombre": nombre, "correo": correo.strip().lower(), "hash": hash_, "sal": sal},
    )


def asegurar_usuarios_demo():
    """Si la tabla usuarios está vacía, crea dos cuentas de prueba."""
    total = int(consultar("SELECT COUNT(*) AS n FROM usuarios").iloc[0]["n"])
    if total == 0:
        crear_usuario("Juan Carlos", "jc@somewhere.com", "123", "administrador")
        crear_usuario("Salvador", "sal@somewhere.com", "456", "coordinador_logistico")


def id_usuario_por_correo(correo):
    df = consultar("SELECT id_usuario FROM usuarios WHERE correo = :c", {"c": correo})
    return None if df.empty else int(df.iloc[0]["id_usuario"])


# ---------------------------------------------------------------------
# Embalaje (Formato A)
# ---------------------------------------------------------------------
def registrar_embalaje(id_pedido, id_material, descripcion, peso_kg, id_usuario):
    """Inserta un renglón del Formato A y descuenta el material del almacén (hub)."""
    with get_engine().begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO pedido_embalaje
                  (id_pedido, id_material, descripcion, peso_kg, registrado_por, origen_registro)
                VALUES (:p, :m, :d, :w, :u, 'app')
                """
            ),
            {"p": id_pedido, "m": id_material, "d": descripcion or None, "w": peso_kg, "u": id_usuario},
        )
        hub = conn.execute(
            text("SELECT id_locacion FROM locaciones WHERE tipo = 'hub' ORDER BY id_locacion LIMIT 1")
        ).scalar()
        if hub:
            conn.execute(
                text(
                    """
                    INSERT INTO movimientos_material
                      (id_material, id_locacion, tipo, cantidad_kg, id_pedido, id_usuario)
                    VALUES (:m, :l, 'salida', :w, :p, :u)
                    """
                ),
                {"m": id_material, "l": hub, "w": peso_kg, "p": id_pedido, "u": id_usuario},
            )
            conn.execute(
                text(
                    """
                    UPDATE inventario_materiales
                    SET existencia_kg = GREATEST(existencia_kg - :w, 0)
                    WHERE id_material = :m AND id_locacion = :l
                    """
                ),
                {"w": peso_kg, "m": id_material, "l": hub},
            )


# ---------------------------------------------------------------------
# Factores de emisión (editables por el administrador, con historial)
# ---------------------------------------------------------------------
SQL_FACTOR_VIGENTE = """
    SELECT id_factor, kg_co2_por_litro, vigente_desde
    FROM factores_emision
    WHERE combustible = :c
      AND vigente_desde <= CURDATE()
      AND (vigente_hasta IS NULL OR vigente_hasta >= CURDATE())
    ORDER BY vigente_desde DESC
    LIMIT 1
"""


def factor_emision_vigente(combustible):
    df = consultar(SQL_FACTOR_VIGENTE, {"c": combustible})
    return None if df.empty else df.iloc[0]


def actualizar_factor_emision(combustible, nuevo_valor, motivo, id_usuario):
    """Cierra el factor vigente, crea el nuevo y registra quién y cuándo."""
    with get_engine().begin() as conn:
        vig = conn.execute(text(SQL_FACTOR_VIGENTE + " FOR UPDATE"), {"c": combustible}).mappings().first()
        anterior = float(vig["kg_co2_por_litro"]) if vig else None
        if anterior is not None and abs(anterior - nuevo_valor) < 1e-9:
            return False  # sin cambios

        if vig is not None and vig["vigente_desde"] >= date.today():
            # Factor creado hoy: se corrige en sitio para no dejar vigencias vacías.
            conn.execute(
                text("UPDATE factores_emision SET kg_co2_por_litro = :v, creado_por = :u WHERE id_factor = :i"),
                {"v": nuevo_valor, "u": id_usuario, "i": vig["id_factor"]},
            )
            id_factor = vig["id_factor"]
        else:
            if vig is not None:
                conn.execute(
                    text("UPDATE factores_emision SET vigente_hasta = CURDATE() - INTERVAL 1 DAY WHERE id_factor = :i"),
                    {"i": vig["id_factor"]},
                )
            res = conn.execute(
                text(
                    """
                    INSERT INTO factores_emision (combustible, kg_co2_por_litro, vigente_desde, fuente, creado_por)
                    VALUES (:c, :v, CURDATE(), :f, :u)
                    """
                ),
                {"c": combustible, "v": nuevo_valor, "f": motivo or "Actualización desde el dashboard", "u": id_usuario},
            )
            id_factor = res.lastrowid

        conn.execute(
            text(
                """
                INSERT INTO factores_historial
                  (tabla_factor, id_factor, valor_anterior, valor_nuevo, cambiado_por, motivo)
                VALUES ('factores_emision', :i, :a, :n, :u, :m)
                """
            ),
            {"i": id_factor, "a": anterior, "n": nuevo_valor, "u": id_usuario, "m": motivo or None},
        )
    return True
