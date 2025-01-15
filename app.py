from flask import Flask, render_template,jsonify ,request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import http.client


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
        
        if objeto_mensaje:
            messages = objeto_mensaje[0]
            
            if "type" in messages:
                tipo = messages["type"]
                
                if tipo == "interactive":
                    return 0
                
                if "text" in messages:
                    text = messages["text"]["body"]
                    numero = messages ["from"]
                    
                    enviar_mensaje_whatsapp(text,numero)
                    
        
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
    

def enviar_mensaje_whatsapp(texto,number):
   
   texto =texto.lower()
   
   if "hola" in texto:
       data = {
            "messaging_product": "whatsapp",    
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Hola, como estas?. Bienvenido"
            }
        }

   else:
       data = {
            "messaging_product": "whatsapp",    
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "🚀 Hola, Gracias por comunicarte.\n \n📌Por favor, ingresa un número #️⃣ para recibir información.\n \n1️⃣. Información del Restaurante. ❔\n2️⃣. Ubicación del local. 📍\n3️⃣. Enviar carta en PDF. 📄\n4️⃣. Audio explicando el lugar. 🎧\n5️⃣. Video del local. ⏯️\n6️⃣. Hablar con el local. 🙋‍♂️\n7️⃣. Horario de Atención. 🕜 \n0️⃣. Regresar al Menú. 🕜"
            }
        }
       #Convertir el diccionario a json
       
       data = json.dumps(data)
       
       headers = {
           "Content-Type": "application/json",
           "Authorization": "Bearer EAANJNT5ngBABOzVsZByb1uhClQJ2o2ekZAjkUOpbGAZCMZBKYibvSmCsAZCSYyy34nK5rPHhOgyU4I2EyODmkxlZCwBAAidnNttK7hgh1ZBILMiXEyTPmGANLk1t9RPjkTGE5dT1VGvGXXfOW55CQfsvrADzkBZATtPZCY6IReARPZC7Ri5655RApM3pcf6c6QEX41gMJzZA0CMroPfnj4AT6CW64B5"
       }
       
       
       connection = http.client.HTTPSConnection("graph.facebook.com")
       
       try:
           connection.request("POST","/v21.0/444454825426756/messages", data, headers)
           response = connection.getresponse()
           print(response.status, response.reason)
        
       except Exception as e:
            agregar_mensajes_log(json.dumps(e))
       
       finally:
           connection.close()
       
       
    


       
# Main
if __name__ == '__main__':
    # Cambiar a un puerto no privilegiado si no se desea usar sudo
    app.run(host='0.0.0.0', port=5000, debug=True)
    