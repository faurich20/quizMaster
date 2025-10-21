# 🎮 Implementación del Modo Grupal - QuizPlatform

## 📋 Resumen de Cambios

Se ha implementado el **modo grupal** que permite a los profesores controlar cuándo los estudiantes comienzan a responder un quiz. Los estudiantes esperan en una sala de espera hasta que el profesor presione "INICIAR QUIZ".

---

## 🔄 Flujo de Funcionamiento

### **Modo Individual** (sin cambios)
```
/play → Ingresar PIN → Jugar inmediatamente ✅
```

### **Modo Grupal** (NUEVO)
```
1. Profesor: Dashboard → Crea/selecciona quiz en modo "Grupal" → Obtiene PIN
2. Alumnos: /play → Ingresar PIN → Redirige a /lobby (sala de espera)
3. Alumnos: Esperan en lobby.html viendo participantes conectados
4. Profesor: Dashboard → Ve sesión activa → Presiona "🚀 INICIAR QUIZ"
5. Alumnos: Automáticamente redirigidos a play.html para responder
```

---

## 📁 Archivos Modificados/Creados

### ✅ **Nuevos Archivos**
1. **`templates/lobby.html`** - Sala de espera para estudiantes
2. **`update_schema.sql`** - Script para actualizar la base de datos
3. **`MODO_GRUPAL_README.md`** - Este archivo

### ✏️ **Archivos Modificados**
1. **`schema.sql`** - Agregado campo `status` a `game_sessions`
2. **`app.py`** - Nuevos endpoints y ruta `/lobby`
3. **`templates/play.html`** - Detecta modo grupal y redirige a lobby
4. **`templates/dashboard.html`** - Panel de sesiones activas con botón INICIAR QUIZ

---

## 🗄️ Cambios en Base de Datos

### **Ejecutar este comando SQL:**

```sql
-- Agregar campo 'status' a game_sessions
ALTER TABLE game_sessions 
ADD COLUMN status VARCHAR(20) DEFAULT 'waiting';
```

O ejecutar el archivo completo:
```bash
mysql -u tu_usuario -p tu_base_de_datos < update_schema.sql
```

### **Estados posibles:**
- `waiting` - Esperando que el profesor inicie
- `started` - Quiz iniciado, estudiantes jugando
- `finished` - Quiz terminado

---

## 🆕 Nuevos Endpoints en `app.py`

### 1. **GET `/lobby`**
- Renderiza la sala de espera
- Accesible para todos

### 2. **GET `/api/session/<session_id>/info`**
- Obtiene información de la sesión y participantes
- Usado por lobby.html

### 3. **GET `/api/session/<session_id>/status`**
- Verifica el estado de la sesión (polling)
- Retorna: `{ status: 'waiting'|'started', participants: [...] }`

### 4. **POST `/api/session/<session_id>/start`**
- Inicia una sesión grupal (solo profesor)
- Cambia status de 'waiting' a 'started'

### 5. **GET `/api/active_sessions`**
- Lista sesiones grupales activas del profesor
- Usado por dashboard.html

---

## 🎨 Características Implementadas

### **Lobby (Sala de Espera)**
- ✅ Muestra información del quiz (título, descripción, PIN)
- ✅ Lista de participantes conectados en tiempo real
- ✅ Animación de carga mientras espera
- ✅ Polling cada 2 segundos para detectar inicio
- ✅ Navbar para usuarios logueados
- ✅ Botón "Salir de la Sala" para usuarios no logueados

### **Dashboard del Profesor**
- ✅ Sección "Sesiones Grupales Activas"
- ✅ Muestra PIN, participantes conectados, estado
- ✅ Botón "🚀 INICIAR QUIZ" (solo si status = 'waiting')
- ✅ Actualización automática cada 5 segundos
- ✅ Indicador visual de estado (naranja = esperando, verde = iniciado)

### **Play.html**
- ✅ Detecta automáticamente si el quiz es grupal
- ✅ Redirige a lobby si es grupal
- ✅ Inicia automáticamente cuando viene del lobby (auto_start=true)

---

## 🚀 Instrucciones de Uso

### **Para el Profesor:**

1. **Crear Quiz Grupal:**
   - Dashboard → "+ Crear Quiz"
   - Seleccionar modo: "Grupal"
   - Guardar y compartir el PIN

2. **Iniciar Quiz:**
   - Esperar a que los estudiantes se conecten
   - Ver la sección "🎮 Sesiones Grupales Activas"
   - Presionar "🚀 INICIAR QUIZ"
   - Los estudiantes comenzarán automáticamente

### **Para los Estudiantes:**

1. **Unirse:**
   - Ir a `/play`
   - Ingresar PIN del quiz grupal
   - Esperar en la sala de espera

2. **Jugar:**
   - Cuando el profesor inicie, serán redirigidos automáticamente
   - Responder las preguntas normalmente

---

## 🔧 Configuración Técnica

### **Polling Intervals:**
- Lobby: Verifica estado cada **2 segundos**
- Dashboard: Actualiza sesiones cada **5 segundos**

### **Seguridad:**
- Solo el profesor dueño del quiz puede iniciar la sesión
- Verificación de `teacher_id` en el endpoint `/start`
- Decoradores `@requiere_sesion` y `@requiere_docente`

---

## 📝 Notas Importantes

1. **Compatibilidad:** El modo individual sigue funcionando exactamente igual
2. **Sin grupos:** Esta implementación NO crea grupos de estudiantes, solo sincroniza el inicio
3. **Base de datos:** Ejecutar `update_schema.sql` antes de usar
4. **Navegadores:** Funciona en todos los navegadores modernos

---

## 🐛 Troubleshooting

### **Los estudiantes no ven el quiz iniciado:**
- Verificar que el polling esté funcionando (consola del navegador)
- Verificar que el status en BD cambió a 'started'

### **Error "Sesión no encontrada":**
- Verificar que el session_id sea correcto
- Verificar que la sesión esté activa (is_active = 1)

### **El profesor no ve sesiones activas:**
- Solo muestra quizzes en modo 'group'
- Solo muestra sesiones con is_active = 1
- Verificar que haya estudiantes conectados

---

## ✅ Testing Checklist

- [ ] Ejecutar `update_schema.sql`
- [ ] Crear quiz en modo grupal
- [ ] Estudiante se une y ve lobby
- [ ] Lobby muestra participantes en tiempo real
- [ ] Dashboard muestra sesión activa
- [ ] Profesor presiona INICIAR QUIZ
- [ ] Estudiantes redirigidos automáticamente
- [ ] Estudiantes pueden responder preguntas
- [ ] Modo individual sigue funcionando

---

## 📞 Soporte

Si encuentras algún problema, verifica:
1. Logs de la consola del navegador (F12)
2. Logs del servidor Flask
3. Estado de la base de datos (campo `status`)

---

**¡Implementación completa y lista para usar!** 🎉
