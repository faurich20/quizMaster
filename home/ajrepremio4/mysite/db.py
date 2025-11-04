# Archivo de conexión a la base de datos (comentarios en español)
import pymysql

HOST = 'localhost'#'ajrepremio4.mysql.pythonanywhere-services.com'
USER = 'root' #ajrepremio4
PASSWORD = '' #unpassword1
DB = 'ajrepremio4$quiz_bd'
PORT = 3327

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
                                port=PORT,
                                cursorclass=clasecursor)

# Alias 
obtener_conexion_db = obtener_conexion
