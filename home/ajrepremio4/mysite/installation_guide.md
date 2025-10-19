# 🎯 QuizPlatform - Guía de Instalación

## Descripción
Plataforma web de aprendizaje gamificado para crear y jugar quizzes interactivos en tiempo real. Inspirada en Kahoot, permite a profesores crear cuestionarios y a estudiantes participar desde sus dispositivos móviles.

## Características Principales

✅ **Autenticación Segura**
- Registro con verificación de correo electrónico
- Contraseñas con requisitos de seguridad
- Recuperación de contraseña por email
- Reenvío de código de verificación

✅ **Gestión de Quizzes**
- Creación y edición de cuestionarios
- Preguntas con 4 opciones de respuesta
- Soporte para imágenes y videos
- Tiempo configurable por pregunta
- Modo individual o grupal
- Quizzes públicos y privados
- Duplicación de quizzes

✅ **Interfaz de Juego**
- Unión mediante código PIN
- Timer visual con cuenta regresiva
- Puntuación basada en velocidad y precisión
- Ranking en tiempo real
- Resultados finales

✅ **Confirmaciones de Seguridad**
- Confirmación al guardar quizzes
- Confirmación al actualizar preguntas
- Confirmación al eliminar contenido

## Requisitos del Sistema

### Software Necesario
- Python 3.8 o superior
- MySQL 5.7 o superior (o MariaDB)
- pip (gestor de paquetes de Python)

### Dependencias de Python
```
Flask==2.3.0
Flask-Mail==0.9.1
PyMySQL==1.1.0
```

## Instalación Paso a Paso

### 1. Configurar la Base de Datos MySQL

```sql
-- Crear la base de datos
CREATE DATABASE quiz_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Crear un usuario (opcional pero recomendado)
CREATE USER 'quiz_user'@'localhost' IDENTIFIED BY 'tu_contraseña_segura';
GRANT ALL PRIVILEGES ON quiz_platform.* TO 'quiz_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Instalar Dependencias de Python

```bash
# Crear un entorno virtual (recomendado)
python -m venv venv

# Activar el entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install Flask==2.3.0
pip install Flask-Mail==0.9.1
pip install PyMySQL==1.1.0
```

### 3. Configurar el Servidor de Correo

Edita el archivo `app.py` y configura tus credenciales de correo:

```python
# Configuración de correo (líneas 14-18)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'tu_email@gmail.com'  # ⚠️ CAMBIAR
app.config['MAIL_PASSWORD'] = 'tu_contraseña_app'   # ⚠️ CAMBIAR
```

**Importante para Gmail:**
1. Activa la verificación en dos pasos en tu cuenta de Google
2. Genera una "Contraseña de aplicación" en https://myaccount.google.com/apppasswords
3. Usa esa contraseña en `MAIL_PASSWORD`

### 4. Configurar la Conexión a MySQL

Edita el archivo `app.py` en la sección de configuración de base de datos:

```python
# Configuración de base de datos (líneas 21-27)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'quiz_user',        # ⚠️ Tu usuario de MySQL
    'password': 'tu_contraseña', # ⚠️ Tu contraseña de MySQL
    'database': 'quiz_platform',
    'charset': 'utf8mb4'
}
```

### 5. Estructura de Carpetas

Organiza los archivos así:

```
quiz_platform/
│
├── app.py                      # Backend Flask
│
├── templates/                  # Plantillas HTML
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── forgot_password.html
│   ├── reset_password.html
│   ├── dashboard.html
│   ├── quiz_editor.html
│   ├── play.html
│   └── view_quiz.html
│
└── venv/                       # Entorno virtual (opcional)
```

### 6. Inicializar la Base de Datos

La aplicación creará automáticamente todas las tablas necesarias al iniciar por primera vez.

### 7. Ejecutar la Aplicación

```bash
# Asegúrate de estar en el directorio del proyecto
cd quiz_platform

# Activa el entorno virtual si lo usaste
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Ejecutar la aplicación
python app.py
```

La aplicación estará disponible en: `http://localhost:5000`

## Uso de la Plataforma

