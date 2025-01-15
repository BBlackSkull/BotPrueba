from flask import Flask, render_template,jsonify ,request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json


app = Flask(__name__)

# Configuración de la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de la tabla
class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_y_hora = db.Column(db.DateTime, default=datetime.now)
    texto = db.Column(db.TEXT)

# Crear tabla si no existe
with app.app_context():
    db.create_all()


    
#Funcion para ordenar los registros por fecha y hora

def ordenar_por_fecha_y_hora(registros):
    return sorted(registros, key=lambda x: x.fecha_y_hora,reverse=True)



mensajes_log =[]

# Función para agregar mensajes y guardar en la base de datos
#def agregar_mensajes_log(texto):
#    mensajes_log.append(texto)
    
#    nuevo_registro = Log(texto=texto)  # Crear el nuevo registro
#    db.session.add(nuevo_registro)    # Agregarlo a la sesión
#    db.session.commit()               # Confirmar cambios

def agregar_mensajes_log(texto):
    if isinstance(texto, dict):  # Verifica si el texto es un diccionario
        texto = json.dumps(texto, ensure_ascii=False, indent=2)  # Convierte a JSON

    mensajes_log.append(texto)  # Almacena en memoria
    nuevo_registro = Log(texto=texto)  # Crea el registro en la base de datos
    try:
        db.session.add(nuevo_registro)
        db.session.commit()  # Inserta el registro en la base de datos
    except Exception as e:
        print(f"Error al guardar en la base de datos: {e}")

#token de veririfacion para la configuracion
TOKEN_VERIFICACION = "52660808"

    
#Verifica el token
def verificar_token(req):
    token = req.args.get('hub.verify_token')
    challenge = req.args.get('hub.challenge')
    
    if challenge and token == TOKEN_VERIFICACION:
        return challenge
    else:
        return jsonify({'error':'Token Invalido'}),401
    


def recibir_mensajes(req):
    try:
        
        req = request.get_json()
        entry = req['entry'][0]
        changes= entry['changes'][0]
        value = changes['value']
        objeto_mensaje = value['messages']
        
        agregar_mensajes_log(objeto_mensaje)
        
        return jsonify({'message': 'EVENT_RECEIVED'})
    
    except Exception as e:
        return jsonify({'message': 'EVENT_RECEIVED'})
    

@app.route('/')
def index():
    # Obtener todos los registros de la base de datos
    registros = Log.query.all()
    registros_ordenados = ordenar_por_fecha_y_hora(registros)
    #registros_dict = [{"fecha_y_hora" : log.fecha_y_hora, "texto": log.texto}for log in registros]
    return render_template('index.html', registros=registros_ordenados)

@app.route('/webhook',methods=['GET','POST'])
def webhook():
    if request.method == 'GET':
        challenge = verificar_token(request)
        return challenge
    elif request.method == 'POST':
        response = recibir_mensajes(request)
        return response
    
    
# Main
if __name__ == '__main__':
    # Cambiar a un puerto no privilegiado si no se desea usar sudo
    app.run(host='0.0.0.0', port=5000, debug=True)
    