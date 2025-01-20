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
        # Obtiene el JSON del cuerpo de la solicitud
        req = request.get_json()
        mensajes = []

        # Verifica si la estructura del primer tipo de JSON (entry)
        if "entry" in req:
            entry = req['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']
            
            # Si existen mensajes en "value"
            if "messages" in value:
                objeto_mensaje = value['messages']
                
                for message in objeto_mensaje:
                    mensajes.append(message)

        # Verifica si el JSON tiene el otro formato directo de mensajes
        elif "from" in req and "type" in req:
            mensajes.append(req)

        # Procesar todos los mensajes recolectados
        for messages in mensajes:
            if "type" in messages:
                tipo = messages["type"]

                # Guardar log en la BD
                agregar_mensajes_log(json.dumps(messages))

                if tipo == "interactive":
                    tipo_interactivo = messages["interactive"]["type"]

                    if tipo_interactivo == "button_reply":
                        text = messages["interactive"]["button_reply"]["id"]
                        numero = messages["from"]

                        enviar_mensaje_whatsapp(text, numero)
                    
                    elif tipo_interactivo == "list_reply":
                        text = messages["interactive"]["list_reply"]["id"]
                        numero = messages["from"]

                        enviar_mensaje_whatsapp(text, numero)

                elif tipo == "text":
                    text = messages["text"]["body"]
                    numero = messages["from"]

                    enviar_mensaje_whatsapp(text, numero)

                    # Guardar log en la BD
                    agregar_mensajes_log(json.dumps(messages))

        return jsonify({'message': 'EVENT_RECEIVED'})
    except Exception as e:
        return jsonify({'message': 'ERROR_PROCESSING_REQUEST', 'error': str(e)})

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
    data = {}
    texto = texto.lower()

    if "hola" in texto:
        data = {
            "messaging_product": "whatsapp",    
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body":"Hola, Gracias por comunicarte para más información.\n \n📌Por favor, ingresa un número #️⃣ para recibir información.\n \n1️⃣. Información del local. ❔\n2️⃣. Ubicación del local. 📍\n3️⃣. Enviar temario en PDF. 📄\n4️⃣. Audio explicando el sitio. 🎧\n5️⃣. Video de Introducción. ⏯️\n6️⃣. Hablar con el Personal. 🙋‍♂️\n7️⃣. Horario de Atención. 🕜 \n0️⃣. Regresar al Menú. 🕜"
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
                "body": "Hola, como estas?. Bienvenido este es el Estadio Centenario "
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
                "caption": "Informe del lugar"
            }
        }
    elif "4" in texto:
        data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "audio",
            "audio": {
                "link": "https://filesamples.com/samples/audio/mp3/sample1.mp3"
            }
        }
    elif "5" in texto:
        data = {
            "messaging_product": "whatsapp",
            "to": number,
            "text": {
                "preview_url": True,
                "body": "recordido del sitio! https://youtu.be/6ULOE2tGlBM"
            }
        }
    elif "6" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type":"text",
            "text": {
                "preview_url":False,
                "body" : "En breves un representante nuestro se pondra en contacto con usted"
            }
        }
    elif "7" in texto:
        data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "📅 Horario de Atención : Lunes a Viernes. \n🕜 Horario : 9:00 am a 5:00 pm 🤓"
            }
        }
    elif "0" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Hola, Gracias por comunicarte para más información.\n \n📌Por favor, ingresa un número #️⃣ para recibir información.\n \n1️⃣. Información del local. ❔\n2️⃣. Ubicación del local. 📍\n3️⃣. Enviar temario en PDF. 📄\n4️⃣. Audio explicando el sitio. 🎧\n5️⃣. Video de Introducción. ⏯️\n6️⃣. Hablar con el Personal. 🙋‍♂️\n7️⃣. Horario de Atención. 🕜 \n0️⃣. Regresar al Menú. 🕜"
            }
        }
    elif "boton" in texto or "botón" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "interactive",
            "interactive":{
                "type": "button",
                "body":{
                    "text": "¿Confirmas tu registro?"
                },
                "footer":{
                    "text": "Selecciona una de las opciones"
                },
                "action":{
                    "buttons":[
                        {
                            "type": "reply",
                            "reply":{
                                "id":"btnsi",
                                "title":"Si"
                            }
                        },{
                            "type": "reply",
                            "reply":{
                                "id":"btnnp",
                                "title":"No"
                            }
                        },{
                            "type": "reply",
                            "reply":{
                                "id":"btnlopensare",
                                "title":"Lo pensare"
                            }
                        }
                    ]
                }
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
                "body": "Hola, Gracias por comunicarte para más información.\n \n📌Por favor, ingresa un número #️⃣ para recibir información.\n \n1️⃣. Información del local. ❔\n2️⃣. Ubicación del local. 📍\n3️⃣. Enviar temario en PDF. 📄\n4️⃣. Audio explicando el sitio. 🎧\n5️⃣. Video de Introducción. ⏯️\n6️⃣. Hablar con el Personal. 🙋‍♂️\n7️⃣. Horario de Atención. 🕜 \n0️⃣. Regresar al Menú. 🕜"
            }
        }
#Convertir el diccionario a json 
    
    data = json.dumps(data)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer EAANJNT5ngBABO2smWvMQ3G4gI0gnji7oA6FD7ZA8H7i8EZBcbWU9ps1iZAepvgHOUZBhKHmjZAFZBLd8BtHbf94ryWZCt6By87mrJLZCnUcAPx1kBIotG4BuBzZAZB6eKpQAy4S1WoKQY7cNhY2PLMbp2xSBvknEKhiwNZAlck4OikHn2fD9n63hbK5fwwA4TXpYtANu2ZBOUcYoBZCJko6zbXYQZBc6fQ"
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
    