### Para Profesores:

1. **Registrarse**
   - Ir a `/register`
   - Seleccionar rol "Profesor"
   - Completar datos y contraseña segura
   - Verificar email con el código de 6 dígitos

2. **Crear un Quiz**
   - Iniciar sesión en `/login`
   - Click en "Crear Quiz"
   - Configurar título, descripción, modo y tiempo
   - Agregar preguntas con 4 opciones
   - Marcar la respuesta correcta
   - Guardar el quiz

3. **Compartir el Quiz**
   - Obtener el código PIN del quiz
   - Compartir el PIN con los estudiantes
   - O compartir el enlace directo

4. **Ver Resultados**
   - Los resultados se guardan automáticamente
   - Exportables a Excel (función a implementar)

### Para Estudiantes:

1. **Unirse a un Juego**
   - Ir a `/play`
   - Ingresar código PIN del quiz
   - Escribir nombre de usuario
   - Click en "Unirse al Juego"

2. **Jugar**
   - Leer cada pregunta
   - Seleccionar una opción (A, B, C o D)
   - Responder antes de que termine el tiempo
   - Ver retroalimentación inmediata

3. **Ver Resultados**
   - Al finalizar, ver puntuación total
   - Ver posición en el ranking
   - Comparar con otros jugadores

## Estructura de la Base de Datos

### Tablas Principales:

- **users**: Almacena usuarios (profesores y estudiantes)
- **quizzes**: Cuestionarios creados
- **questions**: Preguntas de cada quiz
- **options**: Opciones de respuesta (4 por pregunta)
- **game_sessions**: Sesiones de juego activas
- **participants**: Jugadores en cada sesión
- **answers**: Respuestas de los participantes

## Seguridad Implementada

✅ Contraseñas hasheadas con SHA-256
✅ Verificación de correo electrónico obligatoria
✅ Tokens seguros para recuperación de contraseña
✅ Validación de contraseñas robustas
✅ Protección contra inyección SQL (consultas parametrizadas)
✅ Sesiones seguras de Flask
✅ Confirmaciones para acciones críticas

## Requisitos de Contraseña

- Mínimo 8 caracteres
- Al menos una letra mayúscula
- Al menos una letra minúscula
- Al menos un número
- Al menos un carácter especial (!@#$%^&*...)

## Solución de Problemas

### Error de Conexión a MySQL
```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server...")
```
**Solución**: Verifica que MySQL esté ejecutándose y que las credenciales sean correctas.

### Error al Enviar Correos
```
SMTPAuthenticationError
```
**Solución**: 
- Para Gmail, usa una contraseña de aplicación
- Verifica que MAIL_USERNAME y MAIL_PASSWORD sean correctos
- Asegúrate de permitir aplicaciones menos seguras (si no usas contraseña de app)

### Las Tablas No Se Crean
**Solución**: 
- Ejecuta `python app.py` al menos una vez
- Verifica permisos del usuario en MySQL
- Revisa los logs en la consola

### Error 404 en Templates
```
TemplateNotFound
```
**Solución**: Asegúrate de que todos los archivos HTML estén en la carpeta `templates/`

## Mejoras Futuras Sugeridas

🔄 Exportación a Excel/Google Drive
🔄 Gráficos de rendimiento
🔄 Chat en tiempo real durante el juego
🔄 Modo batalla (1 vs 1)
🔄 Avatares personalizados
🔄 Sistema de logros y badges
🔄 Análisis de estadísticas avanzadas
🔄 Importación de quizzes desde CSV/Excel
🔄 API REST completa
🔄 WebSockets para actualización en tiempo real

## Licencia

Este proyecto es de código abierto y está disponible bajo licencia MIT.

## Soporte

Para problemas o preguntas:
1. Revisa esta guía
2. Verifica los logs en la consola
3. Asegúrate de que todas las dependencias estén instaladas

## Créditos

Desarrollado como plataforma educativa inspirada en metodologías de gamificación y M-Learning (Mobile Learning).

---

**¡Disfruta creando quizzes interactivos! 🎉📚🎮**