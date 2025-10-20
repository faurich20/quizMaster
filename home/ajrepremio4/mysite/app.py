from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_mail import Mail, Message
import pymysql
import hashlib
import secrets
import string
import re
from datetime import datetime, timedelta
from functools import wraps
import json
from db import obtener_conexion as obtener_conexion_db

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


def validar_contrasena(password):
    """Valida que la contraseña sea segura"""
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe contener al menos una mayúscula"
    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe contener al menos una minúscula"
    if not re.search(r'[0-9]', password):
        return False, "La contraseña debe contener al menos un número"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "La contraseña debe contener al menos un carácter especial"
    return True, "Contraseña válida"

def generar_codigo_verificacion():
    """Genera un código de verificación de 6 dígitos"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))

def generar_pin():
    """Genera un PIN único para el quiz"""
    return ''.join(secrets.choice(string.digits + string.ascii_uppercase) for _ in range(8))

def enviar_correo_verificacion(email, code):
    """Envía email de verificación"""
    try:
        msg = Message('Verificación de cuenta - QuizPlatform',
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[email])
        msg.body = f'''
        Bienvenido a QuizPlatform!
        
        Tu código de verificación es: {code}
        
        Este código expirará en 15 minutos.
        
        Si no solicitaste esta verificación, ignora este correo.
        '''
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False

def enviar_correo_recuperacion(email, token):
    """Envía email de recuperación de contraseña"""
    try:
        reset_url = url_for('restablecer_contrasena', token=token, _external=True)
        msg = Message('Recuperación de contraseña - QuizPlatform',
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[email])
        msg.body = f'''
        Has solicitado recuperar tu contraseña.
        
        Haz clic en el siguiente enlace para restablecer tu contraseña:
        {reset_url}
        
        Este enlace expirará en 1 hora.
        
        Si no solicitaste esto, ignora este correo.
        '''
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False

def requiere_sesion(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('iniciar_sesion'))
        return f(*args, **kwargs)
    return decorated_function

def requiere_docente(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_teacher'):
            return jsonify({'error': 'Acceso denegado'}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/play')
@app.route('/play/')
def jugar():
    return render_template('play.html')

@app.route('/register', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        is_teacher = data.get('is_teacher', False)
        
        # Validar contraseña
        valid, msg = validar_contrasena(password)
        if not valid:
            return jsonify({'error': msg}), 400
        
        # Hash de contraseña
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Generar código de verificación
        code = generar_codigo_verificacion()
        expires = datetime.now() + timedelta(minutes=15)
        
        conn = obtener_bd()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password, is_teacher, 
                                 verification_code, verification_expires)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (username, email, password_hash, is_teacher, code, expires))
            conn.commit()
            
            # Enviar email de verificación
            if enviar_correo_verificacion(email, code):
                return jsonify({
                    'success': True,
                    'message': 'Registro exitoso. Revisa tu correo para verificar tu cuenta.'
                })
            else:
                return jsonify({
                    'success': True,
                    'message': 'Registro exitoso, pero hubo un error enviando el correo.'
                })
        except pymysql.IntegrityError:
            return jsonify({'error': 'Usuario o correo ya existe'}), 400
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    is_teacher = data.get('is_teacher', False)
    valid, msg = validar_contrasena(password)
    if not valid:
        return jsonify({'error': msg}), 400
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    code = generar_codigo_verificacion()
    expires = datetime.now() + timedelta(minutes=15)
    conn = obtener_bd()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password, is_teacher, 
                             verification_code, verification_expires)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (username, email, password_hash, is_teacher, code, expires))
        conn.commit()
        if enviar_correo_verificacion(email, code):
            return jsonify({'success': True, 'message': 'Registro exitoso. Revisa tu correo para verificar tu cuenta.'})
        else:
            return jsonify({'success': True, 'message': 'Registro exitoso, pero hubo un error enviando el correo.'})
    except pymysql.IntegrityError:
        return jsonify({'error': 'Usuario o correo ya existe'}), 400
    finally:
        conn.close()

@app.route('/verify', methods=['POST'])
def verificar_cuenta():
    data = request.json
    email = data.get('email')
    code = data.get('code')
    
    conn = obtener_bd()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute('''
        SELECT * FROM users 
        WHERE email = %s AND verification_code = %s 
        AND verification_expires > NOW()
    ''', (email, code))
    
    user = cursor.fetchone()
    
    if user:
        cursor.execute('''
            UPDATE users SET is_verified = 1, 
            verification_code = NULL, verification_expires = NULL
            WHERE email = %s
        ''', (email,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Cuenta verificada exitosamente'})
    else:
        conn.close()
        return jsonify({'error': 'Código inválido o expirado'}), 400

@app.route('/resend_code', methods=['POST'])
def reenviar_codigo():
    data = request.json
    email = data.get('email')
    
    code = generar_codigo_verificacion()
    expires = datetime.now() + timedelta(minutes=15)
    
    conn = obtener_bd()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users SET verification_code = %s, verification_expires = %s
        WHERE email = %s AND is_verified = 0
    ''', (code, expires, email))
    
    if cursor.rowcount > 0:
        conn.commit()
        conn.close()
        if enviar_correo_verificacion(email, code):
            return jsonify({'success': True, 'message': 'Código reenviado'})
    
    conn.close()
    return jsonify({'error': 'No se pudo reenviar el código'}), 400

@app.route('/login', methods=['GET', 'POST'])
def iniciar_sesion():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = obtener_bd()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute('''
            SELECT * FROM users 
            WHERE username = %s AND password = %s
        ''', (username, password_hash))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            if not user['is_verified']:
                return jsonify({'error': 'Debes verificar tu cuenta primero'}), 403
            
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_teacher'] = user['is_teacher']
            
            return jsonify({
                'success': True,
                'is_teacher': user['is_teacher']
            })
        else:
            return jsonify({'error': 'Credenciales inválidas'}), 401
    
    return render_template('login.html')

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = obtener_bd()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute('''
        SELECT * FROM users 
        WHERE username = %s AND password = %s
    ''', (username, password_hash))
    user = cursor.fetchone()
    conn.close()
    if user:
        if not user['is_verified']:
            return jsonify({'error': 'Debes verificar tu cuenta primero'}), 403
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['is_teacher'] = user['is_teacher']
        return jsonify({'success': True, 'is_teacher': user['is_teacher']})
    else:
        return jsonify({'error': 'Credenciales inválidas'}), 401

@app.route('/forgot_password', methods=['GET', 'POST'])
def olvido_contrasena():
    if request.method == 'POST':
        data = request.json
        email = data.get('email')
        
        token = secrets.token_urlsafe(32)
        expires = datetime.now() + timedelta(hours=1)
        
        conn = obtener_bd()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET reset_token = %s, reset_expires = %s
            WHERE email = %s
        ''', (token, expires, email))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            if enviar_correo_recuperacion(email, token):
                return jsonify({
                    'success': True,
                    'message': 'Se ha enviado un enlace de recuperación a tu correo'
                })
        
        conn.close()
        return jsonify({'error': 'Correo no encontrado'}), 404
    
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def restablecer_contrasena(token):
    if request.method == 'POST':
        data = request.json
        new_password = data.get('password')
        
        valid, msg = validar_contrasena(new_password)
        if not valid:
            return jsonify({'error': msg}), 400
        
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        
        conn = obtener_bd()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET password = %s, reset_token = NULL, reset_expires = NULL
            WHERE reset_token = %s AND reset_expires > NOW()
        ''', (password_hash, token))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Contraseña actualizada'})
        
        conn.close()
        return jsonify({'error': 'Token inválido o expirado'}), 400
    
    return render_template('reset_password.html', token=token)

@app.route('/api/join_game', methods=['POST'])
def unirse_juego():
    data = request.json
    pin_code = data.get('pin_code')
    username = data.get('username')
    
    conn = obtener_bd()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # Buscar quiz activo con ese PIN
    cursor.execute('''
        SELECT * FROM quizzes WHERE pin_code = %s
    ''', (pin_code,))
    
    quiz = cursor.fetchone()
    
    if not quiz:
        conn.close()
        return jsonify({'error': 'PIN inválido'}), 404
    
    # Crear o unirse a sesión
    cursor.execute('''
        SELECT * FROM game_sessions 
        WHERE quiz_id = %s AND is_active = 1
        ORDER BY started_at DESC LIMIT 1
    ''', (quiz['id'],))
    
    session_data = cursor.fetchone()
    
    if not session_data:
        cursor.execute('''
            INSERT INTO game_sessions (quiz_id, pin_code)
            VALUES (%s, %s)
        ''', (quiz['id'], pin_code))
        session_id = cursor.lastrowid
    else:
        session_id = session_data['id']
    
    # Registrar participante
    cursor.execute('''
        INSERT INTO participants (session_id, username)
        VALUES (%s, %s)
    ''', (session_id, username))
    
    participant_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'participant_id': participant_id,
        'quiz': quiz
    })

@app.route('/api/save_answer', methods=['POST'])
def guardar_respuesta():
    data = request.json
    
    conn = obtener_bd()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO answers (participant_id, question_id, option_id, 
                               response_time, points_earned)
            VALUES (%s, %s, %s, %s, %s)
        ''', (data.get('participant_id'), data.get('question_id'),
              data.get('option_id'), data.get('response_time'),
              data.get('points_earned', 0)))
        
        # Actualizar score del participante
        cursor.execute('''
            UPDATE participants 
            SET total_score = total_score + %s
            WHERE id = %s
        ''', (data.get('points_earned', 0), data.get('participant_id')))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/game_results/<int:session_id>')
def resultados_juego(session_id):
    conn = obtener_bd()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute('''
        SELECT username, total_score 
        FROM participants 
        WHERE session_id = %s
        ORDER BY total_score DESC
        LIMIT 20
    ''', (session_id,))
    
    ranking = cursor.fetchall()
    conn.close()
    
    return jsonify(ranking)

@app.route('/dashboard')
@requiere_sesion
@requiere_docente
def dashboard():
    """Dashboard para docentes"""
    return render_template('dashboard.html')

@app.route('/api/quizzes', methods=['GET', 'POST'])
@requiere_sesion
@requiere_docente
def gestionar_quizzes():
    """Obtener todos los quizzes o crear uno nuevo"""
    conn = obtener_bd()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT * FROM quizzes 
            WHERE teacher_id = %s OR is_public = 1
            ORDER BY created_at DESC
        ''', (session['user_id'],))
        quizzes = cursor.fetchall()
        conn.close()
        return jsonify(quizzes)
    
    elif request.method == 'POST':
        data = request.json
        pin_code = generar_pin()
        
        cursor.execute('''
            INSERT INTO quizzes (teacher_id, title, description, mode, 
                               countdown_time, is_public, pin_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (session['user_id'], data.get('title'), data.get('description'),
              data.get('mode', 'individual'), data.get('countdown_time', 30),
              data.get('is_public', True), pin_code))
        
        quiz_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'quiz_id': quiz_id, 'pin_code': pin_code})

@app.route('/api/quizzes/<int:quiz_id>', methods=['GET', 'PUT', 'DELETE'])
@requiere_sesion
def gestionar_quiz(quiz_id):
    """Obtener, actualizar o eliminar un quiz específico"""
    conn = obtener_bd()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM quizzes WHERE id = %s', (quiz_id,))
        quiz = cursor.fetchone()
        conn.close()
        
        if quiz:
            return jsonify(quiz)
        return jsonify({'error': 'Quiz no encontrado'}), 404
    
    elif request.method == 'PUT':
        # Verificar que el usuario es el creador
        cursor.execute('SELECT teacher_id FROM quizzes WHERE id = %s', (quiz_id,))
        quiz = cursor.fetchone()
        
        if not quiz or quiz['teacher_id'] != session['user_id']:
            conn.close()
            return jsonify({'error': 'No autorizado'}), 403
        
        data = request.json
        cursor.execute('''
            UPDATE quizzes 
            SET title = %s, description = %s, mode = %s, 
                countdown_time = %s, is_public = %s
            WHERE id = %s
        ''', (data.get('title'), data.get('description'), data.get('mode'),
              data.get('countdown_time'), data.get('is_public'), quiz_id))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        # Verificar que el usuario es el creador
        cursor.execute('SELECT teacher_id FROM quizzes WHERE id = %s', (quiz_id,))
        quiz = cursor.fetchone()
        
        if not quiz or quiz['teacher_id'] != session['user_id']:
            conn.close()
            return jsonify({'error': 'No autorizado'}), 403
        
        cursor.execute('DELETE FROM quizzes WHERE id = %s', (quiz_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/quiz_editor/<int:quiz_id>')
@requiere_sesion
@requiere_docente
def editor_quiz(quiz_id):
    """Editor de preguntas del quiz"""
    return render_template('quiz_editor.html', quiz_id=quiz_id)

@app.route('/api/session_info')
@requiere_sesion
def info_sesion():
    """Obtener información de la sesión actual"""
    return jsonify({
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'is_teacher': session.get('is_teacher', False)
    })

@app.route('/logout')
def cerrar_sesion():
    session.clear()
    return redirect(url_for('inicio'))

# Ruta de diagnóstico para listar rutas activas
@app.route('/__routes')
def _list_routes():
    rules = sorted([str(r) for r in app.url_map.iter_rules()])
    return jsonify({ 'routes': rules })

if __name__ == '__main__':
    app.run(debug=True)