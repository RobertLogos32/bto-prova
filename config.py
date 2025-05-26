import os
from dotenv import load_dotenv

# Carica variabili d'ambiente dal file .env
env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)
    print("Configurazione caricata da file .env")
else:
    print("⚠️ File .env non trovato. Utilizzare il file .env.example come riferimento.")

# Database configuration - PostgreSQL URL
DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://otpbot:9LnkweXrxhITgJDeyZfTSIE58XAT4kBK@dpg-d0q357je5dus73ebqe20-a.oregon-postgres.render.com/otp_bot_db")

# Per compatibilità con il codice esistente, manteniamo anche la configurazione separata
# ma ora useremo principalmente DATABASE_URL
DB_CONFIG = {
    'host': 'dpg-d0q357je5dus73ebqe20-a.oregon-postgres.render.com',
    'user': 'otpbot',
    'password': '9LnkweXrxhITgJDeyZfTSIE58XAT4kBK',
    'database': 'otp_bot_db',
    'port': 5432
}

# Telegram Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("⚠️ Bot token non trovato. Imposta BOT_TOKEN nel file .env")

# Converti gli ID degli admin in numeri interi
admin_ids_str = os.getenv('ADMIN_CHAT_IDS')
ADMIN_CHAT_IDS = []
if admin_ids_str:
    ADMIN_CHAT_IDS = [int(x.strip()) for x in admin_ids_str.split(',')]
if not ADMIN_CHAT_IDS:
    print("⚠️ Nessun ID admin trovato. Aggiungi ADMIN_CHAT_IDS nel file .env")

# Service codes
SERVICE_CODES = {
    'bet365': 'ie',
    'sisal': 'bmi',
    'SNAI': 'bqy',
    'Betflag': 'bmj'
}

# Phone number settings
COUNTRY_CODE = int(os.getenv('COUNTRY_CODE', '86'))  # Code per SMS-Activate (86 per Italia)

# SMS Activate API Key
SMS_ACTIVATE_API_KEY = os.getenv('SMS_ACTIVATE_API_KEY')
if not SMS_ACTIVATE_API_KEY:
    print("⚠️ API key SMS Activate non trovata. Imposta SMS_ACTIVATE_API_KEY nel file .env")