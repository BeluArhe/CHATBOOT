import requests
from datetime import datetime
import time
from twilio.rest import Client
import json
from enum import Enum

# Configuración inicial
CONFIG = {
    "twilio_account_sid": "TU_ACCOUNT_SID",
    "twilio_auth_token": "TU_AUTH_TOKEN",
    "twilio_whatsapp_number": "whatsapp:+14155238886",
    "landbot_url": "https://landbot.online/v3/H-3007175-KYDCK011NFEQFFB4/index.html",
    "bonita_api_url": "TU_URL_BONITA_API",
    "bonita_credentials": {"username": "tu_usuario", "password": "tu_contraseña"},
    "database_file": "clientes_db.json",
    "asesores_disponibles": ["asesor1@empresa.com", "asesor2@empresa.com", "asesor3@empresa.com"]
}

# Estados del chatbot
class ChatState(Enum):
    INICIO = 1
    MENU_PRINCIPAL = 2
    TIPOS_SALTO = 3
    REQUISITOS = 4
    PRECIOS = 5
    UBICACION = 6
    ASESOR = 7
    FIN = 8

# Inicializar cliente Twilio
twilio_client = Client(CONFIG["twilio_account_sid"], CONFIG["twilio_auth_token"])

class WhatsAppBot:
    def __init__(self):
        self.client_db = self._load_database()
        self.current_state = {}
        
    def _load_database(self):
        try:
            with open(CONFIG["database_file"], "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_database(self):
        with open(CONFIG["database_file"], "w") as f:
            json.dump(self.client_db, f, indent=2)
    
    def send_whatsapp_message(self, to_number, message):
        """Envía un mensaje a través de WhatsApp Business"""
        try:
            message = twilio_client.messages.create(
                body=message,
                from_=CONFIG["twilio_whatsapp_number"],
                to=f"whatsapp:{to_number}"
            )
            print(f"Mensaje enviado a {to_number}: {message.body}")
            return True
        except Exception as e:
            print(f"Error al enviar mensaje: {e}")
            return False
    
    def receive_whatsapp_message(self, request_data):
        """Procesa un mensaje entrante de WhatsApp"""
        from_number = request_data.get("From", "").replace("whatsapp:", "")
        message_body = request_data.get("Body", "").strip().lower()
        
        print(f"Mensaje recibido de {from_number}: {message_body}")
        
        # Inicializar estado del chat si es nuevo cliente
        if from_number not in self.client_db:
            self.client_db[from_number] = {
                "first_contact": datetime.now().isoformat(),
                "last_contact": datetime.now().isoformat(),
                "conversation": [],
                "state": ChatState.INICIO.value,
                "reserva": False
            }
            self._send_welcome_message(from_number)
        else:
            self.client_db[from_number]["last_contact"] = datetime.now().isoformat()
            self._process_message(from_number, message_body)
        
        self.client_db[from_number]["conversation"].append({
            "timestamp": datetime.now().isoformat(),
            "direction": "inbound",
            "message": message_body,
            "state": self.client_db[from_number]["state"]
        })
        
        self._save_database()
        return True
    
    def _send_welcome_message(self, to_number):
        """Envía mensaje de bienvenida"""
        welcome_msg = "¡Bienvenido! Soy el asistente virtual. ¿En qué puedo ayudarte hoy?\n\n"
        welcome_msg += "Por favor selecciona una opción:\n"
        welcome_msg += "1. Tipos de salto\n"
        welcome_msg += "2. Requisitos\n"
        welcome_msg += "3. Precios\n"
        welcome_msg += "4. Ubicación\n"
        welcome_msg += "5. Hablar con un asesor\n"
        
        self.send_whatsapp_message(to_number, welcome_msg)
        self.client_db[to_number]["state"] = ChatState.MENU_PRINCIPAL.value
    
    def _process_message(self, from_number, message):
        """Procesa el mensaje según el estado actual"""
        current_state = self.client_db[from_number]["state"]
        
        if current_state == ChatState.INICIO.value:
            self._send_welcome_message(from_number)
        
        elif current_state == ChatState.MENU_PRINCIPAL.value:
            self._handle_main_menu(from_number, message)
        
        elif current_state in [ChatState.TIPOS_SALTO.value, ChatState.REQUISITOS.value, 
                              ChatState.PRECIOS.value, ChatState.UBICACION.value]:
            self._handle_info_response(from_number, message)
        
        elif current_state == ChatState.ASESOR.value:
            self._handle_advisor_flow(from_number, message)
    
    def _handle_main_menu(self, from_number, message):
        """Maneja la selección del menú principal"""
        option_map = {
            "1": ChatState.TIPOS_SALTO,
            "2": ChatState.REQUISITOS,
            "3": ChatState.PRECIOS,
            "4": ChatState.UBICACION,
            "5": ChatState.ASESOR
        }
        
        if message in option_map:
            new_state = option_map[message]
            self.client_db[from_number]["state"] = new_state.value
            
            if new_state == ChatState.TIPOS_SALTO:
                response = "Tenemos estos tipos de salto disponibles:\n\n"
                response += "- Salto Tándem\n- Salto Libre\n- Salto Acrobático\n- Salto Nocturno\n\n"
                response += "¿Desea más información sobre alguno en particular? (Sí/No)"
                self.send_whatsapp_message(from_number, response)
            
            elif new_state == ChatState.REQUISITOS:
                response = "Requisitos para saltar:\n\n"
                response += "- Edad mínima: 18 años\n- Peso máximo: 100kg\n- Firmar consentimiento\n"
                response += "- Presentar identificación\n- No condiciones médicas graves\n\n"
                response += "¿Desea reservar ahora? (Sí/No)"
                self.send_whatsapp_message(from_number, response)
            
            elif new_state == ChatState.PRECIOS:
                response = "Nuestros precios:\n\n"
                response += "- Salto Tándem: $300\n- Salto Libre: $250\n"
                response += "- Salto Acrobático: $350\n- Salto Nocturno: $400\n\n"
                response += "¿Desea reservar ahora? (Sí/No)"
                self.send_whatsapp_message(from_number, response)
            
            elif new_state == ChatState.UBICACION:
                response = "Estamos ubicados en:\n\n"
                response += "Av. del Paracaidismo 123, Zona de Saltos\n"
                response += "Horario: 9am - 6pm de lunes a domingo\n\n"
                response += "¿Necesitas indicaciones más detalladas? (Sí/No)"
                self.send_whatsapp_message(from_number, response)
            
            elif new_state == ChatState.ASESOR:
                response = "Conectándote con un asesor...\n\n"
                asesor = self._assign_advisor(from_number)
                if asesor:
                    response += f"Te atenderá: {asesor}\n"
                    response += "Por favor describe tu consulta:"
                    self.send_whatsapp_message(from_number, response)
                else:
                    response += "No hay asesores disponibles en este momento. ¿Deseas que te contactemos más tarde? (Sí/No)"
                    self.send_whatsapp_message(from_number, response)
                    self.client_db[from_number]["state"] = ChatState.MENU_PRINCIPAL.value
        else:
            response = "Opción no válida. Por favor selecciona un número del 1 al 5:"
            self.send_whatsapp_message(from_number, response)
    
    def _handle_info_response(self, from_number, message):
        """Maneja las respuestas después de mostrar información"""
        if "sí" in message or "si" in message or "yes" in message:
            if self.client_db[from_number]["state"] in [ChatState.REQUISITOS.value, ChatState.PRECIOS.value]:
                response = "Por favor indica tu nombre completo y fecha preferida para la reserva:"
                self.client_db[from_number]["reserva"] = True
            else:
                response = "Por favor especifica qué información adicional necesitas:"
            
            self.send_whatsapp_message(from_number, response)
        else:
            response = "¿Hay algo más en lo que pueda ayudarte?\n\n"
            response += "1. Tipos de salto\n2. Requisitos\n3. Precios\n4. Ubicación\n5. Asesor"
            self.send_whatsapp_message(from_number, response)
            self.client_db[from_number]["state"] = ChatState.MENU_PRINCIPAL.value
    
    def _handle_advisor_flow(self, from_number, message):
        """Maneja el flujo de comunicación con asesor"""
        if "no" in message or "nop" in message:
            response = "Gracias por contactarnos. ¿Hay algo más en lo que pueda ayudarte?\n\n"
            response += "1. Tipos de salto\n2. Requisitos\n3. Precios\n4. Ubicación\n5. Asesor"
            self.send_whatsapp_message(from_number, response)
            self.client_db[from_number]["state"] = ChatState.MENU_PRINCIPAL.value
        else:
            # Registrar mensaje para el asesor
            if "asesor_messages" not in self.client_db[from_number]:
                self.client_db[from_number]["asesor_messages"] = []
            
            self.client_db[from_number]["asesor_messages"].append({
                "timestamp": datetime.now().isoformat(),
                "message": message
            })
            
            # Aquí integrarías con Bonita para notificar al asesor
            self._notify_advisor(from_number, message)
            
            response = "Mensaje recibido. El asesor te responderá pronto. ¿Quieres agregar algo más?"
            self.send_whatsapp_message(from_number, response)
    
    def _assign_advisor(self, from_number):
        """Asigna un asesor disponible"""
        # Implementar lógica de asignación real con Bonita
        if CONFIG["asesores_disponibles"]:
            return CONFIG["asesores_disponibles"][0]
        return None
    
    def _notify_advisor(self, from_number, message):
        """Notifica al asesor sobre un nuevo mensaje"""
        # Implementar integración con Bonita
        print(f"Notificando al asesor sobre mensaje de {from_number}: {message}")
        return True
    
    def run_periodic_tasks(self):
        """Tareas periódicas como recordatorios o seguimientos"""
        while True:
            now = datetime.now()
            print(f"Ejecutando tareas periódicas a las {now}")
            
            # Verificar reservas pendientes
            for number, data in self.client_db.items():
                if data.get("reserva", False) and "reserva_confirmada" not in data:
                    self.send_whatsapp_message(number, "Recordatorio: ¿Deseas confirmar tu reserva?")
            
            time.sleep(3600)  # Esperar 1 hora entre ejecuciones

if __name__ == "__main__":
    bot = WhatsAppBot()
    
    # Para uso con webhook (ejemplo usando Flask)
    from flask import Flask, request
    
    app = Flask(__name__)
    
    @app.route("/whatsapp-webhook", methods=["POST"])
    def webhook():
        bot.receive_whatsapp_message(request.form)
        return "", 200
    
    # Iniciar tareas periódicas en segundo plano
    import threading
    periodic_thread = threading.Thread(target=bot.run_periodic_tasks, daemon=True)
    periodic_thread.start()
    
    app.run(port=5000)