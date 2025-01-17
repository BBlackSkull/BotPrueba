from flask import Flask, render_template,jsonify ,request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import requests
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
        data = req.get_json()  # Convertir la solicitud JSON
        print(json.dumps(data, indent=4))  # Imprimir el JSON recibido para depuración

        # Navegar por el JSON para obtener los datos deseados
        entry = data["entry"][0]  # Tomar el primer objeto en "entry"
        changes = entry["changes"][0]  # Tomar el primer cambio
        value = changes["value"]  # Datos dentro de "value"
        messages = value("messages")  # Lista de mensajes

        if messages:  # Si hay mensajes presentes
            message = messages[0]  # Tomar el primer mensaje
            numero_remitente = message.get("from")  # Número del remitente
            texto_mensaje = message.get("text", {}).get("body", "")  # Texto del mensaje

            print(f"Número del remitente: {numero_remitente}")
            print(f"Texto del mensaje: {texto_mensaje}")

            # Enviar una respuesta según el contenido del mensaje
            enviar_mensaje_whatsapp(texto_mensaje, numero_remitente)

            # Guardar en la base de datos para registro
            agregar_mensajes_log(f"Mensaje recibido de {numero_remitente}: {texto_mensaje}")

        return jsonify({'message': 'EVENT_RECEIVED'})

    except KeyError as e:
        print(f"Clave faltante en el JSON: {e}")
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
   elif "1" in texto:
       data ={
           "messaging_product": "whatsapp",    
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Hola, como estas?. Bienvenido este es el restaurante... "
            }
       }
   elif "2" in texto:
       data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "location",
            "location": {
                "latitude": -34.89469,
                "longitude": -56.1539,
                "name": "Estadio Centenario",
                "address": "Montevideo, Uruguay"
            }
        }
   elif "3" in texto:
       data ={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to":number,
            "type": "document",
            "document": {
                "link": "https://www.icat.unam.mx/wp-content/uploads/2022/09/Vigilancia_Tecnologica_en_Ciberseguridad_Boletin.pdf",
                "caption": "Carta"
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
           "Authorization": "Bearer EAANJNT5ngBABOxjgJ6ReknX1C3mmrZCZBT4vECZBDFOd0TbQMVFBfj4eJ5vlE8XrwqkooGo90YIDIz1gpaTZCKWioKnjXrZAwFsrpwFLY1aCvRrpZBG9xPTzXEQZCMl8BD3esSSH0MBlf2VhbPgGxZCJod8n7f4cOmVYGxPbnwZAmjWZBCZCyYZAkA0L8dZBmc6IZAy4ZCkgiCYBpBUZCtX4SkT0pUMTEHfoggZDZD"
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
    