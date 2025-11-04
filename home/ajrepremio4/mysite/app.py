# app.py
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_mail import Mail, Message
import io
import pymysql
import hashlib
import secrets
import string
import re
from datetime import datetime, timedelta
from functools import wraps
import json
from db import obtener_conexion as obtener_conexion_db
import pandas as pd

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Configuración de correo 
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ajrepremio4@gmail.com'  # Tu correo de Gmail
app.config['MAIL_PASSWORD'] = 'elpmdftpncxzgsca'  # ⚠️ Contraseña de aplicación SIN ESPACIOS (16 caracteres)
mail = Mail(app)

def obtener_bd():
    # Usar cursores tipo diccionario por defecto para respuestas consistentes
    return obtener_conexion_db(con_dict=True)


def validar_contrasena(contrasena):
    """Valida que la contraseña sea segura"""
    if len(contrasena) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    if not re.search(r'[A-Z]', contrasena):
        return False, "La contraseña debe contener al menos una mayúscula"
    if not re.search(r'[a-z]', contrasena):
        return False, "La contraseña debe contener al menos una minúscula"
    if not re.search(r'[0-9]', contrasena):
        return False, "La contraseña debe contener al menos un número"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', contrasena):
        return False, "La contraseña debe contener al menos un carácter especial"
    return True, "Contraseña válida"

