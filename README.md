Iniciar: streamlit run app.py

---

## ⚠️ Nota Importante para el Equipo: Archivo `users.json`

Este proyecto utiliza el archivo **`users.json`** como base de datos local para gestionar el inicio de sesión, las contraseñas encriptadas y los roles (Administrador, Empleado, Artesano).

**Credenciales de prueba (por defecto):**
*   **Administrador:** Usuario: `jcarlos` | Contraseña: `123`
*   **Empleado:** Usuario: `salvador` | Contraseña: `456`

**¿Cómo probar el registro?**
En la pantalla de inicio de sesión, ve a la pestaña **"Registrarse"**. Puedes crear un usuario nuevo y seleccionar el rol de **"Artesano"**. Al hacerlo, notarás que el menú lateral se adapta y oculta las opciones administrativas (Facturas, Inventario y Configuración).

**Nota sobre el estado del archivo:**
Dado que este proyecto está desplegado en Streamlit Cloud y el archivo está en el repositorio, **si la app se reinicia, los usuarios nuevos que se registren podrían borrarse** y el archivo volverá a su estado original (con los dos usuarios de prueba). Esto es normal en esta versión de demostración. Si deseas guardar los usuarios de forma permanente, se recomienda no subir `users.json` al repositorio y usar variables de entorno o una base de datos externa en el futuro.

installation  requirements
pip install -r requirements.txt
 
