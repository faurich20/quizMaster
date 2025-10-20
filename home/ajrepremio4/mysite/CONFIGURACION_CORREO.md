# Configuración del Correo Electrónico

## Problema
El sistema no envía correos electrónicos porque las credenciales en `app.py` están con valores de ejemplo.

## Solución

### Paso 1: Obtener una Contraseña de Aplicación de Gmail

1. Ve a tu cuenta de Google: https://myaccount.google.com/
2. En el menú izquierdo, selecciona **Seguridad**
3. En "Cómo inicias sesión en Google", activa la **Verificación en dos pasos** (si no está activada)
4. Una vez activada, busca **Contraseñas de aplicaciones**
5. Selecciona la aplicación: **Correo**
6. Selecciona el dispositivo: **Otro (nombre personalizado)** → escribe "QuizPlatform"
7. Haz clic en **Generar**
8. Google te mostrará una contraseña de 16 caracteres (ejemplo: `abcd efgh ijkl mnop`)
9. **Copia esta contraseña** (sin espacios)

### Paso 2: Configurar en app.py

Abre el archivo `app.py` y busca las líneas 20-21:

```python
app.config['MAIL_USERNAME'] = 'tu_email@gmail.com'  # Configurar
app.config['MAIL_PASSWORD'] = 'tu_contraseña'  # Configurar
```

Reemplázalas con:

```python
app.config['MAIL_USERNAME'] = 'tu_correo_real@gmail.com'  # Tu correo de Gmail
app.config['MAIL_PASSWORD'] = 'abcdefghijklmnop'  # La contraseña de aplicación (sin espacios)
```

### Ejemplo:

```python
app.config['MAIL_USERNAME'] = 'miproyecto@gmail.com'
app.config['MAIL_PASSWORD'] = 'xyzw1234abcd5678'
```

### Paso 3: Reiniciar la aplicación

Después de hacer los cambios, reinicia tu servidor Flask para que los cambios surtan efecto.

## Verificación

Para verificar que el correo funciona:

1. Intenta registrar un nuevo usuario
2. Deberías recibir un correo con el código de verificación
3. Si no llega, revisa:
   - Carpeta de SPAM
   - Que la contraseña de aplicación esté correcta
   - Que no tenga espacios
   - Que el correo sea válido

## Notas Importantes

- **NUNCA** compartas tu contraseña de aplicación públicamente
- **NO** subas el archivo `app.py` con las credenciales a GitHub
- Considera usar variables de entorno para mayor seguridad:

```python
import os
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
```

## Alternativa: Usar otro servicio de correo

Si no quieres usar Gmail, puedes usar otros servicios como:

- **Outlook/Hotmail:**
  ```python
  app.config['MAIL_SERVER'] = 'smtp-mail.outlook.com'
  app.config['MAIL_PORT'] = 587
  ```

- **Yahoo:**
  ```python
  app.config['MAIL_SERVER'] = 'smtp.mail.yahoo.com'
  app.config['MAIL_PORT'] = 587
  ```
