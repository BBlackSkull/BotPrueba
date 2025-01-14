from flask import Flask, render_template,jsonify ,request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


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
def init_db():
    with app.app_context():
        db.create_all()

init_db()


    
#Funcion para ordenar los registros por fecha y hora

def ordenar_por_fecha_y_hora(registros):
    registros_ordenados = sorted(registros, key=lambda x: x.fecha_y_hora, reverse=True)
    for registro in registros_ordenados:
        print(registro.texto)  # Para verificar el orden de los registros
    return registros_ordenados


@app.route('/')
def index():
    # Obtener todos los registros de la base de datos
    registros = Log.query.all()
    registros_ordenados = ordenar_por_fecha_y_hora(registros)
    #registros_dict = [{"fecha_y_hora" : log.fecha_y_hora, "texto": log.texto}for log in registros]
    return render_template('index.html', registros=registros_ordenados)

mensajes_log =[]
# Función para agregar mensajes y guardar en la base de datos
def agregar_mensajes_log(texto):
    mensajes_log.append(texto)
    
    nuevo_registro = Log(texto=texto)  # Crear el nuevo registro
    db.session.add(nuevo_registro)    # Agregarlo a la sesión
    db.session.commit()               # Confirmar cambios


#token de veririfacion para la configuracion
TOKEN_VERIFICACION = "52660808"

@app.route('/webhook',methods=['GET','POST'])
def webhook():
    if request.method == 'GET':
        challenge = verificar_token(request)
        return challenge
    elif request.method == 'POST':
        response = recibir_mensajes(request)
        return response
    
#Verifica el token
def verificar_token(req):
    token = req.args.get('hub.verify_token')
    challenge = req.args.get('hub.challenge')
    
    if challenge and token == TOKEN_VERIFICACION:
        return challenge
    else:
        return jsonify({'error':'Token Invalido'}),401
    
def recibir_mensajes(req):
    data = req.get_json()
    print(data)  # Para verificar la estructura del JSON recibido

    try:
        # Ajuste según el formato del JSON recibido de Meta
        mensaje_texto = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
    except KeyError:
        mensaje_texto = 'Mensaje sin texto'

    agregar_mensajes_log(mensaje_texto)
    return jsonify({'message': 'EVENT_RECEIVED'})




# Main
if __name__ == '__main__':
    # Cambiar a un puerto no privilegiado si no se desea usar sudo
    app.run(host='0.0.0.0', port=5000, debug=True)
    