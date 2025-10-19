import pymysql

HOST = 'ajrepremio4.mysql.pythonanywhere-services.com'
USER = 'ajrepremio4'
PASSWORD = 'unpassword1'
DB = 'ajrepremio4$quiz_bd'

def obtener_conexion(con_dict=False):
    if con_dict:
        clasecursor = pymysql.cursors.DictCursor
    else:
        clasecursor = pymysql.cursors.Cursor
    return pymysql.connect(host=HOST,
                                user=USER,
                                password=PASSWORD,
                                db=DB,
                                cursorclass=clasecursor)
