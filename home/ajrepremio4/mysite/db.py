# Archivo de conexión a la base de datos (comentarios en español)
import pymysql

HOST = 'ajrepremio4.mysql.pythonanywhere-services.com'
USER = 'ajrepremio4'
PASSWORD = 'unpassword1'
DB = 'ajrepremio4$quiz_bd'

def obtener_conexion(con_dict=False):
    # Retorna una conexión PyMySQL; si con_dict=True usa cursores tipo diccionario
    if con_dict:
        clasecursor = pymysql.cursors.DictCursor
    else:
        clasecursor = pymysql.cursors.Cursor
    return pymysql.connect(host=HOST,
                                user=USER,
                                password=PASSWORD,
                                db=DB,
                                cursorclass=clasecursor)

# Alias 
obtener_conexion_db = obtener_conexion
