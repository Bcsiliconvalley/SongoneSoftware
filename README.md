# SongOne Software – Dashboard "Someone Somewhere" (Gestión de proyectos)

Dashboard de trazabilidad de huella de carbono y embalaje para una empresa de artesanías.
Hecho con Streamlit y conectado a una base de datos MySQL/MariaDB (`someone_somewhere`).

**Iniciar:** `python -m streamlit run app.py`

## Requisitos
- Python 3.11 o superior
- MySQL 5.7+ o MariaDB 10.2+ (por ejemplo MAMP o XAMPP)

## Puesta en marcha (local)
1. **Base de datos.** En phpMyAdmin, sin seleccionar ninguna base, ve a *Importar* y carga en este orden:
   1. `database/trazabilidad_huella.sql` – crea la base `someone_somewhere` y sus tablas (si ya existía, la borra)
   2. `database/datos_demo.sql` – datos de ejemplo (opcional)
2. **Configuración.** Copia `.streamlit/secrets.toml.ejemplo` como `.streamlit/secrets.toml` y ajusta el usuario, la contraseña y el puerto de tu MySQL. Cambia también `cookie_key` por una cadena aleatoria:
   ```
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
3. **Dependencias:** `pip install -r requirements.txt`
4. **Ejecutar:** `python -m streamlit run app.py`

## Despliegue en Streamlit Cloud
Streamlit Cloud **no puede conectarse a un MySQL que corre en tu computadora** (MAMP, XAMPP).
Para desplegar necesitas una base MySQL accesible por internet. Cuando la tengas:
1. Importa en ella los dos scripts de `database/`.
2. En Streamlit Cloud abre *Settings → Secrets* y pega el contenido de `secrets.toml.ejemplo` con los datos reales (host, puerto, usuario, contraseña y `cookie_key`).

Nunca subas `secrets.toml` al repositorio.

## Usuarios de prueba
Si la tabla `usuarios` está vacía, la app crea al abrir:

| Usuario (correo) | Contraseña | Rol |
|---|---|---|
| jc@somewhere.com | 123 | administrador |
| sal@somewhere.com | 456 | coordinador_logistico |

**Cambia o elimina estas cuentas antes de usar la app con datos reales.**
Las contraseñas se guardan con bcrypt. El usuario para entrar es el correo.

En la pestaña **Registrarse** se crean cuentas con rol `artesano`, que no ve Facturas, Inventario ni Configuración.
Los demás roles se asignan directamente en la tabla `usuarios`.

## Estructura
```
app.py                      Interfaz (Streamlit)
db.py                       Conexión y consultas a MySQL
database/                   Esquema y datos demo
.streamlit/secrets.toml     Configuración local (no se sube a GitHub)
```

## Notas
- Facturas y Cotizaciones es un módulo demostrativo: no guarda datos en la base.
- Antes los usuarios se guardaban en `users.json`; ese archivo ya no se usa.
