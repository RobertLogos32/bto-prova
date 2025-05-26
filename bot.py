# File: bot.py

import telebot
from telebot import types
import threading
import time
from models import Database, User, NumberRequest, PhoneNumber, Message
from phone_service import PhoneService
from message_listener import MessageListener
from config import BOT_TOKEN, ADMIN_CHAT_IDS, SERVICE_CODES

class OTPBot:
    def __init__(self, token=BOT_TOKEN):
        self.bot = telebot.TeleBot(token)
        self.db = Database()
        self.user_model = User(self.db)
        self.number_request_model = NumberRequest(self.db)
        self.phone_number_model = PhoneNumber(self.db)
        self.message_model = Message(self.db)
        self.phone_service = PhoneService()
        
        # Keep track of user states for conversation flow
        self.user_state = {}
        
        # Setup message handlers
        self.setup_handlers()
        
        # Initialize and start message listener
        self.message_listener = MessageListener(self)
        
    def setup_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def start(message):
            self.handle_start(message)
        
        @self.bot.message_handler(commands=['admin'])
        def admin(message):
            self.handle_admin(message)
        
        @self.bot.message_handler(commands=['request'])
        def request(message):
            self.handle_request(message)
            
        @self.bot.message_handler(commands=['status'])
        def status(message):
            self.handle_status(message)
            
        @self.bot.message_handler(commands=['help'])
        def help(message):
            self.handle_help(message)
            
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            self.process_callback(call)
            
        @self.bot.message_handler(content_types=['text'])
        def handle_text(message):
            self.process_text_message(message)
    
    def handle_start(self, message):
        chat_id = message.chat.id
        user = self.user_model.get_user(chat_id)
        
        if not user:
            # New user, register them
            self.user_model.create_user(
                chat_id,
                message.from_user.username,
                message.from_user.first_name,
                message.from_user.last_name
            )
            
            self.bot.send_message(chat_id, 
                "👋 Benvenuto al servizio di Bot OTP!\n\n"
                "La tua registrazione è in attesa di approvazione da un amministratore.\n"
                "Riceverai una notifica quando il tuo account sarà stato approvato.")
            
            # Notify admins about new user
            for admin_id in ADMIN_CHAT_IDS:
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(
                    types.InlineKeyboardButton("✅ Approva", callback_data=f"approve_user_{chat_id}"),
                    types.InlineKeyboardButton("❌ Nega", callback_data=f"deny_user_{chat_id}")
                )
                
                self.bot.send_message(admin_id, 
                    f"🆕 Nuovo utente registrato!\n\n"
                    f"ID: {chat_id}\n"
                    f"Username: @{message.from_user.username if message.from_user.username else 'Non impostato'}\n"
                    f"Nome: {message.from_user.first_name} {message.from_user.last_name if message.from_user.last_name else ''}\n\n"
                    f"Vuoi approvare questo utente?",
                    reply_markup=keyboard)
        else:
            # Existing user
            if user['status'] == 'approved':
                self.bot.send_message(chat_id, 
                    "👋 Bentornato al servizio di Bot OTP!\n\n"
                    "Puoi richiedere un nuovo numero usando il comando /request")
            elif user['status'] == 'pending':
                self.bot.send_message(chat_id, 
                    "👋 Bentornato!\n\n"
                    "La tua registrazione è ancora in attesa di approvazione da un amministratore.")
            else:  # denied
                self.bot.send_message(chat_id, 
                    "⚠️ Siamo spiacenti, ma la tua richiesta di accesso è stata negata.")
    
    def handle_admin(self, message):
        chat_id = message.chat.id
        
        # Check if user is an admin
        if chat_id in ADMIN_CHAT_IDS:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton("👤 Utenti in attesa", callback_data="list_pending_users"),
                types.InlineKeyboardButton("📱 Richieste di numeri", callback_data="list_pending_requests")
            )
            
            self.bot.send_message(chat_id, "🔐 Pannello di amministrazione", reply_markup=keyboard)
        else:
            self.bot.send_message(chat_id, "⛔ Non hai i permessi per accedere al pannello di amministrazione.")
    
    def handle_request(self, message):
        chat_id = message.chat.id
        user = self.user_model.get_user(chat_id)
        
        if not user or user['status'] != 'approved':
            self.bot.send_message(chat_id, 
                "⚠️ Non puoi richiedere numeri. Assicurati che il tuo account sia stato approvato.")
            return
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("✅ Sì", callback_data="confirm_request"),
                    types.InlineKeyboardButton("❌ No", callback_data="cancel_request"))
        
        self.bot.send_message(chat_id, "Vuoi richiedere un nuovo numero?", reply_markup=keyboard)
    
    def handle_status(self, message):
        chat_id = message.chat.id
        user = self.user_model.get_user(chat_id)
        
        if not user:
            self.bot.send_message(chat_id, "⚠️ Non risulti registrato nel sistema. Usa /start per registrarti.")
            return
        
        status_text = {
            'pending': "⏳ In attesa di approvazione",
            'approved': "✅ Approvato",
            'denied': "❌ Negato"
        }
        
        # Get user's phone numbers
        query = """
        SELECT pn.number, pn.service_code, nr.service, nr.requested_at, pn.assigned_at
        FROM phone_numbers pn
        JOIN number_requests nr ON pn.request_id = nr.id
        WHERE nr.user_id = %s
        ORDER BY pn.assigned_at DESC
        """
        numbers = self.db.fetch_all(query, (user['id'],))
        
        msg = f"👤 *Stato utente*: {status_text.get(user['status'], 'Sconosciuto')}\n\n"
        
        if numbers:
            msg += "*📱 I tuoi numeri:*\n"
            for num in numbers:
                msg += f"- {num['number']} ({num['service']})\n"
                msg += f"  Assegnato: {num['assigned_at'].strftime('%d/%m/%Y %H:%M')}\n"
        else:
            if user['status'] == 'approved':
                msg += "Non hai ancora richiesto numeri. Usa /request per richiederne uno."
        
        self.bot.send_message(chat_id, msg, parse_mode="Markdown")
    
    def handle_help(self, message):
        chat_id = message.chat.id
        
        help_text = (
            "🔍 *Comandi disponibili:*\n\n"
            "/start - Registrazione o accesso al bot\n"
            "/request - Richiedi un nuovo numero\n"
            "/status - Controlla lo stato del tuo account e dei tuoi numeri\n"
            "/help - Mostra questo messaggio di aiuto\n\n"
            
            "📱 *Servizi disponibili:*\n"
        )
        
        for service, code in SERVICE_CODES.items():
            help_text += f"- {service} ({code})\n"
        
        help_text += "\n⚙️ Per problemi o assistenza, contatta un amministratore."
        
        self.bot.send_message(chat_id, help_text, parse_mode="Markdown")
    
    def process_callback(self, call):
        chat_id = call.message.chat.id
        callback_data = call.data
        
        if callback_data.startswith("approve_user_"):
            user_id = int(callback_data.split("_")[-1])
            self.approve_user(chat_id, user_id)
            
        elif callback_data.startswith("deny_user_"):
            user_id = int(callback_data.split("_")[-1])
            self.deny_user(chat_id, user_id)
            
        elif callback_data == "confirm_request":
            self.create_number_request(chat_id)
            
        elif callback_data == "cancel_request":
            self.bot.send_message(chat_id, "❌ Richiesta annullata.")
            
        elif callback_data.startswith("select_service_"):
            service = callback_data.split("_")[-1]
            self.select_service(chat_id, service)
            
        elif callback_data.startswith("approve_request_"):
            request_id = int(callback_data.split("_")[-1])
            self.approve_number_request(chat_id, request_id)
            
        elif callback_data.startswith("deny_request_"):
            request_id = int(callback_data.split("_")[-1])
            self.deny_number_request(chat_id, request_id)
            
        elif callback_data == "list_pending_users":
            self.list_pending_users(chat_id)
            
        elif callback_data == "list_pending_requests":
            self.list_pending_requests(chat_id)
        
        # Remove the loading animation
        self.bot.answer_callback_query(call.id)
    
    def process_text_message(self, message):
        chat_id = message.chat.id
        text = message.text
        
        # Check if user is in a state that expects input
        state = self.user_state.get(chat_id)
        
        if not state:
            # No specific state, send help message
            self.bot.send_message(chat_id, 
                "Non ho capito cosa intendi. Usa /help per vedere i comandi disponibili.")
    
    def approve_user(self, admin_id, user_id):
        if admin_id not in ADMIN_CHAT_IDS:
            return
        
        user = self.user_model.get_user(user_id)
        if user and user['status'] == 'pending':
            self.user_model.update_status(user_id, 'approved')
            
            # Notify the user
            self.bot.send_message(user_id, 
                "✅ Il tuo account è stato approvato!\n"
                "Ora puoi richiedere numeri usando il comando /request")
            
            # Confirm to admin
            self.bot.send_message(admin_id, f"✅ Utente {user_id} approvato con successo.")
        else:
            self.bot.send_message(admin_id, f"⚠️ Impossibile approvare utente {user_id}, utente non trovato o non in attesa.")
    
    def deny_user(self, admin_id, user_id):
        if admin_id not in ADMIN_CHAT_IDS:
            return
        
        user = self.user_model.get_user(user_id)
        if user and user['status'] == 'pending':
            self.user_model.update_status(user_id, 'denied')
            
            # Notify the user
            self.bot.send_message(user_id, 
                "❌ Siamo spiacenti, ma la tua richiesta di accesso è stata negata.")
            
            # Confirm to admin
            self.bot.send_message(admin_id, f"❌ Utente {user_id} negato con successo.")
        else:
            self.bot.send_message(admin_id, f"⚠️ Impossibile negare utente {user_id}, utente non trovato o non in attesa.")
    
    def create_number_request(self, chat_id):
        user = self.user_model.get_user(chat_id)
        if not user or user['status'] != 'approved':
            self.bot.send_message(chat_id, "⚠️ Non puoi richiedere numeri.")
            return
        
        # Ask which service they want
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        buttons = []
        for service in SERVICE_CODES.keys():
            buttons.append(types.InlineKeyboardButton(service, callback_data=f"select_service_{service}"))
        keyboard.add(*buttons)
        
        self.bot.send_message(chat_id, "📱 Per quale servizio desideri un numero?", reply_markup=keyboard)
    
    def select_service(self, chat_id, service):
        user = self.user_model.get_user(chat_id)
        if not user or user['status'] != 'approved':
            self.bot.send_message(chat_id, "⚠️ Non puoi richiedere numeri.")
            return
        
        if not self.phone_service.validate_service(service):
            self.bot.send_message(chat_id, f"⚠️ Servizio {service} non valido.")
            return
        
        # Create the request in the database
        request_id = self.number_request_model.create_request(user['id'], service)
        
        # Notify user that request is pending
        self.bot.send_message(chat_id, 
            f"📱 La tua richiesta per un numero {service} è stata inviata.\n"
            f"Un amministratore la esaminerà a breve.")
        
        # Notify admins
        for admin_id in ADMIN_CHAT_IDS:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton("✅ Approva", callback_data=f"approve_request_{request_id}"),
                types.InlineKeyboardButton("❌ Nega", callback_data=f"deny_request_{request_id}")
            )
            
            self.bot.send_message(admin_id, 
                f"🆕 Nuova richiesta di numero!\n\n"
                f"Utente: {chat_id} (@{user['username'] if user['username'] else 'No username'})\n"
                f"Servizio: {service}\n\n"
                f"Vuoi approvare questa richiesta?",
                reply_markup=keyboard)
    
    def approve_number_request(self, admin_id, request_id):
        if admin_id not in ADMIN_CHAT_IDS:
            return
        
        # Get the request details
        request = self.number_request_model.get_request(request_id)
        if not request or request['status'] != 'pending':
            self.bot.send_message(admin_id, "⚠️ Richiesta non trovata o non in attesa.")
            return
        
        # Get a real phone number from SMS Activate
        service_code = self.phone_service.get_service_code(request['service'])
        if not service_code:
            self.bot.send_message(admin_id, f"⚠️ Servizio {request['service']} non valido.")
            return
            
        # Send wait message to admin
        self.bot.send_message(admin_id, f"⏳ Richiesta in elaborazione, sto ottenendo un numero per {request['service']}...")
        
        # Try to get a real number from SMS Activate
        activation_id, phone_number = self.phone_service.get_number_for_service(request['service'])
        
        if not phone_number:
            self.bot.send_message(admin_id, f"⚠️ Impossibile ottenere un numero per {request['service']}. Servizio non disponibile al momento.")
            return
        
        # Update request status
        self.number_request_model.update_status(request_id, 'approved')
        
        # Assign the number to the user (store activation_id)
        self.phone_number_model.assign_number(request_id, phone_number, service_code, activation_id)
        
        # Get user details
        query = "SELECT telegram_id FROM users WHERE id = %s"
        user = self.db.fetch_one(query, (request['user_id'],))
        
        # Notify the user
        self.bot.send_message(user['telegram_id'], 
            f"✅ La tua richiesta per un numero {request['service']} è stata approvata!\n\n"
            f"📱 Il tuo numero è: {phone_number}\n\n"
            f"Riceverai automaticamente i messaggi inviati a questo numero.")
        
        # Confirm to admin
        self.bot.send_message(admin_id, 
            f"✅ Numero {phone_number} ({request['service']}) assegnato con successo.")
    
    def deny_number_request(self, admin_id, request_id):
        if admin_id not in ADMIN_CHAT_IDS:
            return
        
        # Get the request details
        request = self.number_request_model.get_request(request_id)
        if not request or request['status'] != 'pending':
            self.bot.send_message(admin_id, "⚠️ Richiesta non trovata o non in attesa.")
            return
        
        # Update request status
        self.number_request_model.update_status(request_id, 'denied')
        
        # Get user details
        query = "SELECT telegram_id FROM users WHERE id = %s"
        user = self.db.fetch_one(query, (request['user_id'],))
        
        # Notify the user
        self.bot.send_message(user['telegram_id'], 
            f"❌ La tua richiesta per un numero {request['service']} è stata negata.")
        
        # Confirm to admin
        self.bot.send_message(admin_id, 
            f"❌ Richiesta numero per {request['service']} negata con successo.")
    
    def list_pending_users(self, admin_id):
        if admin_id not in ADMIN_CHAT_IDS:
            return
        
        # Get all pending users
        pending_users = self.user_model.get_all_pending_users()
        
        if not pending_users:
            self.bot.send_message(admin_id, "📝 Non ci sono utenti in attesa di approvazione.")
            return
        
        for user in pending_users:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton("✅ Approva", callback_data=f"approve_user_{user['telegram_id']}"),
                types.InlineKeyboardButton("❌ Nega", callback_data=f"deny_user_{user['telegram_id']}")
            )
            
            self.bot.send_message(admin_id, 
                f"👤 Utente in attesa:\n\n"
                f"ID: {user['telegram_id']}\n"
                f"Username: @{user['username'] if user['username'] else 'Non impostato'}\n"
                f"Nome: {user['first_name']} {user['last_name'] if user['last_name'] else ''}\n"
                f"Registrato il: {user['created_at'].strftime('%d/%m/%Y %H:%M')}\n\n"
                f"Vuoi approvare questo utente?",
                reply_markup=keyboard)
    
    def list_pending_requests(self, admin_id):
        if admin_id not in ADMIN_CHAT_IDS:
            return
        
        # Get all pending requests
        pending_requests = self.number_request_model.get_all_pending_requests()
        
        if not pending_requests:
            self.bot.send_message(admin_id, "📝 Non ci sono richieste di numeri in attesa.")
            return
        
        for request in pending_requests:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton("✅ Approva", callback_data=f"approve_request_{request['id']}"),
                types.InlineKeyboardButton("❌ Nega", callback_data=f"deny_request_{request['id']}")
            )
            
            self.bot.send_message(admin_id, 
                f"📱 Richiesta numero in attesa:\n\n"
                f"Utente: {request['telegram_id']} (@{request['username'] if request['username'] else 'No username'})\n"
                f"Servizio: {request['service']}\n"
                f"Richiesta il: {request['requested_at'].strftime('%d/%m/%Y %H:%M')}\n\n"
                f"Vuoi approvare questa richiesta?",
                reply_markup=keyboard)
    
    def send_message(self, chat_id, text, parse_mode=None, reply_markup=None):
        """Wrapper for sending messages"""
        try:
            self.bot.send_message(chat_id, text, parse_mode=parse_mode, reply_markup=reply_markup)
        except Exception as e:
            print(f"Error sending message to {chat_id}: {e}")
    
    def start_polling(self):
        """Start the bot polling"""
        self.message_listener.start()
        
        try:
            print("Bot started polling...")
            self.bot.polling(none_stop=True, interval=1)
        except Exception as e:
            print(f"Polling error: {e}")
        finally:
            self.message_listener.stop()