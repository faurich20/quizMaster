-- Esquema de base de datos para QuizPlatforma
-- Ejecutar manualmente en MySQL (usar la base de datos que corresponda antes de correr esto)

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre_usuario VARCHAR(50) UNIQUE NOT NULL,
  correo VARCHAR(100) UNIQUE NOT NULL,
  contrasena VARCHAR(64) NOT NULL,
  es_profesor BOOLEAN DEFAULT 0,
  esta_verificado BOOLEAN DEFAULT 0,
  codigo_verificacion VARCHAR(6),
  expira_verificacion DATETIME,
  token_restablecer VARCHAR(64),
  expira_restablecer DATETIME,
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de quizzes
CREATE TABLE IF NOT EXISTS quizzes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  id_profesor INT NOT NULL,
  titulo VARCHAR(200) NOT NULL,
  descripcion TEXT,
  codigo_pin VARCHAR(8) UNIQUE NOT NULL,
  modo VARCHAR(20) DEFAULT 'individual',
  num_grupos INT DEFAULT 0,
  tiempo_cuenta_regresiva INT DEFAULT 30,
  es_publico BOOLEAN DEFAULT 1,
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_profesor) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Tabla de preguntas
CREATE TABLE IF NOT EXISTS preguntas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  quiz_id INT NOT NULL,
  texto_pregunta TEXT NOT NULL,
  url_imagen VARCHAR(500),
  url_video VARCHAR(500),
  tiempo_limite INT DEFAULT 30,
  posicion INT NOT NULL,
  FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

-- Tabla de opciones
CREATE TABLE IF NOT EXISTS opciones (
  id INT AUTO_INCREMENT PRIMARY KEY,
  pregunta_id INT NOT NULL,
  texto_opcion VARCHAR(500) NOT NULL,
  es_correcta BOOLEAN DEFAULT 0,
  FOREIGN KEY (pregunta_id) REFERENCES preguntas(id) ON DELETE CASCADE
);

-- Tabla de sesiones de juego
CREATE TABLE IF NOT EXISTS sesiones_juego (
  id INT AUTO_INCREMENT PRIMARY KEY,
  quiz_id INT NOT NULL,
  codigo_pin VARCHAR(8) NOT NULL,
  estado VARCHAR(20) DEFAULT 'esperando',
  esta_activa BOOLEAN DEFAULT 1,
  intentos_permitidos INT DEFAULT 0,
  intentos_restantes INT DEFAULT 0,
  inicio_en_servidor TIMESTAMP NULL DEFAULT NULL,
  fin_en_servidor TIMESTAMP NULL DEFAULT NULL,
  expira_temporizador DATETIME NULL,
  FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

-- Tabla de participantes
CREATE TABLE IF NOT EXISTS participantes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  sesion_id INT NOT NULL,
  nombre_usuario VARCHAR(50) NOT NULL,
  nombre_grupo VARCHAR(50),
  puntuacion_total INT DEFAULT 0,
  UNIQUE KEY uniq_participante_sesion (sesion_id, nombre_usuario),
  FOREIGN KEY (sesion_id) REFERENCES sesiones_juego(id) ON DELETE CASCADE
);

-- Tabla de respuestas
CREATE TABLE IF NOT EXISTS respuestas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  id_participante INT NOT NULL,
  id_pregunta INT NOT NULL,
  id_opcion INT NOT NULL,
  tiempo_respuesta FLOAT NOT NULL,
  puntos_ganados INT DEFAULT 0,
  momento_respuesta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_participante) REFERENCES participantes(id) ON DELETE CASCADE,
  FOREIGN KEY (id_pregunta) REFERENCES preguntas(id) ON DELETE CASCADE,
  FOREIGN KEY (id_opcion) REFERENCES opciones(id) ON DELETE CASCADE
);
