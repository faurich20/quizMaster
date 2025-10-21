-- Script para actualizar la base de datos existente
-- Ejecutar este script en MySQL para agregar el campo 'status' a game_sessions

-- Agregar campo 'status' a la tabla game_sessions si no existe
ALTER TABLE game_sessions 
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'waiting';

-- Actualizar sesiones existentes para que tengan el estado 'waiting'
UPDATE game_sessions 
SET status = 'waiting' 
WHERE status IS NULL;

-- Verificar que el cambio se aplicó correctamente
SELECT 'Campo status agregado exitosamente a game_sessions' as mensaje;
