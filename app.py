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
        entry = data.get("entry",[])[0]  # Tomar el primer objeto en "entry"
        changes = entry.get("changes",[])[0]  # Tomar el primer cambio
        value = changes.get("value", {}) # Datos dentro de "value"
        objeto_messages = value.get("messages", []) # Lista de mensajes

        if objeto_messages:  # Si hay mensajes presentes
            message = objeto_messages[0]  # Tomar el primer mensaje
            numero_remitente = message.get("from")  # Número del remitente
            texto_mensaje = message.get("text", {}).get("body", "")  # Texto del mensaje
            tipo =message.get("type")
                
            #Hacer logica para extraer la informacion de interactive
            #la raiz de interactive aparentemente no es message como en text
            #revisar logica deambos para ver la diferencia y sus json
                
            agregar_mensajes_log(json.dumps(message))
                
            if tipo == "text":
                texto_mensaje = message.get("text", {}).get("body", "")
            elif tipo == "interactive":
                tipo_interactivo = message ["interactive"]["type"]
                    
                if tipo_interactivo == "button_reply":
                    texto_mensaje = message["interactive"]["button_reply"]["id"]
                        
                    
                elif tipo_interactivo == "list_reply":
                    texto_mensaje = message["interactive"]["list_reply"]["id"]
                        
                        
                        
                

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
    
    # Convertir a JSON con indentación para mejorar la legibilidad
    for registro in registros_ordenados:
        try:
            registro.texto = json.dumps(json.loads(registro.texto), indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            # Si no es un JSON válido, lo dejamos tal cual
            pass
    
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
        "Authorization": "Bearer EAANJNT5ngBABOzIXT2ZCnDxJy5ntaj5uNq8jVfAJjmLplZBP0es5QPTWyXZCFfPZA3loqRhGChYZAuIp4o38sIasRJYUNL8Hxla7lAI7tToQGKTyKiUV6i62vK1MBt32RgK26dJ6lSVUIdlDpDZAwiL4wrmIbOpcmu06DPoZAlHI8HJO2ROl6sHpTGZAnYkaD8UQbE4uiH7wA9TaY2KvLjMZAzgZAhMwZDZD"
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
    