def generar_codigo_verificacion():
    """Genera un código de verificación de 6 dígitos"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))

def generar_pin():
    """Genera un PIN único para el quiz"""
    return ''.join(secrets.choice(string.digits + string.ascii_uppercase) for _ in range(8))

def enviar_correo_verificacion(correo, codigo):
    """Envía correo de verificación"""
    try:
        mensaje = Message('Verificación de cuenta - QuizPlatform',
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[correo])
        mensaje.body = f'''
        Bienvenido a QuizPlatform!
        
        Tu código de verificación es: {codigo}
        
        Este código expirará en 15 minutos.
        
        Si no solicitaste esta verificación, ignora este correo.
        '''
        mail.send(mensaje)
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return False

def enviar_correo_recuperacion(correo, token):
    """Envía correo de recuperación de contraseña"""
    try:
        url_restablecer = url_for('restablecer_contrasena', token=token, _external=True)
        mensaje = Message('Recuperación de contraseña - QuizPlatform',
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[correo])
        mensaje.body = f'''
        Has solicitado recuperar tu contraseña.
        
        Haz clic en el siguiente enlace para restablecer tu contraseña:
        {url_restablecer}
        
        Este enlace expirará en 1 hora.
        
        Si no solicitaste esto, ignora este correo.
        '''
        mail.send(mensaje)
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return False

def requiere_sesion(f):
    @wraps(f)
    def funcion_decorada(*args, **kwargs):
        if 'id_usuario' not in session:
            return redirect(url_for('iniciar_sesion'))
        return f(*args, **kwargs)
    return funcion_decorada

def requiere_docente(f):
    @wraps(f)
    def funcion_decorada(*args, **kwargs):
        if 'id_usuario' not in session or not session.get('es_profesor'):
            return jsonify({'error': 'Acceso denegado'}), 403
        return f(*args, **kwargs)
    return funcion_decorada

@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/jugar')
@app.route('/jugar/')
def jugar():
    return render_template('jugar.html')

@app.route('/sala_espera')
def sala_espera():
    return render_template('sala_espera.html')

@app.route('/seleccion_grupo')
def seleccion_grupo():
    return render_template('seleccion_grupo.html')

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        datos = request.json
        print(f"Datos recibidos: {datos}")  # ← Esto te mostrará exactamente qué está llegando
        # Estandarizar nombres a snake_case
        nombre_usuario = datos.get('nombre_usuario')
        correo = datos.get('correo')
        contrasena = datos.get('contrasena')
        es_profesor = datos.get('es_profesor', False)
        
        # Validar campos requeridos
        if not nombre_usuario or not correo or not contrasena:
            return jsonify({'error': 'Todos los campos son requeridos'}), 400
        
        # El resto del código permanece igual...
        valido, mensaje = validar_contrasena(contrasena)
        if not valido:
            return jsonify({'error': mensaje}), 400
        
        hash_contrasena = hashlib.sha256(contrasena.encode()).hexdigest()
        codigo = generar_codigo_verificacion()
        expira = datetime.now() + timedelta(minutes=15)
        
        conexion = obtener_bd()
        cursor = conexion.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO usuarios (nombre_usuario, correo, contrasena, es_profesor, 
                                 codigo_verificacion, expira_verificacion)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (nombre_usuario, correo, hash_contrasena, es_profesor, codigo, expira))
            conexion.commit()
            
            if enviar_correo_verificacion(correo, codigo):
                return jsonify({
                    'exito': True,
                    'mensaje': 'Registro exitoso. Revisa tu correo para verificar tu cuenta.'
                })
            else:
                return jsonify({
                    'exito': True,
                    'mensaje': 'Registro exitoso, pero hubo un error enviando el correo.'
                })
        except pymysql.IntegrityError:
            return jsonify({'error': 'Usuario o correo ya existe'}), 400
        finally:
            conexion.close()
    
    return render_template('registrar.html')

@app.route('/api/auth/registrar', methods=['POST'])
def api_registrar():
    datos = request.json
    # Estandarizar nombres a snake_case
    nombre_usuario = datos.get('nombre_usuario')
    correo = datos.get('correo')
    contrasena = datos.get('contrasena')
    es_profesor = datos.get('es_profesor', False)
    
    # Validaciones
    if not nombre_usuario or not correo or not contrasena:
        return jsonify({'error': 'Todos los campos son requeridos'}), 400
    
    valido, mensaje = validar_contrasena(contrasena)
    if not valido:
        return jsonify({'error': mensaje}), 400
    
    hash_contrasena = hashlib.sha256(contrasena.encode()).hexdigest()
    codigo = generar_codigo_verificacion()
    expira = datetime.now() + timedelta(minutes=15)
    
    conexion = obtener_bd()
    cursor = conexion.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO usuarios (nombre_usuario, correo, contrasena, es_profesor, 
                             codigo_verificacion, expira_verificacion)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (nombre_usuario, correo, hash_contrasena, es_profesor, codigo, expira))
        conexion.commit()
        
        if enviar_correo_verificacion(correo, codigo):
            return jsonify({'exito': True, 'mensaje': 'Registro exitoso. Revisa tu correo para verificar tu cuenta.'})
        else:
            return jsonify({'exito': True, 'mensaje': 'Registro exitoso, pero hubo un error enviando el correo.'})
    except pymysql.IntegrityError:
        return jsonify({'error': 'Usuario o correo ya existe'}), 400
    finally:
        conexion.close()

@app.route('/verificar', methods=['POST'])
def verificar_cuenta():
    datos = request.json
    correo = datos.get('correo')
    codigo = datos.get('codigo')
    
    conexion = obtener_bd()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute('''
        SELECT * FROM usuarios 
        WHERE correo = %s AND codigo_verificacion = %s 
        AND expira_verificacion > NOW()
    ''', (correo, codigo))
    
    usuario = cursor.fetchone()
    
    if usuario:
        cursor.execute('''
            UPDATE usuarios SET esta_verificado = 1, 
            codigo_verificacion = NULL, expira_verificacion = NULL
            WHERE correo = %s
        ''', (correo,))
        conexion.commit()
        conexion.close()
        return jsonify({'exito': True, 'mensaje': 'Cuenta verificada exitosamente'})
    else:
        conexion.close()
        return jsonify({'error': 'Código inválido o expirado'}), 400

@app.route('/reenviar_codigo', methods=['POST'])
def reenviar_codigo():
    datos = request.json
    correo = datos.get('correo')
    
    codigo = generar_codigo_verificacion()
    expira = datetime.now() + timedelta(minutes=15)
    
    conexion = obtener_bd()
    cursor = conexion.cursor()
    
    cursor.execute('''
        UPDATE usuarios SET codigo_verificacion = %s, expira_verificacion = %s
        WHERE correo = %s AND esta_verificado = 0
    ''', (codigo, expira, correo))
    
    if cursor.rowcount > 0:
        conexion.commit()
        conexion.close()
        if enviar_correo_verificacion(correo, codigo):
            return jsonify({'exito': True, 'mensaje': 'Código reenviado'})
    
    conexion.close()
    return jsonify({'error': 'No se pudo reenviar el código'}), 400

@app.route('/iniciar_sesion', methods=['GET', 'POST'])
def iniciar_sesion():
    if request.method == 'POST':
        datos = request.json
        print(f"DEBUG - Datos recibidos en login: {datos}")  # Para debug
        
        # Aceptar ambos formatos para compatibilidad
        nombre_usuario = datos.get('nombre_usuario') or datos.get('usuario')
        contrasena = datos.get('contrasena')
        
        if not nombre_usuario or not contrasena:
            return jsonify({'error': 'Usuario y contraseña son requeridos'}), 400
        
        hash_contrasena = hashlib.sha256(contrasena.encode()).hexdigest()
        
        conexion = obtener_bd()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute('''
            SELECT * FROM usuarios 
            WHERE nombre_usuario = %s AND contrasena = %s
        ''', (nombre_usuario, hash_contrasena))
        
        usuario = cursor.fetchone()
        conexion.close()
        
        if usuario:
            if not usuario['esta_verificado']:
                return jsonify({'error': 'Debes verificar tu cuenta primero'}), 403
            
            session['id_usuario'] = usuario['id']
            session['nombre_usuario'] = usuario['nombre_usuario']
            session['es_profesor'] = usuario['es_profesor']
            
            return jsonify({
                'exito': True,
                'es_profesor': usuario['es_profesor']
            })
        else:
            return jsonify({'error': 'Credenciales inválidas'}), 401
    
    return render_template('iniciar_sesion.html')

@app.route('/api/auth/iniciar_sesion', methods=['POST'])
def api_iniciar_sesion():
    datos = request.json
    print(f"DEBUG - Datos recibidos en API login: {datos}")  # Para debug
    
    # Aceptar ambos formatos para compatibilidad
    nombre_usuario = datos.get('nombre_usuario') or datos.get('usuario')
    contrasena = datos.get('contrasena')
    
    if not nombre_usuario or not contrasena:
        return jsonify({'error': 'Usuario y contraseña son requeridos'}), 400
    
    hash_contrasena = hashlib.sha256(contrasena.encode()).hexdigest()
    conexion = obtener_bd()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    cursor.execute('''
        SELECT * FROM usuarios 
        WHERE nombre_usuario = %s AND contrasena = %s
    ''', (nombre_usuario, hash_contrasena))
    usuario = cursor.fetchone()
    conexion.close()
    if usuario:
        if not usuario['esta_verificado']:
            return jsonify({'error': 'Debes verificar tu cuenta primero'}), 403
        session['id_usuario'] = usuario['id']
        session['nombre_usuario'] = usuario['nombre_usuario']
        session['es_profesor'] = usuario['es_profesor']
        return jsonify({'exito': True, 'es_profesor': usuario['es_profesor']})
    else:
        return jsonify({'error': 'Credenciales inválidas'}), 401

@app.route('/olvido_contrasena', methods=['GET', 'POST'])
def olvido_contrasena():
    if request.method == 'POST':
        datos = request.json
        correo = datos.get('correo')
        
        token = secrets.token_urlsafe(32)
        expira = datetime.now() + timedelta(hours=1)
        
        conexion = obtener_bd()
        cursor = conexion.cursor()
        
        cursor.execute('''
            UPDATE usuarios SET token_restablecer = %s, expira_restablecer = %s
            WHERE correo = %s
        ''', (token, expira, correo))
        
        if cursor.rowcount > 0:
            conexion.commit()
            conexion.close()
            if enviar_correo_recuperacion(correo, token):
                return jsonify({
                    'exito': True,
                    'mensaje': 'Se ha enviado un enlace de recuperación a tu correo'
                })
        
        conexion.close()
        return jsonify({'error': 'Correo no encontrado'}), 404
    
    return render_template('olvido_contrasena.html')

@app.route('/restablecer_contrasena/<token>', methods=['GET', 'POST'])
def restablecer_contrasena(token):
    if request.method == 'POST':
        datos = request.json
        nueva_contrasena = datos.get('contrasena')
        
        valido, mensaje = validar_contrasena(nueva_contrasena)
        if not valido:
            return jsonify({'error': mensaje}), 400
        
        hash_contrasena = hashlib.sha256(nueva_contrasena.encode()).hexdigest()
        
        conexion = obtener_bd()
        cursor = conexion.cursor()
        
        cursor.execute('''
            UPDATE usuarios SET contrasena = %s, token_restablecer = NULL, expira_restablecer = NULL
            WHERE token_restablecer = %s AND expira_restablecer > NOW()
        ''', (hash_contrasena, token))
        
        if cursor.rowcount > 0:
            conexion.commit()
            conexion.close()
            return jsonify({'exito': True, 'mensaje': 'Contraseña actualizada'})
        
        conexion.close()
        return jsonify({'error': 'Token inválido o expirado'}), 400
    
    return render_template('restablecer_contrasena.html', token=token)

@app.route('/api/unirse_juego', methods=['POST'])
def unirse_juego():
    datos = request.json
    codigo_pin = (datos.get('codigo_pin') or '').strip()
    nombre_usuario = (datos.get('nombre_usuario') or '').strip()
    
    conexion = obtener_bd()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    
    # Buscar quiz activo con ese PIN
    cursor.execute('''
        SELECT * FROM quizzes WHERE codigo_pin = %s
    ''', (codigo_pin,))
    
    quiz = cursor.fetchone()
    
    if not quiz:
        conexion.close()
        return jsonify({'error': 'PIN inválido'}), 404
    
    # Crear o unirse a sesión
    cursor.execute('''
        SELECT * FROM sesiones_juego 
        WHERE quiz_id = %s AND esta_activa = 1
        ORDER BY inicio_en_servidor DESC LIMIT 1
    ''', (quiz['id'],))
    
    datos_sesion = cursor.fetchone()
    
    if not datos_sesion:
        cursor.execute('''
            INSERT INTO sesiones_juego (quiz_id, codigo_pin)
            VALUES (%s, %s)
        ''', (quiz['id'], codigo_pin))
        id_sesion = cursor.lastrowid
    else:
        id_sesion = datos_sesion['id']
    
    # Registrar participante evitando duplicados por nombre en la misma sesión
    cursor.execute('''
        SELECT id FROM participantes 
        WHERE sesion_id = %s AND nombre_usuario = %s
        ORDER BY id LIMIT 1
    ''', (id_sesion, nombre_usuario))
    existente = cursor.fetchone()
    if existente:
        id_participante = existente['id']
    else:
        cursor.execute('''
            INSERT INTO participantes (sesion_id, nombre_usuario)
            VALUES (%s, %s)
        ''', (id_sesion, nombre_usuario))
        id_participante = cursor.lastrowid
    
    conexion.commit()
    conexion.close()
    
    return jsonify({
        'exito': True,
        'id_sesion': id_sesion,
        'id_participante': id_participante,
        'quiz': quiz
    })

@app.route('/api/guardar_respuesta', methods=['POST'])
def guardar_respuesta():
    datos = request.json
    
    conexion = obtener_bd()
    cursor = conexion.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO respuestas (id_participante, id_pregunta, id_opcion, 
                               tiempo_respuesta, puntos_ganados)
            VALUES (%s, %s, %s, %s, %s)
        ''', (datos.get('id_participante'), datos.get('id_pregunta'),
              datos.get('id_opcion'), datos.get('tiempo_respuesta'),
              datos.get('puntos_ganados', 0)))
        
        # Actualizar puntuación del participante
        cursor.execute('''
            UPDATE participantes 
            SET puntuacion_total = puntuacion_total + %s
            WHERE id = %s
        ''', (datos.get('puntos_ganados', 0), datos.get('id_participante')))
        
        conexion.commit()
        return jsonify({'exito': True})
    except Exception as e:
        conexion.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conexion.close()

@app.route('/api/resultados_juego/<int:sesion_id>')
def resultados_juego(sesion_id):
    conexion = obtener_bd()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute('''
        SELECT nombre_usuario, MAX(puntuacion_total) AS puntuacion_total
        FROM participantes
        WHERE sesion_id = %s
        GROUP BY nombre_usuario
        ORDER BY puntuacion_total DESC
        LIMIT 20
    ''', (sesion_id,))
    
    clasificacion = cursor.fetchall()
    conexion.close()
    
    return jsonify(clasificacion)

@app.route('/api/participante/<int:id_participante>/asignar_grupo', methods=['POST'])
def asignar_grupo(id_participante):
    """Asignar un grupo a un participante"""
    datos = request.json
    nombre_grupo = datos.get('nombre_grupo')
    
    if not nombre_grupo:
        return jsonify({'error': 'Nombre de grupo requerido'}), 400
    
    conexion = obtener_bd()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Actualizar el grupo del participante
        cursor.execute('''
            UPDATE participantes 
            SET nombre_grupo = %s
            WHERE id = %s
        ''', (nombre_grupo, id_participante))
        
        conexion.commit()
        
        return jsonify({'exito': True, 'nombre_grupo': nombre_grupo})
    except Exception as e:
        conexion.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conexion.close()

@app.route('/api/participante/<int:id_participante>/salir', methods=['POST'])
def abandonar_sesion(id_participante):
    """Eliminar un participante de la sesión"""
    conexion = obtener_bd()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Eliminar el participante
        cursor.execute('''
            DELETE FROM participantes 
            WHERE id = %s
        ''', (id_participante,))
        
        conexion.commit()
        
        return jsonify({'exito': True})
    except Exception as e:
        conexion.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conexion.close()

@app.route('/api/sesion/<int:id_sesion>/info')
def info_sesion(id_sesion):
    """Obtener información de la sesión y participantes"""
    conexion = obtener_bd()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Obtener información de la sesión
        cursor.execute('''
            SELECT gs.*, q.* 
            FROM sesiones_juego gs
            JOIN quizzes q ON gs.quiz_id = q.id
            WHERE gs.id = %s
        ''', (id_sesion,))
        
        datos_sesion = cursor.fetchone()
        
        if not datos_sesion:
            return jsonify({'error': 'Sesión no encontrada'}), 404
        
        # Obtener participantes
        cursor.execute('''
            SELECT id, nombre_usuario, nombre_grupo, puntuacion_total
            FROM participantes
            WHERE sesion_id = %s
            ORDER BY id
        ''', (id_sesion,))
        
        participantes = cursor.fetchall()
        
        return jsonify({
            'id_sesion': datos_sesion['id'],
            'codigo_pin': datos_sesion['codigo_pin'],
            'estado': datos_sesion['estado'],
            'inicio_en_servidor': datos_sesion.get('inicio_en_servidor'),
            'expira_temporizador': datos_sesion.get('expira_temporizador'),
            'intentos_permitidos': datos_sesion.get('intentos_permitidos', 0),
            'intentos_restantes': datos_sesion.get('intentos_restantes', 0),
            'quiz': {
                'id': datos_sesion['quiz_id'],
                'titulo': datos_sesion['titulo'],
                'descripcion': datos_sesion['descripcion'],
                'modo': datos_sesion['modo'],
                'num_grupos': datos_sesion.get('num_grupos', 0)
            },
            'participantes': participantes
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conexion.close()

@app.route('/api/sesion/<int:id_sesion>/estado')
def estado_sesion(id_sesion):
    """Verificar el estado de la sesión (para consultas periódicas)"""
    conexion = obtener_bd()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT estado, esta_activa
            FROM sesiones_juego
            WHERE id = %s
        """, (id_sesion,))
        fila = cursor.fetchone()
        if not fila:
            return jsonify({'error': 'Sesión no encontrada'}), 404

        cursor.execute("""
            SELECT id, nombre_usuario, nombre_grupo, puntuacion_total
            FROM participantes
            WHERE sesion_id = %s
            ORDER BY id
        """, (id_sesion,))
        participantes = cursor.fetchall()

        return jsonify({
            'estado': fila['estado'],
            'activa': bool(fila['esta_activa']),
            'participantes': participantes
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conexion.close()

@app.route('/api/sesion/<int:id_sesion>/iniciar', methods=['POST'])
@requiere_sesion
@requiere_docente
def iniciar_quiz_grupal(id_sesion):
    """Iniciar una sesión de juego grupal (solo profesor)"""
    conexion = obtener_bd()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    try:
        # Verificar que la sesión existe y pertenece a un quiz del profesor
        cursor.execute('''
            SELECT gs.*, q.id_profesor 
            FROM sesiones_juego gs
            JOIN quizzes q ON gs.quiz_id = q.id
            WHERE gs.id = %s
        ''', (id_sesion,))
        datos_sesion = cursor.fetchone()
        
        if not datos_sesion:
            return jsonify({'error': 'Sesión no encontrada'}), 404
        if datos_sesion['id_profesor'] != session['id_usuario']:
            return jsonify({'error': 'No autorizado'}), 403

        # ✅ Leer 'intentos' del payload (consistente con panel_profesor.html)
        datos = {}
        try:
            datos = request.get_json() or {}
        except:
            datos = {}

        # Frontend envía 'intentos', no 'intentos_restantes'
        intentos = int(datos.get('intentos', 0)) if datos.get('intentos') is not None else 0
        # Duracion (minutos) opcional desde frontend
        minutos = None
        for clave in ('duracion_minutos', 'duracion', 'minutos'):
            if datos.get(clave) is not None:
                try:
                    minutos = int(datos.get(clave))
                except Exception:
                    minutos = None
                break

        # Calcular expiración del temporizador (suma de tiempos por pregunta)
        cursor.execute('''
            SELECT COUNT(*) AS cnt, COALESCE(SUM(tiempo_limite), 0) AS total
            FROM preguntas
            WHERE quiz_id = %s
        ''', (datos_sesion['quiz_id'],))
        fila_t = cursor.fetchone() or {}
        cnt = fila_t.get('cnt', 0) or 0
        total = fila_t.get('total', 0) or 0
        if total and int(total) > 0:
            duracion_seg = int(total)
        else:
            # Respaldo sin columna de quiz: 30s por pregunta
            duracion_seg = int((cnt or 1) * 30)
        # Si el profesor indicó duracion manual en minutos, sobrescribir
        if minutos and minutos > 0:
            duracion_seg = minutos * 60

        # Actualizar estado a 'iniciada'
        cursor.execute('''
            UPDATE sesiones_juego 
            SET estado = 'iniciada',
                intentos_permitidos = %s,
                intentos_restantes = %s,
                inicio_en_servidor = NOW(),
                expira_temporizador = DATE_ADD(NOW(), INTERVAL %s SECOND)
            WHERE id = %s
        ''', (intentos, intentos, duracion_seg, id_sesion))

        conexion.commit()
        return jsonify({
            'exito': True,
            'estado': 'iniciada',
            'intentos_permitidos': intentos,
            'intentos_restantes': intentos,
            'expira_en_seg': duracion_seg
        })
    except Exception as e:
        conexion.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conexion.close()


@app.route('/api/sesion/<int:id_sesion>/consumir_intento', methods=['POST'])
def consumir_intento(id_sesion):
    """
    Endpoint público que decrementa intentos_restantes en 1 si hay intentos.
    Retorna el número de intentos restantes después de consumir.
    """
    conexion = obtener_bd()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    try:
        # Obtener intentos_restantes actual
        cursor.execute('SELECT intentos_restantes FROM sesiones_juego WHERE id = %s FOR UPDATE', (id_sesion,))
        fila = cursor.fetchone()
        if not fila:
            conexion.close()
            return jsonify({'error': 'Sesión no encontrada'}), 404

        restantes = fila.get('intentos_restantes', 0) or 0
        if restantes <= 0:
            conexion.close()
            return jsonify({'error': 'No quedan intentos disponibles'}), 400

        # Decrementar en 1
        nuevos_restantes = restantes - 1
        cursor.execute('UPDATE sesiones_juego SET intentos_restantes = %s WHERE id = %s', (nuevos_restantes, id_sesion))
        conexion.commit()
        conexion.close()
        return jsonify({'exito': True, 'intentos_restantes': nuevos_restantes})
    except Exception as e:
        conexion.rollback()
        conexion.close()
        return jsonify({'error': str(e)}), 500


@app.route('/api/sesion/<int:id_sesion>/finalizar', methods=['POST'])
@requiere_sesion
@requiere_docente
def finalizar_sesion_quiz(id_sesion):
    """Finaliza una sesión de juego (solo profesor dueño del quiz)."""
    conexion = obtener_bd()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    try:
        # Verificar que la sesión existe y pertenece a un quiz del profesor actual
        cursor.execute('''
            SELECT gs.*, q.id_profesor
            FROM sesiones_juego gs
            JOIN quizzes q ON gs.quiz_id = q.id
            WHERE gs.id = %s
        ''', (id_sesion,))
        datos_sesion = cursor.fetchone()

        if not datos_sesion:
            return jsonify({'error': 'Sesión no encontrada'}), 404
        if datos_sesion['id_profesor'] != session['id_usuario']:
            return jsonify({'error': 'No autorizado'}), 403

        # Marcar como finalizada e inactiva
        cursor.execute('''
            UPDATE sesiones_juego
            SET estado = 'finalizada',
                esta_activa = 0,
                fin_en_servidor = NOW()
            WHERE id = %s
        ''', (id_sesion,))
        conexion.commit()
        return jsonify({'exito': True, 'estado': 'finalizada'})
    except Exception as e:
        conexion.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conexion.close()

@app.route('/api/sesion/<int:id_sesion>/verificar_estado', methods=['GET'])
def verificar_estado_sesion(id_sesion):
    """Verificar si la sesión sigue activa (para consultas periódicas de estudiantes)"""
    conexion = obtener_bd()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute('''
            SELECT estado, esta_activa 
            FROM sesiones_juego 
            WHERE id = %s
        ''', (id_sesion,))
        
        datos_sesion = cursor.fetchone()
        
        if not datos_sesion:
            return jsonify({'activa': False, 'estado': 'no_encontrada'}), 404
        
        return jsonify({
            'activa': datos_sesion['esta_activa'] == 1,
            'estado': datos_sesion['estado']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conexion.close()


@app.route('/api/participante/<int:id_participante>/progreso', methods=['GET'])
def obtener_progreso(id_participante):
    """Recuperar el progreso del participante"""
    conexion = obtener_bd()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Obtener última respuesta del participante
        cursor.execute('''
            SELECT id_pregunta, MAX(momento_respuesta) as ultima_respuesta
            FROM respuestas
            WHERE id_participante = %s
            GROUP BY id_pregunta
            ORDER BY momento_respuesta DESC
            LIMIT 1
        ''', (id_participante,))
        
        ultima_respuesta = cursor.fetchone()
        
        # Obtener puntuación total
        cursor.execute('''
            SELECT puntuacion_total
            FROM participantes
            WHERE id = %s
        ''', (id_participante,))
        
        participante = cursor.fetchone()
        
        return jsonify({
            'id_ultima_pregunta': ultima_respuesta['id_pregunta'] if ultima_respuesta else None,
            'puntuacion_total': participante['puntuacion_total'] if participante else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conexion.close()

@app.route('/api/sesiones_activas')
@requiere_sesion
@requiere_docente
def sesiones_activas():
    """Obtener sesiones activas de quizzes del profesor"""
    conexion = obtener_bd()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute('''
            SELECT 
                gs.id as sesion_id, 
                gs.codigo_pin, 
                gs.estado, 
                gs.inicio_en_servidor,
                gs.expira_temporizador,
                gs.intentos_restantes,
                gs.intentos_permitidos,
                q.id as quiz_id, 
                q.titulo, 
                q.modo,
                COUNT(p.id) as participant_count
            FROM sesiones_juego gs
            JOIN quizzes q ON gs.quiz_id = q.id
            LEFT JOIN participantes p ON gs.id = p.sesion_id
            WHERE q.id_profesor = %s AND gs.esta_activa = 1
            GROUP BY 
                gs.id, gs.codigo_pin, gs.estado, gs.inicio_en_servidor, gs.expira_temporizador,
                gs.intentos_restantes, gs.intentos_permitidos, q.id, q.titulo, q.modo
            ORDER BY gs.inicio_en_servidor DESC
        ''', (session['id_usuario'],))
        
        sesiones = cursor.fetchall()
        return jsonify(sesiones)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conexion.close()

@app.route('/panel_control')
@requiere_sesion
@requiere_docente
def panel_control():
    """Panel de control para docentes"""
    return render_template('panel_profesor.html')

@app.route('/api/quizzes', methods=['GET', 'POST'])
@requiere_sesion
@requiere_docente
def gestionar_quizzes():
    """Obtener todos los quizzes o crear uno nuevo"""
    conexion = obtener_bd()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT * FROM quizzes 
            WHERE id_profesor = %s OR es_publico = 1
            ORDER BY creado_en DESC
        ''', (session['id_usuario'],))
        quizzes = cursor.fetchall()
        conexion.close()
        return jsonify(quizzes)
    
    elif request.method == 'POST':
        datos = request.json
        codigo_pin = generar_pin()
        
        cursor.execute('''
            INSERT INTO quizzes (id_profesor, titulo, descripcion, modo, num_grupos,
                               es_publico, codigo_pin)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (session['id_usuario'], datos.get('titulo'), datos.get('descripcion'),
              datos.get('modo', 'individual'), datos.get('num_grupos', 0),
              datos.get('es_publico', True), codigo_pin))
        
        id_quiz = cursor.lastrowid
        conexion.commit()
        conexion.close()
        
        # ✅ CORREGIDO: Retornar 'id_quiz' en lugar de 'quiz_id'
        return jsonify({'exito': True, 'id_quiz': id_quiz, 'codigo_pin': codigo_pin})


@app.route('/api/quizzes/<int:id_quiz>', methods=['GET', 'PUT', 'DELETE'])
@requiere_sesion
def gestionar_quiz(id_quiz):
    """Obtener, actualizar o eliminar un quiz específico"""
    conexion = obtener_bd()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM quizzes WHERE id = %s', (id_quiz,))
        quiz = cursor.fetchone()
        
        if not quiz:
            conexion.close()
            return jsonify({'error': 'Quiz no encontrado'}), 404
        
        # Obtener preguntas del quiz
        cursor.execute('''
            SELECT * FROM preguntas 
            WHERE quiz_id = %s 
            ORDER BY posicion, id
        ''', (id_quiz,))
        
        preguntas = cursor.fetchall()
        
        # Obtener opciones para cada pregunta
        for pregunta in preguntas:
            cursor.execute('''
                SELECT id, texto_opcion, es_correcta 
                FROM opciones 
                WHERE pregunta_id = %s
                ORDER BY id
            ''', (pregunta['id'],))
            pregunta['opciones'] = cursor.fetchall()
        
        quiz['preguntas'] = preguntas
        conexion.close()
        
        return jsonify(quiz)
    
    elif request.method == 'PUT':
        # Verificar que el usuario es el creador
        cursor.execute('SELECT id_profesor FROM quizzes WHERE id = %s', (id_quiz,))
        quiz = cursor.fetchone()
        
        if not quiz or quiz['id_profesor'] != session['id_usuario']:
            conexion.close()
            return jsonify({'error': 'No autorizado'}), 403
        
        datos = request.json
        cursor.execute('''
            UPDATE quizzes 
            SET titulo = %s,
                descripcion = %s,
                modo = %s,
                num_grupos = %s,
                es_publico = %s
            WHERE id = %s
        ''', (
            datos.get('titulo'),
            datos.get('descripcion'),
            datos.get('modo'),
            datos.get('num_grupos', 0),
            datos.get('es_publico'),
            id_quiz
        ))
        
        conexion.commit()
        conexion.close()
        return jsonify({'exito': True})
    
    elif request.method == 'DELETE':
        # Verificar que el usuario es el creador
        cursor.execute('SELECT id_profesor FROM quizzes WHERE id = %s', (id_quiz,))
        quiz = cursor.fetchone()
        
        if not quiz or quiz['id_profesor'] != session['id_usuario']:
            conexion.close()
            return jsonify({'error': 'No autorizado'}), 403
        
        cursor.execute('DELETE FROM quizzes WHERE id = %s', (id_quiz,))
        conexion.commit()
        conexion.close()
        return jsonify({'exito': True})

# ============================================================
# 🔹 ENDPOINT: Gestionar preguntas de un quiz
# ============================================================
@app.route('/api/quizzes/<int:id_quiz>/preguntas', methods=['GET', 'POST'])
@requiere_sesion
def gestionar_preguntas_por_quiz(id_quiz):
    """
    GET: Listar preguntas (y opciones) de un quiz.
    POST: Crear una nueva pregunta para el quiz.
    """
    conexion = obtener_bd()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

    # Verificar que el quiz exista
    cursor.execute('SELECT * FROM quizzes WHERE id = %s', (id_quiz,))
    quiz = cursor.fetchone()
    if not quiz:
        conexion.close()
        return jsonify({'error': 'Quiz no encontrado'}), 404

    # GET - Listar preguntas y opciones
    if request.method == 'GET':
        cursor.execute('''
            SELECT * FROM preguntas WHERE quiz_id = %s ORDER BY posicion, id
        ''', (id_quiz,))
        preguntas = cursor.fetchall()

        for p in preguntas:
            cursor.execute('''
                SELECT id, texto_opcion, es_correcta FROM opciones WHERE pregunta_id = %s
            ''', (p['id'],))
            p['opciones'] = cursor.fetchall()

        conexion.close()
        return jsonify(preguntas), 200

    # POST - Crear nueva pregunta
    if request.method == 'POST':
        datos = request.get_json()

        texto_pregunta = datos.get('texto_pregunta') or datos.get('texto') or datos.get('text')
        url_imagen = datos.get('url_imagen')
        url_video = datos.get('url_video')
        tiempo_limite = datos.get('tiempo_limite', 30)
        posicion = datos.get('posicion', 0)
        opciones = datos.get('opciones', [])

        if not texto_pregunta:
            conexion.close()
            return jsonify({'error': 'Falta el texto de la pregunta'}), 400

        try:
            cursor.execute('''
                INSERT INTO preguntas (quiz_id, texto_pregunta, url_imagen, url_video, tiempo_limite, posicion)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (id_quiz, texto_pregunta, url_imagen, url_video, tiempo_limite, posicion))
            id_pregunta = cursor.lastrowid

            # Insertar opciones
            for opcion in opciones:
                texto_opcion = opcion.get('texto_opcion') or opcion.get('texto') or opcion.get('text')
                es_correcta = bool(opcion.get('es_correcta', False))
                if texto_opcion:
                    cursor.execute('''
                        INSERT INTO opciones (pregunta_id, texto_opcion, es_correcta)
                        VALUES (%s, %s, %s)
                    ''', (id_pregunta, texto_opcion, es_correcta))

            conexion.commit()
            conexion.close()
            return jsonify({'exito': True, 'id_pregunta': id_pregunta}), 201

        except Exception as e:
            conexion.rollback()
            conexion.close()
            return jsonify({'error': str(e)}), 500

# ============================================================
# 📤 Exportar resultados de una sesión (solo profesor del quiz)
# ============================================================
from io import BytesIO
import pandas as pd
from flask import send_file, jsonify

@app.route('/api/sesion/<int:id_sesion>/exportar_resultados', methods=['GET'])
@requiere_sesion
def exportar_resultados(id_sesion):
    """
    Exporta a Excel la lista de preguntas, cada participante y la opción elegida
    (con indicación de si fue correcta). Sólo el profesor dueño del quiz puede exportar.
    """
    # 1) Autorización: debe ser profesor Y dueño del quiz
    if not session.get('es_profesor'):
        return jsonify({'error': 'Solo profesores pueden exportar resultados'}), 403

    conexion = obtener_bd()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

    # 2) Verificar que la sesión exista y pertenece al profesor actual
    cursor.execute("""
        SELECT s.id, s.estado, q.titulo AS titulo_quiz, q.id_profesor
        FROM sesiones_juego s
        JOIN quizzes q ON s.quiz_id = q.id
        WHERE s.id = %s
    """, (id_sesion,))
    sesion = cursor.fetchone()
    if not sesion:
        conexion.close()
        return jsonify({'error': 'Sesión no encontrada'}), 404

    # el profesor actual debe ser el dueño del quiz
    if sesion['id_profesor'] != session.get('id_usuario'):
        return jsonify({'error': 'No autorizado'}), 403

    # (opcional) sólo cuando terminó la sesión
    # if sesion['estado'] != 'finalizado':
    #     conexion.close()
    #     return jsonify({'error': 'Solo se puede exportar al finalizar el quiz'}), 400

    # 3) Traer resultados usando la tabla 'respuestas' del schema.sql
    #    Unimos con participantes (para nombre y grupo), preguntas (texto y posición)
    #    y opciones (texto y si es correcta).
    cursor.execute("""
        SELECT 
            p.texto_pregunta              AS pregunta,
            part.nombre_usuario           AS participante,
            part.nombre_grupo             AS grupo,
            o.texto_opcion                AS respuesta_elegida,
            CASE WHEN o.es_correcta = 1 THEN 'Sí' ELSE 'No' END AS correcta,
            p.posicion                    AS posicion_pregunta,
            r.momento_respuesta           AS respondido_en
        FROM respuestas r
        JOIN participantes part ON r.id_participante = part.id
        JOIN preguntas     p    ON r.id_pregunta     = p.id
        JOIN opciones      o    ON r.id_opcion       = o.id
        WHERE part.sesion_id = %s
        ORDER BY p.posicion, part.id, r.momento_respuesta
    """, (id_sesion,))
    filas = cursor.fetchall()
    conexion.close()

    if not filas:
        return jsonify({'error': 'No hay respuestas registradas para esta sesión'}), 404

    # 4) Armar DataFrame con columnas legibles
    df = pd.DataFrame(filas)
    df = df[[
        'pregunta',
        'participante',
        'grupo',
        'respuesta_elegida',
        'correcta',
        'respondido_en'
    ]]

    # 5) Exportar a Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    output.seek(0)

    nombre_archivo = f"resultados_{sesion['titulo_quiz'].strip().replace(' ', '_')}_sesion_{id_sesion}.xlsx"
    return send_file(
        output,
        download_name=nombre_archivo,
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/editar_quiz/<int:id_quiz>')
@requiere_sesion
@requiere_docente
def editar_quiz(id_quiz):
    """Editar de preguntas del quiz"""
    return render_template('editar_quiz.html', id_quiz=id_quiz)



@app.route('/api/preguntas/<int:id_pregunta>', methods=['GET', 'PUT', 'DELETE'])
@requiere_sesion
def gestionar_pregunta(id_pregunta):
    """Obtener, actualizar o eliminar una pregunta"""
    conexion = obtener_bd()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

    # Obtener la pregunta
    cursor.execute('SELECT * FROM preguntas WHERE id = %s', (id_pregunta,))
    pregunta = cursor.fetchone()
    if not pregunta:
        conexion.close()
        return jsonify({'error': 'Pregunta no encontrada'}), 404

    # GET: devolver pregunta + opciones
    if request.method == 'GET':
        cursor.execute('SELECT * FROM opciones WHERE pregunta_id = %s', (id_pregunta,))
        opciones = cursor.fetchall()
        pregunta['opciones'] = opciones
        conexion.close()
        return jsonify(pregunta), 200

    # PUT: actualizar pregunta y sus opciones
    if request.method == 'PUT':
        datos = request.get_json()
        texto_pregunta = datos.get('texto_pregunta') or pregunta['texto_pregunta']
        url_imagen = datos.get('url_imagen') or pregunta.get('url_imagen')
        url_video = datos.get('url_video') or pregunta.get('url_video')
        tiempo_limite = datos.get('tiempo_limite') or pregunta.get('tiempo_limite')
        posicion = datos.get('posicion') or pregunta.get('posicion')

        # Actualizar datos principales
        cursor.execute('''
            UPDATE preguntas
            SET texto_pregunta=%s, url_imagen=%s, url_video=%s, tiempo_limite=%s, posicion=%s
            WHERE id=%s
        ''', (texto_pregunta, url_imagen, url_video, tiempo_limite, posicion, id_pregunta))

        # Actualizar opciones si las hay
        if 'opciones' in datos:
            cursor.execute('DELETE FROM opciones WHERE pregunta_id = %s', (id_pregunta,))
            for opcion in datos['opciones']:
                texto_opcion = opcion.get('texto_opcion') or opcion.get('texto') or opcion.get('text')
                es_correcta = bool(opcion.get('es_correcta', False))
                if texto_opcion:
                    cursor.execute('''
                        INSERT INTO opciones (pregunta_id, texto_opcion, es_correcta)
                        VALUES (%s, %s, %s)
                    ''', (id_pregunta, texto_opcion, es_correcta))

        conexion.commit()
        conexion.close()
        return jsonify({'exito': True}), 200

    # DELETE: eliminar pregunta
    if request.method == 'DELETE':
        cursor.execute('DELETE FROM preguntas WHERE id = %s', (id_pregunta,))
        conexion.commit()
        conexion.close()
        return jsonify({'exito': True}), 200



@app.route('/api/info_sesion')
def info_sesion_usuario():
    """Obtener información de la sesión actual (si existe)"""
    # No requiere sesión - retorna datos vacíos si no está logueado
    return jsonify({
        'id_usuario': session.get('id_usuario'),
        'nombre_usuario': session.get('nombre_usuario'),
        'es_profesor': session.get('es_profesor', False)
    })

@app.route('/ver_sala_juego/<int:id_sesion>')
@requiere_sesion
@requiere_docente
def ver_sala_juego(id_sesion):
    """Vista del anfitrión (profesor) para observar una sesión en progreso"""
    return render_template('ver_sala_juego.html', id_sesion=id_sesion)

@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.clear()
    return redirect(url_for('inicio'))

# Ruta de diagnóstico para listar rutas activas
@app.route('/__rutas')
def _listar_rutas():
    reglas = sorted([str(r) for r in app.url_map.iter_rules()])
    return jsonify({ 'rutas': reglas })

if __name__ == '__main__':
    app.run(debug=True)

