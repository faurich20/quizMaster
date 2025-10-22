-- Esquema de base de datos para QuizPlatform
-- Ejecutar manualmente en MySQL (usar la base de datos que corresponda antes de correr esto)

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  password VARCHAR(64) NOT NULL,
  is_teacher BOOLEAN DEFAULT 0,
  is_verified BOOLEAN DEFAULT 0,
  verification_code VARCHAR(6),
  verification_expires DATETIME,
  reset_token VARCHAR(64),
  reset_expires DATETIME,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de quizzes
CREATE TABLE IF NOT EXISTS quizzes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  teacher_id INT NOT NULL,
  title VARCHAR(200) NOT NULL,
  description TEXT,
  pin_code VARCHAR(8) UNIQUE NOT NULL,
  mode VARCHAR(20) DEFAULT 'individual',
  num_groups INT DEFAULT 0,
  countdown_time INT DEFAULT 30,
  is_public BOOLEAN DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Tabla de preguntas
CREATE TABLE IF NOT EXISTS questions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  quiz_id INT NOT NULL,
  question_text TEXT NOT NULL,
  image_url VARCHAR(500),
  video_url VARCHAR(500),
  time_limit INT DEFAULT 30,
  position INT NOT NULL,
  FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

-- Tabla de opciones
CREATE TABLE IF NOT EXISTS options (
  id INT AUTO_INCREMENT PRIMARY KEY,
  question_id INT NOT NULL,
  option_text VARCHAR(500) NOT NULL,
  is_correct BOOLEAN DEFAULT 0,
  position INT NOT NULL,
  FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

-- Tabla de sesiones de juego
CREATE TABLE IF NOT EXISTS game_sessions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  quiz_id INT NOT NULL,
  pin_code VARCHAR(8) NOT NULL,
  status VARCHAR(20) DEFAULT 'waiting',
  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ended_at TIMESTAMP NULL,
  is_active BOOLEAN DEFAULT 1,
  FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

-- Tabla de participantes
CREATE TABLE IF NOT EXISTS participants (
  id INT AUTO_INCREMENT PRIMARY KEY,
  session_id INT NOT NULL,
  username VARCHAR(50) NOT NULL,
  group_name VARCHAR(50),
  total_score INT DEFAULT 0,
  FOREIGN KEY (session_id) REFERENCES game_sessions(id) ON DELETE CASCADE
);

-- Tabla de respuestas
CREATE TABLE IF NOT EXISTS answers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  participant_id INT NOT NULL,
  question_id INT NOT NULL,
  option_id INT NOT NULL,
  response_time FLOAT NOT NULL,
  points_earned INT DEFAULT 0,
  answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE,
  FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
  FOREIGN KEY (option_id) REFERENCES options(id) ON DELETE CASCADE
);
